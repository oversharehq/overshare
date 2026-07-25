from __future__ import annotations

import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from urllib.parse import urljoin

SOURCE_MAP_RE = re.compile(r"//[#@]\s*sourceMappingURL=([^\s*'\"]+)")

# Paths that should never be readable but frequently are on misconfigured hosts.
EXPOSED_PATH_PROBES = (
    "/.env",
    "/.env.local",
    "/.env.production",
    "/.git/HEAD",
    "/.git/config",
    "/config.json",
    "/.aws/credentials",
)


@dataclass
class PageAssets:
    html: str = ""
    script_urls: list[str] = field(default_factory=list)
    inline_scripts: list[str] = field(default_factory=list)
    stylesheet_urls: list[str] = field(default_factory=list)
    insecure_urls: list[str] = field(default_factory=list)


class _AssetParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.script_urls: list[str] = []
        self.inline_scripts: list[str] = []
        self.stylesheet_urls: list[str] = []
        self.insecure_urls: list[str] = []
        self._in_script = False

    def _record(self, raw: str) -> str:
        resolved = urljoin(self.base_url, raw)
        if resolved.startswith("http://") and self.base_url.startswith("https://"):
            self.insecure_urls.append(resolved)
        return resolved

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k.lower(): (v or "") for k, v in attrs}

        if tag == "script":
            src = a.get("src")
            if src:
                self.script_urls.append(self._record(src))
            else:
                self._in_script = True

        elif tag == "link":
            href = a.get("href")
            if not href:
                return
            rel = a.get("rel", "").lower()
            as_attr = a.get("as", "").lower()
            if rel in ("modulepreload", "preload") and as_attr in ("script", "", "modulepreload"):
                self.script_urls.append(self._record(href))
            elif rel == "stylesheet":
                self.stylesheet_urls.append(self._record(href))

        elif tag in ("img", "iframe", "source", "video", "audio"):
            src = a.get("src")
            if src:
                self._record(src)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script":
            self._in_script = False

    def handle_data(self, data: str) -> None:
        if self._in_script and data.strip():
            self.inline_scripts.append(data)


def parse_assets(html: str, base_url: str) -> PageAssets:
    parser = _AssetParser(base_url)
    parser.feed(html)
    parser.close()

    def unique(items: list[str]) -> list[str]:
        return list(dict.fromkeys(items))

    return PageAssets(
        html=html,
        script_urls=unique(parser.script_urls),
        inline_scripts=parser.inline_scripts,
        stylesheet_urls=unique(parser.stylesheet_urls),
        insecure_urls=unique(parser.insecure_urls),
    )


def find_source_map_url(js: str, js_url: str) -> str | None:
    matches = SOURCE_MAP_RE.findall(js)
    if not matches:
        return None
    ref = matches[-1].strip()
    if ref.startswith("data:"):
        return None
    return urljoin(js_url, ref)
