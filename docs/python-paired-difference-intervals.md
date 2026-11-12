# Paired-difference intervals — source contract, 2026-11-11

This increment validates **Newcombe's method 10** for a difference of two paired
binary proportions. It is source-only. The installed 0.3.65 package and public R
analyses remain unchanged. `pydecisioncompare` stays planned until native work
passes its separate gates.

## Method and input contract

Input is four integer counts `(a,b,c,d)` = both-success, first-only,
second-only, neither-success. Each count is finite and nonnegative, with total
at most 1,000,000. Confidence defaults to .95 and accepts .80–.99. Boolean,
fractional, malformed, masked, negative or nonfinite counts are errors.
At zero total return undefined estimate/bounds/correlation with `empty` status.

At positive total `n`, estimate `delta=(b-c)/n`. Combine the two marginal Wilson
score intervals with the paired correlation correction: let `A=a*d-b*c`;
use `max(A-n/2,0)` when A is positive and retain A when negative. Divide by
`sqrt((a+b)*(c+d)*(a+c)*(b+d))`; a zero margin gives correlation zero. This is
Newcombe's correction, not a continuity correction to the McNemar statistic.
Use the corrected correlation in the lower and upper square-and-add distances
and bound the resulting limits to [-1,1]. Confidence limits are approximate,
pointwise and unadjusted for multiplicity. Identical paired outcomes do not
produce an automatic zero-width interval or establish equivalence.

The helper returns estimate, limits, total, the original cells, corrected
correlation and interval status. It does not alter McNemar p-values. The existing
source comparison engine adds intervals only with an explicit
`difference_intervals=True` argument; its default stays point-only. Empty
reference classes have undefined intervals and retain their absent-class test
status. Accuracy Holm adjustment does not adjust any confidence limit.
These intervals do not invert the McNemar or Holm tests; their zero-exclusion
and the separately calculated p-values need not give the same verdict.

## Provenance and numerical gates

The missing baseline helper is now pinned from the original `meddecide` commit
`c343bf8a2f9f711e7a0f6ed3941415170d1e3f58`, Git blob
`3fac0f4e7fbe39c0458dde12bc055c1688abc720`, SHA-256
`b59b06c725862412190980797e2a591899263d265b7fa7560e9fc8fc8e098d67`.
It was present at that commit but omitted from the four-file baseline archive;
this supplements provenance without replacing the archive or mutable siblings.

Independent maintained references are the unmodified paired square-and-add and
Wilson functions from `ocbe-uio/contingencytables` commit
`fe8231b58d199039e023fe9e03baf97254bc7abd`, version 3.1.1.9010, GPL-3. Files,
authors/license metadata and hashes are frozen under
`tests/reference/frozen/paired-intervals/`. The harness supplies only argument
validation/result-container adapters; it does not replace their calculations.
Compare 95% results with the original helper and all three confidence levels
with the independent implementation. Independently evaluated MPFR256 arithmetic
checks boundary and large-count cases using double-precision R normal quantiles
lifted exactly to MPFR; it does not qualify arbitrary-precision quantiles.

Freeze fixtures before writing the Python interval implementation. Cover the
0–4 cell grid, degenerate margins, positive/negative/zero corrected correlation,
single pairs, identical/reversed outcomes, near-boundary and 1,000,000-total
tables, the historical R integer-product overflow case, published paired
examples, and all earlier diagnostic comparison pairs. Require agreement within
`1e-12`, including sign reversal and simultaneous complementation identities.

## Prespecified coverage profile

Use exact multinomial enumeration, without Monte Carlo sampling, for n=5, 10,
20 and 50 at 80%, 95% and 99% confidence. Enumerate every four-cell table and
verify probability mass sums to one. Population scenarios, in `(a,b,c,d)` order:

| Scenario | Probabilities |
|---|---|
| Independent balanced | (.25,.25,.25,.25) |
| Positive association | (.45,.05,.05,.45) |
| Negative association | (.05,.45,.45,.05) |
| Asymmetric difference | (.35,.25,.05,.35) |
| Rare successes | (.005,.005,.005,.985) |
| Sparse boundary | (0,.001,.099,.9) |
| First always succeeds | (.6,.4,0,0) |
| Identical fixed failures | (0,0,0,1) |
| Fixed discordance | (0,1,0,0) |

True difference is `p_b-p_c`. Use an explicit `1e-12` endpoint tolerance. Record
coverage, mean width, mass sum and failures of `coverage >= nominal-.02`.
This two-percentage-point screen is a development criterion, not a guarantee of
nominal coverage or clinical acceptance. Report failures without changing the
method or selecting a replacement automatically. Keep public integration
separate from this numerical/calibration evidence.

## Results and delivery boundary

All **39,222 numerical checks** pass across 731 count tables and 2,193 confidence
runs. Maximum absolute difference from the original helper, independent R
functions and MPFR targets is `4.440892098500626e-16`, below the `1e-12` tolerance.
The interval fixture SHA-256 is
`6a63b77191840f8b4597efbf321414e57a9e30f4aa2192dc77f33cafb62a6c10`.
Opt-in adapter checks cover every earlier paired diagnostic fixture at all three
confidence levels and McNemar methods. Removing interval fields reproduces the
original cohort, point estimates and p-values exactly. The original 27,552
paired-comparison checks still pass. Ten focused interval tests pass, including
the small-sample independent coverage replay.

The initial MPFR decimal-string serialization produced R object descriptions.
The harness now uses `Rmpfr::formatMpfr` explicitly. All numeric targets, original
helper results and independent R results are byte-for-byte unchanged as parsed
values; only MPFR strings and the harness hash changed. The original fixture is
retained locally as ignored evidence, rather than used as a numeric reference.

Python and independent R agree within `1e-12` for every exact coverage/mean-width
profile and verify total probability mass. **102/108 profiles pass** the screen.
All six failures remain visible:

| n | Nominal confidence | Population scenario | Exact coverage |
|---:|---:|---|---:|
| 5 | 80% | Independent balanced | 73.4375% |
| 5 | 80% | Negative association | 71.5285% |
| 5 | 95% | Negative association | 91.2976% |
| 5 | 99% | Negative association | 92.2088% |
| 10 | 80% | Independent balanced | 77.8538% |
| 10 | 80% | First always succeeds | 77.7948% |

This is a failed broad small-sample screen, not a numerical implementation
failure. The method is unchanged; no automatic fallback is introduced. Intervals
remain opt-in in the source prototype and absent from jamovi controls. Native
integration may advance as a point/comparison core with paired intervals explicitly
omitted; exposing these intervals requires a separately reviewed scope and clear
approximation/coverage disclosures. Full baseline parity, GUI and clinical gates
remain open.

Five in-memory mutations are detected by assertion failures: omitting the positive
correlation correction, clipping negative correlation, assuming independent pairs,
reversing the difference and forcing zero width for identical outcomes. The source
engine is unchanged by these probes. Reproduce numerical checks with
`tools/check-paired-intervals.py` and the coverage profile with
`tools/check-paired-interval-coverage.py` in bundled Python. Generated reports/logs
remain local and ignored.

All 557 Python regression tests pass, including the original point/comparison
checks. Fresh independent R replays reproduce both interval and coverage fixture
bytes exactly. Generator/status freshness checks pass. The installed 0.3.65
archive is unchanged; no native, GUI, platform or clinical interval qualification
is claimed.

Method sources: [Newcombe (1998), paired proportions](https://pubmed.ncbi.nlm.nih.gov/9839354/)
and the [independent paired square-and-add reference](https://ocbe-uio.github.io/contingencytables/reference/Newcombe_square_and_add_CI_paired_2x2.html).
