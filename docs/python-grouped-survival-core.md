# Grouped Kaplan–Meier and log-rank source contract — 2026-11-16

Target: stable registry identifier `pysurvival`, jsurvival 1.1.1, frozen commit
`283a8275e3dd6704f6bba2164215442d3d293b8c`. Four baseline file hashes are verified
against `docs/baselines/released-2026-10-25.tar.gz` before comparing outputs.
The numerical foundation now has an executable generator-owned SPEC/native source
entry. Registry status is partial. Packaging and bounded macOS desktop acceptance
now pass in 0.3.78; see the [package record](python-grouped-survival-package-validation.md).
Earlier checkpoints below describe their then-current state. Full baseline parity,
clinical review and other-platform qualification remain pending.

## Baseline distinctions

The frozen grouped backend calls `survfit` with its default **log-scale** limits
(median table around lines 1595–1610, horizon table around 2475–2638). It retains
[1,1] confidence limits when survival is one, unlike the single-cohort port's
log-log/boundary-suppressed presentation. The grouped horizon table removes every
row beyond that group's raw maximum follow-up, including terminal-zero curves.
The single-cohort core's documented terminal-zero extension is unchanged.

The baseline cutpoints are 12, 36, 60, declared unit months, with plot/CI/p-value
plot labels off by default. The source core takes numeric requested times. Native controls accept a bounded
comma-separated numeric list without evaluating expressions. No silent change is made
to existing analysis defaults or the established single-cohort output contract.

## Supported computation

- Unweighted right-censored time/event/group triples; explicitly recoded event
  0=censored, 1=event. Reject negative/infinite known times and nonbinary known
  statuses even on otherwise incomplete rows. One common complete-case cohort
  drives curves and the overall test; missing role counts overlap.
- Preserve declared factor order, exact labels and original retained indices.
  Genuine missing levels/codes are excluded; literal `NA` and a level actually
  named `Unused` remain categories when observed. Report inactive declared levels.
  Optional IDs must be exact nonempty strings and unique among retained subjects.
  This audit does not prove independent observations.
- Normalize near-equal times once on the entire retained cohort using survival's
  `aeqSurv` convention, then reuse those times for all group curves and the test.
  Per-group normalization would mishandle cross-group tie chains. Report raw/effective
  maxima, effective times and changed rows separately. `timefix=False` uses exact ties.
- Per group: risk before simultaneous events/censors, product-limit survival,
  Greenwood log variance/survival-scale SE, pointwise log limits, summary.survfit
  median/limit inversion, supported horizon estimates and omitted horizons.
  Limits at S=1 are [1,1]; at S=0, limits/SE are unavailable. No group horizon is
  extrapolated, including zero survival beyond follow-up.
- Overall unweighted log-rank (rho=0): observed and expected events, score vector,
  full covariance matrix, positive-expectation group codes, chi-square, degrees
  of freedom and asymptotic p-value. At each pooled event time, with risk N,
  deaths D and group proportions p, add `D*p` to expectations and
  `D*(N-D)/(N-1)*(diag(p)-p*p')` to covariance when N>1. Remove events and censors
  only after the shared risk set is counted.
- Remove zero-expectation groups from inference and one redundant contrast before
  solving. Do not substitute a pseudoinverse, ridge, continuity correction or p=1
  for unavailable information. One retained group, no events, fewer than two
  positive-expectation groups, singular covariance or a nonfinite result retain
  valid curves with an explicit unavailable-test reason; chi-square/df/p stay blank.
  These guard outcomes are distinct from ordinary estimable R comparisons.
- Keep a bounded audit of the first 1,000 pooled event times with group risks,
  observed/expected events and a truncation count. All data still contribute.
  Limits: 100,000 source rows, 20 retained groups, 1,000 declared levels and
  200 finite nonnegative requested times. Units are declarations, not conversions.

Independence and noninformative right censoring are required. Log-rank is an
asymptotic distribution comparison, not an effect size, hazard ratio, equivalence
test or causal analysis. Crossing curves can reduce its power. Intervals are
pointwise, not simultaneous. Sparse-event inference needs appropriate review;
a computed p-value is not clinical validation.

## Shared helper compatibility

`cpj_kaplan_meier._fit` now accepts private log/log-log and boundary-presentation
settings; its existing defaults remain log-log/suppressed. Horizon selection is
extracted into `_summarize_queries` with the original single-cohort defaults.
All 156 existing frozen single-cohort configurations are compared exactly against
the pre-change module, in addition to their independent R regression tests.

## Independent references and evidence

`tests/reference/grouped-survival-core.R` freezes 30 datasets × three confidence
levels × two timefix settings = **180 configurations**. Interior calculations use
`survfit`, `summary.survfit`, the R survival risk-set routine and R's contrast
solver/chi-square tail. Default-timefix estimable cases additionally agree with the
public `survdiff` call. The final fixture SHA-256 is
`db8e3902d7920fc3b1a306fd91de235e5b7cb81124b24fbab79208fe1739c381`.

The source engine passes **133,020 comparisons** (maximum scaled difference
3.552713678800501e-15; declared tolerance 2e-10). Eleven focused tests cover hand
covariance/score calculations, common missingness, event/censor ties, [1,1] versus
suppressed boundaries, strict support, global tie normalization, label/order/ID
preservation, degenerate tests, invalid inputs, 100,000 observations and audit
bounds. Seven statistical mutations are rejected against the independent fixture.
The existing thirteen single-cohort tests pass. All **768 Python tests** pass
in 326.139 seconds without failures, errors or skips. A supplemental 100,000-row
rare-group risk-set/covariance/statistic comparison also agrees with R, with
contrast condition number 625025000.0624899. This stress check does not validate
asymptotic coverage for sparse groups.

Reference-harness failures remain separate from statistical implementation:

1. Explicit `timefix` in installed survival 3.8.12 `survdiff()` is forwarded into
   `model.frame()` and fails. The reference uses the default public call for TRUE;
   exact ties use the lower-level R risk-set routine and R solver without modifying
   the installed package. The initial all-unavailable reference was rejected before
   Python implementation after its status distribution was audited.
2. Passing integer group codes to `survdiff.fit` reorders them by first appearance;
   passing the declared-order factor preserves the intended mapping. The mismatch
   was caught on reversed singleton groups and corrected in the reference, not
   by changing Python's group order.
3. A focused-test expectation incorrectly treated the observed label `Unused` as
   inactive. The corrected test checks actual membership and retains that label.

The final corrected R fixture is replayed byte-for-byte. Initial outputs/logs are
retained under `/private/tmp/cpj-grouped-survival-*`. No new clinical, native,
GUI, compatibility or platform qualification follows from this source gate.

Reproduce using jamovi's bundled Python and its Resources `PYTHONHOME`:

```sh
Rscript --vanilla tests/reference/grouped-survival-core.R /private/tmp/grouped-replay.json
cmp tests/fixtures/grouped-survival-core.json /private/tmp/grouped-replay.json
python -B tools/check-grouped-survival-core.py
python -B tests/python/test_grouped_survival_core.py
python -B tests/python/test_kaplan_meier_core.py
```

The upstream [survdiff manual](https://stat.ethz.ch/R-manual/R-devel/library/survival/html/survdiff.html)
and [reference risk-set implementation](https://github.com/therneau/survival/blob/master/src/survdiff2.c)
explain rho=0, tied-risk covariance and the supported right-censored setting.
The [R wrapper](https://github.com/therneau/survival/blob/master/R/survdiff.R)
identifies positive-expectation contrasts. These sources informed the contract;
local frozen package results are the numerical oracle.

## Feature and omission matrix

| Feature | This source increment | Remaining gate |
|---|---|---|
| Grouped KM, log limits, medians and horizons | Independent numerical agreement; executable native source and static plot | Package and GUI gates |
| Unweighted overall log-rank and risk audit | Independent agreement; native lifecycle and unavailable reasons pass | Packaged runtime and GUI gates |
| Single-cohort defaults | Exact prior-output and independent R regressions | New source is not installed yet |
| Factor labels, missingness and subject IDs | Native reference transport/row alignment pass | Packaged saved-file qualification |
| Weighted/pairwise/stratified tests, multiplicity | Omitted | Separate baseline contracts and validation |
| Cox, PH diagnostics, RMST, adjusted/parametric models | Omitted | Separate engines and clinical review |
| Dates, delayed entry, competing risks, recurrent events, weights | Omitted | Suitable designs and validated implementations |
| Interaction | Omitted | Explicit Apply semantics and static export counterpart |
| Native/package/desktop/platform | 2,055 native source assertions and restored-state PNG export pass | Packaged artifacts, desktop and supported-platform checks |

## Native source integration

The literal `inst/python/analyses/jsurvival/pysurvival.py` SPEC owns all controls,
native result definitions and UI; use `tools/generate.py` and jamovi compiler
preparation to regenerate integration files. Event/censor selectors, groups,
optional subject IDs, declared units and independent-subject assumptions are
visible. Default plot/CI/censor toggles remain off. Secondary audits and plots
are collapsed. No interactive preview or implicit model refit is introduced.

Native tables include cohort/missingness/mapping, group raw/effective maxima,
medians/horizons, log-rank status and group contributions. Enabling KM steps also
shows covariance and pooled event-time risk rows. Steps, risk rows and retained
source rows each have a 1,000-row display bound; notices disclose truncation while
all retained observations contribute to inference. At most 20 groups, 200 horizons
and 100,000 source observations are supported. Unused declared groups are reported
and excluded from inference. A one-group or otherwise unavailable comparison
retains valid curves and blank test statistics with a reason.

The `groupkm` saved drawing contract holds complete risk/product/limit geometry
for at most 5,000 total group steps and 2 MB. Beyond that bound the chart is omitted
with a warning and full inference retained; there is no display sampling. The
renderer validates group codes, totals, follow-up support, counts, monotonic times,
product-limit probabilities and boundary limits without accessing original data.
Theme colors plus distinct dash patterns distinguish series; legends show stable
factor codes, labels and n. Labels over 120 characters are shortened only in the
drawing and disclosed; native tables retain them. Native Image supplies PNG
export. Log bands are pointwise; censor ticks denote distinct group times.

Four adapter tests check all 180 frozen configurations' native estimates, risk/
score/covariance/test mapping, labels/row IDs and saved plot step/band/censor
geometry, with refitting disabled while rendering. They also exercise explicit
invalid roles/mappings/options, third outcomes even on incomplete rows, corrupted
saved plot data and 5,001-step chart omission with 1,000-row audit bounds. Early
test-only failures were a Matplotlib import before activating the vendored path,
and an all-event fixture lacking its explicitly selected censor level; both were
corrected in test setup without changing statistical behavior.

The synthetic Data Library CSV contains twelve subjects, nine complete triples,
three independent groups, a time-zero event, tied times and three missing-role
rows. It is an example, not real patient data or clinical validation.

Source compiler/native lifecycle/restored-state export and full-suite gates now
pass (see final checkpoint below). Next: actual archive runtime, GUI Sideload/fresh
engine, saved `.omv` reopen/rerun,
HTML/PNG export and prior-analysis compatibility. Other platforms and full baseline
methods remain pending.

## Final source checkpoint

Generator/status freshness and diff checks pass. The final R replay additionally
checks default public-call observed/expected vectors and covariance, not only its
permutation-invariant scalar statistic. The installed 0.3.77 archive SHA-256
`f99c0cdbf6c82a1de7ea333e395251f2c11abf80e53877654d89d3e2a69a3801`
and all 1,544 installed files remain unchanged. Grouped native-source and package
qualification are reported separately below. No stage, commit or push is part of this increment.

Evidence logs: `/private/tmp/cpj-grouped-survival-core-20261116.log`,
`/private/tmp/cpj-grouped-survival-focused-20261116.log`,
`/private/tmp/cpj-grouped-survival-full-python-20261116.log`,
`/private/tmp/cpj-grouped-singlearm-regression-20261116.log` and the R oracle/replay
logs and initial diagnostic snapshots with the same prefix. Supplemental large-row
R construction/reference is under `/private/tmp/cpj-grouped-large-reference-20261116.*`.

## Native source qualification — 2026-11-16

Compiler preparation, generated SPEC/UI/backend freshness and isolated source R
installation pass. Against that isolated library, **2,055 native R assertions**
pass across all 60 independent 95% reference configurations, with no failures,
errors, warnings or skips. These exercise complete-case/group ordering, native
counts/medians/horizons/log-rank vectors/covariance and original row identities.
Lifecycle tests cover optional outputs off, required time/group/event/censor
removed, malformed horizons, third outcomes on incomplete rows, duplicate IDs,
invalid times and recovery. Reused and fresh analyses agree; serialized plot state
exports a PNG after removing source-data access. This is native source integration,
not a desktop `.omv` save/reopen claim.

The synthetic example independently agrees with R `survdiff`: chi-square
8.117197847435179, df 2, p 0.01727320324487263. A 700×500 source preview was
visually inspected for group support, legends and confidence/censor geometry.
No application rendering or accessibility acceptance follows from that preview.

The native log includes recurring subprocess `Error: Operation not permitted`
stderr messages. They are retained as environment diagnostics; the test framework
reports zero errors/warnings and all assertions pass. An early native invocation
preceded completion of isolated installation and could not load the package;
it was rerun after installation completed. An intermediate suite was explicitly
interrupted to add the bounded pooled-risk audit, then regenerated/reinstalled and
rerun completely. These attempts are not counted as passing final evidence.

Logs: `/private/tmp/cpj-grouped-prepare-final-20261116.log`,
`/private/tmp/cpj-grouped-install-final-20261116.log`,
`/private/tmp/cpj-grouped-native-final-20261116.log`,
`/private/tmp/cpj-grouped-example-R-20261116.log`. Restored native PNG:
`/private/tmp/cpj-grouped-native-restored.png`; source preview:
`/private/tmp/cpj-grouped-survival-source-preview.png`.

The installed 0.3.77 archive SHA-256 remains
`f99c0cdbf6c82a1de7ea333e395251f2c11abf80e53877654d89d3e2a69a3801`;
all 1,544 installed files still match archive contents. No package rebuild,
Sideload, commit or push is included in this native-source milestone.

The first complete native-source Python run executed 772 tests in 381.850 seconds:
771 passed and one registry test still hard-coded `pysurvival` as planned. The
corrected regression checks every actual planned entry from the registry for both
absent source and refusal to execute, preserving invalid-path probes. All six
focused migration tests pass. The final full-suite rerun is recorded separately;
the stale test was not a statistical/runtime defect. Initial full-suite evidence:
`/private/tmp/cpj-grouped-native-full-python-final-20261116.log`; focused repair:
`/private/tmp/cpj-grouped-migration-regression-20261116.log`.

The packaged/desktop gate originally had an unexecuted checklist; its [current execution record](python-grouped-survival-gui-checklist.md) now reports the independently checked examples, lifecycle, fresh-engine saves/exports and prior single-cohort compatibility.

## Final native-source checkpoint

The final complete Python rerun passes **all 772 tests in 330.129 seconds**, with
no failures, errors or skips. Log:
`/private/tmp/cpj-grouped-native-full-python-qualified-20261116.log`. All 180
adapter/geometry configurations, pooled risk display checks, prior single-cohort
regressions and existing analyses are included. Compiler preparation, source
installation, all 2,055 native assertions, generator/status freshness and diff
checks pass. Inventory: 39 partial, 22 planned, 15 utilities, 54 entry points;
zero full baseline parity. The next work is the explicitly unexecuted packaged
runtime/desktop protocol, not additional numerical or GUI claims.

## Packaged and desktop follow-up — 0.3.78

The [package/GUI record](python-grouped-survival-package-validation.md) now completes
this increment's actual archive and bounded macOS desktop gates. There are 320,926
grouped archive checks/540 configurations, 638,569 total checks/1,428 configurations
including single-cohort/waffle regressions, 2,055 native assertions against each
built/installed library, two fresh GUI engines, seven saved profiles, native
HTML/PNG export and unchanged prior single-cohort data/tables/cached pixels.
Four artifact corruptions are rejected; all 1,551 installed / 1,438 shipped
R-library files match. The initial concurrent timeout and isolated success with
unchanged limit remain separately recorded. Full methods, clinical review,
accessibility and other platforms remain open. The current implementation plan
identifies next work; earlier pending-package language is historical evidence.
