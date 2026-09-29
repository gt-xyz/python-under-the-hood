# CLAUDE.md

Guidance for Claude Code working in this repo. Read docs/HANDOFF.md for history and next steps, docs/PLAN.md for the product plan.

## What this is

An interactive course and full-stack explorer teaching what code actually does, top-down from a line of Python to bytecode, memory, bits, CPU and logic gates. Audience: people new to computing, often writing Python for data work, who dislike black boxes. The owner has a computer engineering background (C++, architecture) and wants depth to be available on demand.

## Commands

    python3 scripts/build.py                 # src/page.html + data/recorded.json -> site/index.html
    python3 scripts/serve.py [--lan]         # serve site/ on :8000
    python3 tests/walkthrough.py             # needs the server running and Playwright + Chromium
    python3.14 scripts/record_outputs.py     # re-record bytecode/bits (Python must match Pyodide's)
    python3 scripts/record_outputs.py --pandas   # print pandas results to check lesson text
    scripts/fetch_pyodide.sh [version]       # replace site/py/ runtime

Always rebuild after editing src/page.html, and run the walkthrough before calling a change done.

## Rules for content

- **Real outputs only.** Any bytecode, bit pattern, error message, traceback or library result shown to learners must come from actually running it. Bytecode and bits come from data/recorded.json. pandas outputs are currently typed into lesson text; verify them with `record_outputs.py --pandas` and note the pandas version.
- **Concepts over tools.** Teach the idea; tools are labeled examples. Tag every code example with its layer: `py` Python, `std` standard library, `np` NumPy, `pd` pandas, `jp` Jupyter, `sh` Terminal.
- **Content is never gated.** A prediction (PRIMM) blurs only its answer (`.ans`, or the leading `.out` boxes, or the first paragraph of `.reveal`). Everything else in a section stays visible. Make sure visible content doesn't give the answer away.
- **Simplified layers are labeled.** CPU, cache and logic-gate material is simplified today; say so.
- **Audience-neutral framing.** Don't assume data work in labels or headings ("In practice", not "In your data work"). Examples may use pandas.

## Terminology (settled with the owner)

- Lessons are divided into **sections**. Buttons: Previous / Next section / Next lesson. The progress bar says "Section 2 of 3".
- **Step** only means running one instruction in a code runner (Step / Step back / Reset), as in a debugger.
- Don't use "Python" as a count noun: say a **Python process** or a **Python installation**.
- Don't use "floors" or "tours" (early prototype terms). The layers are Code, Bytecode, Memory, Bits, CPU, Logic gates.
- Headings state the takeaway ("A filter builds a new object"), not a question.

## Writing style

Plain, direct, short sentences. Define every technical term on first use for someone with no computing background. No em-dash asides, no "not X but Y" framing.

## Code map (src/page.html)

One file, roughly in this order: CSS tokens (light and dark) and component styles; HTML shell; `DATA` placeholder filled by build.py; helpers (`OPS` descriptions, `bcTable`, `codeBlock` + layer tags, `renderPile` stack drawing, `stepper` bytecode runner, float bit helpers); lesson components (`predict`/`wirePredict`/`reveal`, `tryIt`/`wireTry`, `runPy`); `frameStepper` call-stack runner; `LESSONS` (original 8) and `EXTRA` (4 added later), merged and ordered in one IIFE; `PY_HELPER` (Python run inside Pyodide: runs code, collects bytecode, objects, bits, tracebacks); `loadPython`; the shell (`go()`, lesson nav, sandbox, `jump()`).
