"""Serve site/ for local testing.

    python3 scripts/serve.py          # http://localhost:8000
    python3 scripts/serve.py --lan    # also prints an address for your phone on the same Wi-Fi

Opening site/index.html directly (file://) won't work: browsers block the Python runtime that way.
"""
import functools
import http.server
import socket
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / "site"


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                      ".wasm": "application/wasm", ".mjs": "text/javascript",
                      ".js": "text/javascript", ".html": "text/html; charset=utf-8"}


def main():
    lan = "--lan" in sys.argv
    port = 8000
    print(f"Serving {SITE} on http://localhost:{port}")
    if lan:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            print(f"On your phone (same Wi-Fi): http://{s.getsockname()[0]}:{port}")
            s.close()
        except OSError:
            print(f"Find this computer's local IP address and open http://<that address>:{port} on your phone.")
    handler = functools.partial(Handler, directory=str(SITE))
    http.server.ThreadingHTTPServer(("0.0.0.0" if lan else "127.0.0.1", port), handler).serve_forever()


if __name__ == "__main__":
    main()
