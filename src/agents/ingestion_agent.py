"""
DivAi — Ingestion Agent (Phase 1, Week 1)

WHAT THIS AGENT DOES:
  Visits a target website using a real browser (Playwright), captures:
    1. The full DOM (page structure as JSON)
    2. All network requests the page makes (APIs, third-party calls)
    3. JavaScript globals (framework data like Next.js hydration state)
  Returns a raw_intelligence dict that feeds into the Analysis Agent.

WHERE IT FITS IN DIVAI:
  Layer 1 — Ingestion Layer (see Architecture doc)
  It is the FIRST node in the LangGraph pipeline.
  No other agent can run without its output.

CONCEPT: async/await
  Playwright is asynchronous — it runs browser operations without blocking.
  'async def' means this function can be paused while waiting (e.g. for a page to load).
  'await' means "pause here and wait for this operation to finish".
  Think of it like placing an order at a restaurant:
    - Without async: you stand at the counter waiting until the food is ready
    - With async: you sit down, the waiter notifies you when it's ready
"""

import asyncio
import json
import re
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright, Page, BrowserContext


# ---------------------------------------------------------------------------
# Core scrape function
# ---------------------------------------------------------------------------

async def scrape_website(url: str, depth: str = "surface") -> dict:
    """
    Launch a headless browser, visit the URL, and collect intelligence.

    Args:
        url:   The target website URL (e.g. 'https://stripe.com')
        depth: 'surface' = DOM + network only
               'deep'    = also extract JS globals + linked pages
               'both'    = everything

    Returns:
        A dict with keys: dom, network_log, js_globals, metadata, tech_signals

    CONCEPT: Headless Browser
      A headless browser is a full browser (Chromium) that runs without
      displaying a window. It executes JavaScript, loads CSS, fires events —
      exactly like a real browser — but invisibly in the background.
      This is what lets us capture the *real* page, not just the raw HTML.
    """

    print(f"[Ingestion] Starting scrape: {url} (depth={depth})")

    async with async_playwright() as playwright:
        # Launch Chromium in headless mode (no visible window)
        browser = await playwright.chromium.launch(headless=True)

        # CONCEPT: Browser Context
        # A "context" is like a private browsing session — clean cookies,
        # no stored state. We create one per scrape so websites can't
        # detect we're the same agent visiting repeatedly.
        context = await browser.new_context(
            # Appear as a normal user, not a bot
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            # Standard desktop viewport
            viewport={"width": 1280, "height": 720},
        )

        # Collect all network requests in this list
        network_log = []

        # CONCEPT: Event Listeners in Playwright
        # Playwright lets us "listen" to browser events before they happen.
        # context.on("request", handler) fires our function for EVERY request
        # the page makes — including background API calls, image loads, analytics.
        # This is how we intercept the website's "phone calls".
        context.on("request", lambda req: _on_request(req, network_log))

        page = await context.new_page()

        # Navigate to the URL and wait until no more network activity
        # "networkidle" = wait until there are no requests for 500ms
        # This ensures all async data-fetching has completed
        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
        except Exception as e:
            print(f"[Ingestion] Warning: page load issue — {e}. Proceeding with partial data.")

        # --- Capture DOM ---
        dom_data = await _extract_dom(page)

        # --- Capture JS globals (deep/both only) ---
        js_globals = {}
        if depth in ("deep", "both"):
            js_globals = await _extract_js_globals(page)

        # --- Extract tech signals from DOM ---
        # CONCEPT: Signal Extraction
        # Raw HTML is noisy. We extract "signals" — meaningful patterns that
        # indicate what framework, features, or integrations the site uses.
        # e.g. class="data-reactroot" → React app
        tech_signals = await _extract_tech_signals(page, dom_data["raw_html"])

        # --- Capture page metadata ---
        metadata = await _extract_metadata(page, url)

        await browser.close()

        result = {
            "target_url": url,
            "scrape_depth": depth,
            "dom": dom_data,
            "network_log": network_log,
            "js_globals": js_globals,
            "tech_signals": tech_signals,
            "metadata": metadata,
        }

        print(f"[Ingestion] Complete. DOM chars: {len(dom_data['raw_html'])}, "
              f"Network requests: {len(network_log)}")

        return result


# ---------------------------------------------------------------------------
# Network request interceptor
# ---------------------------------------------------------------------------

def _on_request(request, network_log: list):
    """
    Called automatically for EVERY request the browser makes.

    CONCEPT: Network Interception
      Browsers use a protocol called HTTP to fetch resources.
      Playwright lets us hook into this at the browser level — we see
      every request BEFORE it's sent. This is equivalent to opening
      Chrome DevTools → Network tab.

      We filter out noise (images, fonts, analytics) and keep:
        - API calls (fetch/XHR) — these reveal backend data models
        - Document requests — the main HTML pages
        - Third-party integrations — Stripe, Firebase, etc.
    """
    # Filter to meaningful request types only
    resource_type = request.resource_type
    if resource_type not in ("fetch", "xhr", "document", "script"):
        return  # Skip images, fonts, stylesheets, etc.

    # Extract useful info from the request
    entry = {
        "method": request.method,           # GET, POST, PUT, DELETE
        "url": request.url,                 # Full URL
        "resource_type": resource_type,     # fetch, xhr, document, script
        "headers": _safe_headers(request.headers),  # Auth headers, content-type etc.
    }

    network_log.append(entry)


def _safe_headers(headers: dict) -> dict:
    """Keep headers but redact sensitive values like auth tokens."""
    safe = {}
    for key, value in headers.items():
        key_lower = key.lower()
        # Keep the header key but mask the value if it looks sensitive
        if any(s in key_lower for s in ("authorization", "cookie", "token", "secret", "key")):
            safe[key] = "[REDACTED]"
        else:
            safe[key] = value
    return safe


# ---------------------------------------------------------------------------
# DOM extraction
# ---------------------------------------------------------------------------

async def _extract_dom(page: Page) -> dict:
    """
    Extract structured information from the page DOM.

    CONCEPT: DOM Evaluation via JavaScript
      page.evaluate() runs JavaScript INSIDE the browser context.
      This is powerful — we can access the full rendered DOM, including
      content created by React/Vue after the page loads.
      document.documentElement.outerHTML gives us the entire page as an HTML string.
    """
    # Get the full HTML of the rendered page
    raw_html = await page.evaluate("() => document.documentElement.outerHTML")

    # Count key element types — gives a quick sense of page complexity
    element_counts = await page.evaluate("""() => ({
        forms:    document.querySelectorAll('form').length,
        inputs:   document.querySelectorAll('input, textarea, select').length,
        buttons:  document.querySelectorAll('button, [role=button]').length,
        links:    document.querySelectorAll('a[href]').length,
        images:   document.querySelectorAll('img').length,
        iframes:  document.querySelectorAll('iframe').length,
        scripts:  document.querySelectorAll('script[src]').length,
    })""")

    # Extract all form structures — forms reveal core features (login, checkout, contact)
    forms = await page.evaluate("""() => {
        return Array.from(document.querySelectorAll('form')).map(form => ({
            action: form.action,
            method: form.method,
            fields: Array.from(form.querySelectorAll('input, select, textarea')).map(f => ({
                name: f.name,
                type: f.type,
                placeholder: f.placeholder,
            }))
        }));
    }""")

    # Extract all external script sources — reveals integrations and frameworks
    script_srcs = await page.evaluate("""() =>
        Array.from(document.querySelectorAll('script[src]'))
            .map(s => s.src)
            .filter(src => src.startsWith('http'))
    """)

    return {
        "raw_html": raw_html,
        "element_counts": element_counts,
        "forms": forms,
        "external_scripts": script_srcs,
    }


# ---------------------------------------------------------------------------
# JavaScript globals extraction (deep scrape)
# ---------------------------------------------------------------------------

async def _extract_js_globals(page: Page) -> dict:
    """
    Extract JavaScript global variables — these often contain framework data.

    CONCEPT: JS Globals as Intelligence
      Modern frameworks leak useful data into window.* globals:
        - window.__NEXT_DATA__  → Next.js page props + route info
        - window.__NUXT__       → Nuxt.js state
        - window.Shopify        → Shopify store config
        - window.analytics      → Analytics config, user ID patterns
      This is like finding the building's blueprints in the lobby.
    """
    globals_data = await page.evaluate("""() => {
        const result = {};

        // Next.js
        if (window.__NEXT_DATA__) {
            try { result.nextjs = JSON.parse(JSON.stringify(window.__NEXT_DATA__)); }
            catch(e) { result.nextjs = 'present_but_unserializable'; }
        }

        // Nuxt.js
        if (window.__NUXT__) result.nuxt = 'present';

        // Shopify
        if (window.Shopify) {
            result.shopify = {
                shop: window.Shopify.shop,
                currency: window.Shopify.currency,
            };
        }

        // Redux store shape (without data)
        if (window.__REDUX_DEVTOOLS_EXTENSION__) result.redux = 'present';

        // Firebase
        if (window.firebase) result.firebase = 'present';

        return result;
    }""")

    return globals_data


# ---------------------------------------------------------------------------
# Tech signal extraction
# ---------------------------------------------------------------------------

async def _extract_tech_signals(page: Page, raw_html: str) -> dict:
    """
    Identify technology fingerprints from DOM patterns.

    CONCEPT: Technology Fingerprinting
      Every framework leaves distinctive patterns in the HTML it generates.
      Checks are independent (not elif) so multiple frameworks can be detected
      simultaneously — e.g. WordPress + React is a common combination.
        Next.js:   __NEXT_DATA__, _next/static/ paths
        React:     data-reactroot, react bundle filenames
        Nuxt/Vue:  __NUXT__, _nuxt/ paths, data-v-*, __vue__
        Angular:   ng-version, word-boundary ng-* attributes
        Svelte:    data-svelte, __svelte, _app/immutable/ paths
        WordPress: wp-content/, wp-includes/
        Shopify:   cdn.shopify.com, shopify.theme
        Webflow:   webflow.com + data-wf-* attributes
        Tailwind:  3+ distinct utility class patterns required (gap-, text-*-NNN, etc.)
        Bootstrap: btn- + col-md- together
    """
    signals = {
        "frameworks": [],
        "css_frameworks": [],
        "auth_hints": [],
        "integrations": [],
    }
    html_lower = raw_html.lower()

    # --- Frontend Framework Detection ---
    # Each check is independent (not elif) so multiple can be detected,
    # e.g. WordPress + React is common.

    # Next.js: unique data attributes and chunk path pattern
    if "__NEXT_DATA__" in raw_html or "_next/static/" in raw_html:
        signals["frameworks"].append("Next.js / React")
    # Plain React (without Next.js)
    elif "data-reactroot" in raw_html or "react.development.js" in html_lower or "react.production.min.js" in html_lower:
        signals["frameworks"].append("React")

    # Nuxt (Vue SSR) — check before plain Vue
    if "__NUXT__" in raw_html or "_nuxt/" in raw_html:
        signals["frameworks"].append("Nuxt.js / Vue")
    # Plain Vue — require unambiguous fingerprints only
    elif "data-v-" in raw_html or "__vue__" in raw_html:
        signals["frameworks"].append("Vue.js")

    # Angular — require word-boundary match to avoid false positives
    if "ng-version" in raw_html or re.search(r'\bng-[a-z]', raw_html):
        signals["frameworks"].append("Angular")

    # Svelte / SvelteKit
    if "data-svelte" in raw_html or "__svelte" in raw_html or "_app/immutable/" in raw_html:
        signals["frameworks"].append("Svelte")

    # CMS / site builders
    if "wp-content/" in raw_html or "wp-includes/" in raw_html:
        signals["frameworks"].append("WordPress")
    if "cdn.shopify.com" in html_lower or "shopify.theme" in html_lower:
        signals["frameworks"].append("Shopify")
    if "webflow.com" in html_lower and ("wf-" in raw_html or "data-wf-" in raw_html):
        signals["frameworks"].append("Webflow")

    # --- CSS Framework Detection ---
    # Require multiple Tailwind-specific utility patterns together to reduce false positives
    tailwind_hits = len(re.findall(r'class="[^"]*\b(gap-\d|text-\w+-\d{3}|bg-\w+-\d{3}|rounded-\w+|px-\d|py-\d)\b', raw_html))
    if tailwind_hits >= 3:
        signals["css_frameworks"].append("Tailwind CSS")
    if "btn-" in raw_html and "col-md-" in raw_html:
        signals["css_frameworks"].append("Bootstrap")

    # --- Auth Pattern Hints ---
    # Look for auth-related form fields and links
    if any(pattern in raw_html.lower() for pattern in ["login", "sign in", "sign_in"]):
        signals["auth_hints"].append("login_form_detected")
    if "oauth" in raw_html.lower() or "sign in with google" in raw_html.lower():
        signals["auth_hints"].append("oauth_detected")
    if "register" in raw_html.lower() or "sign up" in raw_html.lower():
        signals["auth_hints"].append("registration_flow_detected")

    # --- Third-party Integrations ---
    # Detect by checking script sources and known patterns
    integration_patterns = {
        "Stripe": ["stripe.com", "js.stripe"],
        "Firebase": ["firebase", "firebaseapp"],
        "Intercom": ["intercom"],
        "Segment": ["segment.io", "cdn.segment"],
        "Sentry": ["sentry.io", "browser.sentry"],
        "Google Analytics": ["google-analytics", "gtag", "googletagmanager"],
        "Twilio": ["twilio"],
        "Clerk": ["clerk.dev", "clerk.com"],
    }
    for name, patterns in integration_patterns.items():
        if any(p in raw_html.lower() for p in patterns):
            signals["integrations"].append(name)

    return signals


# ---------------------------------------------------------------------------
# Metadata extraction
# ---------------------------------------------------------------------------

async def _extract_metadata(page: Page, url: str) -> dict:
    """Extract page title, description, and domain info."""
    title = await page.title()

    # og:description or meta description
    description = await page.evaluate("""() => {
        const og = document.querySelector('meta[property="og:description"]');
        const meta = document.querySelector('meta[name="description"]');
        return (og && og.content) || (meta && meta.content) || '';
    }""")

    parsed = urlparse(url)

    return {
        "title": title,
        "description": description,
        "domain": parsed.netloc,
        "path": parsed.path,
    }


# ---------------------------------------------------------------------------
# CLI entry point — run this file directly to scrape a URL
# ---------------------------------------------------------------------------

async def main():
    """
    CLI tool: python src/agents/ingestion_agent.py
    This is the Phase 1 deliverable — input a URL, get raw intelligence JSON.
    """
    import sys

    url = sys.argv[1] if len(sys.argv) > 1 else "https://stripe.com"
    depth = sys.argv[2] if len(sys.argv) > 2 else "surface"

    print(f"\n{'='*60}")
    print(f"DivAi Ingestion Agent")
    print(f"Target: {url}")
    print(f"Depth:  {depth}")
    print(f"{'='*60}\n")

    result = await scrape_website(url, depth)

    # Pretty print key findings
    print("\n--- TECH SIGNALS ---")
    signals = result["tech_signals"]
    print(f"Frameworks:    {signals['frameworks'] or 'None detected'}")
    print(f"CSS:           {signals['css_frameworks'] or 'None detected'}")
    print(f"Auth hints:    {signals['auth_hints'] or 'None detected'}")
    print(f"Integrations:  {signals['integrations'] or 'None detected'}")

    print("\n--- DOM SUMMARY ---")
    counts = result["dom"]["element_counts"]
    print(f"Forms:    {counts['forms']}")
    print(f"Inputs:   {counts['inputs']}")
    print(f"Buttons:  {counts['buttons']}")
    print(f"Links:    {counts['links']}")

    print("\n--- NETWORK LOG (first 10 requests) ---")
    for req in result["network_log"][:10]:
        print(f"  {req['method']:6} {req['resource_type']:10} {req['url'][:80]}")

    print(f"\n--- METADATA ---")
    print(f"Title:       {result['metadata']['title']}")
    print(f"Description: {result['metadata']['description'][:100]}")

    # Save full result to JSON file
    output_path = f"output_ingestion_{result['metadata']['domain'].replace('.', '_')}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        # We don't save raw_html to keep the file manageable
        result["dom"]["raw_html"] = f"[{len(result['dom']['raw_html'])} chars — omitted from JSON output]"
        json.dump(result, f, indent=2, default=str)

    print(f"\n[Ingestion] Full result saved to: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
