# Lollipop 0.3.74: executed desktop qualification

Executed on **2026-11-15**, macOS arm64, jamovi 28.17.0. An initial connection
timeout was followed by restored GUI access. The standard 0.3.74 module was
installed through Sideload; all 1,480 installed files match the archive before and
after testing. Three fresh sessions (ports 59511, 59870 and 60608) cover old-file
compatibility, recalculation and saved-file reopening. Runtime/native tests remain
separate from this observed desktop evidence. Verified 0.3.72 rollback and the
previous runtime-only 0.3.73 candidate are now retained in `packages/archive/`.

All six lollipop states below were saved through jamovi, with median/no-aggregation
controls also exercised before restoring sum. HTML and direct PNG exports pass
independent base-R CSV checks. Recovered/reopened tables and cached pixels agree;
dataset/metadata bytes remain unchanged. The 1300×900 direct PNG byte-matches the
base-R-checked installed-native CSV render (SHA-256
`2512daedeba75a898dcaabc6d5ae0757656cd10308cf9e2762c899d9692268d8`).
Four deliberate corruptions are rejected. Run `tools/check-lollipop-artifacts.py`
with jamovi's bundled Python to reproduce these artifact checks.

The nine GOF states and their exports pass their separate artifact checker, and
installed native suites pass 2,228 lollipop plus 1,027 pie/GOF assertions without
failures/errors/warnings/skips. Full methods, clinical review, broader accessibility
and other platforms remain open. A minor observed UI issue is clipping of long
secondary lollipop hints at narrower panel widths; essential controls are visible.

## Install and start a fresh engine

1. Open jamovi, then **Modules → Manage installed → Sideload**. Select
   `ClinicoPathPj_0.3.74.jmo`; do not open the archive through Finder.
2. Confirm one **ClinicoPathPj** module, not a separately named experiment. Verify
   all installed file bytes against the new archive, then quit and restart jamovi.
3. Record the app version, architecture and new session. Check the single entry
   **Stats Plots Py → Group comparisons → Lollipop Chart (Core, Python)**.
4. Open Data Library → ClinicoPathPj → **Lollipop Aggregation Examples**. Select
   **Value** as Measurement and **Category** as Categories. Display source rows.

## Reference values and six saved states

The CSV contains eight source rows. Six are complete; two are excluded. Missing
measurement and missing category each count one row. Complete category counts are
Treatment A = 3, Treatment B = 1, Treatment C = 2. Retained source rows are 1–6.
The raw values are 10, 10, 10, 50, 52, 52, with mean 184/6 = 30.666666666666668.
Type-7 Q1 = 10, median = 30, Q3 = 51.5; sample SD uses denominator 5.

Keep the dataset unchanged throughout these profiles. Save native GUI `.omv`
files under `docs/validation-exports/python-lollipop-0.3.74-<suffix>.omv`:

| Suffix | Configuration | Required result |
|---|---|---|
| `mean-default` | Mean aggregation, factor order, vertical, baseline 0; reference off | Plotted values 10, 50, 52; N = 3; plotted mean 112/3 = 37.333333333333336; six retained source rows |
| `sum-horizontal` | Sum aggregation, descending value order, horizontal; reference and value labels on | Values 104, 50, 30 in point order; Treatment C at top, A at bottom; plotted mean 184/3 = 61.333333333333336; one vertical reference line |
| `sum-off` | Keep sum configuration; disable plot, plotted-value table and source-row table | Summaries and declared-category counts remain; optional outputs clear |
| `incomplete` | Remove Measurement | Pending input; clear prior tables, notes, narrative and plot |
| `recovered` | Restore Value and enable all optional outputs | Same sum results, source membership and plot as sum-horizontal |
| `reopened` | Restart; reopen recovered; change orientation and restore horizontal to force recalculation | Fresh-engine sum results and plot agree with recovered |

Before continuing from sum-horizontal, also exercise median and no aggregation,
then restore sum. Median equals mean in this deliberately constant-within-category
example; use sum to demonstrate a numerical aggregation change. No aggregation
produces six points at shared category positions and an explicit overplotting
warning; its reference is the raw mean. Verify source-to-point mapping through
sorting and aggregation, rather than treating sorted point numbers as source IDs.

Export reopened results as HTML and the Image directly as PNG through jamovi.
Check unequal stem lengths and measurement/category axes in both orientations.
Compare exact values at actual display precision; do not confuse the raw mean
with the average of plotted group values. Numbers and tables must remain native,
with copy/export available.

## Persistence and compatibility gates

- Verify ZIP integrity and table/plot contents of every actual GUI save. Require
  unchanged `data.bin`, `metadata.json` and `xdata.json` across the six profiles.
- Require recovered/reopened tables and equivalent-resolution cached plot pixels
  to agree with sum-horizontal. HTML must retain the reopened tables and image.
- Confirm disabled/pending states contain no stale cached plot or computed rows.
- A direct 1300×900 export should agree with a native render using these same
  CSV labels and configuration; the earlier isolated A/B/C-label images are not
  byte-equivalent references for this dataset.
- Open the qualified 0.3.72 pie example in the new module and force a rerun. Its
  default descriptive behavior must remain unchanged. Qualify the new optional
  GOF controls using the existing GOF protocol, adapting filenames to 0.3.74;
  prior source-only or 0.3.73 package evidence is not desktop acceptance.
  Run `tools/check-pie-gof-artifacts.py --version 0.3.74` with jamovi's bundled
  Python only after those actual GUI saves/exports have been created.

The four-category GOF and three-category weighted/group-summary examples do not
qualify all missing-factor encodings, very large displays, theme/accessibility
behavior or additional operating systems. Report those gates separately. Archive
superseded packages only after retaining verified rollback copies and recording
the acceptance status of each artifact.
