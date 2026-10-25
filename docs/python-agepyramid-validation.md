# Age-pyramid validation — 0.3.2

Recorded 2026-10-25 on macOS arm64, jamovi 28.13, using bundled Python and the installed
R package. This is core-port evidence; the 61-analysis migration remains incomplete.

## Numerical evidence

`tools/generate-demographic-oracles.R` extracts the archived `agepyramid.b.R` from
`docs/baselines/released-2026-10-25.tar.gz`, uses its label and fixed-width helpers and
constructs independent base-R `cut()`/`table()` counts and percentages. The committed
`tests/fixtures/demographic-oracles.json` contains 76 cases covering all six presets,
left/right closures, both denominators, boundary ages, fractional ages and custom widths,
singletons, missing/negative ages and custom lower bounds. Python matches all fixtures.

Independent accounting tests check disjoint exclusion totals, absent-group undefined
percentages, multilingual/default level orientation and invalid/resource-limited inputs.
A separate factor-label fixture verifies that an unreadable age label is an invalid age,
while a missing factor code remains a missing age. Plot tests check signed bar lengths,
symmetric limits, age ordering and literal titles.

## Integration and compiler evidence

- Final stable source: **185 Python tests passed**.
- Installed package: **492 R expectations passed**, zero failures/warnings/skips.
- R checks include numeric factor labels, explicit missing factor levels, base-R cell
  counts/denominators and valid -> changed width -> incomplete -> valid transitions.
- All **19 entry points** compile. Generator/status freshness and whitespace checks pass.
- Archive inspection verifies the single module identity, version, registered sources and
  shared helper bytes. **Nine packaged analysis runtimes** execute in bundled Python,
  including `pyagepyramid`.

Early runs exposed a numeric-factor gap and two test assertions requiring correction
(the generator's custom exception type and floating-point limit comparison). These are
resolved. A rebuild overlapped an earlier test run, causing transient missing installed
files and a vendor-library import failure; those runs are excluded from the evidence.
The passing final suites used a stable package with no concurrent rebuild.

## Native desktop evidence

Installed `ClinicoPathPj_0.3.2.jmo` through Modules -> Manage installed -> Sideload, updating
the existing module. The installed demographic helper was compared byte-for-byte with
source. No alternate module namespace was created.

Imported the 19-row synthetic CSV, chose Age/Gender and confirmed automatic label
orientation, then explicitly set Female/Male. Initial counts retained 16 rows with one
missing-age, one negative-age and one unselected-gender exclusion. Changing custom breaks
to `0,18,65,85` produced counts:

| Band | Female | Male | Total |
|---|---:|---:|---:|
| 0-17 | 4 | 3 | 7 |
| 18-64 | 2 | 2 | 4 |
| 65-84 | 1 | 1 | 2 |
| 85+ | 1 | 2 | 3 |
| Total | 8 | 8 | 16 |

Changing the denominator from within-gender to all retained observations gave total
shares of 50% and 50%, with the first female cell changing from 50% to 25%.
Saved `validation-exports/python-agepyramid-0.3.2-validation.omv`, quit jamovi, restarted
and reopened in a fresh process. The four bands, counts, denominator text and plot were
restored. ZIP integrity and the embedded plot resource were also checked independently.

Native Image -> Export -> PNG produced
`validation-exports/pyagepyramid-0.3.2-native-export.png`. The PNG was decoded and visually
checked: female bars left, male bars right, oldest band at top and symmetric count axes.
The pre-existing synthetic document was saved separately before restarting; its preserved
copy is retained under `build/previous-artifacts/python-migration-before-0.3.2-preserved.omv`.

A final metadata-only rebuild records GUI evidence in the authoritative registry. The
statistical, bridge, renderer and UI files are identical to the tested desktop candidate.

## Limits and release status

Full parity remains false. Alternate ggcharts/custom styling and interactive exploration
are omitted. Per-preset desktop transition tests, percentage-bar native export, exhaustive
cancellation scenarios, other macOS architectures, Windows/Linux and clinical review are
pending. Counts are descriptive; no population representativeness or clinical validation
is inferred from passing tests. See [the function guide](python-agepyramid.md) for behavior
and deliberate differences from the frozen R baseline.
