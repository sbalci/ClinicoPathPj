# Single-cohort Kaplan–Meier source contract — 2026-11-15

Stable identifier `pysinglearm`, frozen jsurvival 1.1.1 commit
`283a8275e3dd6704f6bba2164215442d3d293b8c`. Verify all four registry hashes
against the released archive. The actual cached-fit helper at frozen backend
lines 616–635 uses **log-log**, not the inventory's earlier “log” description.
The time-specific table suppresses boundary limits at S=0 or S=1. This core
preserves those rules; no R analysis or statistical default is changed.

The numerical foundation now has a generator-owned SPEC, native tables and a
Python static step renderer under **Survival Py → Survival estimates**. The
registry marks this source entry partial; installed 0.3.76 remains unchanged.
Package installation and desktop acceptance for this increment remain open.
Dates, landmarking, delayed entry, competing risks, groups, weights,
repeated subjects, RMST and regression remain outside this increment.

## Frozen computation contract

- Accept aligned, real one-dimensional elapsed times and **explicitly recoded**
  event indicators, 0=censored and 1=event. Missing values are excluded as pairs;
  reject known negative/infinite times or nonbinary statuses even on an otherwise
  incomplete row. Never infer event orientation or silently censor code 2.
  The labelled-factor interface requires distinct explicit event and censoring
  levels; an observed third category is refused even on a missing-time row.
- Bound source rows to 1–100,000, confidence to 0.50–0.999, requested times to
  200 and declared units to days/weeks/months/years (months default). Units are
  declarations, never implicit conversions. Optional exact nonempty subject IDs
  must be known and unique among retained cases; this does not prove independence.
- Default `timefix=True` reproduces survival's `aeqSurv` right-censoring convention:
  merge adjacent unique times separated by at most sqrt(machine epsilon), or that
  tolerance relative to the mean absolute unique time; use the first time of
  each chain. Audit changed rows and effective times. Explicit false uses exact
  ties. Raw source times and raw maximum follow-up remain distinct from effective
  event times. This tolerance can be unit-sensitive at very small scales.
- At each distinct effective time, use the full risk set before events/censoring;
  update S by (risk−events)/risk, then remove events and censors together. Report
  event/censor counts, cumulative counts and Greenwood variance terms. Return
  pointwise complementary log-log limits and survival-scale standard errors.
  At S=1, SE=0 but limits are blank; at S=0, SE/Greenwood/limits are unavailable.
  These are pointwise intervals, not simultaneous confidence bands.
- Report the median and confidence-limit inversions using `summary.survfit`'s
  convention: at an exact 0.5 plateau with a later lower value, use the midpoint
  of the first half-survival time and the next strictly lower time; otherwise
  use the first crossing. Use R's sqrt(epsilon) comparison tolerance. Missing
  quantiles remain blank, never zero or an extrapolated time. Invert the raw
  reference band (including S=1 boundary values) before display suppression.
- Requested times are finite/nonnegative, sorted and deduplicated. Give the
  post-event estimate at a tie, the number at risk immediately before that time,
  interval event/censor counts since the preceding requested time and separate
  cumulative counts. Omit and audit times beyond raw maximum follow-up unless
  the KM estimate is already zero. Before the first observation, S=1 with all
  records at risk; events at zero produce the post-event origin estimate.
  Unlike the R UI's permissive text parser, this numerical API rejects invalid
  entries rather than silently discarding malformed/missing query values.
- Compute reverse-KM follow-up by interchanging event and censor indicators.
  An unreached reverse-KM median remains unavailable: do not substitute the
  median of observed times. Direct `survfit` is its oracle; the released archive
  does not include the external follow-up helper, so helper-level parity is not
  claimed.
- Sum raw retained times for person-time, separately from KM risk sets and
  tie-normalized times. Report events/person-time with an exact two-sided Poisson
  interval per one declared time unit. Zero exposure or unrepresentable rates
  yield unavailable rate fields with reasons; no artificial denominator is added.
  This interval is exact under its Poisson count model, conditional on supplied
  exposure; that model is not validated by the KM fit. Refuse overflowing
  person-time sums. No clinical labels or treatment-effect
  interpretation is inferred from a single cohort or an unreached median.

## Validation gates

Write and execute the independent R oracle before the Python engine. Compare
`survival::survfit`, `summary.survfit(times=, extend=TRUE)`, summary-table median
inversions, reverse-KM and `stats::poisson.test`/chi-square limits. Cover zero-time
events, event/censor ties, near ties with timefix on/off, all-event/all-censored
cohorts, singletons, missing pairs, half-survival plateaus, unreached quantiles,
requested horizons and extreme numeric/resource/identity refusals. Preserve
fixture hashes and deterministic replay. Reject independent mutations of risk
sets, event counts, survival, interval orientation, median and person-time.

Only after this source gate should native role/level/unit controls, tables,
step curves, lifecycle/export, packaging and GUI qualification be implemented.

## Source evidence

The R oracle was corrected and frozen before implementing Python. It supplies
26 datasets and 156 confidence/timefix configurations. **58,635 comparisons
pass** against survival 3.8.12 / R 4.6.0, with maximum scaled difference
3.89e−16 and maximum relative difference 8.96e−15. R replay is byte-identical.
Fixture SHA-256:
`029cb9c667506eef572bb7b94f36950a9df98e20483e53332fba3bc22891140e`.

Thirteen focused tests pass: independent references, manual risk/Greenwood
identities, interval versus cumulative event counts, time-zero and terminal-zero
handling, zero/tiny/overflowing exposure, median plateaus, all-censored cohorts,
unavailable reverse-KM medians, true pair exclusions and original IDs, timefix
chains, declaration versus explicit scaling, invalid/resource controls and
100,000 tied observations. Six independent mutations of risk sets, events,
survival, interval orientation, median and person-time are rejected.

All **752 final-source Python tests pass** in 264.812 seconds, with no failures,
errors or skips. Generator/status freshness and diff checks pass. The installed
0.3.76 package remains SHA-256
`6f275281f42fea9a095724dced1fb1d87391a96b0dc96de9310f3bf81674cb4f`;
all 1,487 installed files still match its archive. No new native R suite, package
or GUI qualification is inferred from these source checks. Inventory remains
37 partial / 24 planned / 15 utilities / 52 executable entries and zero full
parity. The dated ignored `python-kaplan-meier-core-20261115.json` records
source/reference hashes and separate evidence grades.

The first oracle run was interrupted while `poisson.test` computed an unused
two-sided p-value under its default null rate of 1 for very large exposure.
Its p-value calculation can enumerate a very large Poisson range. The corrected
oracle sets the null to the observed rate (or 1/exposure for zero events), then
checks only the rate estimate and two-sided interval. Those interval endpoints
do not depend on the null rate. They also agree separately with exact chi-square
limits. No such test or p-value is implemented or reported by the Python core.
The initial log is retained under `/private/tmp/cpj-km-oracle-initial-poisson-20261115.log`.

Reproduce from the project root:

```sh
Rscript --vanilla tests/reference/kaplan-meier-core.R /private/tmp/km-replay.json
cmp tests/fixtures/kaplan-meier-core.json /private/tmp/km-replay.json
PYTHONHOME=/Applications/jamovi.app/Contents/Resources \
  /Applications/jamovi.app/Contents/MacOS/python -B tools/check-kaplan-meier-core.py
PYTHONHOME=/Applications/jamovi.app/Contents/Resources \
  /Applications/jamovi.app/Contents/MacOS/python -B tests/python/test_kaplan_meier_core.py
```

## Feature and omission matrix

| Feature | Current evidence | Remaining gate |
|---|---|---|
| Risk sets, KM steps, Greenwood/log-log uncertainty | Independent R and hand identities | Native tables and step renderer |
| Median inversion and reverse-KM | Frozen summary-table references and plateau/boundary fixtures | Native method labels and unavailable-result notices |
| Selected horizons and support counts | R time-specific summaries, separate interval/cumulative audits | Explicit UI cutpoints, units and event level |
| Raw person-time and exact Poisson intervals | R Poisson and chi-square references | Visible units/denominator and rate availability |
| Near-tie normalization and original IDs | R timefix references and source audits | Native disclosures, saved-state alignment/lifecycle |
| Factor event mapping, dates, landmarking, entry, competing risks, weights, RMST, Nelson–Aalen hazards, regression and specialized plots | Omitted | Separate contracts and validation |
| Package, native/GUI and platform acceptance | Not supplied for this core | SPEC/run, compiler, lifecycle/export, archive and desktop gates |

The maintained [survfit manual](https://www.stat.math.ethz.ch/R-manual/R-devel/library/survival/html/survfit.formula.html)
documents interval choices and near-tie preprocessing. The
[survival reference manual](https://www.stat.ethz.ch/CRAN/web/packages/survival/refman/survival.html)
describes median inversion and horizontal-plateau conventions. Exact acceptance
here is against the frozen local 3.8.12 computations, rather than mutable manuals.

## Native presentation contract

- Select elapsed time, status and optional subject ID. Event/censor selectors start
  empty; neither orientation is inferred. Declared units and supplied elapsed-time
  origin remain visible. Dates are rejected by the numeric role guard.
- Preserve baseline plot/CI/censor-mark/person-time defaults (off), months and
  requested times 12, 36, 60. Reverse-KM median is shown by default. Display
  complete-pair counts, exact mapping, overlapping role missingness, medians and
  requested-time estimates; optional steps and retained rows stop at 1,000 with
  disclosure. Source IDs and raw/effective times stay aligned.
- The native Image stores bounded drawing data, including all distinct risk-set
  steps. Rendering reads that state without source data or model refitting. Show
  post-event steps from S=1 at time zero, pointwise intervals over their supported
  step intervals, and one optional mark per distinct censoring time. Repeated
  censors at the same time share a mark; the table gives their count.
- Drawing coordinates are scaled to the observed maximum to avoid numeric axis
  overflow; tick labels show the original declared units without conversion.
  All-zero follow-up receives an explicit note. Long event labels are shortened
  only in the drawing and disclosed; native mapping retains the full label.
- Above 5,000 distinct effective times, omit the optional chart with a notice,
  retaining statistics for all cases. No display sampling is performed. Reject
  corrupt saved risk sets, probabilities, intervals, time order and flags.
- Synthetic Data Library example: `python_singlearm_examples.csv` (11 subjects,
  9 complete pairs, tied times, a zero-time event and two incomplete pairs).

Native integration and desktop/package evidence are recorded separately in the
migration plan. No repeated-subject, date-derived, competing-risk, hazard,
KMunicate, landmark or other full baseline parity is claimed.

## Reproduce the source integration checks

Use jamovi's Python with `PYTHONHOME` pointing to its Resources directory:

```sh
python -B tests/python/test_singlearm_adapter.py
python -B tests/python/test_kaplan_meier_core.py
python3 tools/generate.py --check
python3 tools/migration-status.py --check
```

After compiler preparation and an isolated `R CMD INSTALL`, point the native
checks at that test library (do not replace the installed jamovi module):

```sh
Rscript --vanilla tools/check-singlearm-native.R /private/tmp/cpj-singlearm-native-library
Rscript --vanilla tools/check-singlearm-example.R /private/tmp/cpj-singlearm-native-library
```

The synthetic example independently checks 14 quantities: 11 source rows,
9 complete subjects, 2 incomplete pairs, 4 events, 5 censored, medians 36/48
months (event/reverse-KM), horizons 12/36/60, risks 7/3/1, probabilities
16/21, 128/315, 128/315, interval event counts 2/2/0, interval censor counts
2/1/2, exposure 216 person-months, event rate 4/216 and exact subject IDs.
It exports a native PNG. Native tests additionally restore serialized plot
state, remove source data, and export that state without refitting.

## Source integration evidence — 2026-11-15

All **757 Python tests** pass in 539.567 seconds without failures, errors or
skips (`/private/tmp/cpj-singlearm-full-python-20261115.log`). This is a source
regression gate, not a desktop or clinical-validation claim.

- Five adapter/drawing tests pass in 8.171 seconds, including all 156 frozen
  configurations, subprocess transport, exact source IDs, output limits,
  extreme/zero follow-up, no-refit rendering and seven corrupt state variants.
- Compiler preparation, generated R documentation and isolated installation pass.
  The native suite passes 1,558 assertions across 52 configurations plus state
  recovery, output clearing, restored-state export and reuse/fresh equivalence;
  there are no failed assertions, errors, test warnings or skips. The synthetic
  example passes 14 hand checks and native PNG export. Both native images were
  visually inspected.
- Initial native-harness failures were logical versus numeric all-NA columns and
  default R formatting of near-tied horizon text. Coerce comparison vectors only
  in the test, and serialize requested times with 17 significant digits. No
  statistical implementation changed to satisfy these checks.
- Sandbox `Operation not permitted` process diagnostics appear on stderr even
  when all assertions pass; retain them separately. No cancellation claim follows.
- Installed 0.3.76 is preserved: archive SHA-256
  `6f275281f42fea9a095724dced1fb1d87391a96b0dc96de9310f3bf81674cb4f`
  and all 1,487 installed files match. No new `.jmo`, GUI install or `.omv`
  acceptance is claimed for this source increment.

Local logs: `/private/tmp/cpj-singlearm-adapter.log`,
`/private/tmp/cpj-singlearm-prepare.log`, `/private/tmp/cpj-singlearm-install.log`,
`/private/tmp/cpj-singlearm-native-initial.log`,
`/private/tmp/cpj-singlearm-native.log`, `/private/tmp/cpj-singlearm-example.log`.
Rendered PNGs live in `/private/tmp` and remain outside version control.
