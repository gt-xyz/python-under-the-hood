# Terms used before they are defined

An audit of lesson text on 2026-09-29. The course promises to define every technical term on first use for someone with no computing background. A scan of the prose (the rendered text of every section, in lesson order) against a list of about 150 computing and pandas terms found that only these get a bold definition anywhere: byte, address, process, bytecode, stack, push, pop, object, name, method, argument, DataFrame, mask, filter, immutable, mutable, frame, call stack, code point, relative, working directory, environment.

Fixed on 2026-09-29: object, name, method, argument (lesson 3, first section, and a one-line gloss in lesson 2), DataFrame and column assignment (lesson 3, DataFrame section), mask, filter and `.loc` (lesson 3, filter section), stack, push and pop (lesson 2).

Everything below is still used without a definition. The section number is where the term first appears; "lesson summary" means the one-line summary or practice tip shown at the top of a lesson. Work down the list in order, since a term defined early covers all later uses.

## Lesson 1: What a computer does

- **instruction** (section 1). "One small instruction at a time." Say: one tiny operation such as add two numbers or copy a value.
- **CSV, DataFrame** (section 1, in the prediction). Familiar to the audience as things they type, but say a CSV is a plain text file of comma-separated values and a DataFrame is pandas' table.
- **syntax, type, int, float, list** (section 2). Say: syntax is the grammar of the language; a type is a kind of value; int whole numbers, float decimal numbers, list an ordered collection.
- **module, package, library, standard library, import** (section 2). Module: a file of Python code you can load with `import`. Package: a bundle of modules. Library: the loose word for either. Standard library: the modules that come with Python.
- **operator** (section 2). A symbol that combines values, like `+` or `&`.
- **compiled, C** (section 2). Say what compiled means: translated ahead of time into instructions the processor runs directly.
- **pip, conda** (section 2). Programs that install packages.

## Lesson 2: How Python runs your code

- **notebook, kernel, cell** (lesson summary and section 1). The kernel is glossed as "a Python process" in the diagram; the notebook and cell aren't defined at all.
- **script** (section 1). A file of Python code run top to bottom.
- **interpreter** appears in later lessons; consider naming CPython "the interpreter" here once.

## Lesson 3: Names, objects and copies

- **variable** (lesson summary). Now covered by the name definition; make the summary use the same words.
- **copy** (lesson practice tip). Used before the sections explain what a copy is.
- **string, tuple, dict** (section 2). Text, a fixed sequence, a lookup table of key/value pairs.
- **Series** (section 4, in the pandas warning text). One column of a DataFrame on its own.
- **chained assignment** (section 4, in the warning text). Two bracket operations in a row with `=` at the end.
- **frees** (section 4, diagram note). Say: Python reclaims the memory.

## Lesson 4: Functions and the call stack

- **function, call, return** (section 1). Defined by example only. Say: a function is a named block of code that runs when called; calling it runs the block; return hands a value back to the caller.
- **loop** (section 2, stepper note).

## Lesson 5: Reading errors

- **exception, error type** (section 1 and 2). An exception is Python's report that something went wrong; its type names the kind of problem.
- **attribute** (section 2, table). A value that belongs to an object and is reached with a dot.
- **index** (section 2, table). A position in a sequence, counting from 0.
- **literal** (section 2, table, inside an error message). Text written directly in code, like `'3'`.
- **path, directory, relative** (section 2, table). Defined later in the Text and files lesson; add a short gloss here or move that lesson earlier.
- **site-packages** (section 3, inside a traceback). The folder where installed packages live.

## Lesson 6: Numbers as bits

- **dtype, integer** (lesson practice tip). dtype is defined by usage only, in the Collections lesson which comes later.
- **int8** (section 1). An integer type that uses one byte.
- **binary, IEEE 754, scientific notation** (section 2).
- **fraction, exponent, sign** (section 2). The bit-field names are in the legend, but say what each means before the diagram.

## Lesson 7: Missing values

- **boolean** (section 2). A True or False value.
- **int64, float64, object dtype** (section 3, prediction options).
- **nullable** (section 3).

## Lesson 8: Text and files

- **encoding** (lesson summary). A rule for turning characters into bytes.
- **character, UTF-8** (section 1).
- **decode, codec** (section 2, inside an error message).
- **absolute** path (section 4).

## Lesson 9: Packages and environments

- **terminal** (section 2). A window where you type commands.
- **venv, conda** (section 2).

## Lesson 10: True, False and logic

- **logic gate** (lesson summary). Defined in section 2, but the summary uses it first.
- **bool** (section 1).
- **transistor** (section 2).

## Lesson 11: Collections in memory

- **packed** (section 1). Values stored side by side with nothing between them.
- **pointer** (section 1). An address stored as a value; lesson 1 defines address, so link the two.
- **array** (section 1). A block of packed values of one type.

## Lesson 12: Why vectorized code is fast

- **vectorized** (lesson title). Doing an operation on a whole array in one call instead of one value at a time.
- **cache, cache line** (section 3). Cache line is glossed inline; cache itself isn't.

## How to re-run the audit

The scan is a small script, not yet in the repo: it splits `src/page.html` into sections in lesson order, strips tags, looks for `<b>term</b>` definitions, and lists terms whose first use comes before their definition. Worth adding to `tests/` once the definitions are in, so a new term can't slip in undefined.
