# Optional pie goodness-of-fit: executed desktop qualification

Completed through **0.3.74** on **2026-11-15**, macOS arm64/jamovi 28.17.0, after
GUI access was restored. GUI Sideload, fresh-engine reopening/recalculation of the
qualified 0.3.72 file, all nine states below and native HTML/PNG exports pass.
All saved tables agree with independent base R at display precision; dataset and
metadata bytes remain unchanged, recovered plot pixels agree, and the direct
1300×900 PNG is byte-identical to the qualified descriptive export. Four corruptions
are rejected. Installed native tests pass 1,027 assertions. The steps below retain
the original 0.3.73 filename examples; the executed files use prefix 0.3.74.

The same controls are included in candidate **0.3.74**. Use that version's package
and filename prefix when testing the combined lollipop/GOF candidate. The artifact
checker accepts `--version 0.3.74`; its default remains 0.3.73 for the original
protocol. Nine focused checker tests pass, including version selection and refusal
of invalid/path-like version strings. No GUI artifacts have been generated for
either candidate by these checker tests.

This protocol was initially unexecuted because GUI automation could not connect
on 2026-11-14 and earlier 2026-11-15 retries. Those failures remain in the record;
headless runtime/native checks alone never established desktop acceptance.

## Installation and compatibility

1. Open jamovi and use **Modules → Manage installed → Sideload** to select
   `ClinicoPathPj_0.3.73.jmo`. Opening the archive from Finder is not the
   installation workflow.
2. Check the module identity remains **ClinicoPathPj**, with one pie entry under
   **Stats Plots Py → Categorical comparisons → Pie Chart (Core, Python)**.
3. Quit and restart jamovi to avoid a cached R namespace. Record the app version,
   architecture and fresh session identifier. Compare installed files with the
   archive before running analyses.
4. Open `docs/validation-exports/python-pie-0.3.72-reopened.omv`. Change a label
   option and restore it to force recalculation. Inference must remain off, with
   unchanged observed counts, denominators and plot. Save As the `legacy` state
   below. Retain the original 0.3.72 fixture.

Use Outcome and Frequency from the existing synthetic example. Keep contributing
source rows and the pie enabled, with Count and percentage labels and two decimal
places. All saves belong in `docs/validation-exports/`, with prefix
`python-pie-gof-0.3.73-` and the state suffix shown below.

## Required states

| Suffix | Change from the previous state | Required result |
|---|---|---|
| `legacy` | Open and recalculate the qualified 0.3.72 file | Default descriptive result; no GOF or expected mapping |
| `equal` | Enable Goodness-of-fit test; leave Custom expected ratios off | Equal-probability result and four expected rows |
| `custom` | Enable custom ratios; enter the valid JSON below | Exact label mapping and sparse approximation warning |
| `invalid` | Replace the JSON with the duplicate-label example | Input error; clear all prior computed tables, notes and image |
| `off` | Disable the GOF test, leaving the invalid text present | Descriptives and image recover; inactive ratio text is ignored |
| `expectedoff` | Restore valid JSON, enable GOF, disable Expected counts and Pearson residuals | Test remains; mapping is hidden and cleared |
| `incomplete` | Enable expected mapping, then remove Outcome | Pending input; clear tables, narrative and image |
| `recovered` | Restore Outcome | Custom result and mapping recover without changed dataset |
| `reopened` | Quit/restart; reopen recovered; force a rerun and restore the setting | Same custom results and plot in a fresh engine |

Save each state as `.omv`. Do not construct these fixtures by editing ZIP contents;
they must come from native GUI saves. Export the reopened state as HTML and export
its Image as PNG through the results context menu.

Valid labelled ratios (the keys must match the dataset labels):

```json
{"No":4,"Other":2,"Yes":3,"Zero":1}
```

Invalid duplicate-label probe:

```json
{"No":4,"No":1,"Other":2,"Yes":3,"Zero":1}
```

## Independent numerical reference

Run `Rscript --vanilla tests/reference/pie-gof-example.R` from the repository root.
It uses base R `chisq.test()` independently of the Python implementation.

Source rows = 6, complete = 4, excluded missing = 2, zero frequency = 1,
contributing = 3, total frequency = 25. Outcome and Frequency each have one missing
row. Imported alphabetical category order is No, Other, Yes, Zero; observed
counts are 12, 5, 8, 0. Original contributing rows are 1, 2, 3.

| Null | Expected counts in category order | Pearson X² | df | p | Minimum expected | Expected below 5 |
|---|---|---:|---:|---:|---:|---:|
| Equal | 6.25, 6.25, 6.25, 6.25 | 12.280000000000001 | 3 | 0.0064830336341513113 | 6.25 | 0 |
| Custom | 10, 5, 7.5, 2.5 | 2.9333333333333336 | 3 | 0.40201848834297016 | 2.5 | 1 |

Compare displayed values at their actual rounding precision; do not require
bit-identical R/Python p-values. Check every expected probability, residual and
chi-square contribution against the script, including the zero-observed category.
Neither result is exact inference, and a large p-value does not establish equivalence.

## Saved/exported acceptance

- Inspect native tables and cached images inside each saved archive, checking ZIP
  integrity, expected visibility, cleared states and absence of unused stale PNGs.
- Require unchanged `data.bin`, `metadata.json` and `xdata.json` across these states.
- Require custom, recovered and reopened numerical tables to agree, and the HTML
  export to contain the same visible tables and plot pixels as reopened OMV.
- The plot is descriptive and must not change when GOF is enabled or disabled.
  Compare cached images at equal resolution. The direct 1300×900 PNG should match
  the qualified 0.3.72 direct export, SHA-256
  `6c4c07915c37a8008a892c14ac3deeb47daeb1c1ff8ba7fec291c6300ae64e78`.
- Record results separately from source/native tests. Qualify unweighted subject
  roles, single-category desktop behavior, themes/accessibility and other platforms
  separately; the weighted four-category example cannot establish those claims.

Only after desktop acceptance should 0.3.72 be archived as the superseded package.
Keep validation PNGs and JSON reports ignored under the existing artifact policy.
This condition is now met for the bounded 0.3.74 examples; the verified 0.3.72
rollback and uninstalled/runtime-only 0.3.73 candidate are archived.

## Checker preparation — 2026-11-15

`tools/check-pie-gof-artifacts.py` checks the nine actual saved states above plus
the HTML and native PNG exports. After creating those files through jamovi, run:

```sh
PYTHONHOME=/Applications/jamovi.app/Contents/Resources \
  /Applications/jamovi.app/Contents/MacOS/python -B tools/check-pie-gof-artifacts.py
```

The checker now has eight focused tests using synthetic inference HTML and the
previously qualified descriptive display/image. These tests cover all seven valid
display modes, wrong null mappings/numbers, malformed row widths, unknown state
names, empty-state clearing, missing/duplicate plots, and saved-versus-exported
table/pixel consistency. Five original-code failures were reproduced before adding
strict row-width and state-name checks; the repaired checker passes. Export
comparison also refuses a loss of precision even when both rounded displays could
individually agree with the reference. The independent R values remain unchanged.

The existing 0.3.72 real saved-file/artifact checker also passes again, including its
four corruption probes. Generator/status freshness and diff checks pass. These
checks qualify the test harness and existing descriptive artifacts; they do not
establish 0.3.73 desktop acceptance. The 695-test statistical source gate was not
rerun for this tooling-only change. The candidate archive is unchanged.

During actual 0.3.74 export qualification, HTML inserted a space before numeric
percentage signs while saved tables omitted it. The checker normalizes only that
numeric percentage whitespace, preserving digits, precision, labels and all other
text. The initial failed comparison is retained at
`/private/tmp/cpj-0.3.74-gof-gui-artifacts-20261115.log`. Ten focused tests now pass,
including refusal of reduced percentage precision; the actual artifacts also pass.
No statistical tolerance or production calculation changed.
