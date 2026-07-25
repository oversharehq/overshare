from __future__ import annotations

import json
import re
from urllib.parse import urlsplit

import dns.exception
import dns.resolver

from ..findings.model import Confidence, Finding, Severity

CRT_SH_URL = "https://crt.sh/?q=%25.{domain}&output=json"

# Subdomain labels that suggest a non-production environment. These are the ones
# that get stood up during a build, forgotten, and left with weaker controls.
RISKY_LABELS = re.compile(
    r"^(?:staging|stage|dev|develop|test|testing|uat|qa|preview|demo|beta|admin|"
    r"internal|intranet|backup|old|legacy|tmp|temp|sandbox|api-dev|api-test)\b"
)

COMMON_DKIM_SELECTORS = ("google", "default", "selector1", "selector2", "k1", "mail", "dkim")


def registrable_domain(url: str) -> str:
    host = urlsplit(url).hostname or ""
    parts = host.split(".")
    if len(parts) <= 2:
        return host
    # Handle the common two-part public suffixes without pulling in a PSL dependency.
    if parts[-2] in ("com", "co", "net", "org", "gov", "edu", "ac") and len(parts[-1]) == 2:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def _query(name: str, rdtype: str, timeout: float = 5.0) -> list[str]:
    resolver = dns.resolver.Resolver()
    resolver.timeout = timeout
    resolver.lifetime = timeout
    try:
        answers = resolver.resolve(name, rdtype)
    except (dns.exception.DNSException, ValueError):
        return []
    return [r.to_text().strip('"').replace('" "', "") for r in answers]


def check_mail_auth(domain: str) -> list[Finding]:
    findings: list[Finding] = []
    txt = _query(domain, "TXT")
    mx = _query(domain, "MX")
    spf = next((r for r in txt if r.lower().startswith("v=spf1")), None)

    if not spf:
        findings.append(
            Finding(
                check_id="footprint.mail.spf_missing",
                severity=Severity.LOW,
                confidence=Confidence.CERTAIN,
                title="No SPF record",
                detail="Without SPF, anyone can send mail claiming to be from this domain, which "
                "makes phishing your own users trivial.",
                evidence=f"no v=spf1 TXT record on {domain}",
                location=domain,
                remediation="Publish a TXT record such as: v=spf1 include:_spf.google.com -all",
            )
        )
    elif spf.rstrip().endswith("+all"):
        findings.append(
            Finding(
                check_id="footprint.mail.spf_permissive",
                severity=Severity.HIGH,
                confidence=Confidence.CERTAIN,
                title="SPF record permits any sender",
                detail="The SPF record ends in +all, which explicitly authorises every host on "
                "the internet to send mail as this domain.",
                evidence=spf[:200],
                location=domain,
                remediation="Change the final mechanism to -all (hard fail) or ~all (soft fail).",
            )
        )

    dmarc = _query(f"_dmarc.{domain}", "TXT")
    dmarc_record = next((r for r in dmarc if r.lower().startswith("v=dmarc1")), None)
    if not dmarc_record:
        findings.append(
            Finding(
                check_id="footprint.mail.dmarc_missing",
                severity=Severity.LOW if not mx else Severity.MEDIUM,
                confidence=Confidence.CERTAIN,
                title="No DMARC record",
                detail="Without DMARC, receiving mail servers have no instruction on what to do "
                "with mail that fails SPF or DKIM, so spoofed mail is likely to be delivered.",
                evidence=f"no TXT record at _dmarc.{domain}",
                location=f"_dmarc.{domain}",
                remediation="Start with: v=DMARC1; p=none; rua=mailto:you@yourdomain. Review "
                "reports, then tighten to p=quarantine and finally p=reject.",
            )
        )
    elif "p=none" in dmarc_record.lower():
        findings.append(
            Finding(
                check_id="footprint.mail.dmarc_monitor_only",
                severity=Severity.LOW,
                confidence=Confidence.CERTAIN,
                title="DMARC policy is monitor-only",
                detail="The DMARC policy is p=none, which reports failures but instructs "
                "receivers to deliver spoofed mail anyway.",
                evidence=dmarc_record[:200],
                location=f"_dmarc.{domain}",
                remediation="Once reports look clean, move to p=quarantine and then p=reject.",
            )
        )

    return findings


def check_dns_records(domain: str) -> list[Finding]:
    findings: list[Finding] = []
    records = {rt: _query(domain, rt) for rt in ("A", "AAAA", "MX", "NS", "TXT")}
    summary = {k: v for k, v in records.items() if v}

    findings.append(
        Finding(
            check_id="footprint.dns.records",
            severity=Severity.INFO,
            confidence=Confidence.CERTAIN,
            title="DNS records enumerated",
            detail=json.dumps(summary, indent=2)[:1500],
            evidence=f"{sum(len(v) for v in summary.values())} records across "
            f"{len(summary)} types",
            location=domain,
        )
    )

    dkim_found = [s for s in COMMON_DKIM_SELECTORS if _query(f"{s}._domainkey.{domain}", "TXT")]
    if dkim_found:
        findings.append(
            Finding(
                check_id="footprint.mail.dkim_present",
                severity=Severity.INFO,
                confidence=Confidence.CERTAIN,
                title="DKIM selectors present",
                detail=f"Found DKIM keys at selectors: {', '.join(dkim_found)}.",
                evidence=", ".join(dkim_found),
                location=domain,
            )
        )

    return findings


def check_certificate_transparency(domain: str, client, max_subdomains: int = 400) -> list[Finding]:
    """Mine public CT logs for subdomains the owner may have forgotten.

    CT logs are a public append-only record of every issued certificate. Reading
    them touches only crt.sh, never the target.
    """
    resp = client.try_get(CRT_SH_URL.format(domain=domain))
    if resp is None or not resp.ok:
        return [
            Finding(
                check_id="footprint.ct.unavailable",
                severity=Severity.INFO,
                confidence=Confidence.CERTAIN,
                title="Certificate transparency lookup unavailable",
                detail="crt.sh did not return usable data, so forgotten-subdomain discovery was "
                "skipped for this scan.",
                evidence="crt.sh request failed",
                location=domain,
            )
        ]

    try:
        entries = json.loads(resp.text)
    except json.JSONDecodeError:
        return []

    names: set[str] = set()
    for entry in entries[:5000]:
        for name in str(entry.get("name_value", "")).split("\n"):
            name = name.strip().lower().lstrip("*.")
            if name.endswith(domain) and name != domain:
                names.add(name)
        if len(names) >= max_subdomains:
            break

    findings: list[Finding] = [
        Finding(
            check_id="footprint.ct.subdomains",
            severity=Severity.INFO,
            confidence=Confidence.CERTAIN,
            title=f"{len(names)} subdomains found in certificate transparency logs",
            detail="These names appear in public CT logs. They are discoverable by anyone.\n"
            + "\n".join(sorted(names)[:60]),
            evidence=f"{len(names)} names",
            location=domain,
        )
    ]

    risky_live: list[str] = []
    for name in sorted(names):
        label = name[: -len(domain)].rstrip(".").split(".")[-1]
        if RISKY_LABELS.match(label) and _query(name, "A"):
            risky_live.append(name)

    if risky_live:
        findings.append(
            Finding(
                check_id="footprint.ct.nonprod_subdomain_live",
                severity=Severity.MEDIUM,
                confidence=Confidence.CERTAIN,
                title=f"{len(risky_live)} non-production subdomain(s) resolving publicly",
                detail="These names suggest staging, development, or admin environments and they "
                "currently resolve. Such environments routinely carry weaker authentication, "
                "verbose errors, and copies of production data:\n" + "\n".join(risky_live[:20]),
                evidence=", ".join(risky_live[:10]),
                location=domain,
                remediation="Take these offline, put them behind authentication or an IP "
                "allowlist, and confirm they hold no production data.",
            )
        )

    return findings


def run(url: str, client, *, include_ct: bool = True) -> list[Finding]:
    domain = registrable_domain(url)
    if not domain:
        return []

    findings = check_dns_records(domain)
    findings.extend(check_mail_auth(domain))
    if include_ct:
        findings.extend(check_certificate_transparency(domain, client))
    return findings
