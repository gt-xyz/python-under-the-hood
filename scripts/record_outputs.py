"""Record the real outputs the lessons display, so nothing is written from memory.

Run with the same Python version the site's Pyodide uses (currently CPython 3.14):

    python3.14 scripts/record_outputs.py            # writes data/recorded.json
    python3.14 scripts/record_outputs.py --check    # re-records and compares, ignoring object addresses (CI)
    python3.14 scripts/record_outputs.py --pandas   # prints pandas results to compare with lesson text

Bytecode differs between Python versions, so re-run this whenever Pyodide is upgraded. "seeds" holds a
full run (output, bytecode, stack trace, call stack, objects) of every example seeded in a runnable box,
made by the same tracer the page uses, so the machine view can show it before Python has started in the
browser.
"""
import ast
import dis
import json
import re
import struct
import sys
import types
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "recorded.json"
sys.path.insert(0, str(ROOT / "src"))
import helper  # noqa: E402  the same tracer that runs in the page
HIDE = ("RESUME", "NOP", "NOT_TAKEN", "CACHE")
NO_ARG = ("POP_TOP", "RETURN_VALUE", "GET_ITER", "END_FOR", "POP_ITER")


def instrs(src):
    """Bytecode for a snippet as [opname, argument] pairs, minus bookkeeping instructions."""
    out = []
    for i in dis.get_instructions(compile(src, "<cell>", "exec")):
        if i.opname in HIDE:
            continue
        arg = i.argrepr
        if isinstance(i.argval, types.CodeType):
            arg = f"code for {i.argval.co_name}"  # instead of a repr with a memory address
        elif not arg and i.argval is not None and i.opname not in NO_ARG:
            arg = repr(i.argval)
        out.append([i.opname, arg])
    if out[-2:] == [["LOAD_CONST", "None"], ["RETURN_VALUE", ""]]:
        out = out[:-2]  # the implicit "return None" at the end of every module
    return out


def seeded_examples():
    """Every snippet a learner can run: tryIt("...") boxes and the sandbox's default code, from src/page.html."""
    page = (ROOT / "src" / "page.html").read_text()
    found = {json.loads('"' + m + '"') for m in re.findall(r'tryIt\("((?:[^"\\]|\\.)*)"', page)}
    sandbox = re.search(r'<textarea id="src"[^>]*>([^<]*)</textarea>', page)
    if sandbox:
        found.add(sandbox.group(1).replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&"))
    return sorted(found)


def depends_on_environment(src):
    """Examples whose output is about the machine they run on; they are only shown live, in the page."""
    return "os.getcwd" in src or "sys.path" in src


def normalized(d):
    """The recorded data with object addresses blanked, so two runs can be compared."""
    if isinstance(d, dict):  # JSON turns the heap's integer keys (object ids) into strings
        return {("0" if k.isdigit() and int(k) >= 1 << 24 else k): normalized(v) for k, v in d.items()}
    if isinstance(d, list):
        return [normalized(v) for v in d]
    if isinstance(d, int) and not isinstance(d, bool) and d >= 1 << 24:
        return 0
    if isinstance(d, str):
        return re.sub(r"0x[0-9a-fA-F]+", "0x", d)
    return d


def fbits(x):
    s = format(struct.unpack(">Q", struct.pack(">d", x))[0], "064b")
    return {"sign": s[0], "exp": s[1:12], "frac": s[12:],
            "exact": format(Decimal(x), "f") if x == x else "nan"}


def record():
    d = {"python": sys.version.split()[0]}
    d["t1"] = instrs("total = price * qty")
    d["t2"] = instrs("b = a\nb.append(4)")
    d["t3"] = instrs("x = a + b")
    d["t3_folded"] = instrs("x = 0.1 + 0.2")
    d["t3_bits"] = {k: fbits(v) for k, v in {"0.1": 0.1, "0.2": 0.2, "0.1 + 0.2": 0.1 + 0.2, "0.3": 0.3}.items()}
    d["t3_repr"] = repr(0.1 + 0.2)
    d["t4_loop"] = instrs("count = 0\nfor v in values:\n    if v > 0:\n        count += 1")
    d["t4_mask"] = instrs("count = (arr > 0).sum()")
    d["t5"] = instrs("mask = (df.a > 0) & (df.b == 1)")
    d["t5_bad_ast"] = ast.unparse(ast.parse("df.a > 0 & df.b == 1").body[0].value)
    nan = float("nan")
    d["t6"] = instrs("keep = df[df.x != 0]")
    d["t6_bits"] = fbits(nan)
    d["t6_eq"] = [nan == nan, nan != 0, nan > 0]
    d["t7"] = instrs("df[df.x > 0]['y'] = 5")
    d["t7_good"] = instrs("df.loc[df.x > 0, 'y'] = 5")
    d["imm"] = instrs("y = x\ny += 1")
    d["seeds"] = {src: json.loads(helper._decompose(src)) for src in seeded_examples() if not depends_on_environment(src)}
    d["t_names"] = instrs("x = 5\nx = 'five'")
    d["t_def"] = instrs("def add_tax(price):\n    return price * 1.25\n\ntotal = add_tax(100)")
    return d


def write():
    d = record()
    OUT.write_text(json.dumps(d, indent=1) + "\n")
    print(f"Wrote {OUT} with Python {d['python']} ({len(d['seeds'])} seeds)")


def check():
    old = json.loads(OUT.read_text())
    new = record()
    if normalized(old) != normalized(new):
        for k in sorted(set(old) | set(new)):
            if normalized(old.get(k)) != normalized(new.get(k)):
                print("differs:", k)
        raise SystemExit(f"{OUT} is out of date: run scripts/record_outputs.py")
    print(f"{OUT} is current ({len(new['seeds'])} seeds)")


def pandas_report():
    """pandas results that are currently written into lesson text. Compare by eye; see docs/HANDOFF.md."""
    import warnings
    import numpy as np
    import pandas as pd
    warnings.simplefilter("always")
    print("pandas", pd.__version__, "numpy", np.__version__)
    df = pd.DataFrame({"x": [1, -1, 2], "y": [0, 0, 0]}); df2 = df; df2["y"] = 9
    print("alias:", df.y.tolist())
    df = pd.DataFrame({"x": [1, -1, 2], "y": [0, 0, 0]}); df3 = df.copy(); df3["y"] = 9
    print("copy:", df.y.tolist())
    df = pd.DataFrame({"x": [1, -1, 2], "y": [0, 0, 0]})
    with warnings.catch_warnings(record=True) as w:
        df[df.x > 0]["y"] = 5
        print("chained:", df.y.tolist(), "|", [type(x.message).__name__ for x in w])
    df.loc[df.x > 0, "y"] = 5
    print("loc:", df.y.tolist())
    print("Series([1, None]).dtype:", pd.Series([1, None]).dtype)
    print("Int64:", pd.Series([1, None], dtype="Int64").tolist())
    print("int8 wrap:", np.array([127], dtype="int8") + 1)
    print("np.array([1, 2.5]).dtype:", np.array([1, 2.5]).dtype, "| [1,'a']:", np.array([1, "a"]).dtype)
    print("text column dtype:", pd.DataFrame({"name": ["Ana", "Ben"]}).dtypes.to_dict())
    try:
        pd.DataFrame({"score": [90]})["Score"]
    except KeyError as e:
        print("KeyError:", e)
    print("--- What pandas adds (lesson 9)")
    print(pd.Series([4.5, 3.0, 12.25]))
    df = pd.DataFrame({"name": ["Ana", "Ben", "Cy"], "score": [90, 85, 72]})
    print(df); print(df["score"])
    print(repr((pd.Series([1, 2, 3]).dtype, pd.Series([1, 2.5]).dtype, pd.Series([1, "a"]).dtype)))
    print(df.score > 86); print(df[df.score > 86])
    df.sort_values("score"); print(df)


if __name__ == "__main__":
    pandas_report() if "--pandas" in sys.argv else check() if "--check" in sys.argv else write()
