# Python Under the Hood: Plan

Exported from the Claude Doc of the same name on 2026-09-29, then revised here the same day (curriculum, roadmap). The Claude Doc is behind this file until synced.

## Vision and audience

Build a full-stack explorer of what code actually does, and an approachable course that uses it to teach computer engineering and computer science side by side.

- **Audience:** people who write code, often Python for data work, without a computing background, and who don't like black boxes.
- **Approach:** start from a line of code the learner already writes and let them go down as far as they want: bytecode, memory, bits, CPU, logic gates.
- **First user:** a Pitt Master of Data Science student. Deploy the simple version, watch where she stalls, and let that shape the curriculum.
- **Longer term:** free public content on a personal site, with the option of paid deeper modules or licensing to programs.

Success for a learner: after a lesson they can explain the why to someone else, and they write different code because of it.

## Design principles

The course teaches a "notional machine": a simplified but accurate model of what the computer does when it runs code. Research treats building that model as an explicit goal rather than something learners absorb.

1. **Top-down.** Start from code the learner already writes, then go down only as far as the answer needs.
1a. **The language layer gets its own lessons.** Types, names, collections, functions, loops and modules are defined before any library or tool appears, each by what it is in the machine, each inspectable in the live stepper. Concise and accurate; no abstraction a construct doesn't need.
2. **Concepts over tools.** Teach the idea, and use tools (pandas, Jupyter) as labeled examples of it. Every example carries a layer tag: Python, standard library, NumPy, pandas, Jupyter or Terminal.
3. **Predict, run, investigate (PRIMM).** Most sections ask for a prediction, then show the real result, then let the learner look inside and change the code.
4. **Content is never gated.** A prediction blurs only its answer; the explanation, diagrams and runnable code are always visible.
5. **Real outputs only.** Bytecode, bit patterns, tracebacks and library results are recorded by running real Python, never written from memory.
6. **Depth on demand.** The main path stays short; deeper layers are always one click away.
7. **Plain, consistent terms.** Lessons are split into sections; "Step" only means running one instruction. "Python" as a noun is qualified: a Python process, a Python installation.

## Explorer and course

The product has two parts. The **explorer** shows any code at every layer, as deep as the learner wants to go. The **course** is a set of guided paths through the explorer. Keeping them separate lets one tool support a free intro, deeper paid modules, or versions for specific programs.

| Layer | What it shows | Today |
| --- | --- | --- |
| 1. Code | A line of Python or pandas the learner already writes | Real |
| 2. Bytecode | The instructions the interpreter steps through | Real |
| 3. Objects in memory | Names point to objects; lists hold pointers, arrays hold packed values | Real |
| 4. Bits | How ints, floats, NaN and text are stored | Real |
| 5. CPU | Fetch, decode, execute; caches reward packed data | Simplified |
| 6. Logic gates | AND, OR, XOR; where pandas' `&` comes from | Simplified |
| 7. Transistors | A switch turned on and off by electricity | Simplified |

The top four layers show real data: CPython compiled to WebAssembly (Pyodide) runs in the page, so bytecode, object ids and bit patterns come from the real interpreter, and lesson examples are recorded from real runs. Making the lower layers real, with object layouts from CPython's C source, a steppable CPU and a cache model, is where the course can stand out.

## Curriculum

Revised 2026-09-29. The first version went from hardware straight to bytecode and treated the language itself as known. That left the language layer, the one between the machine and the libraries, with no lesson: types, names, collections, functions, loops and modules were used but never defined. Three lessons fill that gap. The rule for them is the rule for the whole course: say concisely and accurately what is there, define each construct by what it is in the machine, and add no abstraction the construct doesn't need. A learner who already has the model answers each section's opening prediction and moves on.

| # | Lesson | What it covers | Layers | Status |
| --- | --- | --- | --- | --- |
| 1 | What a computer does | Processor, memory and addresses, storage, processes; the four software layers | Hardware, software | Done |
| 2 | How Python runs your code | Bytecode and the stack; push and pop; the live stepper | Bytecode, memory | Done (notebook sections move to 8) |
| 3 | Values, names and collections | Every value is an object with a type; int, float, str, bool, None; names and assignment; expressions and statements; list, tuple, dict, set and what each costs | Memory, bytecode | Done |
| 4 | Functions, loops and modules | def, call, arguments, return; if; for as iterator plus jump; attributes and methods; modules and import | Bytecode, memory | Done |
| 5 | Functions and the call stack | Frames, local names, arguments as shared objects | Memory | Done (moved up) |
| 6 | Names, objects and copies | Assignment, mutability, copies (pure Python; the pandas sections move to 9) | Memory, bytecode | Done |
| 7 | Reading errors | Tracebacks as the call stack, common error types, finding your line in library errors | Memory, code | Done (library example to become standard library) |
| 8 | Notebooks and scripts | Script vs. kernel; one process across cells; run order | Software, memory | Done (moved from 2) |
| 9 | What pandas adds, and why | Series, DataFrame, dtype and array as new types; why a packed column beats a list; DataFrame aliasing; filters and chained assignment | Memory | Done |
| 10 | Packages and environments | import and site-packages, one Python installation per environment, versions changing behavior | Software | Done (moved up) |
| 11 | Numbers as bits | Binary integers, int8 overflow, the float format, why 0.1 + 0.2 ≠ 0.3 | Bits | Done |
| 12 | Missing values | NaN's bit pattern and comparisons, filters that keep NaN, nullable integers | Bits | Done |
| 13 | Text and files | UTF-8, encoding errors, CSV as text and dtype guessing, paths and working directory | Bits, hardware | Done |
| 14 | True, False and logic | Booleans as bits, logic gates, masks with &, \| and ~, precedence | Bits, logic gates | Done |
| 15 | Collections in memory | List of pointers vs. packed array in detail, dtypes, DataFrames as column arrays | Memory | Done (motivation moves to 9) |
| 16 | Why vectorized code is fast | Bytecode per value vs. compiled loops, cache lines and packed data | Bytecode, CPU | Done |

### Groups

The lesson list shows four groups, for a sense of progress. A group heading has to be true of every lesson under it, so two lessons move to make that so: the two pandas sections of "Names, objects and copies" (DataFrame aliasing; the chained-assignment filter) join "What pandas adds", leaving the copies lesson pure Python; and "Packages and environments" moves up beside notebooks and pandas. The errors lesson's library-traceback section should use a standard-library example, since it comes before pandas is introduced. Group sizes are uneven on purpose.

| Group | Lessons |
| --- | --- |
| The machine | What a computer does · How Python runs your code |
| The language | Values, names and collections · Functions, loops and modules · Functions and the call stack · Names, objects and copies · Reading errors |
| Tools and libraries | Notebooks and scripts · What pandas adds, and why · Packages and environments |
| Bits, memory and the CPU | Numbers as bits · Missing values · Text and files · True, False and logic · Collections in memory · Why vectorized code is fast |

The grouping, the reorder and the three new lessons landed on 2026-09-29.

### Outline of the new lessons

Each section: a takeaway heading, a prediction, the real result, a runnable box whose live bytecode stepper shows the construct doing what the text says. Headings below are drafts.

**3. Values, names and collections**

1. *Every value is an object with a type.* `type(5)`, `type(5.0)`, `type('5')`. An object is a piece of memory holding the value and its type. The bytecode shows LOAD_CONST pushing each one.
2. *A name is a label on an object.* `x = 5` then `x = 'five'`: the name moves, the objects don't change. STORE_NAME in the stepper. Expression (has a value) vs. statement (does something) in one paragraph, because the stepper makes the difference visible: an expression leaves a value on the stack, a statement leaves nothing.
3. *The five built-in values you'll meet everywhere.* int, float, str, bool, None: what each is for, and one thing each can't do (a str can't be added to an int). Sets up the bits lessons.
4. *A list holds anything, in order.* Indexing from 0, append, len. The list is a block of pointers, so items can be any type; that is its cost too, which lesson 7 returns to.
5. *Tuples, dicts and sets are lists with a rule.* Tuple: can't change. Dict: look up by key, not position. Set: no duplicates, no order. One prediction each, then when to reach for which.

**4. Functions, loops and modules**

1. *A function is a recipe with a name.* def creates a function object and does not run it; calling runs it; return hands back a value. MAKE_FUNCTION and CALL in the stepper. Arguments are the inputs; parameters are their names inside.
2. *A call gives back a value, or None.* `print` returns None; `len` returns a number. The most common data-work bug: `df.dropna()` without keeping the result.
3. *if chooses; for repeats.* A condition is any expression turned into True or False. A for loop asks an iterator for one item at a time; the stepper shows GET_ITER, FOR_ITER and the jump back.
4. *Dots reach inside an object.* Attribute: a value that belongs to an object. Method: a function that belongs to one. `'abc'.upper()`, `[1].append(2)`. Explains every `df.something` that follows.
5. *import loads a module once.* A module is a file of Python; import runs it once and gives you a name for it. Standard library vs. installed packages, ahead of lesson 13.

**9. What pandas adds, and why**

1. *A Series is one column.* Values of one type, packed side by side, plus a label for each row. Compare a list of floats (pointers to objects) with the same numbers packed as an array: the picture from lesson 15, without the byte counts.
2. *A DataFrame is a set of columns that share the row labels.* `df['x']` is a Series; `df.x` is the same thing; rows are numbered unless you say otherwise.
3. *A dtype is one type for the whole column.* int64, float64, bool, object, string. Why a column has to choose, and what happens when it can't (object dtype). Sets up missing values and dtype guessing.
4. *Arithmetic and comparisons apply to every row at once.* `df.x > 0` builds a Series of booleans, a mask; `df[mask]` keeps rows. Same idea as a loop, done in compiled code; lesson 16 measures it.
5. *pandas methods return new objects.* `df.dropna()`, `df.sort_values()` give back a new DataFrame; `inplace` exists but is discouraged.
6. *Two names, one DataFrame.* The aliasing section moved from the copies lesson: `df2 = df` then `df2['y'] = 9` changes both, `.copy()` gives an independent one.
7. *A filter builds a new object.* The chained-assignment section moved from the copies lesson: `df[df.x > 0]['y'] = 5` writes into a copy; `.loc` writes into df.

## Landscape

Full-stack teaching exists; doing it top-down, from a language learners already use, with one live explorer and real outputs, does not seem to. Nearest neighbors: Nand2Tetris (bottom-up), Computer Systems: A Programmer's Perspective (for C programmers), Python Tutor and Pandas Tutor (one layer each), float.exposed (one topic), How a Computer Works (bottom-up, not tied to real code), *Code* by Petzold and Ben Eater's videos (not interactive).

## Roadmap

1. Deploy the simple version to your own site and test on laptop and phone.
2. Work through what remains of docs/TERMS.md after the language lessons.
3. Watch the first learner use it; that is the first real curriculum data.
4. Move to a repo with TypeScript modules, lesson content as data, and the recording script as a build step.
5. Separate the explorer from the course.
6. Make the lower layers real: object layouts, the evaluation loop, a steppable CPU, a cache model.
7. Publish the intro free, then decide on paid modules or licensing.

## Risks

- **Scope:** keep the main path short; depth behind "go deeper".
- **Upkeep:** Python and pandas change (pandas 3 already changed text dtypes and chained-assignment warnings); re-recording must be one command.
- **Accuracy:** label simplified layers until they're real.
- **Hosting:** in-page Python needs WebAssembly allowed.

## Tech

- **Now:** one static page plus Pyodide 314.0.7 (CPython 3.14, about 12 MB on first run). No backend.
- **Next:** TypeScript + Vite, lessons as typed data, Playwright tests at desktop and phone widths.
- **Not needed:** C++ or Go compiled to WebAssembly for the app itself; only for a heavy simulator if JavaScript proves too slow.

## Open questions

- Should the explorer accept whole notebook cells, and load NumPy and pandas in the page?
- Free, paid, or both, and which modules sit where?

## Sources

- Sorva, Notional Machines and Introductory Programming Education (2013)
- PRIMM, King's College London: https://computingeducationresearch.org/projects/primm/
- ProgMiscon: https://progmiscon.org/ (Chiodini et al., ITiCSE 2021)
- Singh et al., Investigating Student Mistakes in Introductory Data Science Programming, SIGCSE 2024: https://afariha.github.io/papers/DS_SIGCSE_2024.pdf
- McKinney, Python for Data Analysis, 3rd edition: https://wesmckinney.com/book/
- Pyodide supported browsers: https://pyodide.org/en/stable/usage/index.html
