from __future__ import annotations

from overshare.fetch.assets import find_source_map_url, parse_assets

HTML = """
<!doctype html>
<html><head>
  <script type="module" crossorigin src="/assets/index-a3f2.js"></script>
  <link rel="modulepreload" href="/assets/vendor-9b1.js">
  <link rel="stylesheet" href="/assets/index-c4d5.css">
  <script src="https://cdn.example.net/analytics.js"></script>
  <script src="http://insecure.example.net/legacy.js"></script>
</head><body>
  <script>window.__CONFIG__={apiUrl:"https://abcdefghijklmnopqrst.supabase.co"};</script>
  <img src="http://insecure.example.net/logo.png">
</body></html>
"""


def test_extracts_and_resolves_script_urls():
    assets = parse_assets(HTML, "https://app.test/index.html")
    assert "https://app.test/assets/index-a3f2.js" in assets.script_urls
    assert "https://app.test/assets/vendor-9b1.js" in assets.script_urls
    assert "https://cdn.example.net/analytics.js" in assets.script_urls


def test_extracts_stylesheets_separately():
    assets = parse_assets(HTML, "https://app.test/index.html")
    assert assets.stylesheet_urls == ["https://app.test/assets/index-c4d5.css"]
    assert not any(u.endswith(".css") for u in assets.script_urls)


def test_captures_inline_script_content():
    assets = parse_assets(HTML, "https://app.test/index.html")
    assert any("supabase.co" in s for s in assets.inline_scripts)


def test_flags_plaintext_subresources_on_https_page():
    assets = parse_assets(HTML, "https://app.test/index.html")
    assert "http://insecure.example.net/legacy.js" in assets.insecure_urls
    assert "http://insecure.example.net/logo.png" in assets.insecure_urls


def test_no_mixed_content_flagged_on_http_page():
    assets = parse_assets(HTML, "http://app.test/index.html")
    assert assets.insecure_urls == []


def test_script_urls_deduplicated():
    html = '<script src="/a.js"></script><script src="/a.js"></script>'
    assert parse_assets(html, "https://app.test/").script_urls == ["https://app.test/a.js"]


def test_finds_source_map_reference():
    js = "console.log(1);\n//# sourceMappingURL=index-a3f2.js.map"
    assert find_source_map_url(js, "https://app.test/assets/index-a3f2.js") == (
        "https://app.test/assets/index-a3f2.js.map"
    )


def test_inline_data_uri_source_map_ignored():
    js = "//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozfQ=="
    assert find_source_map_url(js, "https://app.test/a.js") is None


def test_no_source_map_reference():
    assert find_source_map_url("console.log(1)", "https://app.test/a.js") is None


def test_malformed_html_does_not_crash():
    assets = parse_assets("<script src=/a.js><div><p>unclosed", "https://app.test/")
    assert "https://app.test/a.js" in assets.script_urls
