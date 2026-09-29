# Python Under the Hood

An interactive introduction for people new to computing: what your Python code is actually doing, from the code you write down to the bits. Twelve lessons plus a sandbox, running real CPython 3.14 in the browser via [Pyodide](https://pyodide.org/).

## Quick start

    python3 scripts/serve.py          # http://localhost:8000
    python3 scripts/serve.py --lan    # also reachable from a phone on the same Wi-Fi

`site/` is ready to deploy as is. Open it through a server, not as a file: browsers block the Python runtime from `file://`.

## Layout

    src/page.html            the whole app: styles, lessons, components (one file for now)
    data/recorded.json       bytecode and bit patterns recorded from real CPython
    site/index.html          built output (generated, but committed so site/ deploys as is)
    site/py/                 Pyodide runtime, about 13 MB
    scripts/build.py         src + data -> site/index.html
    scripts/record_outputs.py  re-record data/recorded.json from real Python
    scripts/fetch_pyodide.sh   download a Pyodide version into site/py/
    scripts/serve.py         local server with the right MIME types
    tests/walkthrough.py     headless walk through every section, desktop and phone
    docs/PLAN.md             product plan: vision, curriculum, roadmap
    docs/HANDOFF.md          current state, decisions, known issues, next steps

## Workflow

    python3.14 scripts/record_outputs.py   # only when Python/Pyodide versions change
    python3 scripts/build.py
    python3 scripts/serve.py &
    python3 tests/walkthrough.py

## Deploy

Copy `site/` to any static host. It must serve `.wasm` as `application/wasm` and `.mjs`/`.js` as JavaScript. A strict Content-Security-Policy needs `'wasm-unsafe-eval'` in `script-src`, or in-page Python won't start.

Browser support follows Pyodide: Chrome and Firefox 112+, Safari 16.4+ (including iPhone and iPad).
