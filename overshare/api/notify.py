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

# Mailgun's EU region is api.eu.mailgun.net. Which one is correct depends on
# where the domain was created, and sending to the wrong one authenticates fine
# and then 404s on the domain.
DEFAULT_BASE_URL = "https://api.mailgun.net/v3"

TIMEOUT_SECONDS = 5.0


def notify_waitlist_signup(email: str) -> None:
    api_key = os.environ.get("OVERSHARE_MAILGUN_API_KEY")
    domain = os.environ.get("OVERSHARE_MAILGUN_DOMAIN")
    recipient = os.environ.get("OVERSHARE_NOTIFY_EMAIL")
    # Unconfigured is the normal case in tests and local development, and it is
    # not a warning — the feature is opt-in.
    if not api_key or not domain or not recipient:
        return

    base_url = os.environ.get("OVERSHARE_MAILGUN_BASE_URL", DEFAULT_BASE_URL)
    # Defaults to the sending domain, not oversharehq.com. That domain's SPF
    # ends in -all and does not list Mailgun, so mail from it would be dropped
    # silently — the hardest failure mode to notice.
    sender = os.environ.get(
        "OVERSHARE_NOTIFY_SENDER", f"Overshare <postmaster@{domain}>"
    )

    try:
        response = httpx.post(
            f"{base_url}/{domain}/messages",
            auth=("api", api_key),
            data={
                "from": sender,
                "to": recipient,
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
