# ClinicoPathPj

An experiment in **generating jamovi analyses from Python**. You write one Python file per
analysis: a literal `SPEC` (options, results and organized UI) plus a `run()` function. A generator turns it
into the jamovi files, and the statistics run in **the Python bundled with jamovi** (numpy, scipy),
so users install nothing.

Status: experimental, 0.3.7 (descriptive ports; full migration remains incomplete). Verified only on jamovi 28.13 for macOS (Apple Silicon), with
jmvtools 28.4.

| Analysis | What it does | Checked against |
|---|---|---|
| `pyruntime` | Lists the interpreter and its numpy/scipy versions | — |
| `pydescriptives` | n, missing, mean, SD, min, quartiles, max per variable | base R (`quantile(type = 7)`) |
| `pywelch` | Welch two-sample t-test with group descriptives, a group-means plot and a narrative | `stats::t.test(var.equal = FALSE)` |
| `pycotest` | Post-test probabilities for two tests used together, independent or conditionally dependent (Gardner et al. 2000). **New:** Monte Carlo uncertainty intervals from the validation sample sizes (Jeffreys priors, seeded) | an independent R oracle; `qbeta` closed forms; an R Monte Carlo |
| `pyexacttests` | 2×2 tables: Fisher's exact test with the conditional-MLE odds ratio and its exact CI, Barnard's and Boschloo's unconditional exact tests, exact McNemar for paired data, and a Newcombe risk difference. Larger tables are refused, because scipy's r×c Fisher test is Monte Carlo | `fisher.test`, `Exact::exact.test`, `exact2x2::mcnemar.exact`, brute force |
| `pykappaci` / `pykappafixedn` / `pykappapower` | Kappa sample size for 2–5 categories and 2–6 raters (CI approach, lowest kappa for a fixed N, power approach). **New:** a seeded Monte Carlo check of coverage or power, offered for a binary rating with two raters only, where it is validated (Donner & Eliasziw 1992) | `kappaSize` 1.2 to 1e-8 |

Six additional validated cores are available: `pydecision`, `pydecisioncalculator`,
`pysequentialtests`, `pychisqposttest`, `pybenford` and `pydecisioncurve`. They add diagnostic
accuracy, sequential-testing projections, contingency post-tests, Benford screening and
net-benefit curves. These use Python for calculations and native jamovi tables/plots.
See [inputs, examples, methods and omitted features](docs/python-core-analyses.md).
Open **Data Library > ClinicoPathPj > Python Core Examples**, or import
`data/python_core_examples.csv`, for the synthetic examples.

Build the single standard module without installing it:
`Rscript --vanilla tools/build.R --build-only` → `ClinicoPathPj_0.3.6.jmo`.
After replacing a loaded development build, use a fresh jamovi engine to avoid stale namespaces.

`pywelch` reports the mean difference as *comparison minus reference*. The reference defaults to
the second level, so the sign matches jamovi's own Independent Samples T-Test (level 1 minus
level 2). When the outcome is constant within both groups, it shows the difference and leaves t, df,
p and the interval empty, as R's `t.test` refuses such data. scipy would report df = 1 instead.

`pyexacttests` defaults the reference group to the first level, the orientation of
`fisher.test(table(group, outcome))`. Its odds ratio then equals jamovi's Contingency Tables odds
ratio when the event is the outcome's second level, and is the reciprocal when it is the first.

## Single-variable screening in 0.3.6

`pycheckdata` adds completeness, descriptive summaries, repeated/category frequencies,
Z/IQR/MAD consensus screening, transformation fallback, saved row-aligned flags and
optional local row inspection. See [methods and explicit omissions](docs/python-single-quality.md).

## Observable comparison in 0.3.5

`pyobservablecutoff` adds locally bundled Observable Plot and Inputs, including linked
cutoff/ROC views, crosshairs, tooltips and searchable row highlighting. It shares the
Python workflow with `pyd3cutoff`, preserving native results for direct comparison.
See [the three-way comparison and usage guide](docs/python-observable-cutoff.md).

## Separate cutoff experiment in 0.3.4

`pyd3cutoff` adds linked D3 dotplot/ROC exploration with Python-computed threshold
results, three optimization criteria, exact/Wilson intervals and native static plots.
Apply updates a local HTML snapshot; saved jamovi options control native results.
The existing dotplot remains available. See [comparison and example](docs/python-d3-cutoff.md).

## New descriptive analyses in 0.3.1

- `pysummarydata`: continuous summaries, Shapiro-Wilk diagnostics, skewness/Pearson kurtosis,
  IQR outlier rows, draft reporting, and native histograms with separate variable scales.
- `pycategorize`: equal, quantile, manual, mean/SD, median, and exact Fisher-Jenks bins;
  endpoint/denominator controls; row previews; ordered or nominal saved columns; and R
  code that applies the exact displayed boundaries.

See [methods, examples and current limits](docs/python-descriptive-ports.md). Large-sample
seeded Jenks subsampling remains unsupported and is rejected explicitly. The existing
`pydescriptives` utility remains available with its original contract.

## Migration foundation

The single module follows five families: Descriptives, Statistical Plots, Medical Decisions,
Survival, and Oncology. All public identifiers start with `py`; existing identifiers,
including `pykappaci`, `pykappafixedn`, and `pykappapower`, are unchanged. Original R names
are recorded only as baseline provenance. There are no duplicate unprefixed menu entries.

The [61-analysis status matrix](docs/python-migration-status.md) distinguishes planned,
partial, and fully qualified ports. Frozen R specifications and source hashes live in
`docs/baselines/`; normal builds never refresh them from mutable sibling repositories.

The organized UI is now generator-owned (`compilerMode: tame`). Variable roles and adjacent
level selectors come first; method controls, uncertainty, plots, and advanced settings are
grouped and enabled only when applicable. Statistical defaults are preserved.

`pyreportcat` adds native categorical frequency/summary tables, missingness and tied-mode
reporting, ordinal level ordering, copy-ready text, and a native distribution plot.
Its full release acceptance remains tracked separately in the matrix.

Static plots now use Python/Matplotlib Agg. The diagnostic explorer has a native static
applied-cutoff plot for export. Ten pinned plotting dependencies, their licenses, and hashes
are bundled for CPython 3.11 on macOS arm64; users install nothing. See
[vendor provenance](vendor/README.md). R only supplies theme/palette metadata and displays PNGs.

## The author loop

1. Register a stable `py…` identifier in `inst/python/registry.json` and create its source in
   `inst/python/analyses/<family>/`. The public identifier and source filename are independent.
   Copy an existing literal `SPEC`, including its explicit `ui` tree, as a starting point.
2. `Rscript --vanilla tools/build.R` regenerates the jamovi files, builds the module and installs
   it into jamovi. It exits non-zero on any failure.
3. `tools/check.sh` runs the Python unit tests, then testthat against the *installed* module in an
   environment like jamovi's engine.

Never edit the generated files (`jamovi/<name>.a.yaml`, `jamovi/<name>.r.yaml`, `R/<name>.b.R`).
The Python generator also owns `jamovi/<name>.u.yaml`. jmvtools writes `R/<name>.h.R` and the `analyses:` list in
`jamovi/0000.yaml`. `python tools/generate.py --check` exits 1 if any generated file is stale.

## SPEC reference

```python
from cpj_runtime import Factor, InputError

SPEC = {
    "name": "pywelch",                    # stable registry identifier
    "title": "Welch Two-Sample t-Test (Python)",
    "menuGroup": "ClinicoPathPj",
    "menuSubgroup": "Statistical Plots",
    "version": "0.1.0",
    "options": [...],
    "results": [...],
    "ui": {"children": [...]},           # explicit native jamovi layout
}
```

SPEC is read with `ast.literal_eval`, so it must be a plain literal. The generator never imports
the analysis file.

**Options.** Variable options come first. jmvtools otherwise opens a second variable list in the
panel, so the generator refuses that order.

| type | keys besides `name`, `title` | value in `options[...]` |
|---|---|---|
| `Variable` | `permitted`, `suggested`, `required` | column name or `None` |
| `Variables` | `permitted`, `suggested`, `required` | list of column names (always a list) |
| `Level` | `variable: "(x)"` (an earlier single Variable), `allowNone`, `role: "event"` | level label or `None` |
| `Number` | `default`, `min`, `max` | number |
| `Integer` | `default`, `min`, `max` (whole numbers) | int |
| `Bool` | `default` | `True` / `False` |
| `List` | `options: [{name, title}, ...]`, `default` (one of the names) | the chosen name |
| `String` | `default` | text (validate it in `run()`) |

**`role: "event"`** on a Level is for an event, positive or "abnormal" level, which must never be
guessed. The dropdown starts at "- None -", and until the user chooses, the analysis lists the levels
with their counts and does not run. A Level without the role, such as pywelch's reference group, may
use `allowNone` and treat `None` as a documented default.

**`required`.** If nothing required is chosen, the analysis stays silent. If only some required
boxes are chosen, it shows a note naming the missing ones, and Python is not started.
`required` never goes into the `.a.yaml`: jamovi would then skip the run entirely, and the note
could not be shown.

**Results.**
- `Table`: `columns` is a list of `{name, title, type, format?, superTitle?, visible?}`, where
  `type` is `text`, `integer` or `number`. `format` takes comma-separated tokens from `zto`,
  `pvalue`, `pc` and `log10`. Other tokens are refused, because jamovi ignores them silently.
  - `pc` always prints one decimal, so a 0.003% risk reads "0.0 %". For values that can be that
    small, show a text column formatted with `fmt_num()` and keep the exact number in a column with
    `visible: False`. jmvcore leaves hidden columns out of `asDF`; read them with
    `table$columns$<name>`.
  - `visible` also takes `"(boolOption)"`.
- `Preformatted`: plain text.
- `Text`: Markdown, e.g. a narrative interpretation. Pass user strings through `md_escape()`, and
  numbers through `fmt_num()` (3 significant digits, never scientific notation).
- `Image`: a plot constructed by Python/Matplotlib; R displays the completed PNG. It follows jamovi's theme
  and palette, resizes, and exports like any jamovi plot. Keys: `plot` (the kind), `width`,
  `height`, `xlab`, `ylab`. The kinds and the columns `out.plot` rows carry are:
  - `interval`: `label`, `estimate`, `lower`, `upper` (forest/CI plot; optional reference line);
  - `line`: `x`, `y`, optional `group` (`step=True` draws step curves, e.g. survival-type);
  - `box`: `group`, `value` (box plot with seeded jitter);
  - `bar`: `label`, `value`, `group` (grouped bars, up to 2,000 rows).
  - `scatter`: `x`, `y`, `group` (diagnostic dotplots, up to 5,000 rows).

  An interval plot takes at most 200 rows, a line or box plot 20,000, because the data is saved in
  the `.omv`. A plot with no rows shows jamovi's empty placeholder.
- `Html`: trusted module-authored interactive content through `out.html()`; escape user data
  before embedding it. The diagnostic dotplot is the existing example.
- Any result can have `visible: "(boolOption)"`, e.g. a plot that shows only when ticked.

**Added to every analysis by the generator:**
- the `data` option;
- a "Python console output" checkbox (`showConsole`);
- a `console` result. It starts with a report of the run:
  - the analysis and its version, and the Python and numpy versions;
  - the scipy version, or "scipy not imported";
  - the interpreter;
  - the data and options Python received (names and levels JSON-quoted, each line at most 1000
    characters);
  - the status and timing.

  Then come what `run()` printed and, when it fails, the traceback. A real one, from pywelch on
  8 rows:

  ```
  pywelch 0.2.0: Python 3.11.9, numpy 2.1.1, scipy 1.17.1
  Interpreter: /Applications/jamovi.app/Contents/MacOS/python
  Data received: 8 rows; "y" (number); "g" (factor, 2 levels: ["a", "b"])
  Options received: {"dep": "y", "group": "g", "refLevel": null, "ciWidth": 95, "showPlot": true}
  Status: ok. run() took 0.910 s, including its scipy import; 1.01 s since the runtime started.
  ----- Python output -----
  (the analysis printed nothing)
  ```

  Without a report, the console says why:
  - "Python was not started: ..." when a required box is empty or an event level is not chosen;
  - "Python stopped before it answered ..." when Python died, with Python's own error output when
    there is any. `faulthandler` puts the stack of a crash in C code there.
  - "No report from Python: the run stopped with the error shown above." when the run ended earlier,
    e.g. at the time limit or on an infinite value.

  What `run()` prints is held in memory and passed on with Python's answer, so it is lost when
  Python dies.

**Reserved names:**
- `data`, `showConsole`, `console`, and anything starting with `cpjNotice`;
- R keywords;
- jmvcore's `Options` members for option names (e.g. `levels`, `get`, `check`);
- results-element members for result names (e.g. `title`, `items`, `state`).

The generator lists them all. It also refuses:
- titles containing quotes, backslashes or control characters, or ending in ` [word]`;
- result titles containing `{`, `}` or backticks, or wrapped in parentheses, because jmvcore
  evaluates those.

**Numeric-only options** (`permitted` without `"factor"`) also accept jamovi's integer
Nominal/Ordinal columns, which jamovi gives to R as factors carrying their values. The bridge
converts them back to numbers with `jmvcore::toNumeric()`.

## `run(data, options, out)`

```python
def run(data, options, out):
    import numpy as np                 # import inside run(); only numpy and scipy are available
    from scipy import stats
    y = data[options["dep"]]           # numeric column -> float64 ndarray, NaN = missing
    g = data[options["group"]]         # factor -> Factor(codes, levels): codes -1 = missing; level order and unused levels kept
    out.row("test", t=..., p=...)      # one table row; numpy scalars converted; NaN/inf and left-out columns show "."
    out.note("test", "...")            # table note
    out.text("details", "...")         # Preformatted result
    out.markdown("summary", "Mean " + md_escape(options["dep"]) + " was ...")   # Text result
    out.plot("means", [{"label": "a", "estimate": 1.2, "lower": 0.9, "upper": 1.5}],
             xlab="Mean", ylab="Group", reference=None)                       # Image result
    out.warn("..."); out.info("...")   # jamovi notices
    raise InputError("...")            # the user's input cannot be analysed -> shown as the analysis error
```

- Text columns arrive as lists of strings, with `None` for missing values.
- `out.row` checks the table and column names, and the value types, against SPEC, so a mistake
  fails at the line that made it.
- A failed run shows no partial tables.
- `print()` output and Python warnings are captured. Warnings become notices, with duplicates
  merged and a maximum of 10.
- `sys.exit()` inside `run()` is reported as an error.
- **Cancellable.** When the user changes an option while Python is running, jamovi's checkpoint asks
  for a restart. The bridge kills that Python process at once and the new run starts.
- Runs are stopped after 60 s. The runtime also ends itself after 75 s, in case jamovi's R
  process is killed first.
- Every run is a fresh Python process, so no state leaks between runs or analyses. Importing scipy
  costs about 0.7–1 s per run on an idle machine.
  - A persistent "warm" worker would remove that cost. It was deferred after a design review: it
    brings cross-analysis state leakage, misattributed responses, hung or idle-racing workers and
    four resident interpreters.
- Use `np.random.default_rng(seed)` with a seed option for anything random, and say the seed in a note.

The bundled standard library is a trimmed, `.pyc`-only zip; `unittest/__main__`, for example, is
missing. Import only modules you have checked exist (`tests/python` runs in that interpreter).

## How it works

```
jamovi engine (R)                                  jamovi's bundled Python
R/<name>.b.R --> .cpjRun() (R/utils-python.R)
  options + columns -> request.json  ------------> inst/python/cpj_runtime.py
                                                     loads analyses/<name>.py, calls run()
  fills declared tables, notes, notices <---------- response.json (status ok | input_error | exception)
```

- **Process.** Python is started with processx, from jamovi's own R library. R polls the process
  every 200 ms and calls jamovi's checkpoint after every poll, so an option change cancels the run.
  - When a run ends early (an option change, the time limit, an R error), Python and anything it
    started are killed. `kill()` signals Python's process group; `kill_tree()` then catches
    descendants that left the group. `kill_tree()` alone misses Apple binaries such as `/bin/sleep`.
    Tests check that nothing survives.
  - If the engine itself exits, processx's supervisor kills Python, but not its children.
  - A run that finishes normally kills nothing, so an analysis must not leave background processes.
- **Interpreter.** jamovi's engine runs with `PYTHONHOME=<jamovi.app>/Contents/Resources`, an
  **empty `PATH`** and cwd `Contents/MacOS`. The bridge therefore finds Python as
  `dirname(PYTHONHOME)/MacOS/python`, with absolute paths only.
  - Any other Python started from the engine inherits jamovi's `PYTHONHOME` and fails at startup.
  - `-I`/`-E` make even the bundled one fail, because they ignore `PYTHONHOME`.
- **Data.**
  - Factors travel as zero-based codes plus levels, which keeps level order and unused levels.
  - Infinite values are refused, with the column named.
  - Numbers keep 17 significant digits.
- **Display.** jamovi renders table text, notes and notices as HTML, so the bridge:
  - breaks up `<` before a letter;
  - drops control characters (the notice renderer treats U+0004 as a translation delimiter);
  - changes `[]` to `()` in notes and notices, because jamovi cuts a trailing ` [word]` as a
    translation context.

  The console is capped at 100 kB.
- **Failures.** Each failure gives a specific message in jamovi: Python missing, timeout, a crash
  before a response, an unreadable response, an input error, or an exception. The console report
  and the notices are filled before the error is raised. When there is no report, the console says
  why.
- **Results.** All results are declared in the `.r.yaml`, so no `.load()` override is needed,
  unlike Pj.
  - Every change re-runs Python. jmvcore restores none of the rows, notes or notices added in
    `.run()`.
  - jmvcore *does* restore Preformatted and Text content (the console, the interpretation) from the
    saved state, even after an option change; it only marks them stale. The bridge therefore
    clears both at the start of each run.
  - Plots keep their data in the image state (`requiresData: false`), so jamovi can redraw them
    after a resize, a theme change or a reopened file without running Python.

## Known gaps

- Only macOS is supported; other platforms are refused with a clear message.
- Only numpy and scipy are available: no pandas, matplotlib or scikit-learn. Plots are drawn by R
  from Python data, in the three kinds above.
- Deleting or renaming an analysis means removing its five files and its `jamovi/0000.yaml`
  `analyses:` entry by hand.
- Rows, notes and notices are rebuilt on every run, not restored from saved state.
- The generator does not write the `.u.yaml` panel. jmvtools lays it out with
  `compilerMode: aggressive`, which rewrites it on every build, so an `enable:` binding or a
  collapsed section added by hand would be lost. Owning the panel is the next generator step.
- Messages from Python are English only (no i18n). Column super-titles are static.

## Pj (Python editor module) on macOS

`docs/pj-macos-fix.patch` is a minimal fix for Pj 1.1.0 on macOS. `docs/pj-probe-*.txt` hold the
before/after evidence:

| | Pj 1.1.0 | with the patch |
|---|---|---|
| "jamovi Python" | the finder returns NULL; `sh: - : invalid option`; "exit status 2" | `Contents/MacOS/python` 3.11.9 |
| "System Python" | silently runs jamovi's own `./python` (empty PATH) | Homebrew `python3` (PYTHONHOME cleared) |

Both builds are in `build/pj/` for side-loading (jamovi library → Side-load). Pj builds only with
jmvtools ≥ 28.4, because 28.3.1 rejects its `File` UI control and its `openExternal` action. Its
`minApp: 28.3.0` is also too low: the 28.3 client has neither that control nor the
`openExternal`/`export` actions, and module file export arrived in jamovi 28.7. Verified working on
28.13.

## License

GPL (>= 2). See `COPYING`. The bridge design was informed by Pj (Maurizio Agosti, GPL >= 2), but no
Pj code is included.

Descriptive-port verification and limitations are recorded in [the 0.3.1 validation report](docs/python-descriptive-validation.md).

`pyagepyramid` adds demographic age-band counts, percentages, explicit exclusions and a native Python pyramid. See [methods, synthetic example and limits](docs/python-agepyramid.md).

For numeric roles that also permit factors, `coerceNumeric: True` in SPEC requests numeric-metadata conversion in the R bridge; the Python engine must explicitly validate any remaining factor labels. Number/Integer options may omit either bound while keeping a finite default and finite supplied bounds.

`pydataquality` adds native missingness and duplicate accounting, quality maps and a local keyboard-accessible missingness preview. See [methods, examples and limits](docs/python-dataquality.md).

## Native SVG cutoff experiment

Version 0.3.7 adds `pysvgcutoff` alongside the D3 and Observable experiments.
The shared Python engine supplies all statistics; local SVG interaction supports
cutoff preview, keyboard control and native current-view SVG/PNG export.
See [behaviour and comparison](docs/python-svg-cutoff.md).
