# Welch standardized effects — independent replication and sensitivity

## Prespecified protocol (2026-11-12, before generating results)

This study leaves the original 24,000-draw screen and its decisions intact. It
neither pools its outcomes with that screen nor changes the .925 minimum. The
Python estimator, inversion domain, confidence (.95) and unavailable-value policy
remain frozen. The inversion domain is inclusive `2 <= df <= 100000` and
`abs(t) <= 40`. Supported intervals have status `ok`; outside that domain status
is `interval_unavailable`, finite points retained, limits null. A zero SE or
`SE < 10*machine_epsilon*max(abs(mean1),abs(mean2))` is raw `degenerate`.
This is source-method validation, not native/GUI qualification.

Freeze these 17 profiles before examining their outcomes:

1. Independent replication: normal populations, n1=20, n2=5, sigma1=1, sigma2=4,
   true delta_RMS=0; 20,000 fresh independent datasets.
2. Eight small-sample normal profiles: each of (n1,n2)=(2,2),(2,5),(5,2),(3,3),
   sigma1=1, sigma2=4, crossed with true delta_RMS=0 and 1.5;
   4,000 datasets per profile.
3. Eight nonnormal sensitivity profiles: standardized lognormal(exp(Z)) and
   standardized Student t(5), each with (n1,n2)=(5,20),(20,5), sigma1=1,
   sigma2=4, crossed with true delta_RMS=0 and 1.5; 4,000 datasets per profile.

All observations and groups are independent. For each distribution start with
known population mean zero/variance one: normal Z; `(exp(Z)-exp(.5))/sqrt((exp(1)-1)*exp(1))`;
or t(5)/sqrt(5/3). Scale by the group's population sigma. Shift the first group's
mean by `delta_RMS*sqrt((sigma1²+sigma2²)/2)`; the second mean is zero.
Nonnormal profiles are sensitivity checks outside the normal-model assumption,
not a claim of intended distribution-free inference.

R alone generates the observations using seed 37112026 (Mersenne-Twister,
Inversion normal generator, Rejection sampler). Freeze the actual observed sample
means/variances and R NCT-CDF values in a compressed CSV, plus selected original
observation arrays in the manifest. A seed is provenance, not a shared-draw oracle.
Record R/package versions and SHA-256 of the unchanged production helper and the
original three reference fixtures. The Python checker must verify those hashes.

Use Welch SE/df, RMS-SD, and true population delta to assess interval inclusion via
NCT CDF monotonicity. Missing/unavailable intervals count as noncoverage. Report
both availability and coverage among available intervals, so domain restrictions
are distinguished from statistical undercoverage. The decision denominator is
always all prespecified datasets, never only successful fits.

For each profile, use exact Clopper–Pearson bounds at family confidence .95,
Bonferroni across all 17 profiles (tail .05/(2*17)). Pass the limited screen if
the lower bound >= .925; fail if the upper bound < .925; otherwise inconclusive.
Do not stop early, change sample counts, relax thresholds, pool prior results,
selectively rerun profiles or adjust methods after examining outcomes.

Freeze four original datasets per profile: first, last, and closest R CDF values
to .025 and .975 (unique indices; if duplicated, retain unique datasets). Obtain
independent R pt/uniroot limits for supported datasets; unsupported datasets have
null limits. The checker calls the actual Python public helper on these original
observations and compares moments, point estimates, df, intervals and classification.
Point relative tolerance 1e-10; interval scaled absolute tolerance 2e-7;
CDF absolute tolerance 2e-9. Zero targets use absolute tolerance 1e-12.

Record every numerical mismatch separately from a coverage failure. Require a
byte-identical R regeneration of the compressed fixture and manifest, independent
Python replay, focused corruption/mutation checks and the full frozen-source suite.
Leave installed 0.3.68 unchanged. Native inference cannot be promoted from numerical
agreement alone; document unresolved normal/small-sample and sensitivity limits
and explicitly decide the next scope after the screen.

## Executed results

The independent R builder did not inspect the target Python formulas. It generated
and froze the reference data before Python replay. Both compressed draws and the
manifest regenerate byte-identically, including their warning provenance. Existing
production helper hashes and the three original reference fixtures remain unchanged.

**Numerical evidence (EXEC-IND):** all 84,000 R/SciPy probabilities agree within
7.43e-13. The actual public Python helper agrees with independent R on all 68
selected original datasets, including those closest to coverage boundaries.
The 1,037 numeric/metadata comparisons have maximum scaled difference 8.87e-12;
no probability, point, availability, inclusion or endpoint mismatch remains.
Six focused tests reject altered probabilities, missing/duplicated replicates,
fabricated coverage, changed original observations, source/prior-fixture hash
drift, and deliberately shifted engine intervals. The initial replay stopped on a
schema mismatch (R uses string profile identifiers and quoted CSV fields); the
Python reader was corrected without changing references, methods or tolerances.

**Simulation evidence (SIM):** the independent replication covers 18,949/20,000
(94.745%), with simultaneous Clopper–Pearson bounds [94.2592%, 95.2027%]. It passes
the frozen .925 minimum; the original screen's inconclusive result remains recorded
separately. Across the complete new study, seven profiles pass, seven fail and
three are inconclusive. These are method-screen outcomes, not numerical test
failures. Coverage includes all requested datasets; unavailable intervals count
as noncoverage. Availability is 69,211/84,000; 14,789 intervals are unavailable.

| Kind / distribution | n1, n2 | True delta | Available / N | Coverage | Simultaneous CP bounds | Decision |
|---|---|---:|---:|---:|---:|---|
| replication / normal | 20, 5 | 0 | 20,000 / 20,000 | 94.745% | 94.259–95.203% | pass |
| small_sample / normal | 2, 2 | 0 | 0 / 4,000 | 0.000% | 0.000–0.163% | fail |
| small_sample / normal | 2, 2 | 1.5 | 0 / 4,000 | 0.000% | 0.000–0.163% | fail |
| small_sample / normal | 2, 5 | 0 | 3,918 / 4,000 | 94.000% | 92.801–95.060% | pass |
| small_sample / normal | 2, 5 | 1.5 | 3,931 / 4,000 | 94.250% | 93.072–95.288% | pass |
| small_sample / normal | 5, 2 | 0 | 708 / 4,000 | 8.150% | 6.917–9.515% | fail |
| small_sample / normal | 5, 2 | 1.5 | 660 / 4,000 | 7.875% | 6.662–9.221% | fail |
| small_sample / normal | 3, 3 | 0 | 4,000 / 4,000 | 94.200% | 93.018–95.242% | pass |
| small_sample / normal | 3, 3 | 1.5 | 3,999 / 4,000 | 94.025% | 92.828–95.083% | pass |
| sensitivity / lognormal | 5, 20 | 0 | 4,000 / 4,000 | 92.350% | 91.021–93.546% | inconclusive |
| sensitivity / lognormal | 5, 20 | 1.5 | 4,000 / 4,000 | 57.925% | 55.580–60.245% | fail |
| sensitivity / lognormal | 20, 5 | 0 | 4,000 / 4,000 | 82.650% | 80.806–84.391% | fail |
| sensitivity / lognormal | 20, 5 | 1.5 | 3,995 / 4,000 | 64.800% | 62.520–67.034% | fail |
| sensitivity / student_t5 | 5, 20 | 0 | 4,000 / 4,000 | 94.750% | 93.617–95.741% | pass |
| sensitivity / student_t5 | 5, 20 | 1.5 | 4,000 / 4,000 | 91.825% | 90.458–93.060% | inconclusive |
| sensitivity / student_t5 | 20, 5 | 0 | 4,000 / 4,000 | 95.500% | 94.440–96.416% | pass |
| sensitivity / student_t5 | 20, 5 | 1.5 | 4,000 / 4,000 | 92.975% | 91.693–94.122% | inconclusive |

Both normal n=(2,2) profiles have zero available intervals under the frozen df>=2
inversion domain. This is an explicit refusal, not a returned incorrect interval.
For normal n=(5,2), availability is only 708/4,000 and 660/4,000; even among
available intervals, coverage is 46.05% and 47.73%, respectively. The restrictions
alone therefore do not explain every small-sample failure. The normal n=(3,3)
profiles pass this limited screen; they do not establish general small-sample validity.

For lognormal observations at delta=1.5, coverage is 57.925% and 64.8%, despite
nearly complete availability. These are clear failures of a distribution-free
claim; the existing prototype explicitly assumes normal populations. Student-t(5)
profiles at delta=1.5 remain inconclusive under the simultaneous .925 screen.
Do not reinterpret failure as numerical disagreement or silently omit those profiles.

R recorded 237 noncentral-t precision warnings: 19 emitted during vectorized
coverage calculations in two lognormal profiles, and 218 during selected endpoint
inversion. The fixture records warning text and contexts. All final probabilities
and selected endpoints agree with the independent SciPy route at the prespecified
tolerances. Warnings are retained as oracle evidence, not silently called a clean R run.
No observations fell within 16 machine epsilons of the df=2 domain boundary.

## Regression and package preservation

The final frozen-source suite passes **622 Python tests** in 248.149 seconds.
Generator/status freshness and `git diff --check` pass. The independent R
compressed fixture/manifest replay is byte-identical; six production/prior-fixture
hashes match. The installed 0.3.68 JMO retains SHA-256
`69f1a62d823a4718d493a6981669cb3fc833b1dd1f8c28eb1cdb57efaeba5088`,
and all 1,453 installed files match its bytes. No new package was built or installed;
there is no new native/GUI/platform qualification claim.

## Delivery decision

Keep generic Welch NCT plug-in inference **source-only**. The original inconclusive
normal profile has an independent passing replication, but that does not resolve
tiny-sample availability/conditional coverage or nonnormal sensitivity. No sample
size threshold, normality-test switch, continuity correction, resampling fallback,
new CI convention or relaxed rule was introduced to obtain a passing result.

Next bounded implementation candidate: optional native RMS-SD **point-only**
results for Welch, with the denominator, orientation and cohort explicit. Reuse the
already independently verified point engine; omit its approximate adjusted point
and all standardized limits from that native route. Keep the existing default
switch off and existing Student/paired behavior. Require adapter/native integration,
packaged-runtime and desktop lifecycle/export evidence before claiming it shipped.
A future uncertainty method needs its own frozen contract and independent evidence.

## Reproduction

From the ClinicoPathPj root, with existing development R packages jsonlite/digest:

```sh
Rscript --vanilla tests/reference/welch-standardized-replication.R
PYTHONHOME=/Applications/jamovi.app/Contents/Resources \
  /Applications/jamovi.app/Contents/MacOS/python -B tools/check-welch-replication.py
PYTHONHOME=/Applications/jamovi.app/Contents/Resources \
  /Applications/jamovi.app/Contents/MacOS/python -B tests/python/test_welch_replication.py
```

The checker exits nonzero for numerical/provenance mismatches. It reports
prespecified statistical failures explicitly while succeeding when it faithfully
reproduces them. A green software check is not a passing inference screen.
Production dependencies, native interfaces, registry status and version remain
unchanged; the installed 0.3.68 module is outside this source-method qualification.
