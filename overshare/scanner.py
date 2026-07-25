from __future__ import annotations

import time

from .checks import footprint, platform as platform_checks, secrets, transport
from .fetch.assets import EXPOSED_PATH_PROBES, find_source_map_url, parse_assets
from .fetch.client import SafeClient
from .fetch.ssrf import BlockedTarget
from .findings.model import Confidence, Finding, ScanResult, Severity, dedupe

MAX_SCRIPTS = 25


def scan(
    url: str,
    *,
    timeout: float = 10.0,
    allow_private: bool = False,
    include_footprint: bool = True,
    include_ct: bool = True,
    client: SafeClient | None = None,
) -> ScanResult:
    started = time.monotonic()
    result = ScanResult(url=url)

    owns_client = client is None
    client = client or SafeClient(timeout=timeout, allow_private=allow_private)

    try:
        _run(url, client, result, include_footprint, include_ct)
    finally:
        if owns_client:
            client.close()

    result.findings = dedupe(result.findings)
    result.duration_seconds = time.monotonic() - started
    return result


def _run(url, client, result, include_footprint, include_ct) -> None:
    try:
        page = client.get(url, extra_headers={"Origin": transport.PROBE_ORIGIN})
    except BlockedTarget as exc:
        result.errors.append(f"target rejected: {exc}")
        return
    except Exception as exc:
        result.errors.append(f"could not fetch {url}: {exc}")
        return

    final_url = page.final_url
    result.assets.append(final_url)

    if page.redirect_chain:
        result.findings.append(
            Finding(
                check_id="transport.redirect_chain",
                severity=Severity.INFO,
                confidence=Confidence.CERTAIN,
                title="Request was redirected",
                detail=" -> ".join(page.redirect_chain + [final_url]),
                evidence=f"{len(page.redirect_chain)} redirect(s)",
                location=url,
            )
        )

    result.findings.extend(transport.check_headers(page.headers, final_url))
    result.findings.extend(transport.check_cors(page.headers, final_url))
    result.findings.extend(transport.check_tls(final_url, timeout=5.0))
    result.findings.extend(
        transport.check_cookies(list(page.headers.items()), final_url)
    )

    assets = parse_assets(page.text, final_url)

    if assets.insecure_urls:
        result.findings.append(
            Finding(
                check_id="transport.mixed_content",
                severity=Severity.MEDIUM,
                confidence=Confidence.CERTAIN,
                title="Mixed content: plaintext resources on an HTTPS page",
                detail="Resources are loaded over http:// from an https:// page. Browsers block "
                "or downgrade these, and they can be tampered with in transit.",
                evidence="; ".join(assets.insecure_urls[:5]),
                location=final_url,
                remediation="Serve every subresource over https.",
            )
        )

    # Secrets can appear in the HTML itself, not just in bundles.
    result.findings.extend(secrets.scan_content(page.text, final_url))

    combined = [page.text]

    for script_url in assets.script_urls[:MAX_SCRIPTS]:
        resp = client.try_get(script_url)
        if resp is None or not resp.ok:
            continue
        result.assets.append(script_url)
        combined.append(resp.text)
        result.findings.extend(secrets.scan_content(resp.text, script_url))

        map_url = find_source_map_url(resp.text, script_url)
        if map_url:
            map_resp = client.try_get(map_url)
            if map_resp is not None and map_resp.ok and '"sources"' in map_resp.text[:5000]:
                result.assets.append(map_url)
                result.findings.append(
                    Finding(
                        check_id="exposure.source_map",
                        severity=Severity.MEDIUM,
                        confidence=Confidence.CERTAIN,
                        title="Source map publicly accessible",
                        detail="A .map file is served alongside the bundle, which reconstructs "
                        "your original source including comments, file structure, and any "
                        "logic you assumed was obscured by minification.",
                        evidence=map_url,
                        location=map_url,
                        remediation="Disable source map generation for production builds, or "
                        "upload maps to your error tracker without serving them publicly.",
                    )
                )
                result.findings.extend(secrets.scan_content(map_resp.text, map_url))

    for probe in EXPOSED_PATH_PROBES:
        probe_url = final_url.rstrip("/") + probe
        resp = client.try_get(probe_url)
        if resp is None:
            continue
        result.findings.extend(
            transport.check_exposed_paths(probe, resp.status, resp.text, final_url)
        )
        if resp.ok:
            result.findings.extend(secrets.scan_content(resp.text, probe_url))

    all_content = "\n".join(combined)
    fingerprint, platform_findings = platform_checks.fingerprint(
        all_content, page.text, final_url, page.headers
    )
    result.platform = fingerprint
    result.findings.extend(platform_findings)

    if include_footprint:
        try:
            result.findings.extend(footprint.run(final_url, client, include_ct=include_ct))
        except Exception as exc:
            result.errors.append(f"footprint checks failed: {exc}")
