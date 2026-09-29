"""Build the deployable site: src/page.html + data/recorded.json -> site/index.html.

    python3 scripts/build.py

site/py/ holds the Python runtime (Pyodide) and is not touched here; see scripts/fetch_pyodide.sh.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLACEHOLDER = "/*DATA*/null"

HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
"""
# Minimal reset. src/page.html was first written for the claude.ai artifact viewer, which wraps
# pages in its own skeleton; this recreates that skeleton for a standalone site.
RESET = """<style>html{color-scheme:light}body{margin:0;font-size:14px}img{max-width:100%}[hidden]{display:none!important}
:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}</style>"""


def main():
    page = (ROOT / "src" / "page.html").read_text()
    data = json.loads((ROOT / "data" / "recorded.json").read_text())
    if PLACEHOLDER not in page:
        raise SystemExit(f"{PLACEHOLDER} not found in src/page.html")
    page = page.replace(PLACEHOLDER, json.dumps(data, separators=(",", ":")))
    split = page.index("</style>") + len("</style>")  # title, fonts and styles go in <head>
    html = HEAD + page[:split] + "\n" + RESET + "\n</head>\n<body>\n" + page[split:] + "\n</body>\n</html>\n"
    out = ROOT / "site" / "index.html"
    out.write_text(html)
    print(f"Wrote {out} ({len(html):,} bytes)")


if __name__ == "__main__":
    main()
