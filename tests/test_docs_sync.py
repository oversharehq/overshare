"""Keeps the public claims aligned with the code that has to honour them.

Overshare states its scoring, its scan tiers and its retention window in three
places: the scanner itself, the markdown docs at the repo root, and the website.
The website cannot read the markdown at build time — the web image builds from
`web/` alone — so `web/lib/docs.ts` restates those facts, and the two copies can
drift.

On a security product that is not a cosmetic problem. A methodology page quoting
a penalty the scorer no longer applies, or a policy page promising a retention
window the API no longer honours, is a false statement to a user who had no way
to check it. The scanner is treated as canonical here; the docs and the site
must agree with it.

Prose is deliberately not compared. Only headings and load-bearing numbers are.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from overshare.findings.model import SEVERITY_PENALTY, ScanResult, Severity

ROOT = Path(__file__).resolve().parent.parent
METHODOLOGY_MD = ROOT / "METHODOLOGY.md"
ACCEPTABLE_USE_MD = ROOT / "ACCEPTABLE_USE.md"
DOCS_TS = ROOT / "web" / "lib" / "docs.ts"


def read(path: Path) -> str:
    if not path.exists():
        pytest.fail(
            f"{path.relative_to(ROOT)} is missing. It is referenced by the "
            f"website and by this test; do not delete it without updating both."
        )
    return path.read_text(encoding="utf-8")


def markdown_headings(text: str) -> list[str]:
    """The `##` headings only — `###` are subsections the website may nest."""
    return re.findall(r"^## +(.+?)\s*$", text, flags=re.MULTILINE)


def ts_string_array(source: str, name: str) -> list[str]:
    """Extracts a `NAME = [ "a", 'b' ] as const;` array from the TS module."""
    match = re.search(rf"{name}\s*=\s*\[(.*?)\]\s*as const", source, flags=re.DOTALL)
    if match is None:
        pytest.fail(f"could not find `{name}` in web/lib/docs.ts")
    return re.findall(r"""["'](.+?)["'],""", match.group(1), flags=re.DOTALL)


def ts_grade_thresholds(source: str) -> list[tuple[str, int]]:
    return [
        (grade, int(floor))
        for grade, floor in re.findall(
            r"""grade:\s*["']([A-F])["'],\s*min:\s*(\d+)""", source
        )
    ]


def grade_of(score: int) -> str:
    """ScanResult.grade() at an exact score.

    The penalty steps are 40/20/8/3, so most scores cannot be reached by adding
    up real findings — 90 among them. Overriding score() is what makes the
    boundaries themselves testable.
    """

    class FixedScore(ScanResult):
        def score(self) -> int:
            return score

    return FixedScore(url="https://example.test").grade()


@pytest.fixture(scope="module")
def docs_ts() -> str:
    return read(DOCS_TS)


class TestHeadingsMatch:
    """A section renamed in the doc but not on the site, or dropped entirely."""

    def test_methodology(self, docs_ts: str) -> None:
        assert ts_string_array(docs_ts, "METHODOLOGY_SECTIONS") == markdown_headings(
            read(METHODOLOGY_MD)
        )

    def test_acceptable_use(self, docs_ts: str) -> None:
        assert ts_string_array(
            docs_ts, "ACCEPTABLE_USE_SECTIONS"
        ) == markdown_headings(read(ACCEPTABLE_USE_MD))


class TestScoringMatchesTheScorer:
    """The scorer is canonical. The doc and the site quote it, so they must agree."""

    def test_penalties_in_methodology_md(self) -> None:
        rows = re.findall(
            r"^\| \*\*(\w+)\*\* \|.*\| (\d+) \|$",
            read(METHODOLOGY_MD),
            flags=re.MULTILINE,
        )
        assert rows, "severity/penalty table not found in METHODOLOGY.md"
        documented = {level.lower(): int(penalty) for level, penalty in rows}
        assert documented == {
            severity.value: penalty for severity, penalty in SEVERITY_PENALTY.items()
        }

    def test_penalties_in_docs_ts(self, docs_ts: str) -> None:
        pairs = re.findall(
            r"""level:\s*["'](\w+)["'][\s\S]*?penalty:\s*(\d+)""", docs_ts
        )
        assert pairs, "SEVERITY_LEVELS not found in web/lib/docs.ts"
        published = {level.lower(): int(penalty) for level, penalty in pairs}
        assert published == {
            severity.value: penalty for severity, penalty in SEVERITY_PENALTY.items()
        }

    def test_documented_thresholds_match_the_site(self, docs_ts: str) -> None:
        documented = [
            (grade, int(floor))
            for grade, floor in re.findall(
                r"\*\*([A-D])\*\* +≥ +(\d+)", read(METHODOLOGY_MD)
            )
        ]
        assert documented, "grade thresholds not found in METHODOLOGY.md"
        assert documented == ts_grade_thresholds(docs_ts)

    def test_scorer_honours_the_documented_thresholds(self, docs_ts: str) -> None:
        """
        Pins the `≥` in the docs against an off-by-one in either direction: at
        each published floor the scorer must give that grade, and one point below
        it must give the next grade down.
        """
        thresholds = ts_grade_thresholds(docs_ts)
        below = [grade for grade, _ in thresholds[1:]] + ["F"]

        for (grade, floor), next_grade in zip(thresholds, below):
            assert grade_of(floor) == grade
            assert grade_of(floor - 1) == next_grade


class TestRetentionPromise:
    """The retention window is a privacy claim, so all three copies must agree."""

    def test_api_default(self) -> None:
        from overshare.api.app import Settings

        assert Settings.retention_days == self.published_days()

    def test_acceptable_use_md(self) -> None:
        text = read(ACCEPTABLE_USE_MD)
        # \s+ rather than a space: the markdown is hard-wrapped, so either
        # phrase can straddle a line break.
        kept = re.search(r"kept for (\d+)\s+days", text)
        expires = re.search(r"expires in (\d+)\s+days", text)
        assert kept and expires, "retention window not stated in ACCEPTABLE_USE.md"
        assert int(kept.group(1)) == int(expires.group(1)) == self.published_days()

    @staticmethod
    def published_days() -> int:
        match = re.search(r"RETENTION_DAYS\s*=\s*(\d+)", read(DOCS_TS))
        if match is None:
            pytest.fail("could not find `RETENTION_DAYS` in web/lib/docs.ts")
        return int(match.group(1))


class TestNoUnmeasuredClaims:
    """
    The false-positive rate is the headline differentiator and is not measured
    yet. marketing/04-landing-page.md forbids placeholder statistics, so a
    number must not appear next to it until the calibration run is done.
    """

    def test_false_positive_rate_is_still_marked_unmeasured(self) -> None:
        text = read(METHODOLOGY_MD)
        section = text.split("## Measured false-positive rate", 1)
        assert len(section) == 2, "the false-positive rate section was renamed"
        body = section[1].split("\n## ", 1)[0]
        assert "Not yet measured" in body, (
            "METHODOLOGY.md no longer says the false-positive rate is unmeasured. "
            "If it has been measured, update web/app/methodology/page.tsx and the "
            "landing page Todo in the same change."
        )
        assert not re.search(r"\b\d+(\.\d+)?\s*%", body), (
            "a percentage appeared in the false-positive section. Publishing a "
            "rate that has not been measured is the one thing this document "
            "exists to avoid."
        )

    def test_severity_enum_is_covered(self) -> None:
        """A new severity would need a penalty, a doc row and a site row."""
        assert set(SEVERITY_PENALTY) == set(Severity)
