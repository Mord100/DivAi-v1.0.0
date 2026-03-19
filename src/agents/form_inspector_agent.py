"""
DivAi — Form Inspector Agent

WHAT THIS AGENT DOES:
  Given a website URL it:
    1. Navigates to the site's signup / register page
    2. Extracts every form field (id, name, type, label, placeholder, required)
    3. Returns a structured field map the UI can render as a sign-up form

  A second function takes that field map + user-provided values, fills the
  form via Playwright, submits it, and captures the resulting auth cookies.
  Those cookies are then passed to the Ingestion Agent for authenticated scraping.

WHY THIS IS LEGITIMATE:
  - Inspecting form field IDs is reading public HTML (view-source equivalent)
  - The user provides their own real credentials — we never fabricate an identity
  - Playwright filling a form is what a browser extension or password manager does
  - The resulting cookie belongs to the user's own account

CONCEPT: Playwright Browser Context
--------------------------------------
A BrowserContext is an isolated browser session — it has its own cookies, local
storage, and cache. Think of it as a fresh private window. We use it here to:
  1. Inspect a signup form (one context, no cookies)
  2. Fill and submit the form as the user (same context, captures the auth cookie set
     by the server after successful registration)

CONCEPT: page.evaluate()
--------------------------
page.evaluate() lets us run JavaScript directly inside the page.
We use it to query the live DOM for form field metadata — far more reliable
than trying to parse HTML with regex, because the JS can follow label[for] links,
read aria-label attributes, and handle dynamically rendered React/Vue forms.
"""

import asyncio
import json
from typing import Optional
from playwright.async_api import async_playwright, Page


# Common patterns for finding the signup page from a homepage
SIGNUP_LINK_SELECTORS = [
    'a[href*="signup"]',
    'a[href*="sign-up"]',
    'a[href*="register"]',
    'a[href*="create-account"]',
    'a[href*="get-started"]',
    'a[href*="join"]',
    'a:text-is("Sign up")',
    'a:text-is("Sign Up")',
    'a:text-is("Create account")',
    'a:text-is("Create Account")',
    'a:text-is("Get started")',
    'a:text-is("Get Started")',
    'a:text-is("Register")',
    'button:text-is("Sign up")',
    'button:text-is("Get started")',
]

# Fields we always ignore — they add noise without being user-fillable
IGNORED_FIELD_TYPES = {"hidden", "submit", "button", "image", "reset", "file"}


# ---------------------------------------------------------------------------
# DOM extraction — runs inside the browser
# ---------------------------------------------------------------------------

EXTRACT_FIELDS_JS = """
() => {
    const results = [];
    const inputs = document.querySelectorAll('input, select, textarea');

    inputs.forEach(el => {
        const type = (el.type || '').toLowerCase();
        // Skip hidden, submit, button etc.
        const skip = ['hidden','submit','button','image','reset','file'];
        if (skip.includes(type)) return;

        // Find the human-readable label for this field
        let label = null;

        // 1. <label for="fieldId">
        if (el.id) {
            const lbl = document.querySelector(`label[for="${el.id}"]`);
            if (lbl) label = lbl.textContent.trim();
        }
        // 2. aria-label attribute
        if (!label) label = el.getAttribute('aria-label') || null;
        // 3. aria-labelledby
        if (!label) {
            const lblId = el.getAttribute('aria-labelledby');
            if (lblId) {
                const lbl = document.getElementById(lblId);
                if (lbl) label = lbl.textContent.trim();
            }
        }
        // 4. placeholder as last resort
        if (!label && el.placeholder) label = el.placeholder;
        // 5. parent label (implicit association)
        if (!label) {
            const parent = el.closest('label');
            if (parent) label = parent.textContent.replace(el.value || '', '').trim();
        }

        results.push({
            tag:          el.tagName.toLowerCase(),
            type:         type || 'text',
            id:           el.id || null,
            name:         el.name || null,
            placeholder:  el.placeholder || null,
            label:        label,
            required:     el.required || false,
            autocomplete: el.autocomplete || null,
            // For <select> — return options so the UI can render a dropdown
            options: el.tagName === 'SELECT'
                ? Array.from(el.options).map(o => ({ value: o.value, text: o.text }))
                : null,
        });
    });

    // Also find the submit button selector so we can click it later
    // Note: :text() is Playwright-only — not valid in native querySelector.
    // So we first try standard CSS, then fall back to text-content matching.
    const SUBMIT_TEXTS = ['sign up', 'create account', 'register', 'continue', 'get started', 'submit', 'join'];
    let submitBtn = document.querySelector('button[type="submit"], input[type="submit"]');
    if (!submitBtn) {
        submitBtn = Array.from(document.querySelectorAll('button')).find(b =>
            SUBMIT_TEXTS.some(t => b.textContent.trim().toLowerCase().includes(t))
        ) || null;
    }
    const submitSelector = submitBtn
        ? (submitBtn.id ? `#${submitBtn.id}` : submitBtn.getAttribute('data-testid')
            ? `[data-testid="${submitBtn.getAttribute('data-testid')}"]`
            : 'button[type="submit"]')
        : 'button[type="submit"]';

    return { fields: results, submit_selector: submitSelector };
}
"""


# ---------------------------------------------------------------------------
# Step 1 — Find the signup URL and extract field map
# ---------------------------------------------------------------------------

async def inspect_signup_form(base_url: str) -> dict:
    """
    Navigate to a website, find the signup page, and return the form field map.

    Returns:
        {
            "signup_url":      str,                     # URL of the signup page found
            "fields":          list[dict],              # all fillable form fields
            "submit_selector": str,                     # CSS selector for the submit button
            "screenshot_b64":  str | None,              # base64 PNG for preview (optional)
            "error":           str | None,
        }
    """
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            )
        )
        page = await context.new_page()

        try:
            # Navigate to the homepage
            await page.goto(base_url, wait_until="domcontentloaded", timeout=20_000)
            await page.wait_for_timeout(1500)

            # Try to find and click a "Sign up" link
            found_signup = False
            for selector in SIGNUP_LINK_SELECTORS:
                try:
                    el = await page.query_selector(selector)
                    if el:
                        await el.click()
                        await page.wait_for_load_state("domcontentloaded", timeout=8_000)
                        await page.wait_for_timeout(1200)
                        found_signup = True
                        break
                except Exception:
                    continue

            # If no link found, try common signup URL patterns directly
            if not found_signup:
                from urllib.parse import urlparse
                parsed = urlparse(base_url)
                root = f"{parsed.scheme}://{parsed.netloc}"
                for path in ["/signup", "/sign-up", "/register", "/create-account", "/join"]:
                    try:
                        resp = await page.goto(root + path, wait_until="domcontentloaded", timeout=8_000)
                        if resp and resp.status < 400:
                            await page.wait_for_timeout(1000)
                            found_signup = True
                            break
                    except Exception:
                        continue

            signup_url = page.url

            # Extract form fields from the live DOM
            result = await page.evaluate(EXTRACT_FIELDS_JS)
            fields = result.get("fields", [])
            submit_selector = result.get("submit_selector", "button[type='submit']")

            return {
                "signup_url": signup_url,
                "fields": fields,
                "submit_selector": submit_selector,
                "found_signup_link": found_signup,
                "error": None,
            }

        except Exception as e:
            return {
                "signup_url": page.url if page else base_url,
                "fields": [],
                "submit_selector": "button[type='submit']",
                "found_signup_link": False,
                "error": str(e),
            }
        finally:
            await browser.close()


# ---------------------------------------------------------------------------
# Step 2 — Fill the form with user credentials and capture auth cookies
# ---------------------------------------------------------------------------

async def fill_and_capture(
    signup_url: str,
    field_values: dict,          # { field_id_or_name: value }
    submit_selector: str = "button[type='submit']",
    wait_for_redirect: bool = True,
) -> dict:
    """
    Fill in a signup form with the user's own credentials and capture the
    resulting auth cookies.

    Args:
        signup_url:      The URL of the signup page (from inspect_signup_form)
        field_values:    Mapping of field id/name → value to fill in
                         e.g. {"email": "me@example.com", "password": "mypassword"}
        submit_selector: CSS selector for the submit button
        wait_for_redirect: If True, wait for navigation after submit (most flows
                           redirect to a dashboard on success)

    Returns:
        {
            "success":    bool,
            "cookies":    list[dict],   # all cookies after submission
            "auth_cookie": dict | None, # the most likely session/auth cookie
            "final_url":  str,          # URL after redirect
            "error":      str | None,
        }
    """
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            )
        )
        page = await context.new_page()

        try:
            await page.goto(signup_url, wait_until="domcontentloaded", timeout=20_000)
            await page.wait_for_timeout(1000)

            # Fill each field
            for field_key, value in field_values.items():
                # Try by id first, then name attribute
                selector = f'#{field_key}' if field_key else None
                filled = False

                if selector:
                    try:
                        el = await page.query_selector(selector)
                        if el:
                            await el.fill(str(value))
                            filled = True
                    except Exception:
                        pass

                if not filled:
                    # Try by name attribute
                    try:
                        el = await page.query_selector(f'[name="{field_key}"]')
                        if el:
                            await el.fill(str(value))
                    except Exception:
                        pass

            await page.wait_for_timeout(400)

            # Submit the form
            if wait_for_redirect:
                async with page.expect_navigation(timeout=15_000, wait_until="domcontentloaded"):
                    await page.click(submit_selector)
            else:
                await page.click(submit_selector)
                await page.wait_for_timeout(3000)

            final_url = page.url
            all_cookies = await context.cookies()

            # Heuristic: the auth cookie is usually the one with the longest value
            # and a name containing "token", "session", "auth", or "jwt"
            auth_keywords = {"token", "session", "auth", "jwt", "access", "sid", "user"}
            auth_cookie = None
            for c in all_cookies:
                if any(kw in c["name"].lower() for kw in auth_keywords):
                    auth_cookie = c
                    break
            # Fallback: longest cookie value (usually the session token)
            if not auth_cookie and all_cookies:
                auth_cookie = max(all_cookies, key=lambda c: len(c.get("value", "")))

            return {
                "success": True,
                "cookies": all_cookies,
                "auth_cookie": auth_cookie,
                "final_url": final_url,
                "error": None,
            }

        except Exception as e:
            return {
                "success": False,
                "cookies": [],
                "auth_cookie": None,
                "final_url": page.url if page else signup_url,
                "error": str(e),
            }
        finally:
            await browser.close()


# ---------------------------------------------------------------------------
# CLI — quick test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    url = sys.argv[1] if len(sys.argv) > 1 else "https://linear.app"

    print(f"\nInspecting signup form for: {url}\n{'='*60}")
    result = asyncio.run(inspect_signup_form(url))

    if result["error"]:
        print(f"Error: {result['error']}")
    else:
        print(f"Signup URL : {result['signup_url']}")
        print(f"Found link : {result['found_signup_link']}")
        print(f"Submit btn : {result['submit_selector']}")
        print(f"\nFields ({len(result['fields'])}):")
        for f in result["fields"]:
            label = f.get("label") or f.get("placeholder") or "(no label)"
            ident = f.get("id") or f.get("name") or "(no id)"
            print(f"  [{f['type']:12}]  id/name: {ident:30}  label: {label}")
