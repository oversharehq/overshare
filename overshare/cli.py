from __future__ import annotations

import argparse
import json
import sys

from .findings.model import Severity
from .report.sarif import render as render_sarif
from .report.terminal import render
from .scanner import scan

EXIT_CLEAN = 0
EXIT_FINDINGS = 1
EXIT_ERROR = 2

FAIL_THRESHOLDS = {
    "critical": (Severity.CRITICAL,),
    "high": (Severity.CRITICAL, Severity.HIGH),
    "medium": (Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM),
    "low": (Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW),
    "never": (),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="overshare",
        description="Passive (Tier A) security scan of a public web application.",
        epilog="Only scan applications you own or have written permission to test.",
    )
    parser.add_argument("url", help="Target URL, e.g. https://example.com")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a report")
    # A side channel rather than an output format: CI wants the readable report
    # in the job log *and* a SARIF file to upload, from one scan of the target.
    parser.add_argument(
        "--sarif-file",
        metavar="FILE",
        help="Also write a SARIF 2.1.0 report to FILE, for GitHub code scanning",
    )
    parser.add_argument("--output", metavar="FILE", help="Write output to FILE")
    parser.add_argument("--show-info", action="store_true", help="Include informational findings")
    parser.add_argument("--timeout", type=float, default=10.0, help="Per-request timeout (s)")
    parser.add_argument("--no-footprint", action="store_true", help="Skip DNS/mail/CT checks")
    parser.add_argument("--no-ct", action="store_true", help="Skip certificate transparency lookup")
    parser.add_argument(
        "--fail-on",
        choices=sorted(FAIL_THRESHOLDS),
        default="high",
        help="Minimum severity that produces a non-zero exit code (default: high)",
    )
    parser.add_argument(
        "--unsafe-allow-private-ips",
        action="store_true",
        help="Disable SSRF protection so localhost can be scanned. Local testing only.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    url = args.url
    if "://" not in url:
        url = f"https://{url}"

    if args.unsafe_allow_private_ips:
        print(
            "WARNING: SSRF protection disabled. Only use this against your own local test app.",
            file=sys.stderr,
        )

    try:
        result = scan(
            url,
            timeout=args.timeout,
            allow_private=args.unsafe_allow_private_ips,
            include_footprint=not args.no_footprint,
            include_ct=not args.no_ct,
        )
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return EXIT_ERROR
    except Exception as exc:
        print(f"scan failed: {exc}", file=sys.stderr)
        return EXIT_ERROR

    stream = open(args.output, "w", encoding="utf-8") if args.output else sys.stdout
    try:
        if args.json:
            json.dump(result.to_dict(), stream, indent=2)
            stream.write("\n")
        else:
            render(result, stream=stream, show_info=args.show_info)
    finally:
        if args.output:
            stream.close()

    if args.sarif_file:
        with open(args.sarif_file, "w", encoding="utf-8") as sarif_stream:
            render_sarif(result, stream=sarif_stream, show_info=args.show_info)

    if result.errors and not result.findings:
        return EXIT_ERROR

    failing = FAIL_THRESHOLDS[args.fail_on]
    if any(f.severity in failing for f in result.findings):
        return EXIT_FINDINGS
    return EXIT_CLEAN


if __name__ == "__main__":
    raise SystemExit(main())
