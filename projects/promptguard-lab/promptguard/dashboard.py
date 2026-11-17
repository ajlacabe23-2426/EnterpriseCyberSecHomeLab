"""Local-only, standard-library PromptGuard review dashboard.

No network access beyond 127.0.0.1, source storage, model calls, or
execution of any text submitted for screening.
"""

from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path

from .detector import scan_text

_WEB = Path(__file__).resolve().parent / "web"
_BODY_LIMIT = 450_000
_CSP = (
    "default-src 'none'; script-src 'self'; style-src 'self'; "
    "connect-src 'self'; img-src 'none'; font-src 'self'; "
    "base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
)
_STATIC = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
}


class PromptGuardServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


class Handler(BaseHTTPRequestHandler):
    server_version = "PromptGuardLab/1"
    sys_version = ""

    def log_message(self, format: str, *args: object) -> None:
        # Avoid logging user-submitted text or request paths.
        return

    def _headers(self, status: int, content_type: str, length: int) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Content-Security-Policy", _CSP)
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        self.end_headers()

    def _json(self, status: int, payload: dict[str, object]) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._headers(status, "application/json; charset=utf-8", len(encoded))
        self.wfile.write(encoded)

    def _error(self, status: int, message: str) -> None:
        self._json(status, {"error": message})

    def _valid_host(self) -> bool:
        host = self.headers.get("Host", "")
        port = self.server.server_port
        return host in {f"127.0.0.1:{port}", f"localhost:{port}"}

    def _valid_origin(self) -> bool:
        origin = self.headers.get("Origin", "")
        port = self.server.server_port
        return origin in {f"http://127.0.0.1:{port}", f"http://localhost:{port}"}

    def do_GET(self) -> None:
        if not self._valid_host():
            return self._error(403, "Local host required")
        item = _STATIC.get(self.path)
        if item is None:
            return self._error(404, "Not found")
        filename, content_type = item
        try:
            contents = (_WEB / filename).read_bytes()
        except OSError:
            return self._error(503, "Dashboard asset unavailable")
        self._headers(200, content_type, len(contents))
        self.wfile.write(contents)

    def do_POST(self) -> None:
        if not self._valid_host():
            return self._error(403, "Local host required")
        if self.path != "/api/analyze":
            return self._error(404, "Not found")
        if (
            not self._valid_origin()
            or self.headers.get("Sec-Fetch-Site", "same-origin") not in {"same-origin", "none"}
        ):
            return self._error(403, "Same-origin browser request required")
        if self.headers.get("Content-Type", "").split(";")[0].strip().lower() != "application/json":
            return self._error(415, "JSON content type required")
        try:
            length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            return self._error(411, "Content-Length required")
        if length < 1:
            return self._error(400, "Input required")
        if length > _BODY_LIMIT:
            return self._error(413, "Request too large")
        try:
            payload = json.loads(self.rfile.read(length))
        except (UnicodeError, json.JSONDecodeError):
            return self._error(400, "Invalid JSON")
        if not isinstance(payload, dict) or "text" not in payload or not set(payload) <= {"text", "source_type"}:
            return self._error(400, "Expected text and optional source_type only")
        try:
            report = scan_text(payload["text"], source_type=payload.get("source_type", "unknown"))
        except (TypeError, ValueError):
            return self._error(422, "Invalid or oversized text")
        self._json(200, report)

    def do_OPTIONS(self) -> None:
        self._error(405, "Method not allowed")


def make_server(port: int = 4186) -> PromptGuardServer:
    if not isinstance(port, int) or not 0 <= port <= 65535:
        raise ValueError("Port must be between 0 and 65535")
    return PromptGuardServer(("127.0.0.1", port), Handler)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the offline PromptGuard review dashboard on loopback only")
    parser.add_argument("--port", type=int, default=4186)
    args = parser.parse_args(argv)
    server = make_server(args.port)
    print(f"PromptGuard Lab dashboard: http://127.0.0.1:{server.server_port}")
    print("Local educational screening only. Press Ctrl+C to stop.")
    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
