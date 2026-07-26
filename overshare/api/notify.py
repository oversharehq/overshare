"""Outbound notification for waitlist signups.

Deliberately best-effort. A signup that succeeded must never be reported as
failed because an email provider was down, so every failure here is swallowed
and logged. The address is already committed to the database by the time this
runs; the email is a convenience, not the record.
"""

from __future__ import annotations

import logging
import os

import httpx

logger = logging.getLogger(__name__)

RESEND_ENDPOINT = "https://api.resend.com/emails"

# Resend's shared sending domain rather than @oversharehq.com. Sending from our
# own domain would require adding Resend to SPF, and that record ends in -all,
# so getting the order wrong silently drops the mail.
DEFAULT_SENDER = "Overshare <onboarding@resend.dev>"

TIMEOUT_SECONDS = 5.0


def notify_waitlist_signup(email: str) -> None:
    api_key = os.environ.get("OVERSHARE_RESEND_API_KEY")
    recipient = os.environ.get("OVERSHARE_NOTIFY_EMAIL")
    # Unconfigured is the normal case in tests and local development, and it is
    # not a warning — the feature is opt-in.
    if not api_key or not recipient:
        return

    sender = os.environ.get("OVERSHARE_NOTIFY_SENDER", DEFAULT_SENDER)

    try:
        response = httpx.post(
            RESEND_ENDPOINT,
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "from": sender,
                "to": [recipient],
                "subject": "Overshare — new waitlist signup",
                "text": f"{email} joined the Overshare Cloud waitlist.",
            },
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except Exception:
        # No address in the log line. Notification failures get investigated by
        # reading logs, and a signup address is not something to leave there.
        logger.warning("waitlist notification failed", exc_info=True)
