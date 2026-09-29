# Python Under the Hood: Plan

Exported from the Claude Doc of the same name on 2026-09-29. The doc is the living version.

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

| # | Lesson | What it covers | Layers |
| --- | --- | --- | --- |
| 1 | What a computer does | Processor, memory and addresses, storage, processes; the four software layers | Hardware, software |
| 2 | How Python runs your code | Script vs. Jupyter kernel, bytecode and the stack, run order in notebooks | Bytecode, memory |
| 3 | Names, objects and copies | Assignment, mutability, DataFrame aliasing, filters and chained assignment | Memory, bytecode |
| 4 | Functions and the call stack | Frames, local names, arguments as shared objects | Memory |
| 5 | Reading errors | Tracebacks as the call stack, common error types, finding your line in library errors | Memory, code |
| 6 | Numbers as bits | Binary integers, int8 overflow, the float format, why 0.1 + 0.2 ≠ 0.3 | Bits |
| 7 | Missing values | NaN's bit pattern and comparisons, filters that keep NaN, nullable integers | Bits |
| 8 | Text and files | UTF-8, encoding errors, CSV as text and dtype guessing, paths and working directory | Bits, hardware |
| 9 | Packages and environments | import and site-packages, one Python installation per environment, versions changing behavior | Software |
| 10 | True, False and logic | Booleans as bits, logic gates, masks with &, \| and ~, precedence | Bits, logic gates |
| 11 | Collections in memory | List of pointers vs. packed array, dtypes, DataFrames as column arrays | Memory |
| 12 | Why vectorized code is fast | Bytecode per value vs. compiled loops, cache lines and packed data | Bytecode, CPU |

## Landscape

Full-stack teaching exists; doing it top-down, from a language learners already use, with one live explorer and real outputs, does not seem to. Nearest neighbors: Nand2Tetris (bottom-up), Computer Systems: A Programmer's Perspective (for C programmers), Python Tutor and Pandas Tutor (one layer each), float.exposed (one topic), How a Computer Works (bottom-up, not tied to real code), *Code* by Petzold and Ben Eater's videos (not interactive).

## Roadmap

1. Deploy the simple version to your own site and test on laptop and phone.
2. Watch the first learner use it; that is the first real curriculum data.
3. Move to a repo with TypeScript modules, lesson content as data, and the recording script as a build step.
4. Separate the explorer from the course.
5. Make the lower layers real: object layouts, the evaluation loop, a steppable CPU, a cache model.
6. Publish the intro free, then decide on paid modules or licensing.

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
