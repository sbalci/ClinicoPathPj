# Age pyramid: own execution versus the Pj service

This experiment runs the existing Python age pyramid through a second execution
route. It tests the Pj API with a familiar analysis that has native tables, level
selection, missing-value handling and a static plot.

| Property | Age Pyramid | Age Pyramid via Pj |
|---|---|---|
| Analysis ID | `pyagepyramid` | `pyagepyramidpj` |
| Menu | Descriptives Py → Distributions | Python Lab → Execution services |
| Execution | ClinicoPathPj's own Python subprocess | Installed Pj public service |
| Interpreter | jamovi bundled Python | jamovi bundled Python |
| Additional installed module | None | Pj; 1.5.0 recommended for checkpoints |
| Calculation | Existing age-pyramid `run()` and demographic engine | Calls that same `run()` |
| Results | Native tables, text and static image | Same results plus route explanation and elapsed time |
| Editor required | No | No |

The existing age pyramid's identifier, methods, defaults, options and results stay
unchanged. The new entry is an execution-service utility, not another migrated
baseline analysis. The 61-analysis migration denominator stays unchanged.

## Try the examples

Build ClinicoPathPj 0.3.62, then use **jamovi → Modules → Sideload** to install the
standard `ClinicoPathPj_0.3.62.jmo` package. Opening the package in Finder does not
install it. Install Pj separately and restart jamovi to load fresh namespaces.
Build/GUI qualification is tracked below; source availability does not imply a
qualified installation package exists.

Open **Data Library → ClinicoPathPj → Age Pyramid Service Examples**. Add both analyses:

1. Select **Age** and **Gender**.
2. Set female level **Female** and male level **Male** explicitly.
3. Select **WHO/UN standard** age groups.
4. Initially select **Counts**, with **Within each gender** percentages.
5. Compare the tables and bars, then switch both to **Percentages** and to
   **All retained observations** to compare denominators.

Expected results from the 22 synthetic rows:

| Age band | Female | Male |
|---|---:|---:|
| 0–4 | 2 | 1 |
| 5–9 | 1 | 2 |
| 10–14 | 1 | 3 |
| 15–19 | 1 | 0 |
| 20–24 | 2 | 2 |
| 65–69 | 0 | 1 |
| 85+ | 1 | 1 |
| Total | 8 | 10 |

Both retain 18 observations and exclude two missing pairs, one negative age and
one unselected gender level. Within-gender percentages divide female counts by
8 and male counts by 10. Total-cohort percentages divide both sides by 18.
The bars should have unequal lengths; the male 10–14 bar has length 3 in count
mode. Empty bands are omitted, so vertical distance is not elapsed years.
The data are illustrative, not clinical population estimates.

## Implementation difference

The new [Python specification](../inst/python/analyses/utilities/pyagepyramidpj.py)
sets `executionBackend: pj`. Its calculation delegates directly:

```python
from analyses.descriptives.pyagepyramid import run as run_age_pyramid
run_age_pyramid(data, options, out)
```

The generated R backend therefore calls:

```r
.cpjRun(self, "pyagepyramidpj", backend = "pj", ...)
```

The [Pj adapter](../R/utils-pj-service.R) locates the installed public service,
passes a trusted entry script and an encoded data/options request, validates the
returned versioned envelope, then lets the host populate its native results.
The original backend instead uses the host's own subprocess executor.
Both current routes use processx, so this compares responsibility for execution,
not processx versus system2. No inference is moved into JavaScript.

The static plot renderer is shared and remains owned by ClinicoPathPj. This
experiment routes **analysis calculation** through Pj; it does not use Pj's D3 or
Plotly helpers. Plot data are returned by the analysis, and the host renders the
same image from those data. No interactive state or SVG save/export behaviour is
introduced. The Pj elapsed-time output excludes image rendering; the existing
analysis has no matching timing element, so compare timings only with a matched
external harness and do not interpret one observation as a speed benchmark.

See the [public API walkthrough](python-service-examples.md) for a minimal call,
service discovery, response mapping and cancellation. A Pj editor never opens;
the service call itself is synchronous.

## Qualification

- Python tests: matched tables, plot data, notes and interpretation across the
  existing frozen R fixtures and both plot modes; unchanged options/UI/result
  contracts; explicit factor labels and unused levels; exclusions; failure and
  subsequent recovery; independently specified unequal bar widths.
- Native validation harness: [check-age-pyramid-service.R](../tools/check-age-pyramid-service.R)
  calls both packaged routes and compares native tables and plot state against
  independent base R `cut()`/`table()` counts and explicit percentage denominators.
- Packaged execution, actual service calls, fresh-engine GUI save/reopen/export,
  cancellation and additional platforms require their own evidence. They are not
  established by running both entry points inside the Python test process.

Evidence will be recorded below as checks complete. Existing broad qualification
of earlier versions does not qualify this new entry automatically.

### Historical local attempts, 2026-11-09 (superseded below)

Independent standard-library enumeration of the CSV confirms the expected bands,
8/10 side totals and four excluded records. AST checks confirm unchanged options,
UI and core results; generator freshness, registry-status freshness and whitespace
checks passed. See `validation-exports/python-age-pyramid-service-source-checks.json`.

The bundled-Python test job and build job stalled before producing test/compile
results and were cancelled. System load exceeded 500 during verification. Their
logs are retained as `python-age-pyramid-service-focused.log` (empty, no test result)
and `python-age-pyramid-service-build.log` (generation/vendor progress only).
The prepared numerical/geometry tests, actual Pj API calls and desktop lifecycle
checks remain pending. No new `.jmo` was installed; the existing installation was
left unchanged. Do not count earlier summary-example test results as age-pyramid
service validation.

A focused retry also stalled before its interpreter-started marker and was
cancelled. Its log is `python-age-pyramid-service-runtime-retry.log`; it supplies
no passing numerical or graphical test evidence.

## Verified on 2026-11-10 / ClinicoPathPj 0.3.62

The module was built and installed through **Modules → Manage installed → Sideload**.
The installed manager reports 0.3.62 and Pj 1.5.0. A fresh jamovi 28.17 process opened
**Age Pyramid Service Examples** from Data Library and ran both configured analyses.
Both returned the expected 18 retained observations (8 female, 10 male), with distinct
bar lengths. The Pj result reported processx and an enabled checkpoint callback.
No Pj editor analysis was opened.

| Evidence | Result | Boundary |
|---|---|---|
| Focused Python suites | 58 tests passed | Generator, registry, summary, demographic and new service contracts; not the full module suite |
| Source-level real API | Four own/Pj configurations matched independent base R counts and percentages | Both plot modes and both denominators, bundled Python |
| Packaged native R analyses | Four age-pyramid comparisons and invalid-input/recovery checks passed | Fresh R processes loading the built module |
| Same-instance lifecycle | 11 assertions passed | Changed bands matched a fresh instance; incomplete roles cleared tables, text and plot; restoration passed |
| Packaged runtime | 33 smoke cases passed, including all three new utilities | Separate from full method parity |
| GUI persistence/export | Passed on this Mac | Sideload, fresh engine, two analyses, `.omv` save/reopen, Pj percentage/count rerun, HTML with two native PNGs |

Open the ready-configured [comparison file](validation-exports/python-age-pyramid-0.3.62-reopened.omv)
or its [portable HTML results](validation-exports/python-age-pyramid-0.3.62-reopened.html).
The [native count image](validation-exports/pyagepyramidpj-0.3.62-native-counts.png) is also available.
Both saved files retain the source data bytes and factor codes/labels. The artifact validator
allows only the two additional false label flags written by this jamovi version.

[Qualification record](validation-exports/python-0.3.62-qualification-20261110.json),
[artifact checks](validation-exports/python-age-pyramid-artifacts-20261110.json),
[native comparison](validation-exports/python-age-pyramid-native-20261110.log),
[lifecycle assertions](validation-exports/python-age-pyramid-lifecycle-20261110.log),
and [Python checks](validation-exports/python-age-pyramid-20261110-focused.log) record separate evidence.
The installed Python payload and R databases match the `.jmo`; mutable Python bytecode
caches are excluded from that comparison. The superseded 0.3.61 package is archived.

### Developer probe without rebuilding the host

[check-age-pyramid-source-api.R](../tools/check-age-pyramid-source-api.R) can first send
`--service-smoke` (a Python sum without ClinicoPathPj calculations), then `--all` for
four actual own/Pj age-pyramid comparisons. It verifies interpreter/version agreement
and independently enumerated base R tables. The standalone script initializes jamovi's
protobuf classes; an ordinary R6 backend already runs inside an initialized engine.
The diagnostic `--timeout` flag does not change the module's 60-second default.

Historical sandbox process-denial, machine-load timeouts and the initial missing-protobuf
harness setup must not be interpreted as numerical failures. The secondary Python 3.9 /
Matplotlib 3.5.2 run passed numerical tests but failed two renderer checks because that
Matplotlib lacks `text.parse_math`; the bundled/pinned renderer subsequently passed.
The standalone app-R plot harness explicitly loads the existing system-R PNG dependency;
it installs no packages and does not establish clean-machine dependency qualification.

Additional platforms, clean installations, GUI long-job cancellation, System Python for
this entry, Word/LaTeX export and the full 0.3.62 suites remain unverified. These results
qualify the demonstrated core and current Mac setup; they do not establish full R-method
parity or clinical approval for the 61-analysis migration.
