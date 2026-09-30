"""Python that runs inside Pyodide, in the page. build.py inlines it as the PY_HELPER string.

_decompose(src) runs a cell of code and returns JSON for the page:
  instrs   the cell's bytecode, from dis, with bookkeeping instructions removed
  stdout, value, error, tb   the real run's output
  vars     the names the cell created: type, id, size, repr and bit patterns
  frames   the call stack at every line of the real run (recorded with sys.settrace)
  trace    the value stack after every instruction, from a small interpreter that
           executes the same bytecode on real objects. It is checked against the real
           run; if the two disagree or the code uses something the interpreter doesn't
           handle, trace is null and trace_why says why.

Test it outside the page with python3.14 tests/test_helper.py.
"""
import ast, builtins, contextlib, dis, io, json, linecache, operator, struct, sys, traceback, types

_NULL = object()      # a placeholder slot on the value stack, hidden in the display
_UNBOUND = object()   # a fast local with no value yet
MAX_STACK_STEPS = 300
MAX_FRAME_STEPS = 400
SKIP = ("RESUME", "NOP", "NOT_TAKEN", "CACHE", "EXTENDED_ARG")


class _Unsupported(Exception):
    pass


def _show(v, n=40):
    """A short label for a value on the stack or in a frame."""
    if v is _NULL:
        return "NULL"
    if v is _UNBOUND:
        return "unbound"
    if isinstance(v, types.ModuleType):
        return f"module {v.__name__}"
    if isinstance(v, type):
        return f"class {v.__name__}"
    if isinstance(v, types.FunctionType):
        return f"function {v.__name__}"
    if isinstance(v, types.MethodType):
        return f"{type(v.__self__).__name__}.{v.__func__.__name__}"
    if isinstance(v, (types.BuiltinFunctionType, types.MethodWrapperType)):
        s = getattr(v, "__self__", None)
        if s is None or s is builtins:
            return v.__name__
        if isinstance(s, types.ModuleType):
            return f"{s.__name__}.{v.__name__}"
        return f"{type(s).__name__}.{v.__name__}"
    if isinstance(v, (types.MethodDescriptorType, types.WrapperDescriptorType, types.ClassMethodDescriptorType)):
        return f"{v.__objclass__.__name__}.{v.__name__}"
    if isinstance(v, types.CodeType):
        return f"code for {v.co_name}"
    if isinstance(v, (bool, int, float, complex, str, bytes, type(None), list, tuple, dict, set, frozenset, range, slice)):
        r = repr(v)
    else:
        r = repr(v)
        if r.startswith("<"):
            name = type(v).__name__
            if name.endswith("iterator"):
                return name.replace("_", " ")
            if name == "generator":
                return "generator"
            return f"{name} object"
    return r if len(r) <= n else r[: n - 1] + "…"


# ---------- the value-stack interpreter ----------
_BIN = {
    "NB_ADD": operator.add, "NB_AND": operator.and_, "NB_FLOOR_DIVIDE": operator.floordiv, "NB_LSHIFT": operator.lshift,
    "NB_MATRIX_MULTIPLY": operator.matmul, "NB_MULTIPLY": operator.mul, "NB_REMAINDER": operator.mod, "NB_OR": operator.or_,
    "NB_POWER": operator.pow, "NB_RSHIFT": operator.rshift, "NB_SUBTRACT": operator.sub, "NB_TRUE_DIVIDE": operator.truediv,
    "NB_XOR": operator.xor, "NB_INPLACE_ADD": operator.iadd, "NB_INPLACE_AND": operator.iand,
    "NB_INPLACE_FLOOR_DIVIDE": operator.ifloordiv, "NB_INPLACE_LSHIFT": operator.ilshift, "NB_INPLACE_MATRIX_MULTIPLY": operator.imatmul,
    "NB_INPLACE_MULTIPLY": operator.imul, "NB_INPLACE_REMAINDER": operator.imod, "NB_INPLACE_OR": operator.ior,
    "NB_INPLACE_POWER": operator.ipow, "NB_INPLACE_RSHIFT": operator.irshift, "NB_INPLACE_SUBTRACT": operator.isub,
    "NB_INPLACE_TRUE_DIVIDE": operator.itruediv, "NB_INPLACE_XOR": operator.ixor, "NB_SUBSCR": operator.getitem,
}
_CMP = {"<": operator.lt, "<=": operator.le, "==": operator.eq, "!=": operator.ne, ">": operator.gt, ">=": operator.ge}
_CONVERT = {1: str, 2: repr, 3: ascii}
_UNSUPPORTED_WHY = {
    "LOAD_SPECIAL": "a with statement", "BEFORE_WITH": "a with statement", "PUSH_EXC_INFO": "try/except",
    "CHECK_EXC_MATCH": "try/except", "POP_EXCEPT": "try/except", "RERAISE": "try/except",
    "GET_LEN": "a match statement", "MATCH_CLASS": "a match statement", "MATCH_MAPPING": "a match statement",
    "MATCH_SEQUENCE": "a match statement", "MATCH_KEYS": "a match statement", "GET_AWAITABLE": "async code",
    "GET_AITER": "async code", "LOAD_DEREF": "a nested scope", "STORE_DEREF": "a nested scope",
    "MAKE_CELL": "a nested scope", "LOAD_CLOSURE": "a nested scope", "COPY_FREE_VARS": "a nested scope",
    "DELETE_DEREF": "a nested scope", "BUILD_TEMPLATE": "a t-string", "BUILD_INTERPOLATION": "a t-string",
}


def _display_indices(full):
    """Map each instruction's position to its row in the displayed table, or None."""
    shown = [k for k, ins in enumerate(full) if ins.opname not in SKIP]
    if len(shown) >= 2 and full[shown[-2]].opname == "LOAD_CONST" and full[shown[-2]].argval is None and full[shown[-1]].opname == "RETURN_VALUE":
        shown = shown[:-2]
    return {k: d for d, k in enumerate(shown)}


def _instrs(full):
    rows = []
    for k in sorted(_display_indices(full), key=lambda k: k):
        i = full[k]
        r = i.argrepr
        if isinstance(i.argval, types.CodeType):
            r = f"code for {i.argval.co_name}"
        elif not r and i.argval is not None and i.opname not in ("POP_TOP", "RETURN_VALUE", "GET_ITER", "END_FOR", "POP_ITER"):
            r = repr(i.argval)
        rows.append([i.opname, r])
    return rows


def _io_for(op, arg, val, ns):
    """Where an instruction reads from and writes to: [mode, table, key] triples. Real for every op listed."""
    if op == "LOAD_CONST":
        return [["r", "const", arg]]
    if op == "LOAD_SMALL_INT":
        return [["r", "small", arg]]
    if op in ("LOAD_NAME", "LOAD_GLOBAL"):
        return [["r", "name" if val in ns else "builtin", val]]
    if op in ("STORE_NAME", "STORE_GLOBAL", "DELETE_NAME", "DELETE_GLOBAL"):
        return [["w", "name", val]]
    if op in ("LOAD_FAST", "LOAD_FAST_BORROW", "LOAD_FAST_CHECK", "LOAD_FAST_AND_CLEAR"):
        return [["r", "slot", arg]]
    if op in ("LOAD_FAST_LOAD_FAST", "LOAD_FAST_BORROW_LOAD_FAST_BORROW"):
        return [["r", "slot", arg >> 4], ["r", "slot", arg & 15]]
    if op in ("STORE_FAST", "DELETE_FAST"):
        return [["w", "slot", arg]]
    if op == "STORE_FAST_STORE_FAST":
        return [["w", "slot", arg >> 4], ["w", "slot", arg & 15]]
    if op == "STORE_FAST_LOAD_FAST":
        return [["w", "slot", arg >> 4], ["r", "slot", arg & 15]]
    if op == "LOAD_ATTR":
        return [["r", "attr", val]]
    if op in ("STORE_ATTR", "DELETE_ATTR"):
        return [["w", "attr", val]]
    if op == "IMPORT_NAME":
        return [["r", "module", val]]
    if op == "IMPORT_FROM":
        return [["r", "attr", val]]
    return []


def _heap(ns, stack):
    """Objects reachable from the names and the stack, one level of items deep: id -> [type, label, size, item ids]."""
    out = {}
    def add(v, deep=True):
        if v is _NULL or v is _UNBOUND:
            return
        k = id(v)
        if k in out:
            return
        items = None
        if deep and isinstance(v, (list, tuple)):
            items = [id(x) for x in v[:12]]
        elif deep and isinstance(v, dict):
            items = [id(x) for x in list(v.values())[:12]]
        out[k] = [type(v).__name__, _show(v), sys.getsizeof(v), items]
        if items is not None:
            src = v[:12] if isinstance(v, (list, tuple)) else list(v.values())[:12]
            for x in src:
                add(x, deep=False)
    for k, v in ns.items():
        if not k.startswith("__"):
            add(v)
    for v in stack:
        add(v)
    return out


def _run_stack(code, ns):
    """Execute module-level bytecode on real objects, recording the stack after each instruction.

    Returns (steps, why). steps is None when the code uses something unsupported, and why says what.
    A step is {"i": table row, "line": source line, "stack": labels, "ids": stack object ids, "io": where it
    read and wrote, "names": [[name, object id]], "heap": reachable objects, "note": text} plus "error" on
    the last step if the code raised.
    """
    full = list(dis.get_instructions(code, show_caches=False))
    at = {ins.offset: k for k, ins in enumerate(full)}
    disp = _display_indices(full)
    handlers = list(dis._parse_exception_table(code))
    fast = [_UNBOUND] * code.co_nlocals
    stack, steps = [], []
    pc = 0

    def emit(note, live=None, **extra):
        if live is None:
            live = [v for v in stack if v is not _NULL]
        step = {"i": disp[pc], "line": ins.line_number, "stack": [_show(v) for v in live], "ids": [id(v) for v in live],
                "io": _io_for(op, arg, val, ns), "names": [[k, id(v)] for k, v in ns.items() if not k.startswith("__")],
                "heap": _heap(ns, live), "note": note}
        step.update(extra)
        steps.append(step)

    def pop():
        return stack.pop()

    def push(v):
        stack.append(v)

    def take(n):
        if n == 0:
            return []
        items = stack[-n:]
        del stack[-n:]
        return items

    def call(fn, self_or_null, args, kwargs=None):
        if self_or_null is not _NULL:
            args = [self_or_null] + list(args)
        return fn(*args, **(kwargs or {}))

    while pc < len(full):
        ins = full[pc]
        op, arg, val = ins.opname, ins.arg, ins.argval
        before = len(stack)
        snapshot = [v for v in stack if v is not _NULL]  # what was on the stack if this instruction fails
        jumped = False
        note = ""
        nxt = pc + 1
        try:
            if op in SKIP:
                pass
            elif op == "LOAD_CONST":
                push(val); note = f"Push the constant {_show(val)}."
            elif op == "LOAD_SMALL_INT":
                push(arg); note = f"Push the constant {arg}."
            elif op == "LOAD_NAME" or op == "LOAD_GLOBAL":
                if val in ns:
                    v = ns[val]
                elif hasattr(builtins, val):
                    v = getattr(builtins, val)
                else:
                    raise NameError(f"name '{val}' is not defined")
                push(v)
                if op == "LOAD_GLOBAL" and arg & 1:
                    push(_NULL)
                note = f"Find the object named {val} and push it."
            elif op in ("STORE_NAME", "STORE_GLOBAL"):
                v = pop(); ns[val] = v; note = f"Pop {_show(v)} and give it the name {val}."
            elif op in ("DELETE_NAME", "DELETE_GLOBAL"):
                del ns[val]; note = f"Forget the name {val}."
            elif op in ("LOAD_FAST", "LOAD_FAST_BORROW", "LOAD_FAST_CHECK"):
                v = fast[arg]
                if v is _UNBOUND:
                    raise UnboundLocalError(f"cannot access local variable '{val}' where it is not associated with a value")
                push(v); note = f"Push the value of {val}."
            elif op == "LOAD_FAST_AND_CLEAR":
                v = fast[arg]; push(_NULL if v is _UNBOUND else v); fast[arg] = _UNBOUND
                note = f"Set aside any outer value of {val}; the comprehension gets its own."
            elif op in ("LOAD_FAST_LOAD_FAST", "LOAD_FAST_BORROW_LOAD_FAST_BORROW"):
                for idx in (arg >> 4, arg & 15):
                    v = fast[idx]
                    if v is _UNBOUND:
                        raise UnboundLocalError(f"cannot access local variable '{code.co_varnames[idx]}' where it is not associated with a value")
                    push(v)
                note = f"Push the values of {val[0]} and {val[1]}."
            elif op == "STORE_FAST":
                v = pop(); fast[arg] = _UNBOUND if v is _NULL else v; note = f"Pop {_show(v)} and store it as {val}."
            elif op == "STORE_FAST_STORE_FAST":
                fast[arg >> 4] = pop(); fast[arg & 15] = pop(); note = f"Store the top two as {val[0]} and {val[1]}."
            elif op == "STORE_FAST_LOAD_FAST":
                fast[arg >> 4] = pop(); push(fast[arg & 15]); note = f"Store the top as {val[0]}, then push {val[1]}."
            elif op == "DELETE_FAST":
                fast[arg] = _UNBOUND
            elif op == "POP_TOP":
                v = pop(); note = f"Discard {_show(v)}; nothing keeps it."
            elif op == "PUSH_NULL":
                push(_NULL); note = "Push a placeholder slot the call will use (hidden here)."
            elif op == "COPY":
                push(stack[-arg]); note = f"Push a second reference to {_show(stack[-1])}."
            elif op == "SWAP":
                stack[-1], stack[-arg] = stack[-arg], stack[-1]; note = f"Swap the top with the item {arg - 1} below it."
            elif op == "BINARY_OP":
                name, sym = dis._nb_ops[arg]
                rhs = pop(); lhs = pop(); push(_BIN[name](lhs, rhs))
                note = (f"Pop the key and the container, push {_show(lhs)}[{_show(rhs)}]." if name == "NB_SUBSCR"
                        else f"Pop both, compute {_show(lhs)} {sym.rstrip('=') if sym.endswith('=') and sym != '==' else sym} {_show(rhs)}, push the result.")
            elif op == "BINARY_SLICE":
                stop = pop(); start = pop(); c = pop(); push(c[start:stop]); note = "Pop the bounds and the container, push the slice."
            elif op == "STORE_SLICE":
                stop = pop(); start = pop(); c = pop(); v = pop(); c[start:stop] = v; note = "Assign into a slice of the container."
            elif op == "STORE_SUBSCR":
                key = pop(); c = pop(); v = pop(); note = f"Set {_show(c)}[{_show(key)}] = {_show(v)}."; c[key] = v
            elif op == "DELETE_SUBSCR":
                key = pop(); c = pop(); del c[key]; note = "Delete an item from the container."
            elif op == "LOAD_ATTR":
                obj = pop(); v = getattr(obj, val); push(v)
                if arg & 1:
                    push(_NULL); note = f"Look up the method {val} on {_show(obj)}."
                else:
                    note = f"Look up .{val} on {_show(obj)} and push it."
            elif op == "STORE_ATTR":
                obj = pop(); v = pop(); setattr(obj, val, v); note = f"Set .{val} on {_show(obj)}."
            elif op == "DELETE_ATTR":
                obj = pop(); delattr(obj, val)
            elif op == "COMPARE_OP":
                rhs = pop(); lhs = pop(); r = _CMP[val](lhs, rhs)
                if ins.argrepr.startswith("bool("):
                    r = bool(r)
                push(r); note = f"Pop both, test {_show(lhs)} {val} {_show(rhs)}, push {_show(r)}."
            elif op == "CONTAINS_OP":
                rhs = pop(); lhs = pop(); r = lhs in rhs; push(not r if arg else r); note = f"Pop both, test whether {_show(lhs)} is {'not ' if arg else ''}in {_show(rhs)}."
            elif op == "IS_OP":
                rhs = pop(); lhs = pop(); r = lhs is rhs; push(not r if arg else r); note = f"Pop both, test whether they are {'not ' if arg else ''}the same object."
            elif op == "TO_BOOL":
                stack[-1] = bool(stack[-1]); note = f"Turn the top item into {stack[-1]}."
            elif op == "UNARY_NEGATIVE":
                stack[-1] = -stack[-1]; note = "Negate the top item."
            elif op == "UNARY_NOT":
                stack[-1] = not stack[-1]; note = "Replace the top item with its opposite truth value."
            elif op == "UNARY_INVERT":
                stack[-1] = ~stack[-1]; note = "Invert the bits of the top item."
            elif op in ("BUILD_TUPLE", "BUILD_LIST", "BUILD_SET"):
                items = take(arg); v = {"BUILD_TUPLE": tuple, "BUILD_LIST": list, "BUILD_SET": set}[op](items); push(v)
                note = f"Pop {arg} item{'s' if arg != 1 else ''} and push them packed as a new {type(v).__name__}."
            elif op == "BUILD_MAP":
                items = take(2 * arg); push(dict(zip(items[::2], items[1::2]))); note = f"Pop {arg} key/value pair{'s' if arg != 1 else ''} and push a new dict."
            elif op == "BUILD_STRING":
                push("".join(take(arg))); note = f"Join {arg} pieces into one string."
            elif op == "BUILD_SLICE":
                push(slice(*take(arg)))
            elif op == "LIST_APPEND":
                v = pop(); stack[-arg].append(v); note = f"Append {_show(v)} to the list being built."
            elif op == "SET_ADD":
                v = pop(); stack[-arg].add(v)
            elif op == "MAP_ADD":
                v = pop(); k = pop(); stack[-arg][k] = v
            elif op == "LIST_EXTEND":
                v = pop(); stack[-arg].extend(v); note = "Extend the list with these items."
            elif op == "SET_UPDATE":
                v = pop(); stack[-arg].update(v)
            elif op in ("DICT_UPDATE", "DICT_MERGE"):
                v = pop(); stack[-arg].update(v)
            elif op == "UNPACK_SEQUENCE":
                items = list(pop())
                if len(items) != arg:
                    raise ValueError(f"{'too many' if len(items) > arg else 'not enough'} values to unpack (expected {arg}, got {len(items)})")
                for v in reversed(items):
                    push(v)
                note = f"Pop the sequence and push its {arg} items, first item on top."
            elif op == "UNPACK_EX":
                b, a = arg & 0xFF, arg >> 8
                items = list(pop())
                if len(items) < a + b:
                    raise ValueError(f"not enough values to unpack (expected at least {a + b}, got {len(items)})")
                parts = items[:b] + [items[b:len(items) - a]] + (items[len(items) - a:] if a else [])
                for v in reversed(parts):
                    push(v)
                note = f"Pop the sequence and push its parts: {b} first item{'s' if b != 1 else ''}, the rest as a list{f', then {a} last' if a else ''}."
            elif op == "FORMAT_SIMPLE":
                v = pop(); push(v if type(v) is str else format(v)); note = f"Format {_show(v)} as text."
            elif op == "FORMAT_WITH_SPEC":
                spec = pop(); v = pop(); push(format(v, spec)); note = f"Format {_show(v)} with the spec {spec!r}."
            elif op == "CONVERT_VALUE":
                stack[-1] = _CONVERT[arg](stack[-1]); note = f"Convert the top item with {_CONVERT[arg].__name__}()."
            elif op == "CALL":
                args = take(arg); sn = pop(); fn = pop(); r = call(fn, sn, args); push(r)
                note = f"Call {_show(fn)} with {arg} argument{'s' if arg != 1 else ''}; push what it returns, {_show(r)}."
            elif op == "CALL_KW":
                names = pop(); args = take(arg); k = len(names)
                kwargs = dict(zip(names, args[arg - k:])); sn = pop(); fn = pop(); r = call(fn, sn, args[:arg - k], kwargs); push(r)
                note = f"Call {_show(fn)} with {arg} argument{'s' if arg != 1 else ''} ({k} by keyword); push {_show(r)}."
            elif op == "CALL_FUNCTION_EX":
                kw = pop(); a = pop(); sn = pop(); fn = pop()
                r = call(fn, sn, list(a), {} if kw is _NULL else dict(kw)); push(r)
                note = f"Call {_show(fn)} with unpacked arguments; push {_show(r)}."
            elif op == "GET_ITER":
                stack[-1] = iter(stack[-1]); note = "Replace the top item with an iterator that hands out its items one at a time."
            elif op == "FOR_ITER":
                try:
                    v = next(stack[-1]); push(v); note = f"Ask the iterator for the next item: {_show(v)}."
                except StopIteration:
                    jumped = True; nxt = at[val] + 1  # exhausted: skip END_FOR, land on POP_ITER
                    note = "The iterator is empty: leave the loop."
            elif op == "END_FOR":
                pop()
            elif op == "POP_ITER":
                pop(); note = "Discard the finished iterator."
            elif op in ("JUMP_FORWARD", "JUMP_BACKWARD", "JUMP_BACKWARD_NO_INTERRUPT"):
                jumped = True; nxt = at[val]; note = "Jump back to the top of the loop." if "BACKWARD" in op else "Skip ahead."
            elif op in ("POP_JUMP_IF_FALSE", "POP_JUMP_IF_TRUE", "POP_JUMP_IF_NONE", "POP_JUMP_IF_NOT_NONE"):
                v = pop()
                go = {"POP_JUMP_IF_FALSE": not v, "POP_JUMP_IF_TRUE": bool(v), "POP_JUMP_IF_NONE": v is None, "POP_JUMP_IF_NOT_NONE": v is not None}[op]
                if go:
                    jumped = True; nxt = at[val]
                note = f"Pop {_show(v)}: {'jump' if go else 'carry on to the next instruction'}."
            elif op == "RETURN_VALUE":
                pop(); note = "The end of the cell."; nxt = len(full)
            elif op == "IMPORT_NAME":
                fromlist = pop(); level = pop(); m = builtins.__import__(val, ns, ns, fromlist, level); push(m)
                note = f"Load the module {val} (running it first if this is its first import) and push it."
            elif op == "IMPORT_FROM":
                m = stack[-1]
                try:
                    v = getattr(m, val)
                except AttributeError:
                    v = sys.modules[f"{m.__name__}.{val}"]
                push(v); note = f"Push {val} from the module."
            elif op == "MAKE_FUNCTION":
                c = pop(); f = types.FunctionType(c, ns); push(f); note = f"Wrap the code of {c.co_name} in a function object. Nothing inside it runs yet."
            elif op == "SET_FUNCTION_ATTRIBUTE":
                f = pop(); a = pop()
                if arg == 1:
                    f.__defaults__ = a
                elif arg == 2:
                    f.__kwdefaults__ = a
                elif arg == 4:
                    f.__annotations__ = a
                elif arg == 16:
                    f.__annotate__ = a
                else:
                    raise _Unsupported("a nested scope")
                push(f); note = f"Attach the {ins.argrepr} to the function."
            elif op == "LOAD_BUILD_CLASS":
                push(builtins.__build_class__); note = "Push the built-in helper that builds classes."
            elif op == "LOAD_COMMON_CONSTANT":
                push(dis._common_constants[arg]); note = f"Push {ins.argrepr}."
            elif op == "RAISE_VARARGS":
                if arg == 1:
                    raise pop()
                if arg == 2:
                    cause = pop(); exc = pop(); raise exc from cause
                raise _Unsupported("a bare raise")
            elif op == "CALL_INTRINSIC_1":
                which = dis._intrinsic_1_descs[arg]
                if which == "INTRINSIC_PRINT":
                    v = pop(); sys.displayhook(v); push(None)
                elif which == "INTRINSIC_IMPORT_STAR":
                    m = pop()
                    for k in getattr(m, "__all__", [n for n in dir(m) if not n.startswith("_")]):
                        ns[k] = getattr(m, k)
                    push(None)
                elif which == "INTRINSIC_UNARY_POSITIVE":
                    stack[-1] = +stack[-1]
                elif which == "INTRINSIC_LIST_TO_TUPLE":
                    stack[-1] = tuple(stack[-1])
                else:
                    raise _Unsupported(which.replace("INTRINSIC_", "").lower())
            else:
                raise _Unsupported(_UNSUPPORTED_WHY.get(op, op))
        except _Unsupported as u:
            return None, f"it uses {u}"
        except Exception as e:
            if any(h.start <= ins.offset < h.end for h in handlers):
                return None, "it uses try/except or with, and something raised inside it"
            if pc in disp:
                emit("This instruction failed.", live=snapshot, error=f"{type(e).__name__}: {e}")
            return steps, None
        expected = dis.stack_effect(ins.opcode, arg, jump=jumped) if op not in SKIP else 0
        if op == "FOR_ITER" and jumped:
            expected = 0  # the iterator stays; END_FOR is skipped and POP_ITER drops it
        elif op == "RETURN_VALUE":
            expected = -1  # dis counts the returned value as still there
        if len(stack) - before != expected:
            return None, f"the stepper hit an internal mismatch at {op}"
        if pc in disp:
            emit(note)
            if len(steps) >= MAX_STACK_STEPS:
                steps[-1]["note"] += f" Stopped here after {MAX_STACK_STEPS} instructions."
                steps[-1]["truncated"] = True
                return steps, None
        pc = nxt
    return steps, None


# ---------- the call-stack recorder (real execution under sys.settrace) ----------
def _trace_frames(run):
    steps = []
    fresh, failing = set(), set()
    module, failed = [], []

    def label(f):
        return "top level" if f.f_code.co_name == "<module>" else f.f_code.co_name

    def names(f):
        return [[k, _show(v)] for k, v in list(f.f_locals.items())
                if not k.startswith("__") and not isinstance(v, types.ModuleType)]

    def chain(f):
        out = []
        while f is not None:
            if f.f_code.co_filename == "<cell>":
                out.append(f)
            f = f.f_back
        return out[::-1]

    def record(frames, line, note):
        if len(steps) >= MAX_FRAME_STEPS:
            if not steps[-1].get("truncated"):
                steps[-1]["note"] += f" Stopped here after {MAX_FRAME_STEPS} steps."
                steps[-1]["truncated"] = True
            return
        steps.append({"line": line, "frames": [{"fn": label(f), "vars": names(f)} for f in frames], "note": note})

    def tracer(frame, event, arg):
        if frame.f_code.co_filename != "<cell>":
            return None
        fid = id(frame)
        if event == "call":
            if frame.f_code.co_name != "<module>":
                fresh.add(fid)
            elif not module:
                module.append(frame)
        elif event == "line":
            if not frame.f_lineno:
                return tracer
            failing.discard(fid)
            note = ""
            if fid in fresh:
                fresh.discard(fid)
                if frame.f_code.co_flags & 1:  # CO_OPTIMIZED: a function body, not a class body
                    note = f"A new frame for the call to {label(frame)}. Its arguments are its first names."
                else:
                    note = f"A frame for the body of class {label(frame)}. Its names become the class's attributes."
            record(chain(frame), frame.f_lineno, note)
        elif event == "return":
            below = chain(frame)[:-1]
            if below:
                if fid in failing:
                    note = f"The error is not caught in {label(frame)}, so its frame is erased and the error moves down."
                else:
                    note = f"{label(frame)} returns {_show(arg)}. Its frame is erased, and its names with it."
                record(below, below[-1].f_lineno, note)
        elif event == "exception":
            failing.add(fid)
            if frame.f_code.co_name == "<module>":
                failed.append(True)
            fresh.discard(fid)
            msg = f"{arg[0].__name__}: {arg[1]}"
            record(chain(frame), frame.f_lineno, (msg if len(msg) <= 120 else msg[:119] + "…") + f" (in {label(frame)})")
        return tracer

    sys.settrace(tracer)
    try:
        run()
    finally:
        sys.settrace(None)
    if module and steps and not failed:
        record(module, steps[-1]["line"], "The cell has finished. These names are what it left behind.")
    return steps


# ---------- the entry point the page calls ----------
def _normal(vars_):
    import re
    return [(v["name"], v["type"], re.sub(r"0x[0-9a-fA-F]+", "0x", v["repr"])) for v in vars_]


def _collect_vars(ns):
    out, seen = [], {}
    for k, v in ns.items():
        if k.startswith("__") or callable(v) and not isinstance(v, (list, dict)):
            continue
        info = {"name": k, "type": type(v).__name__, "id": hex(id(v)), "size": sys.getsizeof(v), "repr": repr(v)[:120], "same": seen.get(id(v))}
        seen.setdefault(id(v), k)
        if isinstance(v, float):
            info["bits"] = format(struct.unpack(">Q", struct.pack(">d", v))[0], "064b")
        elif isinstance(v, bool):
            info["intbits"] = "1" if v else "0"
        elif isinstance(v, int):
            info["intbits"] = bin(v)
        elif isinstance(v, str):
            info["bytes"] = " ".join(f"{b:08b}" for b in v.encode("utf-8")[:12])
        elif isinstance(v, list):
            info["items"] = len(v)
        out.append(info)
    return out


def _decompose(src):
    res = {"instrs": [], "stdout": "", "error": None, "value": None, "vars": [], "frames": [], "trace": None, "trace_why": None, "consts": []}
    try:
        tree = ast.parse(src, "<cell>")
    except SyntaxError as e:
        res["error"] = f"SyntaxError: {e.msg} (line {e.lineno})"
        return json.dumps(res)
    last = None
    if tree.body and isinstance(tree.body[-1], ast.Expr):
        last = ast.Expression(tree.body.pop().value)
    code = compile(tree, "<cell>", "exec")
    whole = compile(src, "<cell>", "exec")
    full = list(dis.get_instructions(whole, show_caches=False))
    res["instrs"] = _instrs(full)
    res["consts"] = [[_show(c), id(c)] for c in whole.co_consts]
    linecache.cache["<cell>"] = (len(src), None, src.splitlines(True), "<cell>")

    # The real run.
    ns = {}
    out = io.StringIO()
    err = [None]

    def run():
        try:
            with contextlib.redirect_stdout(out):
                exec(code, ns)
                if last is not None:
                    v = eval(compile(last, "<cell>", "eval"), ns)
                    if v is not None:
                        res["value"] = repr(v)[:300]
        except Exception as e:
            err[0] = e

    res["frames"] = _trace_frames(run)
    if err[0] is not None:
        e = err[0]
        res["error"] = f"{type(e).__name__}: {e}"
        frames = [f for f in traceback.extract_tb(e.__traceback__) if f.filename == "<cell>"]
        if frames:
            res["tb"] = "Traceback (most recent call last):\n" + "".join(traceback.format_list(frames)) + res["error"]
    res["stdout"] = out.getvalue()[:2000]
    res["vars"] = _collect_vars(ns)

    # The stack trace: a second run through the small interpreter, checked against the first.
    ns2 = {}
    out2 = io.StringIO()
    try:
        with contextlib.redirect_stdout(out2):
            steps, why = _run_stack(whole, ns2)
    except Exception as e:  # a bug in the interpreter must never break the page
        steps, why = None, f"an internal error ({type(e).__name__})"
    if steps is None:
        res["trace_why"] = why
    else:
        same = (_normal(_collect_vars(ns2)) == _normal(res["vars"]) and out2.getvalue()[:2000] == res["stdout"]
                and (steps[-1].get("error") if steps else None) == res["error"])
        if same:
            res["trace"] = steps
        else:
            res["trace_why"] = "its second run gave a different result (it may depend on time, randomness or object ids)"
    return json.dumps(res)
