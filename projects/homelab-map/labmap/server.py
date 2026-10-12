"""Serve a curated evidence snapshot on loopback. No host inspection or writes."""
import argparse
import hashlib
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PUBLIC = Path(__file__).resolve().parent / 'public'
ROOT = Path(__file__).resolve().parents[3]
FILES = {
    '/': (PUBLIC / 'index.html', 'text/html; charset=utf-8'),
    '/app.js': (PUBLIC / 'app.js', 'text/javascript; charset=utf-8'),
    '/core.mjs': (PUBLIC / 'core.mjs', 'text/javascript; charset=utf-8'),
    '/styles.css': (PUBLIC / 'styles.css', 'text/css; charset=utf-8'),
    '/data.json': (PUBLIC / 'data.json', 'application/json; charset=utf-8'),
    '/sources/current': (ROOT / 'docs/MAC_ACCEPTANCE_AND_INTEGRATION_2026-10-11.md', 'text/plain; charset=utf-8'),
    '/sources/purple': (ROOT / 'docs/purple-team-workflow-validation-2026-09-04.md', 'text/plain; charset=utf-8'),
    '/sources/migration': (ROOT / 'docs/ENTERPRISE_CYBER_LAB_V2.md', 'text/plain; charset=utf-8'),
}
CSP = "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass  # Do not retain access logs or echo request details.

    def respond(self, code, body=b'', kind='text/plain; charset=utf-8', head=False):
        self.send_response(code)
        for key, value in {
            'Content-Type': kind, 'Content-Length': str(len(body)),
            'Content-Security-Policy': CSP, 'Cache-Control': 'no-store',
            'X-Content-Type-Options': 'nosniff', 'X-Frame-Options': 'DENY',
            'Referrer-Policy': 'no-referrer',
            'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
        }.items():
            self.send_header(key, value)
        self.end_headers()
        if not head:
            self.wfile.write(body)

    def allowed(self):
        port = self.server.server_address[1]
        return (self.headers.get('Host') in {f'127.0.0.1:{port}', f'localhost:{port}'}
                and self.headers.get('Sec-Fetch-Site') not in {'cross-site', 'same-site'}
                and self.headers.get('Origin') in {None, f'http://127.0.0.1:{port}', f'http://localhost:{port}'})

    def serve(self, head=False):
        if not self.allowed():
            return self.respond(403, b'Local same-origin access required.', head=head)
        entry = FILES.get(self.path)
        if entry is None:
            return self.respond(404, b'Not found.', head=head)
        try:
            body = entry[0].read_bytes()
        except OSError:
            return self.respond(500, b'Curated source is unavailable.', head=head)
        if self.path.startswith('/sources/'):
            try:
                snapshot = json.loads((PUBLIC / 'data.json').read_text())
                source = snapshot['sources'][self.path.rsplit('/', 1)[1]]
                matches = hashlib.sha256(body).hexdigest() == source['sha256']
            except (OSError, ValueError, KeyError, TypeError):
                matches = False
            if not matches:
                return self.respond(409, b'Recorded source changed; rebaseline the curated snapshot.', head=head)
        self.respond(200, body, entry[1], head=head)

    def do_GET(self):
        self.serve()

    def do_HEAD(self):
        self.serve(head=True)

    def do_POST(self):
        self.respond(405, b'Read-only map; mutations are unavailable.')

    do_PUT = do_POST
    do_PATCH = do_POST
    do_DELETE = do_POST
    do_OPTIONS = do_POST


def make_server(port=4187):
    if not isinstance(port, int) or isinstance(port, bool) or not 0 <= port <= 65535:
        raise ValueError('Invalid local port')
    return ThreadingHTTPServer(('127.0.0.1', port), Handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=4187)
    args = parser.parse_args()
    if args.port < 1024 or args.port > 65535:
        parser.error('Choose a local port from 1024 to 65535.')
    with make_server(args.port) as server:
        print(f'Homelab map: http://127.0.0.1:{args.port} (curated snapshot; no VM access)', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
