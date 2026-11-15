# Single-factor goodness-of-fit — frozen source contract (2026-11-14)

Extend the reusable pie engines in source; keep the qualified 0.3.72 JMO and
installed module unchanged. No SPEC/menu change, statistical default change,
native inference table, new package or GUI claim belongs to this increment.

`pie_gof(outcome, weights=None, subject_ids=None, enabled=False, ratios=None)`
reuses the validated pie cohort/count engine. Return descriptives unchanged and
a separate goodness-of-fit object. Require a genuine Bool enable flag. Off means
no ratio parsing, expected counts, test or residual calculation; stale inactive
ratio settings must not block descriptive results. Off status is `disabled` with
null method/statistic/df/p and no expected rows.

When enabled, null support is **all nonmissing declared categories**, including
unused/zero-count categories, in declared factor order. Actual missing level
labels are excluded; a literal NA category remains. Equal probabilities over that
support are the default. Custom ratios are an exact label-to-positive-number map
covering that whole support, with no missing/extra labels, booleans, strings,
nonfinite, zero or negative values. Ratios need not sum to one. Normalize via a
bounded scale to avoid overflowing the sum of otherwise finite ratios. Refuse
underflowed probabilities or expectations rather than silently dropping a null
category. Structural zero probabilities and positional/string ratio interfaces
are outside this increment. The eventual native parser must reject duplicate keys.

For k>=2, expected counts are E=N*p; Pearson X2=sum((O-E)^2/E), df=k-1, upper-tail
asymptotic chi-square p. No Yates/continuity correction, fitted-null parameters,
Fisher switch, automatic exact binomial test or Monte Carlo calculation. Return
separate labelled expected rows (original code, label, observed count, null
probability, expected count, Pearson residual and X2 contribution). No per-cell
p-values, standardized residuals, effect-size points/intervals or clinical bands.

Any E<5 sets an explicit sparse warning/status; p remains a labelled approximation,
never an exact result. Record minimum expected count and number below 5, including
the exact E=5 boundary. Independence and a prespecified fixed null are assumptions;
this does not test independence or make a data-estimated null valid. A large p
does not establish equivalence. Underflow of a valid extreme tail p to zero is a
floating-point limit, not an exact zero-probability claim. Reject nonfinite derived
statistics. With only one declared category, keep descriptives/expected row but
return `unavailable`, reason `one_declared_category`, with no statistic/df/p.

Freeze independent R `chisq.test()` references before writing Python. Include the
existing pie cohorts, custom/scaled ratios, reordered/missing/zero levels, sparse
and E=5 cases, a published manual example, a perfect fit, extreme valid counts,
one-category unavailability and invalid/domain refusals. Compare the released
ggpiestats frequentist subtitle where available, separately from base R. Record
baseline limits instead of fabricating parity. Replay R byte-for-byte; test tiny
arithmetic/closed-form df=2 p, ratio-scaling/reordering identities, disabled gating,
retained source identities and deliberate corrupted outputs.

Method sources: [base R chisq.test](https://stat.ethz.ch/R-manual/R-devel/library/stats/html/chisq.test.html)
defines the one-dimensional multinomial null and asymptotic p;
[SciPy chisquare](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.chisquare.html)
documents the fixed-null df and small-expected-count limitations. Sparse inference
is approximate; exact/Monte Carlo methods and their resource policy need a later
contract. Neither references nor numerical parity establish clinical validity.


## Earlier source-only evidence

The frozen R fixture covers **18 datasets / 54 enabled runs**, plus 18 disabled
requests for **72 source configurations**. All **2,286 comparisons** pass; maximum
scaled difference is **3.497202527569243e-15**. Twelve small ggpiestats frequentist
subtitle checks agree on statistic/df/p. The one-factor baseline subtitle also
reports Pearson's C and an ncp interval; neither is implemented by this source
core. A one-category base-R error is represented here as explicit unavailability,
with descriptive data retained. Larger counts use the validated non-expanded
pie engine; the baseline's frequency-expansion limits remain documented separately.

Ten focused tests pass, covering tiny exact arithmetic and the df=2 exponential
tail, zero-count null support, labelled ratio mapping/reordering/scaling, sparse
and exact E=5 cases, calculation-off gating, invalid/extreme probabilities,
missing levels and exact subject IDs, one-category unavailability, and five
corrupted outputs rejected by the independent checker. No Monte Carlo or clinical
calibration claim is made. A low expected count warning does not make asymptotic
inference exact or establish adequate sample size.

The first checker compared a statistic serialized by R as JSON integer 10 with
strict integer equality. The source value was 10.000000000000002, a difference
of 1.7763568394002505e-15. A third calculation using SciPy chisquare with the
frozen R expected counts returned 10.0. The checker now treats statistic/expected/
residual fields as floating quantities regardless of their JSON spelling, using
the original prespecified 2e-12 scaled tolerance (and 1e-10 relative p tolerance).
Counts, degrees of freedom, codes, flags and category support retain exact checks.
No tolerance, method, null support or input was changed. Adjudication is retained
in /private/tmp/cpj-pie-gof-initial-roundtrip-20261114.log.

R replay is byte-identical. Fixture SHA-256:
`13b588b4ab5dc1de3bcaee1771679944d1c479f41389029706c356a6af62d240`.
Oracle script SHA-256:
`bf14995269ee3be00c5014de9213c487d1a2b0461eea7e63def76111f6edb1d1`.
The qualified 0.3.72 JMO and all 1,473 installed files remain unchanged. There is
no native GOF result, changed public default, new menu entry or packaged/desktop
qualification for this source increment.

```sh
Rscript --vanilla tests/reference/pie-gof-core.R /private/tmp/pie-gof-replay.json
cmp tests/fixtures/pie-gof-core.json /private/tmp/pie-gof-replay.json
PYTHONHOME=/Applications/jamovi.app/Contents/Resources \
  /Applications/jamovi.app/Contents/MacOS/python -B tools/check-pie-gof-core.py
PYTHONHOME=/Applications/jamovi.app/Contents/Resources \
  /Applications/jamovi.app/Contents/MacOS/python -B tests/python/test_pie_gof_core.py
```

Next design native expected-ratio controls that reveal and preserve the actual null
support and raw labels. Add optional expected-count and test tables with sparse/
one-category messages, then test native transitions and saved-state behavior before
building the next package. Keep fixed-null assumptions visible; do not imply that
ratios fitted from these observations retain df=k-1 calibration.

Final source gate: **689 Python tests** pass in 256.531 seconds, with no failures,
errors or skips. Generator/status freshness and whitespace checks pass.


## Native source increment (2026-11-14)

The same `pyjjpiestats` identifier now has an extended literal SPEC/run interface
in source (analysis contract 0.2.0). Existing data roles, label/plot defaults and
source-row options remain. `resultssubtitle` enables optional fixed-null Pearson
results and defaults **false**. `customRatios` defaults false; equal probabilities
therefore cover every declared nonmissing category unless a custom null is selected.
`ratio` accepts a labelled object, for example `{"No":4,"Other":2,"Yes":3,"Zero":1}`;
`showExpected` defaults true but only applies to enabled inference. No expected
counts or tests are calculated while inference is disabled.

The organized Analysis and Model panel contains the test switch and enabled custom
ratio controls, with support/independence guidance. Results and Interpretation has
expected-count and source-row switches. Input/output bindings are generator-owned.
Custom ratios use exact dataset labels, including spaces and zero categories.
The parser permits at most 20,000 characters; rejects duplicate decoded keys
(including escaped duplicates), malformed/deep/executable text, nonfinite constants
and non-object roots; and delegates strict label/positive-value checks to the frozen
engine. Inactive custom text is ignored. No code evaluation is performed.

Native tables separate the observed frequency table from the fixed-null test and
expected mapping. The latter reports null probabilities, expected counts, Pearson
residuals and chi-square contributions; no per-category tests or intervals are
implied. Sparse expected counts produce a warning and labelled approximation, with
no method switch. A single declared category produces an information message and
unavailable statistic/df/p, retaining the descriptive results and expected row.
The assumptions require independent observations and externally prespecified
probabilities; a large p does not establish equivalence.

Six adapter tests execute all 54 independent enabled runs, check parser refusal and
inactive-input gates, exact/reordered labels, expected-table visibility and the
actual subprocess route. All six prior descriptive-renderer tests still pass.
The complete Python suite passes **695 tests** in **338.113 seconds**, without
failures/errors/skips; focused adapters were rechecked after the code-heading and
display-contract refinements. The isolated native library passes **1,027 assertions**,
without failures/errors/warnings/skips. These exercise all 54 expected mappings and
statistical runs, default descriptive results, strict custom-input failures,
disabled/invalid/required-input clearing and recovery, and drawing-state restoration
with analysis data removed before PNG export. All six relevant isolated Python files
byte-match final source. Compiler preparation/roxygen and generator/status freshness
pass; NAMESPACE remains managed by the existing export pattern.

The first native run reported nine harness mismatches. Six concerned wholly empty
numeric columns (logical NA in jmvcore's data-frame view versus double NA in the
reference); the tests now compare numeric values and missingness. Three concerned
true missing factor levels: the existing R bridge removes those levels and renumbers
the transported codes. Labels, observed counts and null mappings agreed. The audit
column key `code` is retained, its heading now says **Category Code (0-Based)**,
and a note explains the transport semantics. Native tests check transported codes;
the direct Python API continues to preserve its own input codes. No statistical
method, numeric tolerance or expected label/probability was changed. The failed run
is preserved at /private/tmp/cpj-pie-gof-native-20261114.log.

The synthetic six-row CSV yields N=25 with counts No=12, Other=5, Yes=8, Zero=0.
Equal null: native X2=12.279999999999999, df=3, p=0.0064830336341513148;
base R X2=12.280000000000001, p=0.0064830336341513113. Custom 4:2:3:1 null:
X2=2.9333333333333336, df=3, native p=0.40201848834297005 versus base R
0.40201848834297016, with minimum expected=2.5 and one expected count below 5.
These are numerical examples, not proposed clinical nulls. Both preserve identical
observed rows and drawing state. The exported 1300×900 PNG byte-matches the qualified
0.3.72 descriptive PNG (SHA-256
`6c4c07915c37a8008a892c14ac3deeb47daeb1c1ff8ba7fec291c6300ae64e78`).

No JMO was built or GUI installed for this increment. The qualified 0.3.72 archive
and all 1,473 installed files remain unchanged. Next qualify the actual new package,
prior descriptive saved-file compatibility, fresh-engine equal/custom/invalid/off
transitions and saved/exported inference tables. Full methods, clinical review and
other platforms remain separate gates.

```sh
PYTHONHOME=/Applications/jamovi.app/Contents/Resources \
  Rscript --vanilla tools/check-pie-native.R <isolated-library>
PYTHONHOME=/Applications/jamovi.app/Contents/Resources \
  Rscript --vanilla tools/check-pie-gof-example.R <isolated-library> /private/tmp/pie-gof.png
```

The future package checker also passes against the **source runtime**: 5,148
checks / 131 configurations. This is source execution, not an archived-JMO gate;
the actual next package still requires its own extraction/execution and GUI tests.

## 0.3.73 candidate package gate — 2026-11-14

The subsequent package build succeeds as `ClinicoPathPj_0.3.73.jmo`, 23,638,449
bytes, SHA-256 `f1ba37792893132502a0d0214959aa39eaa284a0c1305a11ad9dd0764774f898`.
CRC, metadata, unique paths, source/UI bindings and extracted Python execution pass:
5,148 pie checks/131 configurations, 5,435 bar/90, 6,692 histogram/270 and
2,008 mean/102. The built native library passes 1,027 assertions with no
failures/errors/warnings/skips. Every shipped R-library file (1,393 files) is
byte-identical to that tested library. The prior 695-test final-source gate is
retained; packaging/documentation changes do not rerun it.

Two GUI connection attempts fail with `Sky Computer Use native pipe startup failed`.
Consequently no 0.3.73 Sideload, legacy saved-file reopening, fresh-engine interaction
or native desktop export is claimed. All 1,473 installed files remain byte-identical
to qualified 0.3.72, whose root archive is retained for rollback. Follow the
[desktop checklist](python-pie-gof-gui-checklist.md) when GUI access is restored;
it includes independent base-R values from `tests/reference/pie-gof-example.R`.
The candidate remains outside desktop/release acceptance. Full methods, clinical
review and other platforms are still separate gates.
