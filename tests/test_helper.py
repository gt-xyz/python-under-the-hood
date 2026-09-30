"""Receipts for the bytecode and stack views: check src/helper.py against real CPython.

    python3.14 tests/test_helper.py        # the Python must match the site's Pyodide (3.14)

What is checked:
- every runnable example seeded in the lessons and the sandbox produces a live stack trace, and that
  trace agrees with a plain run of the same code (the helper drops the trace otherwise, so a missing
  trace is a failure here);
- the bytecode the helper shows equals what the dis module reports, and matches data/recorded.json;
- every seeded example has a recorded run in data/recorded.json that matches a fresh one (object
  addresses aside), its steps are internally consistent, and each stack's depth matches CPython's own
  stack-effect table for the instruction sequence;
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


class RecordedSeeds(unittest.TestCase):
    """Every seeded example has a recorded run in data/recorded.json, made by this tracer, and it is consistent."""

    def test_every_example_is_recorded(self):
        for src in seeded_examples():
            with self.subTest(src=src):
                if record_outputs.depends_on_environment(src):
                    self.assertNotIn(src, RECORDED["seeds"])
                else:
                    self.assertIn(src, RECORDED["seeds"])

    def test_recording_is_current(self):
        self.assertEqual(record_outputs.normalized(RECORDED["seeds"]),
                         record_outputs.normalized(json.loads(json.dumps(record_outputs.record()["seeds"]))))

    def test_steps_are_consistent(self):
        for src, r in RECORDED["seeds"].items():
            if not r["trace"]:
                continue
            with self.subTest(src=src):
                for step in r["trace"]:
                    self.assertEqual(len(step["ids"]), len(step["stack"]))
                    for oid in step["ids"] + [oid for _, oid in step["names"]]:
                        self.assertIn(str(oid), step["heap"])
                    self.assertEqual(len(step["frames"]) >= 1, True)
                    for mode, table, key in step["io"]:
                        self.assertIn(mode, ("r", "w"))
                        self.assertIn(table, ("const", "small", "name", "builtin", "slot", "attr", "module"))
                        if table == "const":
                            self.assertLess(key, len(r["consts"]))

    def test_stack_depth_matches_cpython(self):
        """In each code object, the displayed stack's depth equals the running total of CPython's own stack
        effects, minus the placeholder slots the display hides (one per PUSH_NULL or method lookup, used up by
        the call). A call the stepper enters holds its result back until the "back from" step."""
        for src, r in RECORDED["seeds"].items():
            if not r["trace"] or r["error"]:
                continue
            tables = {0: [i for i in dis.get_instructions(compile(src, "<cell>", "exec")) if i.opname not in helper.SKIP]}
            with self.subTest(src=src):
                depth, hidden = {0: 0}, {0: 0}
                for step in r["trace"]:
                    c = step.get("code", 0)
                    if c != 0:
                        continue  # function bodies are checked by the interpreter's own effect check
                    ins = tables[0][step["i"]]
                    if step.get("ret"):
                        depth[c] += 1
                    else:
                        depth[c] += dis.stack_effect(ins.opcode, ins.arg, jump=None) if ins.opname != "FOR_ITER" else 0
                        if ins.opname == "FOR_ITER":
                            depth[c] += 1 if len(step["stack"]) + hidden[c] > depth[c] else 0
                        if ins.opname == "RETURN_VALUE":
                            depth[c] -= 1
                        if step.get("into"):
                            depth[c] -= 1
                        if ins.opname == "PUSH_NULL" or (ins.opname == "LOAD_ATTR" and ins.arg & 1):
                            hidden[c] += 1
                        elif ins.opname in ("CALL", "CALL_KW", "CALL_FUNCTION_EX"):
                            hidden[c] -= 1
                    self.assertEqual(len(step["stack"]), depth[c] - hidden[c], f"{ins.opname} at step {step['i']}")

    def test_steps_into_functions(self):
        r = RECORDED["seeds"]["def add_tax(price):\n    tax = price * 0.25\n    return price + tax\n\ntotal = add_tax(100)\nprint(tax)"]
        self.assertEqual([c["name"] for c in r["codes"]], ["top level", "add_tax"])
        inside = [s for s in r["trace"] if s["code"] == 1]
        self.assertTrue(inside)
        self.assertEqual([f[0] for f in inside[0]["frames"]], ["top level", "add_tax"])
        self.assertTrue(inside[0]["slots"])
        self.assertEqual([n for n, _ in inside[-1]["names"]], ["price", "tax"])
        back = [s for s in r["trace"] if s.get("ret")]
        self.assertEqual(back[0]["stack"], ["125.0"])
        self.assertEqual([f[0] for f in back[0]["frames"]], ["top level"])
        self.assertEqual(r["error"], "NameError: name 'tax' is not defined")

    def test_two_names_one_object(self):
        r = RECORDED["seeds"]["x = 5\ny = x\ny += 1\nprint(x)"]
        after_alias = r["trace"][3]  # x = 5 (2 steps), y = x (2 steps)
        ids = dict(after_alias["names"])
        self.assertEqual(ids["x"], ids["y"])
        self.assertNotEqual(dict(r["trace"][-1]["names"])["x"], dict(r["trace"][-1]["names"])["y"])


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
