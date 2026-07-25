from __future__ import annotations

from .store import COMPLETE, FAILED, QUEUED, RUNNING, ScanRecord

# Findings where a generated fix would be materially better than the generic
# remediation text we already give away free. Everything else is a one-line
# change that `remediation` already covers in full — advertising a paid fix for
# "add a nosniff header" would be selling nothing.
_FIX_AVAILABLE_PREFIXES = ("secret.",)
_FIX_AVAILABLE_IDS = frozenset(
    {
        # The whole moat: the actual policy for that table, not generic advice.
        "platform.supabase.rls_untested",
        # A CSP is only useful when built from the scripts the app really loads.
        "transport.header.csp_missing",
        "transport.header.csp_weak",
        # Needs the caller's real origin allowlist.
        "transport.cors.origin_reflected",
        "transport.cors.wildcard_with_credentials",
        # The build-config change differs per framework and bundler.
        "exposure.source_map",
    }
)


def fix_available(check_id: str) -> bool:
    return check_id.startswith(_FIX_AVAILABLE_PREFIXES) or check_id in _FIX_AVAILABLE_IDS


def _finding_to_dict(finding: dict) -> dict:
    """Add the paid-tier fields the contract requires.

    `remediation` (generic guidance) stays free. `fix` is the app-specific
    generated artifact and is always null until M5 ships the generator.
    """
    return {
        **finding,
        "fix": None,
        "fix_available": fix_available(finding.get("check_id", "")),
    }


def result_to_dict(result: dict) -> dict:
    return {**result, "findings": [_finding_to_dict(f) for f in result.get("findings", [])]}


def _poll_after_ms(status: str) -> int:
    if status == QUEUED:
        return 1000
    if status == RUNNING:
        return 2000
    return 0


def scan_to_dict(record: ScanRecord) -> dict:
    error = None
    if record.status == FAILED and record.error_code:
        error = {"code": record.error_code, "message": record.error_message or ""}

    return {
        "id": record.id,
        "status": record.status,
        "url": record.url,
        "tier": record.tier,
        "created_at": record.created_at,
        "started_at": record.started_at,
        "completed_at": record.completed_at,
        # The scanner runs as one blocking call, so there is nothing truthful to
        # report mid-scan. The contract permits null and the frontend falls back
        # to an indeterminate indicator; faking a percentage is worse than none.
        "progress": None,
        "result": result_to_dict(record.result) if record.status == COMPLETE and record.result else None,
        "error": error,
        "poll_after_ms": _poll_after_ms(record.status),
    }
