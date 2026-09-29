"""Receipts for the bytecode and stack views: check src/helper.py against real CPython.

    python3.14 tests/test_helper.py        # the Python must match the site's Pyodide (3.14)

What is checked:
- every runnable example seeded in the lessons and the sandbox produces a live stack trace, and that
  trace agrees with a plain run of the same code (the helper drops the trace otherwise, so a missing
  trace is a failure here);
- the bytecode the helper shows equals what the dis module reports, and matches data/recorded.json;
- the stack states recorded for the lessons' curated steppers are what the tracer produces, and each
  stack's depth matches CPython's own stack-effect table for the instruction sequence;
- the call-stack recording of the functions lesson's examples has the frames the lesson describes;
- code the tracer doesn't handle degrades to a reason, never a crash.
"""
import dis
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
import helper  # noqa: E402
import record_outputs  # noqa: E402

PAGE = (ROOT / "src" / "page.html").read_text()
RECORDED = json.loads((ROOT / "data" / "recorded.json").read_text())


def js_string(lit):
    """Decode a double-quoted JavaScript string literal from page.html."""
    return json.loads('"' + lit + '"')


def seeded_examples():
    """Every snippet a learner can run: tryIt("...") boxes and the sandbox's default code."""
    found = {js_string(m) for m in re.findall(r'tryIt\("((?:[^"\\]|\\.)*)"', PAGE)}
    sandbox = re.search(r'<textarea id="src"[^>]*>([^<]*)</textarea>', PAGE)
    if sandbox:
        found.add(sandbox.group(1).replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&"))
    return sorted(found)


def decompose(src):
    return json.loads(helper._decompose(src))


class SeededExamples(unittest.TestCase):
    def test_examples_found(self):
        self.assertGreater(len(seeded_examples()), 10)

    def test_every_example_traces(self):
        for src in seeded_examples():
            with self.subTest(src=src):
                r = decompose(src)
                if not r["instrs"]:
                    continue  # a bare constant expression compiles to nothing
                self.assertIsNotNone(r["trace"], r["trace_why"])
                self.assertEqual([s["i"] for s in r["trace"] if s["i"] >= len(r["instrs"])], [])

    def test_bytecode_matches_dis(self):
        for src in seeded_examples():
            with self.subTest(src=src):
                self.assertEqual(decompose(src)["instrs"], record_outputs.instrs(src))

    def test_python_version_matches_recording(self):
        self.assertEqual(RECORDED["python"].split(".")[:2], sys.version.split()[0].split(".")[:2])


class RecordedSteppers(unittest.TestCase):
    """The two curated steppers use data/recorded.json; it must be what the tracer says now."""

    def check(self, src, names, key):
        code = compile(src, "<cell>", "exec")
        steps, why = helper._run_stack(code, dict(names))
        self.assertIsNotNone(steps, why)
        self.assertEqual(record_outputs.instrs(src), RECORDED[key])
        self.assertEqual([s["stack"] for s in steps], RECORDED[key + "_stacks"])
        # Each displayed stack's depth equals the running total of CPython's own stack effects,
        # minus the placeholder slots the display hides (one per PUSH_NULL or method lookup, used up by the call).
        depth = hidden = 0
        shown = [i for i in dis.get_instructions(code) if i.opname not in helper.SKIP][: len(steps)]
        for ins, step in zip(shown, steps):
            depth += dis.stack_effect(ins.opcode, ins.arg)
            if ins.opname == "PUSH_NULL" or (ins.opname == "LOAD_ATTR" and ins.arg & 1):
                hidden += 1
            elif ins.opname in ("CALL", "CALL_KW", "CALL_FUNCTION_EX"):
                hidden -= 1
            self.assertEqual(len(step["stack"]), depth - hidden, ins.opname)

    def test_t1(self):
        self.check("total = price * qty", {"price": 2.5, "qty": 4}, "t1")
        self.assertEqual(RECORDED["t1_stacks"], [["2.5"], ["2.5", "4"], ["10.0"], []])

    def test_t2(self):
        self.check("b = a\nb.append(4)", {"a": [1, 2, 3]}, "t2")
        self.assertEqual(RECORDED["t2_stacks"][-2:], [["None"], []])


class Tracer(unittest.TestCase):
    def stacks(self, src):
        r = decompose(src)
        self.assertIsNotNone(r["trace"], r["trace_why"])
        return r, [s["stack"] for s in r["trace"]]

    def test_loop_revisits_instructions(self):
        r, stacks = self.stacks("s = 0\nfor x in [1, 2]:\n    s += x\ns")
        self.assertEqual(r["value"], "3")
        rows = [s["i"] for s in r["trace"]]
        self.assertGreater(len(rows), len(set(rows)))
        self.assertEqual(stacks[-1], [])

    def test_error_ends_trace_with_the_real_error(self):
        r = decompose("x = 1\ndel x\nx")
        self.assertEqual(r["error"], "NameError: name 'x' is not defined")
        self.assertEqual(r["trace"][-1]["error"], r["error"])

    def test_comprehension_and_fstring_and_import(self):
        for src in ["xs = [1, 2]\n[x * 2 for x in xs]", "n = 3\nf'{n:>4} items {n!r}'", "import math\nmath.sqrt(2)",
                    "class A:\n    pass\nA()", "def f(a, b=2):\n    return a + b\nf(1, b=3)", "a, *rest = [1, 2, 3]\nrest",
                    "d = {'k': [1]}\nd['k'][0] += 1\nd", "print(*[1, 2])", "x = None\nx is None and 3 in [3]"]:
            with self.subTest(src=src):
                self.stacks(src)

    def test_unsupported_code_gives_a_reason(self):
        for src, word in [("try:\n    1/0\nexcept ZeroDivisionError:\n    pass", "try/except"),
                          ("import contextlib\nwith contextlib.nullcontext():\n    pass", "with")]:
            with self.subTest(src=src):
                r = decompose(src)
                self.assertIsNone(r["trace"])
                self.assertIn(word, r["trace_why"])
                self.assertNotIn("internal", r["trace_why"])

    def test_hidden_slots_only(self):
        r, stacks = self.stacks("print(1)")
        self.assertEqual(stacks, [["print"], ["print"], ["print", "1"], ["None"], []])


class CallStack(unittest.TestCase):
    def test_add_tax_frames(self):
        src = "def add_tax(price):\n    tax = price * 0.25\n    return price + tax\n\ntotal = add_tax(100)\nprint(tax)"
        r = decompose(src)
        seq = [(s["line"], [f["fn"] for f in s["frames"]]) for s in r["frames"]]
        self.assertEqual(seq[:5], [(1, ["top level"]), (5, ["top level"]), (2, ["top level", "add_tax"]),
                                   (3, ["top level", "add_tax"]), (5, ["top level"])])
        self.assertEqual(r["frames"][2]["frames"][1]["vars"], [["price", "100"]])
        self.assertEqual(r["frames"][3]["frames"][1]["vars"], [["price", "100"], ["tax", "25.0"]])
        self.assertIn("NameError", r["frames"][-1]["note"])

    def test_three_frames_deep(self):
        src = "def total(xs):\n    s = 0\n    for x in xs:\n        s += x\n    return s\n\ndef mean(xs):\n    return total(xs) / len(xs)\n\nm = mean([2, 4, 9])"
        r = decompose(src)
        self.assertEqual(max(len(s["frames"]) for s in r["frames"]), 3)
        self.assertEqual(r["frames"][-1]["frames"][0]["vars"][-1], ["m", "5.0"])


if __name__ == "__main__":
    unittest.main(verbosity=1)
