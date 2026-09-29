# Python Under the Hood

[![tests](https://github.com/gtaylor214/python-under-the-hood/actions/workflows/test.yml/badge.svg)](https://github.com/gtaylor214/python-under-the-hood/actions/workflows/test.yml)

An interactive introduction for people new to computing: what your Python code is actually doing, from the code you write down to the bits. Sixteen short lessons in four groups (the machine, the language, tools and libraries, bits and memory) plus a sandbox, running real CPython 3.14 in the browser via [Pyodide](https://pyodide.org/).

## Quick start

    python3 scripts/serve.py          # http://localhost:8000
    python3 scripts/serve.py --lan    # also reachable from a phone on the same Wi-Fi

`site/` is ready to deploy as is. Open it through a server, not as a file: browsers block the Python runtime from `file://`.

## Layout

    src/page.html            the whole app: styles, lessons, components (one file for now)
    src/helper.py            the Python that runs in the page: runs a cell, records its bytecode,
                             value stack (a small bytecode interpreter checked against the real run)
                             and call stack (sys.settrace)
    data/recorded.json       bytecode, stack states and bit patterns recorded from real CPython
    site/index.html          built output (generated, but committed so site/ deploys as is)
    site/py/                 Pyodide runtime, about 13 MB
    scripts/build.py         src/page.html + src/helper.py + data -> site/index.html
    scripts/record_outputs.py  re-record data/recorded.json from real Python
    scripts/fetch_pyodide.sh   download a Pyodide version into site/py/
    scripts/serve.py         local server with the right MIME types
    tests/test_helper.py     receipts: the tracer against real CPython 3.14 (see Testing)
    tests/walkthrough.py     headless walk through every section, desktop and phone
    docs/PLAN.md             product plan: vision, curriculum, roadmap
    docs/HANDOFF.md          current state, decisions, known issues, next steps

## Workflow

    python3.14 scripts/record_outputs.py   # only when Python/Pyodide versions change
    python3 scripts/build.py
    python3 scripts/serve.py &
    python3.14 tests/test_helper.py
    python3 tests/walkthrough.py

## Testing

This is a learning tool, so everything it shows about bytecode has receipts:

- `tests/test_helper.py` runs every code example seeded in the lessons through `src/helper.py` on real
  CPython 3.14 and checks that the bytecode shown equals what the `dis` module reports, that the live
  stack trace agrees with a plain run of the same code, that the recorded stack states used by the
  lessons' steppers are what the tracer produces, and that each stack's depth matches CPython's own
  stack-effect table. It needs Python 3.14 (`uv python install 3.14` if yours is older).
- `tests/walkthrough.py` opens every section in headless Chromium at desktop and phone sizes, runs
  each example in the page's own Python, and steps the live bytecode stepper it produces.
- `.github/workflows/test.yml` runs both on every push, and fails if `data/recorded.json` or
  `site/index.html` is stale.

## Deploy

Copy `site/` to any static host. It must serve `.wasm` as `application/wasm` and `.mjs`/`.js` as JavaScript. A strict Content-Security-Policy needs `'wasm-unsafe-eval'` in `script-src`, or in-page Python won't start.

Browser support follows Pyodide: Chrome and Firefox 112+, Safari 16.4+ (including iPhone and iPad).
