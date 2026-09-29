# Terms used before they are defined

The course promises to define every technical term on first use for someone with no computing background. This is the running audit: a script splits `src/page.html` into sections in lesson order, strips the markup, treats `<b>term</b>` as a definition, and lists terms whose first use comes before their definition. Last run 2026-09-29, after the language lessons landed.

## Defined now, in order of first definition

byte, address, process (lesson 1) · bytecode, object, name, stack, push, pop (lesson 2) · type, expression, statement, int, float, str, bool, None, list, pointer, tuple, dict, key, set (lesson 3) · function, call, argument, parameter, for, iterator, if, attribute, method, module, standard library, package (lesson 4) · frame, call stack (lesson 5) · immutable, mutable (lesson 6) · Series, array, index, dtype, DataFrame, int64, float64, mask, filter (lesson 9) · environment (lesson 10) · code point, relative path, working directory (lesson 13)

## Still used before a definition

Lesson 1's layers table names types, modules, packages, import, pip and conda as a preview, with a note saying lessons 3 and 4 define them. That is deliberate. The rest, in order, each with a suggested one-line gloss:

- **instruction** (lesson 1, section 1). One tiny operation, such as add two numbers or copy a value.
- **CSV** (lesson 1, section 1, in the prediction). A plain text file of comma-separated values.
- **operator** (lesson 1, section 2). A symbol that combines values, like `+` or `&`.
- **variable** (lesson 3, section 2). Used as the everyday word for name; fine as is.
- **string** (lesson 3, section 3). Say once that string is the long form of str.
- **return** (lesson 4, section 1). Defined by example; add "return hands a value back to the caller" in bold.
- **copy** (lesson 5, section 3). "A copy is a second, independent object with the same contents."
- **index** as a position (lesson 7, section 2, in the errors table). Lesson 3 says positions count from 0; use "position" in the table.
- **relative path** (lesson 7, section 2, in the errors table). Defined in lesson 13; say "a path that starts from the current folder" here.
- **kernel** (lesson 8, summary). The diagram glosses it; the summary should too.
- **packed** (lesson 9, summary). "Stored side by side with nothing between them."
- **boolean** (lesson 9, section 4). "A True or False value; bool for short."
- **site-packages, terminal, venv** (lesson 10). The folder where installed packages live; a window where you type commands; the tool that makes an environment.
- **integer, int8, binary, fraction, exponent, sign** (lesson 11). Integer is the long form of int. The float bit-field names are in the legend; say what each means before the diagram.
- **NaN, nullable** (lesson 12).
- **encoding, character, UTF-8, absolute path** (lesson 13). Encoding: a rule for turning characters into bytes.
- **logic gate, transistor** (lesson 14). The summary uses "logic gate" before section 2 defines it.
- **vectorized** (lesson 16, title). Doing an operation on a whole array in one call instead of one value at a time.
- **cache** (lesson 16, section 3). Cache line is glossed inline; cache itself isn't.

## Re-running the audit

The script isn't in the repo yet. It should move to `tests/` with a fixed list of terms, so a new term can't slip in undefined without a test failing.
