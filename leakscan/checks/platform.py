from __future__ import annotations

import re

from ..findings.model import Confidence, Finding, Severity

SUPABASE_URL_RE = re.compile(r"https://([a-z0-9]{20})\.supabase\.co")
FIREBASE_PROJECT_RE = re.compile(r"['\"]projectId['\"]\s*:\s*['\"]([A-Za-z0-9_-]+)['\"]")
CONVEX_URL_RE = re.compile(r"https://([a-z-]+-\d+)\.convex\.cloud")


def _any(content: str, needles: tuple[str, ...]) -> bool:
    return any(n in content for n in needles)


def detect_backend(content: str) -> dict:
    backend: dict = {}

    if _any(content, ("supabase.co", "@supabase/supabase-js", "supabase.auth")):
        backend["backend"] = "supabase"
        m = SUPABASE_URL_RE.search(content)
        if m:
            backend["project_ref"] = m.group(1)
            backend["api_url"] = m.group(0)
    elif _any(content, ("firebaseapp.com", "firebaseio.com", "firebase/app", "initializeApp")):
        backend["backend"] = "firebase"
        m = FIREBASE_PROJECT_RE.search(content)
        if m:
            backend["project_id"] = m.group(1)
    elif "convex.cloud" in content:
        backend["backend"] = "convex"
        m = CONVEX_URL_RE.search(content)
        if m:
            backend["deployment"] = m.group(1)
    elif _any(content, ("pocketbase", "PocketBase")):
        backend["backend"] = "pocketbase"

    return backend


def detect_builder(content: str, url: str, headers: dict[str, str]) -> str | None:
    haystack = f"{content}\n{url}"
    if _any(haystack, ("lovable.app", "lovableproject.com", "gpteng.co", "lovable-tagger")):
        return "lovable"
    if _any(haystack, ("bolt.new", "stackblitz", "webcontainer")):
        return "bolt"
    if _any(haystack, ("v0.dev", "v0-")):
        return "v0"
    if _any(haystack, ("replit.dev", "repl.co", "replit.com")):
        return "replit"
    if "base44" in haystack:
        return "base44"
    return None


def detect_framework(content: str, html: str) -> str | None:
    if "__NEXT_DATA__" in html or "/_next/" in html:
        return "nextjs"
    if "__NUXT__" in html or "/_nuxt/" in html:
        return "nuxt"
    if "__SVELTEKIT" in html or "svelte-" in content:
        return "sveltekit"
    if "astro-island" in html:
        return "astro"
    if _any(content, ("react-dom", "React.createElement", "_jsxDEV", "createRoot")):
        return "react"
    if _any(content, ("createApp", "__vue__", "Vue.createApp")):
        return "vue"
    return None


def detect_host(headers: dict[str, str]) -> str | None:
    if "x-vercel-id" in headers or "vercel" in headers.get("server", "").lower():
        return "vercel"
    if "x-nf-request-id" in headers:
        return "netlify"
    if "x-render-origin-server" in headers:
        return "render"
    if headers.get("server", "").lower() == "cloudflare" or "cf-ray" in headers:
        return "cloudflare"
    if "x-github-request-id" in headers:
        return "github-pages"
    if "fly-request-id" in headers:
        return "fly.io"
    return None


def fingerprint(content: str, html: str, url: str, headers: dict[str, str]) -> tuple[dict, list[Finding]]:
    platform: dict = {}
    platform.update(detect_backend(content))

    builder = detect_builder(content, url, headers)
    if builder:
        platform["builder"] = builder

    framework = detect_framework(content, html)
    if framework:
        platform["framework"] = framework

    host = detect_host(headers)
    if host:
        platform["host"] = host

    findings: list[Finding] = []
    if platform:
        summary = ", ".join(f"{k}={v}" for k, v in platform.items())
        findings.append(
            Finding(
                check_id="platform.fingerprint",
                severity=Severity.INFO,
                confidence=Confidence.CERTAIN,
                title="Platform fingerprint",
                detail=f"Identified stack: {summary}.",
                evidence=summary,
                location=url,
            )
        )

    if platform.get("backend") == "supabase":
        findings.append(
            Finding(
                check_id="platform.supabase.rls_untested",
                severity=Severity.INFO,
                confidence=Confidence.CERTAIN,
                title="Supabase detected — Row Level Security not tested by this scan",
                detail=(
                    "This app talks to Supabase from the browser, so every table in the public "
                    "schema is reachable by anyone holding the anon key, which ships to every "
                    "visitor. Whether that is safe depends entirely on RLS policies. A passive "
                    "scan cannot determine this."
                ),
                evidence=platform.get("api_url", "supabase"),
                location=url,
                remediation=(
                    "Verify RLS is enabled on every table and that each has a policy scoping "
                    "rows to the authenticated user. Enabling RLS without adding a policy denies "
                    "all access; adding a permissive policy like USING (true) is equivalent to "
                    "no protection at all."
                ),
            )
        )

    return platform, findings
