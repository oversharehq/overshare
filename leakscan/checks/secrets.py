from __future__ import annotations

import base64
import binascii
import json
import re
from dataclasses import dataclass

from ..findings.model import Confidence, Finding, Severity, redact

JWT_RE = re.compile(r"eyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}")


@dataclass(frozen=True)
class Pattern:
    check_id: str
    regex: re.Pattern[str]
    severity: Severity
    title: str
    detail: str
    remediation: str


def _p(check_id, regex, severity, title, detail, remediation) -> Pattern:
    return Pattern(check_id, re.compile(regex), severity, title, detail, remediation)


# Every pattern here is anchored on a vendor-issued prefix or a structurally
# unambiguous format. Nothing is matched on entropy alone: minified bundles are
# full of build hashes that look exactly like secrets.
PATTERNS: list[Pattern] = [
    _p(
        "secret.supabase.secret_key",
        r"\bsb_secret_[A-Za-z0-9_-]{20,}",
        Severity.CRITICAL,
        "Supabase secret key in client bundle",
        "A Supabase secret API key was shipped to the browser. It bypasses Row Level "
        "Security entirely, granting full read/write access to every table.",
        "Revoke this key in the Supabase dashboard immediately, then move any code that "
        "needs it into an Edge Function or server route. Never reference it from client code.",
    ),
    _p(
        "secret.stripe.live_secret",
        r"\bsk_live_[0-9a-zA-Z]{20,}",
        Severity.CRITICAL,
        "Stripe live secret key in client bundle",
        "A Stripe live-mode secret key is exposed. It permits arbitrary charges, refunds, "
        "and full access to customer payment records.",
        "Roll the key in the Stripe dashboard now. Client code should only ever use the "
        "publishable key (pk_live_); all secret-key calls belong on a server.",
    ),
    _p(
        "secret.stripe.restricted",
        r"\brk_live_[0-9a-zA-Z]{20,}",
        Severity.HIGH,
        "Stripe restricted key in client bundle",
        "A Stripe restricted API key is exposed. Its blast radius depends on the scopes "
        "granted, but it is not intended for client-side use.",
        "Roll the key and review which scopes it was granted.",
    ),
    _p(
        "secret.aws.access_key_id",
        r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b",
        Severity.CRITICAL,
        "AWS access key ID in client bundle",
        "An AWS access key ID is exposed. Paired with a secret access key it grants "
        "whatever IAM permissions the principal holds.",
        "Deactivate and delete the key in IAM, audit CloudTrail for use, and move AWS "
        "calls behind a server endpoint or use Cognito with scoped credentials.",
    ),
    _p(
        "secret.openai.api_key",
        r"\bsk-(?!ant-)(?:proj-|svcacct-)?[A-Za-z0-9_-]{32,}",
        Severity.CRITICAL,
        "OpenAI API key in client bundle",
        "An OpenAI API key is exposed. Anyone can bill arbitrary usage to this account.",
        "Revoke the key at platform.openai.com immediately and proxy model calls through "
        "your own backend so the key never reaches the browser.",
    ),
    _p(
        "secret.anthropic.api_key",
        r"\bsk-ant-(?:api\d{2}|sid\d{2})-[A-Za-z0-9_-]{40,}",
        Severity.CRITICAL,
        "Anthropic API key in client bundle",
        "An Anthropic API key is exposed. Anyone can bill arbitrary usage to this account.",
        "Revoke the key in the Anthropic console and proxy model calls through your backend.",
    ),
    _p(
        "secret.github.token",
        r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36}\b",
        Severity.CRITICAL,
        "GitHub token in client bundle",
        "A GitHub access token is exposed, granting repository access under the token's scopes.",
        "Revoke the token in GitHub developer settings and audit repository access logs.",
    ),
    _p(
        "secret.github.fine_grained_pat",
        r"\bgithub_pat_[A-Za-z0-9_]{60,}",
        Severity.CRITICAL,
        "GitHub fine-grained PAT in client bundle",
        "A GitHub fine-grained personal access token is exposed.",
        "Revoke the token in GitHub developer settings immediately.",
    ),
    _p(
        "secret.slack.token",
        r"\bxox[baprs]-[A-Za-z0-9-]{10,}",
        Severity.CRITICAL,
        "Slack token in client bundle",
        "A Slack API token is exposed, allowing message read/write in the workspace.",
        "Revoke the token in the Slack app configuration and rotate the app credentials.",
    ),
    _p(
        "secret.sendgrid.api_key",
        r"\bSG\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{40,}",
        Severity.CRITICAL,
        "SendGrid API key in client bundle",
        "A SendGrid API key is exposed, allowing mail to be sent from your domain. "
        "This is commonly abused for phishing that passes your SPF and DKIM.",
        "Revoke the key in the SendGrid dashboard and send mail from a server endpoint only.",
    ),
    _p(
        "secret.paddle.api_key",
        r"\bpdl_live_apikey_[A-Za-z0-9_]{20,}",
        Severity.CRITICAL,
        "Paddle live API key in client bundle",
        "A Paddle live API key is exposed, granting access to billing and customer data.",
        "Roll the key in the Paddle dashboard and keep billing calls server-side.",
    ),
    _p(
        "secret.mailgun.api_key",
        r"\bkey-[0-9a-f]{32}\b",
        Severity.HIGH,
        "Mailgun API key in client bundle",
        "A Mailgun API key is exposed, allowing mail to be sent from your domain.",
        "Revoke the key in the Mailgun dashboard.",
    ),
    _p(
        "secret.google.api_key",
        r"\bAIza[0-9A-Za-z_-]{35}\b",
        Severity.MEDIUM,
        "Google API key in client bundle",
        "A Google API key is exposed. Firebase and Maps keys are public by design, so this "
        "is only a problem if the key lacks application restrictions or grants billable APIs.",
        "In Google Cloud Console, restrict the key by HTTP referrer and to the specific APIs "
        "it needs. An unrestricted key can be used by anyone at your expense.",
    ),
    _p(
        "secret.private_key",
        r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----",
        Severity.CRITICAL,
        "Private key material in client bundle",
        "A PEM-encoded private key block is present in client-accessible content.",
        "Treat this key as compromised: rotate it and reissue anything signed with it.",
    ),
    _p(
        "secret.db_connection_string",
        r"\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|amqp)://[^\s:'\"/@]+:[^\s:'\"@]+@[^\s'\"<>]+",
        Severity.CRITICAL,
        "Database connection string with credentials",
        "A database URI including a password is exposed in client-accessible content.",
        "Rotate the database password immediately and move all database access behind a "
        "server-side API. Client code must never hold a direct database connection string.",
    ),
    _p(
        "secret.jwt_signing_secret",
        r"(?i)\b(?:jwt|token)[_-]?secret\s*[:=]\s*['\"][^'\"]{16,}['\"]",
        Severity.CRITICAL,
        "JWT signing secret in client bundle",
        "What appears to be a JWT signing secret is assigned in client code. Anyone holding "
        "it can forge authentication tokens for any user.",
        "Rotate the signing secret. This invalidates existing sessions, which is the point. "
        "Keep it server-side only.",
    ),
]


def _b64url_decode(segment: str) -> bytes:
    padding = "=" * (-len(segment) % 4)
    return base64.urlsafe_b64decode(segment + padding)


def decode_jwt_payload(token: str) -> dict | None:
    """Decode a JWT payload without verifying the signature.

    Signature verification is impossible without the secret and unnecessary here:
    we only need the claims to tell an anon key from a service_role key.
    """
    parts = token.split(".")
    if len(parts) != 3:
        return None
    try:
        payload = json.loads(_b64url_decode(parts[1]))
    except (binascii.Error, ValueError, UnicodeDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def check_jwts(content: str, location: str) -> list[Finding]:
    findings: list[Finding] = []
    for token in set(JWT_RE.findall(content)):
        payload = decode_jwt_payload(token)
        if payload is None:
            continue

        role = payload.get("role")
        issuer = payload.get("iss", "")

        if role == "service_role":
            findings.append(
                Finding(
                    check_id="secret.supabase.service_role",
                    severity=Severity.CRITICAL,
                    confidence=Confidence.CERTAIN,
                    title="Supabase service_role key in client bundle",
                    detail=(
                        "A JWT with the service_role claim was found in content served to the "
                        "browser. This key bypasses Row Level Security completely: any visitor "
                        "can read, modify, or delete every row in every table. Decoded claims "
                        f"confirm role=service_role, project ref={payload.get('ref', 'unknown')}."
                    ),
                    evidence=redact(token),
                    location=location,
                    remediation=(
                        "Rotate the JWT secret in Supabase (Settings > API) immediately, which "
                        "invalidates this key. Remove it from client code and any committed .env "
                        "file, then move privileged operations into an Edge Function. Assume the "
                        "data has already been read and act accordingly."
                    ),
                )
            )
        elif role == "anon" and "supabase" in str(issuer).lower():
            findings.append(
                Finding(
                    check_id="platform.supabase.anon_key",
                    severity=Severity.INFO,
                    confidence=Confidence.CERTAIN,
                    title="Supabase anon key detected",
                    detail=(
                        "A Supabase anon key was found. This is expected and not itself a "
                        "vulnerability, since the key is public by design. Its safety depends "
                        "entirely on whether Row Level Security is enabled and correctly "
                        f"policed on every table. Project ref: {payload.get('ref', 'unknown')}."
                    ),
                    evidence=redact(token),
                    location=location,
                    remediation=(
                        "Confirm RLS is enabled on every table in the public schema. This scan "
                        "does not test enforcement; that requires a Tier B scan."
                    ),
                )
            )
    return findings


def scan_content(content: str, location: str) -> list[Finding]:
    findings: list[Finding] = []

    for pattern in PATTERNS:
        for match in set(pattern.regex.findall(content)):
            value = match if isinstance(match, str) else match[0]
            findings.append(
                Finding(
                    check_id=pattern.check_id,
                    severity=pattern.severity,
                    confidence=Confidence.CERTAIN,
                    title=pattern.title,
                    detail=pattern.detail,
                    evidence=redact(value),
                    location=location,
                    remediation=pattern.remediation,
                )
            )

    findings.extend(check_jwts(content, location))
    return findings
