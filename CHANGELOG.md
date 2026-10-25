# Changelog

## 0.2.0 — Six Python cores — 2026-10-25

- Added diagnostic accuracy from row data or counts, sequential testing, chi-square post-tests,
  Benford leading-digit analysis and decision curves, with native tables and plots.
- Shared diagnostic engine with exact proportion intervals and explicit undefined/infinite ratios.
- Added grouped native bars and synthetic examples; documented core boundaries and omitted features.
- Encode genuine missing factor levels as missing while preserving literal NA labels.
- Added build-only mode and generated version/date synchronization from DESCRIPTION.
- Module identity remains ClinicoPathPj; standard package: ClinicoPathPj_0.2.0.jmo.

## Interactive dotplot and GUI installation check — 2026-10-25

- Added the interactive diagnostic dotplot to the existing ClinicoPathPj module.
- Use the single standard `ClinicoPathPj_0.1.0.jmo` package in the repository root.
  The alternate dotplot-experimental filename is retired; the module identity has
  always been `ClinicoPathPj`.
- GUI sideload succeeded. A running jamovi engine retained the earlier module
  namespace, causing `optionsClass$new(): attempt to apply non-function` for the new
  analysis. Read-only Rj diagnostics confirmed that `pydotdecisionOptions` was absent
  in memory but present in the installed package; a namespace reload fixed it.
  Restart jamovi after replacing an already loaded development build.
- Native GUI checks: analysis initialization, explicit positive reference level,
  automatic cutoff, numeric live preview and Apply updating the native count/accuracy tables.


## Console report — 2026-10-19

- **Bug, reported from the GUI: "Python console output does not show anything."** The console
  carried only what `run()` printed and tracebacks. No shipped analysis prints, so every successful
  run showed an empty box. So did input errors, and runs where Python was not started.
- **Fix:** the runtime returns a report with every response, and the bridge shows it above what
  Python printed (or "(the analysis printed nothing)"). The report gives:
  - the analysis and its version;
  - the Python, numpy and scipy versions ("scipy not imported" when it was not);
  - the interpreter;
  - the data and options received;
  - the status and timing, naming a scipy import inside `run()` when there was one.
- **Without a report, the console says why:**
  - "Python was not started: ..." when a required box is empty or no event level is chosen;
  - "Python stopped before it answered ..." when Python died, with its own error output when there
    is any;
  - "No report from Python: ..." for errors raised in R before Python answers (the time limit, an
    infinite value, Python missing).
- **The report is robust:**
  - Names and levels are JSON-quoted, so a comma, a newline or an NA level cannot blur or forge a
    line.
  - The options and data lines are clipped to 1000 characters, and factors to 5 levels shown.
  - `run()` gets a copy of the options.
  - The report is built after the run and guarded. When the result cannot be encoded, a line in
    the report says so.
- **Verified:**
  - Each path has a regression test, including the three the review showed were uncovered.
  - 25 mutants (15 Python, 10 R) were all killed.
  - A three-lens adversarial review (7 agents) found the problems fixed in this list.

### Review (three lenses, then a refuter per serious finding)
Confirmed and fixed:
- **"(Python printed nothing.)" was false after a hard crash.** The runtime holds `run()`'s
  output in memory until it answers, so a kill, segfault or abort loses it.
  - The text now says that.
  - `faulthandler.enable()`, called before the capture starts, puts the Python stack of a crash in
    C code on the real stderr, which R reads.
  - Rule: never state what a channel cannot see. Say what reached R.
- **The data line joined user text with separators,** so a level "a, b" read as two levels, a
  newline in a label made a fake "Status: ok." line, and an NA level (only via the R API) raised
  TypeError and lost the whole report to the guard.
  - Rule: quote user text in a diagnostic, with JSON as for the options line. A guard is a last
    resort, not the formatting strategy.

Refuted or judged harmless:
- The blank console on R-side errors: the error box above already explains it. It now gets the
  "No report" line anyway, because that blank was exactly the reported symptom.
- The timing wording: it was accurate. It now names a scipy import inside `run()`, because that
  import was most of the time.

### Lessons
- **A diagnostic pane that only echoes `print()` is empty for every analysis that doesn't print.**
  - Signal: the user's report, reproduced in the engine-like environment for success, input error
    and crash.
  - Rule: a diagnostic always says something: what ran, on what, with which inputs, how it ended,
    and why nothing else is there.
- **A test helper's new `...` swallowed a positional callback.**
  - I had put `...` first in `engineRun()`, so the old call `engineRun(function(analysis) ...)`
    landed in it. `modifyList()` drops unnamed elements.
  - The stale-console half of that test stopped seeding its stale text and passed vacuously. The
    earlier mutation check had covered only the Text half.
  - Signal: reading the test while fixing the console.
  - Rule: after changing a helper's signature, grep its call sites and pass callbacks by name.
    Mutation-check every assertion a fix relies on, not one per test.
- **A fix can make an older regression test vacuous.**
  - The console now always gets the report, so seeding stale text before a successful run proves
    nothing about the clearing.
  - The clearing still matters where Python never answers (an error, the time limit), so the test
    now ends a run early.
  - Rule: after a fix, re-run the mutants of the neighbouring tests.

## Increment 2 — 2026-10-18

- **Bridge:** processx replaces `system2`. R polls every 200 ms and calls jamovi's checkpoint after
  every poll, so an option change kills the running Python process and starts the new run. Timeouts
  and early exits kill the process tree, and tests check that none survives.
- **Generator:** new option types List, Integer and String; Level `role: "event"` (nothing
  preselected, plus a pending notice that lists the levels); Image results (plot kinds interval, line
  and box, drawn by ggplot2 from Python data); Text (Markdown) results; `visible: "(boolOption)"`.
- **Runtime:** `out.plot`, `out.markdown` and `md_escape`; console capture is bounded while running;
  analysis files load inside the warnings capture.
- **pywelch:** the reference defaults to the second level, so the sign matches jamovi's T-Test; adds a
  group-means plot and an interpretation.
- **New analyses:** pycotest, pyexacttests, pykappaci, pykappafixedn and pykappapower.

### Lessons
- **The warm worker was rejected after a Codex design review.** It would save about 0.8 s per run.
  The risks the review listed:
  1. stale or misattributed responses;
  2. cancellation losing to completion;
  3. partial stdin frames;
  4. unbounded pipes;
  5. supervise vs cleanup semantics;
  6. helper-module, RNG and numpy state leaking across analyses;
  7. mtime-based invalidation;
  8. per-request watchdogs.

  Rule: prefer a fresh process per run until measured latency justifies a worker, and then write
  those eight tests first.
- **Each independent verifier found something the porting agent missed:**
  - draw counts were reported as accepted rather than requested;
  - Fisher's p and its odds-ratio CI can disagree with no explanation;
  - a multi-rater Monte Carlo check was anti-conservative (8.75% false rejections against a nominal 5%);
  - a tiny prevalence crashed `pykappafixedn`.

  Rule: every new analysis gets a second agent that re-derives the oracles and runs mutants.
- **Machine load inflates timings.** With a load average of 27, `import scipy.stats` took 1.7 s,
  against 0.7–1.0 s when idle. Rule: report the load average with any timing.
- **A pending notice built from `table()` counts rows,** not a weights/counts variable. It now says
  "rows".

### Final review (D), 2026-10-19
Each finding below was reproduced before fixing, has a regression test, and was mutation-checked:
the test fails when the fix is reverted.
- **jmvcore restores Text content too, even after an option change.** It only marks it stale, so
  emptying a box left the previous run's interpretation on screen.
  - Signal: the source of `Text$fromProtoBuf`.
  - Rule: clear every Preformatted *and* Text at the start of a run.
- **processx `poll_io()` reports a pipe at EOF as ready forever.** When Python closed stderr, the
  wait loop spun and called the checkpoint thousands of times a second.
  - Signal: a test counting checkpoint calls.
  - Rule: poll only the connections that are still open.
- **`kill_tree()` misses Apple binaries such as `/bin/sleep`.** It finds descendants by an
  environment marker.
  - Signal: a test in which Python starts `/bin/sleep`.
  - Rule: call `kill()` first, which signals the process group, then `kill_tree()`.
- **A discrete axis keyed by label merges rows that share a label**, so an interval plot drew two
  estimates on one line.
  - Rule: position by row and label the axis with a named vector.
- **jamovi's `pc` format always prints one decimal** (`toFixed(dp - 2)` in the client), so a real
  0.003% residual risk read "0.0 %", while the interpretation said 0.0031%.
  - Rule: show such values as text formatted like the narrative, and keep the exact value in a
    hidden column.
- **jmvcore's `asDF` leaves out hidden columns.** The generator comment said otherwise, so R tests
  reading `asDF$prob` failed.
  - Data-frame `$` partial matching turned the missing `lower` into `lowerText`, which gave an
    error. `[["lower"]]` would have returned `NULL`, and `all(abs(NULL - x) <= tol)` is `TRUE`: a
    silent pass.
  - Rule: read hidden columns with `table$columns$<name>`, and check that a vector is non-empty
    before asserting `all()` over it.
- **Reference-level defaults must name their convention.**
  - pyexacttests now defaults to the first level, the orientation of
    `fisher.test(table(group, outcome))`.
  - Its labels name both groups, e.g. "Odds ratio, B vs A".
  - A test pins the default against the R oracle.

## 0.1.0 — 2026-10-18

First experimental version: the generator (`tools/generate.py`), the runtime
(`inst/python/cpj_runtime.py`), the bridge (`R/utils-python.R`), three analyses (pyruntime,
pydescriptives, pywelch) and the `tools/build.R` / `tools/check.sh` loop.

### Lessons (failure mode → detection signal → prevention rule)

Caught by the red-team review of the plan, before implementation:
- **The plan assumed the jamovi app was still 28.3; the user had upgraded to 28.13.**
  - Signal: the app's `version` file and Info.plist.
  - Rule: re-read the app version before each build decision, and never carry over a measurement
    from earlier in a session.
- **A hand-seeded `0000.yaml` without `analyses: []` crashes the compiler.**
  - Signal: none from `Rscript`, which exits 0; only the node exit status shows it.
  - Rule: seed `analyses: []`, and check `jmvtools::install()`'s return value.
- **`required: true` in `.a.yaml` makes jamovi skip `.run()` while a box is empty.**
  - Signal: the engine source (`gtg`).
  - Rule: keep `required` in SPEC and the `.b.R`, never in the `.a.yaml`.
- **jsonlite unboxes a one-variable Variables option into a bare string, and encodes NULL as `{}`.**
  - Signal: an encoding probe.
  - Rule: send array options with `as.list(as.character(v))`, and use `null = "null"`.
- **`as.list()` on data columns is 73–144× slower than `I()`.**
  - Signal: timing.
  - Rule: use `I()` for data columns.
- **A runtime run as `__main__` is imported a second time by `from cpj_runtime import InputError`,
  so `except InputError` misses.**
  - Signal: a mutation test (removing the alias turns `input_error` into `exception`).
  - Rule: alias with `sys.modules.setdefault("cpj_runtime", sys.modules[__name__])`.
- **The client renders Notice content as HTML.**
  - Signal: the resultsview bundle.
  - Rule: every displayed string goes through `.cpjSafeText()`.

Found during implementation:
- **The generator's `vector()` got a generator object, which is always truthy, so an empty list
  rendered as `c()` (NULL).**
  - Signal: reading the generated `.b.R`.
  - Rule: materialise iterables before testing emptiness.
- **`python -m unittest` fails in jamovi's Python: the trimmed stdlib has no `unittest/__main__`.**
  - Rule: run `unittest.main(module=None, argv=[...])` instead.
- **The first SIGINT test was vacuous.** `time.sleep` is interruptible, and Python re-raises SIGINT
  on exit, so the test passed even without `SIG_DFL`.
  - Signal: a mutation run.
  - Rule: test the timeout kill with an uninterruptible C loop (`sum(range(10**11))`).
- **A shell `&` job inherits SIGINT=ignored, so a mutation run from the shell measured nothing.**
  - Rule: drive signal tests from Python's `subprocess`.
- **`jmvcore::select()` fails for wrapper calls with `data=` and no selected variable.**
  - Rule: test the unconfigured path through the R6 class with an empty frame. The engine reads
    data with `readDataset()` and never calls `select()`.
- **A running jamovi installs a `.jmo` asynchronously, so an immediate mtime check said "not
  installed".**
  - Rule: poll, as `tools/build.R` does.

Caught by the adversarial code review (each was reproduced against the installed module before
fixing, and has a regression test):
- **Integer Nominal/Ordinal columns** (jamovi's default for integer columns with ≤ 49 distinct values)
  pass `permitted: numeric` but reach R as factors carrying their values. pydescriptives refused
  them, and pywelch crashed.
  - Rule: the generator marks numeric-only options, and the bridge applies `jmvcore::toNumeric()` to
    their columns.
- **Stale console.** jmvcore restores Preformatted text from saved state, so a failed run's
  traceback stayed under the next good run.
  - Rule: clear every Preformatted at the start of `.cpjRun()`. Unlike the Html view, the client's
    Preformatted view does render `""`.
- **Constant groups.** scipy replaces a NaN df with 1, so pywelch showed df 1, p "< .001" and a
  zero-width CI where `t.test` refuses the data.
  - Rule: apply `t.test`'s guard (se ≤ 10·eps·max|mean|, or non-finite), show only the difference,
    and add a note. The "computed, never defaulted" rule applies to library internals too.
- **Smaller fixes:**
  - An int in a number column became an integer cell, which ignores the column format; ints are now
    sent as floats.
  - `sys.exit()` in `run()` lost the response; it is now caught.
  - Control characters (U+0004) could reach the notice renderer; they are now stripped.
  - Console output written straight to file descriptors was uncapped; it is now capped in R.
  - The generator now refuses R keywords, jmvcore member names, unsafe titles and mistyped
    `allowNone`/Number/results values.
  - The runtime now ends itself after 75 s if R was killed.
  - pywelch's tests assert its notes and group means, which four surviving mutants showed was needed.
