"""
DivAi — Auth Capture Routes

Two endpoints:

  POST /api/auth/inspect
    Given a URL, find the signup page and return all form field metadata.
    The frontend renders these as a fillable form.

  POST /api/auth/capture
    Given a URL + user-provided field values, fill the signup form via
    Playwright, submit it, and return the resulting auth cookies.
    Those cookies are stored in the session and injected into the
    Ingestion Agent's browser context for authenticated scraping.
"""

import sys
import os
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from agents.form_inspector_agent import inspect_signup_form, fill_and_capture

router = APIRouter()


class InspectRequest(BaseModel):
    url: str


class CaptureRequest(BaseModel):
    signup_url: str
    field_values: dict[str, str]        # { field_id_or_name: value }
    submit_selector: str = "button[type='submit']"


@router.post("/auth/inspect")
async def inspect(payload: InspectRequest):
    """
    Inspect a website's signup form and return field metadata.

    Returns a list of fields the frontend can render as a sign-up form,
    plus the signup URL and submit button selector needed for /auth/capture.
    """
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: asyncio.run(inspect_signup_form(payload.url))
    )
    if result.get("error") and not result.get("fields"):
        raise HTTPException(status_code=422, detail=result["error"])
    return result


@router.post("/auth/capture")
async def capture(payload: CaptureRequest):
    """
    Fill the signup form with user-provided credentials and capture auth cookies.

    The user is signing up with their own real information — we are just
    automating the form submission and returning the resulting session cookie.
    """
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: asyncio.run(fill_and_capture(
            signup_url=payload.signup_url,
            field_values=payload.field_values,
            submit_selector=payload.submit_selector,
        ))
    )
    if not result.get("success"):
        raise HTTPException(status_code=422, detail=result.get("error", "Form submission failed"))
    return {
        "auth_cookie": result["auth_cookie"],
        "all_cookies": result["cookies"],
        "final_url":   result["final_url"],
    }
