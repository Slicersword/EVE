"""M01 - local web server (Python standard library only): the face, a control page and a small JSON API.

Default: listens on 127.0.0.1 only. If the owner sets network.host to 0.0.0.0 the home LAN can reach it;
then every request except the face page itself needs the token. Commands ALWAYS need the token.
"""
from __future__ import annotations
import hmac, ipaddress, json, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

WEB = Path(__file__).resolve().parent / "web"
MAX_BODY = 4096
PAGES = {"/": "face.html", "/control": "control.html"}


def host_allowed(host_header: str) -> bool:
    """Blocks DNS-rebinding: the browser must be addressing this Pi by IP, localhost or *.local."""
    host = (host_header or "").rsplit(":", 1)[0].strip("[]").lower()
    if host in ("localhost",) or host.endswith(".local"):
        return True
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False


def make_handler(runtime):
    class Handler(BaseHTTPRequestHandler):
        server_version = "EVE"
        sys_version = ""
        protocol_version = "HTTP/1.1"

        def log_message(self, *args):                    # no access log: nothing private ends up on disk
            pass

        def _send(self, code, body: bytes, ctype="application/json"):
            self.send_response(code)
            self.send_header("Content-Type", ctype + "; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Content-Security-Policy", "default-src 'self' 'unsafe-inline'; connect-src 'self'")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, code, obj):
            self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"))

        def _local(self) -> bool:
            return self.client_address[0] in ("127.0.0.1", "::1")

        def _token_ok(self, query=None) -> bool:
            given = self.headers.get("X-EVE-Token") or ((query or {}).get("t") or [""])[0]
            return isinstance(given, str) and hmac.compare_digest(given.encode(), runtime.token.encode())

        def do_GET(self):
            if not host_allowed(self.headers.get("Host", "")):
                return self._json(403, {"ok": False, "message": "bad host"})
            url = urlparse(self.path)
            if url.path in PAGES:
                return self._send(200, (WEB / PAGES[url.path]).read_bytes(), "text/html")
            if url.path == "/api/status":
                if not (self._local() or self._token_ok(parse_qs(url.query))):
                    return self._json(401, {"ok": False, "message": "token required"})
                return self._json(200, runtime.status())
            self._json(404, {"ok": False, "message": "not found"})

        def do_POST(self):
            if not host_allowed(self.headers.get("Host", "")):
                return self._json(403, {"ok": False, "message": "bad host"})
            if urlparse(self.path).path != "/api/command":
                return self._json(404, {"ok": False, "message": "not found"})
            if not self._token_ok():
                return self._json(401, {"ok": False, "message": "token required"})
            try:
                length = int(self.headers.get("Content-Length", ""))
            except ValueError:
                return self._json(411, {"ok": False, "message": "length required"})
            if not 0 < length <= MAX_BODY:
                return self._json(413, {"ok": False, "message": "request too large"})
            try:
                body = json.loads(self.rfile.read(length).decode("utf-8"))
                name, args = body["name"], body.get("args", {})
            except (ValueError, KeyError, TypeError, UnicodeError):
                return self._json(400, {"ok": False, "message": "bad JSON"})
            ok, message = runtime.execute(name, args, source="owner")
            self._json(200, {"ok": bool(ok), "message": message})

    return Handler


def serve(runtime, host: str, port: int) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((host, port), make_handler(runtime))
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, name="eve3-http", daemon=True).start()
    return server
