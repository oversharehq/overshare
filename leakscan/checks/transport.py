from __future__ import annotations

import datetime as dt
import socket
import ssl
from urllib.parse import urlsplit

from ..findings.model import Confidence, Finding, Severity

PROBE_ORIGIN = "https://leakscan-cors-probe.invalid"
WEAK_TLS = {"SSLv2", "SSLv3", "TLSv1", "TLSv1.1"}


def check_headers(headers: dict[str, str], url: str) -> list[Finding]:
    findings: list[Finding] = []
    is_https = url.startswith("https://")

    def missing(check_id, title, detail, severity, remediation):
        findings.append(
            Finding(
                check_id=check_id,
                severity=severity,
                confidence=Confidence.CERTAIN,
                title=title,
                detail=detail,
                evidence="header absent",
                location=url,
                remediation=remediation,
            )
        )

    csp = headers.get("content-security-policy")
    if not csp:
        missing(
            "transport.header.csp_missing",
            "Content-Security-Policy header missing",
            "Without a CSP, any script injection flaw becomes full script execution. This is "
            "the single most effective header-level defence against XSS.",
            Severity.MEDIUM,
            "Add a CSP starting with default-src 'self'. Deploy it in report-only mode first "
            "to find what breaks, then enforce.",
        )
    else:
        weak = [d for d in ("'unsafe-inline'", "'unsafe-eval'") if d in csp]
        if weak:
            findings.append(
                Finding(
                    check_id="transport.header.csp_weak",
                    severity=Severity.LOW,
                    confidence=Confidence.CERTAIN,
                    title="Content-Security-Policy weakened by unsafe directives",
                    detail=f"The CSP includes {' and '.join(weak)}, which removes most of the "
                    "protection the policy would otherwise provide against injected scripts.",
                    evidence=csp[:200],
                    location=url,
                    remediation="Replace inline scripts with nonces or hashes, then drop the "
                    "unsafe directives.",
                )
            )

    if is_https and "strict-transport-security" not in headers:
        missing(
            "transport.header.hsts_missing",
            "Strict-Transport-Security header missing",
            "Without HSTS, a visitor's first request over http can be intercepted and "
            "downgraded before the redirect to https takes effect.",
            Severity.MEDIUM,
            "Add: Strict-Transport-Security: max-age=31536000; includeSubDomains",
        )

    frame_protected = "x-frame-options" in headers or (
        headers.get("content-security-policy", "").find("frame-ancestors") != -1
    )
    if not frame_protected:
        missing(
            "transport.header.clickjacking",
            "No clickjacking protection",
            "Neither X-Frame-Options nor a CSP frame-ancestors directive is present, so the "
            "page can be framed by an attacker's site and used for clickjacking.",
            Severity.MEDIUM,
            "Add: X-Frame-Options: DENY, or the CSP directive frame-ancestors 'none'.",
        )

    if headers.get("x-content-type-options", "").lower() != "nosniff":
        missing(
            "transport.header.nosniff_missing",
            "X-Content-Type-Options header missing",
            "Browsers may MIME-sniff responses, allowing an uploaded file to be interpreted "
            "as an executable script.",
            Severity.LOW,
            "Add: X-Content-Type-Options: nosniff",
        )

    if "referrer-policy" not in headers:
        missing(
            "transport.header.referrer_policy_missing",
            "Referrer-Policy header missing",
            "Full URLs, which may contain tokens or identifiers in query strings, are sent "
            "to third-party sites in the Referer header.",
            Severity.LOW,
            "Add: Referrer-Policy: strict-origin-when-cross-origin",
        )

    for banner in ("server", "x-powered-by", "x-aspnet-version"):
        value = headers.get(banner)
        if value and value.lower() not in ("cloudflare", "vercel", "netlify"):
            findings.append(
                Finding(
                    check_id="transport.header.version_disclosure",
                    severity=Severity.INFO,
                    confidence=Confidence.CERTAIN,
                    title="Server technology disclosed in headers",
                    detail=f"The {banner} header reveals backend technology, which helps an "
                    "attacker select known exploits.",
                    evidence=f"{banner}: {value}",
                    location=url,
                    remediation=f"Suppress the {banner} header at the proxy or framework level.",
                )
            )

    return findings


def check_cookies(headers_multi: list[tuple[str, str]], url: str) -> list[Finding]:
    findings: list[Finding] = []
    for name, value in headers_multi:
        if name.lower() != "set-cookie":
            continue
        lowered = value.lower()
        cookie_name = value.split("=", 1)[0].strip()
        problems = []
        if "secure" not in lowered:
            problems.append("Secure")
        if "httponly" not in lowered:
            problems.append("HttpOnly")
        if "samesite" not in lowered:
            problems.append("SameSite")
        if problems:
            findings.append(
                Finding(
                    check_id="transport.cookie.insecure_flags",
                    severity=Severity.MEDIUM,
                    confidence=Confidence.CERTAIN,
                    title=f"Cookie '{cookie_name}' missing security flags",
                    detail=f"Missing {', '.join(problems)}. Without HttpOnly a cookie is readable "
                    "by injected JavaScript; without Secure it can be sent over plaintext; "
                    "without SameSite it is attached to cross-site requests.",
                    evidence=f"{cookie_name}: missing {', '.join(problems)}",
                    location=url,
                    remediation="Set Secure; HttpOnly; SameSite=Lax on session cookies.",
                )
            )
    return findings


def check_cors(headers: dict[str, str], url: str) -> list[Finding]:
    """Interpret CORS headers from a response sent with a probe Origin.

    Reading response headers is passive: no state changes, no authentication.
    """
    acao = headers.get("access-control-allow-origin")
    acac = headers.get("access-control-allow-credentials", "").lower() == "true"
    if not acao:
        return []

    if acao == PROBE_ORIGIN:
        return [
            Finding(
                check_id="transport.cors.origin_reflected",
                severity=Severity.HIGH if acac else Severity.MEDIUM,
                confidence=Confidence.CERTAIN,
                title="CORS reflects arbitrary Origin",
                detail=(
                    "The server echoed an arbitrary Origin back in Access-Control-Allow-Origin, "
                    "meaning any website can read responses from this endpoint."
                    + (
                        " Credentials are also allowed, so an attacker's page can read authenticated "
                        "responses using a logged-in victim's cookies."
                        if acac
                        else ""
                    )
                ),
                evidence=f"Access-Control-Allow-Origin: {acao}",
                location=url,
                remediation="Validate Origin against an explicit allowlist and echo back only "
                "known-good values. Never reflect the request's Origin unconditionally.",
            )
        ]

    if acao == "*" and acac:
        return [
            Finding(
                check_id="transport.cors.wildcard_with_credentials",
                severity=Severity.HIGH,
                confidence=Confidence.CERTAIN,
                title="CORS wildcard combined with credentials",
                detail="Access-Control-Allow-Origin is * while credentials are allowed. This "
                "combination indicates a misconfigured CORS layer.",
                evidence="Access-Control-Allow-Origin: * with Allow-Credentials: true",
                location=url,
                remediation="Replace the wildcard with an explicit origin allowlist.",
            )
        ]

    return []


def check_tls(url: str, timeout: float = 10.0) -> list[Finding]:
    parts = urlsplit(url)
    if parts.scheme != "https":
        return [
            Finding(
                check_id="transport.tls.no_https",
                severity=Severity.HIGH,
                confidence=Confidence.CERTAIN,
                title="Site served over plaintext HTTP",
                detail="Traffic is unencrypted and can be read or modified in transit.",
                evidence=url,
                location=url,
                remediation="Enable HTTPS and redirect all http traffic to https.",
            )
        ]

    host = parts.hostname or ""
    port = parts.port or 443
    findings: list[Finding] = []
    context = ssl.create_default_context()

    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=host) as tls:
                version = tls.version() or "unknown"
                cert = tls.getpeercert()
    except ssl.SSLCertVerificationError as exc:
        return [
            Finding(
                check_id="transport.tls.cert_invalid",
                severity=Severity.HIGH,
                confidence=Confidence.CERTAIN,
                title="TLS certificate failed validation",
                detail=f"The certificate could not be verified: {exc.verify_message or exc}. "
                "Visitors will see a browser warning, which trains them to click through it.",
                evidence=str(exc)[:200],
                location=url,
                remediation="Reissue the certificate for the correct hostname, or fix the "
                "intermediate chain.",
            )
        ]
    except (OSError, ssl.SSLError) as exc:
        return [
            Finding(
                check_id="transport.tls.handshake_failed",
                severity=Severity.INFO,
                confidence=Confidence.CERTAIN,
                title="TLS inspection could not complete",
                detail=f"Could not establish a TLS session to inspect: {exc}",
                evidence=str(exc)[:200],
                location=url,
            )
        ]

    if version in WEAK_TLS:
        findings.append(
            Finding(
                check_id="transport.tls.weak_version",
                severity=Severity.HIGH,
                confidence=Confidence.CERTAIN,
                title=f"Obsolete TLS version negotiated ({version})",
                detail=f"The server negotiated {version}, which is deprecated and vulnerable to "
                "known downgrade and padding-oracle attacks.",
                evidence=version,
                location=url,
                remediation="Disable everything below TLS 1.2; prefer TLS 1.3.",
            )
        )

    if cert and cert.get("notAfter"):
        try:
            expiry = dt.datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z").replace(
                tzinfo=dt.timezone.utc
            )
        except ValueError:
            expiry = None
        if expiry:
            days = (expiry - dt.datetime.now(dt.timezone.utc)).days
            if days < 0:
                findings.append(
                    Finding(
                        check_id="transport.tls.cert_expired",
                        severity=Severity.CRITICAL,
                        confidence=Confidence.CERTAIN,
                        title="TLS certificate has expired",
                        detail=f"The certificate expired {abs(days)} days ago. Visitors see a "
                        "full-page browser warning.",
                        evidence=cert["notAfter"],
                        location=url,
                        remediation="Renew the certificate and set up automatic renewal.",
                    )
                )
            elif days < 14:
                findings.append(
                    Finding(
                        check_id="transport.tls.cert_expiring",
                        severity=Severity.MEDIUM,
                        confidence=Confidence.CERTAIN,
                        title=f"TLS certificate expires in {days} days",
                        detail="The certificate is close to expiry and no automatic renewal is "
                        "evident.",
                        evidence=cert["notAfter"],
                        location=url,
                        remediation="Renew now and automate renewal.",
                    )
                )

    return findings


def check_exposed_paths(path: str, status: int, body: str, base_url: str) -> list[Finding]:
    if status != 200:
        return []

    signatures = {
        "/.env": ("=", Severity.CRITICAL, "Environment file publicly readable"),
        "/.env.local": ("=", Severity.CRITICAL, "Environment file publicly readable"),
        "/.env.production": ("=", Severity.CRITICAL, "Environment file publicly readable"),
        "/.git/HEAD": ("ref:", Severity.CRITICAL, "Git repository publicly readable"),
        "/.git/config": ("[core]", Severity.CRITICAL, "Git repository publicly readable"),
        "/.aws/credentials": ("aws_access_key", Severity.CRITICAL, "AWS credentials file readable"),
        "/config.json": ("{", Severity.LOW, "Configuration file publicly readable"),
    }

    if path not in signatures:
        return []
    marker, severity, title = signatures[path]
    check_id = "exposure.path." + path.lstrip("/.").replace("/", ".").replace(".", "_")

    # An SPA that returns index.html for every unknown route would otherwise
    # produce a false positive on every probe.
    lowered = body[:2000].lower()
    if "<!doctype html" in lowered or "<html" in lowered:
        return []
    if marker.lower() not in body[:2000].lower():
        return []

    return [
        Finding(
            check_id=check_id,
            severity=severity,
            confidence=Confidence.CERTAIN,
            title=title,
            detail=f"{path} returned 200 with content matching its expected format. "
            "Anyone can retrieve it.",
            evidence=f"GET {path} -> 200 ({len(body)} bytes)",
            location=base_url.rstrip("/") + path,
            remediation="Block dotfile paths at the web server or CDN. If .git was exposed, "
            "assume full source disclosure and rotate every credential in its history.",
        )
    ]
