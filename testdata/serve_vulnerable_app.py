#!/usr/bin/env python3
"""Deliberately vulnerable app for exercising Overshare locally.

Serves a fake Supabase/Lovable-style SPA that leaks a service_role key, a Stripe
live key, a source map, a .env file, and a .git directory, with no security
headers and a reflected CORS policy.

All credentials are fake and non-functional.

    python3 testdata/serve_vulnerable_app.py
    overshare http://127.0.0.1:8000/ --unsafe-allow-private-ips --no-footprint
"""

from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tests import fixtures as fx  # noqa: E402

PORT = 8000

INDEX_HTML = f"""<!doctype html>
<html><head>
  <title>TaskFlow - built with Lovable</title>
  <script type="module" crossorigin src="/assets/index-a3f2b891.js"></script>
  <link rel="modulepreload" href="/assets/vendor-9b1e2f3a.js">
  <script src="https://cdn.gpteng.co/gptengineer.js"></script>
</head><body>
  <div id="root"></div>
  <script>
    window.__CONFIG__ = {{
      SUPABASE_URL: "https://abcdefghijklmnopqrst.supabase.co",
      SUPABASE_ANON_KEY: "{fx.SUPABASE_ANON_JWT}"
    }};
  </script>
  <img src="http://insecure-cdn.example.net/logo.png">
</body></html>
"""

INDEX_JS = f"""
import {{ createClient }} from "@supabase/supabase-js";
const supabase = createClient(
  "https://abcdefghijklmnopqrst.supabase.co",
  "{fx.SUPABASE_ANON_JWT}"
);
// left in during a late-night debugging session
const adminClient = createClient(
  "https://abcdefghijklmnopqrst.supabase.co",
  "{fx.SUPABASE_SERVICE_ROLE_JWT}"
);
const STRIPE_SECRET = "{fx.STRIPE_LIVE}";
const OPENAI_KEY = "{fx.OPENAI}";
const buildHash = "a3f2b891c7e4d5f60192837465afbdce";
export default supabase;
//# sourceMappingURL=index-a3f2b891.js.map
"""

VENDOR_JS = f"""
!function(){{"use strict";var e=window;
const GOOGLE_MAPS = "{fx.GOOGLE_API}";
const SENDGRID_KEY = "{fx.SENDGRID}";
var _0x4a2b9f=function(a,b){{return a+b}};
}}();
"""

SOURCE_MAP = json.dumps(
    {"version": 3, "file": "index-a3f2b891.js", "sources": ["src/App.tsx"], "mappings": "AAAA"}
)

ENV_FILE = f"""DATABASE_URL={fx.POSTGRES_URI}
STRIPE_SECRET_KEY={fx.STRIPE_LIVE}
AWS_ACCESS_KEY_ID={fx.AWS_KEY_ID}
GITHUB_TOKEN={fx.GITHUB_TOKEN}
"""

ROUTES = {
    "/": (INDEX_HTML, "text/html"),
    "/assets/index-a3f2b891.js": (INDEX_JS, "application/javascript"),
    "/assets/vendor-9b1e2f3a.js": (VENDOR_JS, "application/javascript"),
    "/assets/index-a3f2b891.js.map": (SOURCE_MAP, "application/json"),
    "/.env": (ENV_FILE, "text/plain"),
    "/.git/HEAD": ("ref: refs/heads/main\n", "text/plain"),
    "/.git/config": ("[core]\n\trepositoryformatversion = 0\n", "text/plain"),
}


class Handler(BaseHTTPRequestHandler):
    server_version = "nginx/1.18.0"
    sys_version = ""

    def do_GET(self) -> None:
        path = self.path.split("?")[0]
        if path not in ROUTES:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")
            return

        body, content_type = ROUTES[path]
        encoded = body.encode()

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("X-Powered-By", "Express")
        # Reflect any Origin, allow credentials: the classic CORS misconfiguration.
        origin = self.headers.get("Origin")
        if origin:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Credentials", "true")
        if path == "/":
            self.send_header("Set-Cookie", "session=abc123; Path=/")
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, fmt: str, *args) -> None:
        print(f"  [app] {fmt % args}", file=sys.stderr)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    print(f"Vulnerable test app on http://127.0.0.1:{port}/  (Ctrl-C to stop)")
    print("All credentials served here are fake.\n")
    try:
        ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
