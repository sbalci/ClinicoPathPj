# Concordance correlation: numerical prototype

The 2026-11-10 numerical increment added `cpj_concordance.concordance(x, y)`.
The subsequent [native integration](python-concordance-integration.md)
now calls it from the existing `pyagreement` CCC method in the installed 0.3.63
build. The numerical evidence below predates that build. Bland–Altman and ICC calculations remain unchanged.

## Estimand and outputs

For complete pairs, use population moments with divisor **n**:

```
CCC = 2 cov(x,y) / [var(x) + var(y) + (mean(x)-mean(y))²]
r   = cov(x,y) / sqrt(var(x) var(y))
Cb  = 2 sqrt(var(x) var(y)) / [var(x) + var(y) + (mean(x)-mean(y))²]
```

When both variances are positive, CCC = r × Cb. Pearson r describes the precision
component; Cb describes departure from the identity relationship. Pearson r alone
does not measure concordance. The reference implementation and method background
are documented by [DescTools](https://andrisignorell.github.io/DescTools/reference/CCC.html).
No agreement bands, interchangeability verdict, p-value or interval is returned.

The engine returns CCC, r, Cb, supplied/complete/missing counts and zero-based
retained source positions. `confidence_interval` is explicitly `None`. Original
case IDs, measurement units and data-role metadata belong to the analysis
adapter; this array-level function cannot establish patient independence or detect
an integer column whose semantic role is categorical.

Supported inputs have 1–5,000 aligned source rows and at least three complete
pairs. NaN means missing; pairs are excluded together. Infinity, masks, booleans,
non-numeric arrays and integers outside ±2^53 are refused. Identical constants
produce an explicitly undefined 0/0 CCC. A constant versus another column produces
CCC=0 and Cb=0, with Pearson r explicitly undefined. Exactly zero Pearson r with
positive marginal variances still permits a defined Cb, computed directly.

A common translation before scaling preserves small differences at large shared
offsets. An overflow-safe scaled fallback handles opposing extreme values.
Unresolved variation is refused. Only roundoff within 64 machine epsilons of a
mathematical coefficient bound is rounded to that bound; negative CCC is retained.

## Executed validation — 2026-11-10

An independent oracle builder created the reference script and expected values
without reading the Python implementation or tests. Base R arithmetic and installed
**DescTools 0.99.60** generated 41 regular and eight degenerate fixtures, including
the public 17-pair PEFR example from the package documentation. Inputs and unrounded
expected values are frozen in JSON. Two reference datasets have only two pairs;
these are tested as refusals under the prototype's stated minimum, not discarded
or assigned revised expected values.

- **43 handled datasets** (39 regular and four constant cases), plus **six explicit
  minimum-pair refusals**.
- **436 coefficient/audit comparisons pass** at absolute tolerance 1e-12; largest
  coefficient difference is **8.881784197001252e-16**.
- Nine new unit tests cover hand arithmetic, missing-pair positions, constants,
  reversal/permutation/duplication invariance, common shifts/scales, extreme valid
  values, invalid storage and resource limits. Together with existing Bland–Altman
  and ICC tests, **30 focused tests pass**.
- The subsequent **full source Python suite passes 482 tests** (172.535 seconds).
  This is source-regression evidence; no new native package or GUI CCC gate is claimed.
- Reference regeneration and repeated Python execution produce identical fixture
  and matrix hashes, recorded in the qualification evidence.
- Two zero-Pearson fixtures expose DescTools' `C.b = CCC/r` 0/0 limitation; direct
  base-R arithmetic and the hand-checkable case establish the defined bias factor.
  No confidence-interval agreement is claimed.

[Reference generator](../tests/reference/concordance-points.R),
[frozen fixtures](../tests/fixtures/concordance-points.json),
[Python engine](../inst/python/cpj_concordance.py),
[numerical matrix](validation-exports/python-concordance-points-matrix-20261110.csv),
[numerical report](validation-exports/python-concordance-points-20261110.json), and
[focused regression log](validation-exports/python-concordance-agreement-regressions-20261110.log).
The [qualification record](validation-exports/python-concordance-qualification-20261110.json)
separates the engine, full-suite, baseline, packaging and GUI evidence.

The first test attempt treated the two-pair fixtures as accepted inputs and failed
at the declared guard. Its log is retained; the test was corrected to require
refusal, leaving the oracle and engine's minimum unchanged.
An initial full-suite attempt overlapped a registry formatting edit and encountered
invalid JSON. That edit was corrected, and the suite was restarted against stable
sources. The failed-attempt log is retained in the qualification record.

## Frozen baseline and integration gate

The frozen **meddecide 1.1.2** agreement backend already uses population normalization
for its fallback CCC and calls DescTools for available inference. Its SHA-256 is
`18939ee1429eaaba05a0fed64b9f175f659d1c269b2eadf87b4ad0ac157a5d71`.
That public branch requires at least **10 paired observations**. The numerical
prototype's three-pair minimum is not a change to that released analysis. Native
integration must preserve the frozen public minimum unless a separate method
change is agreed.

The adapter now connects the engine to `pyagreement`, preserving the
ten-pair gate, two-measurement roles and unique independent case-ID checks. It
provides native point/decomposition tables and inactive-control rules. Remaining
gates include interval validation before offering inference, packaged execution
and fresh-engine GUI save/reopen/export. See the integration record for
method-switching, clearing/recovery and static-plot evidence.
CCC depends on case mix and does not replace examination of measurement differences.
Repeated-case inference, multirater pooling and clinical acceptance remain outside
this prototype. No new stable analysis identifier or baseline-completion claim is added.

## Reproduce

```sh
Rscript --vanilla tests/reference/concordance-points.R
PYTHONHOME=/Applications/jamovi.app/Contents/Resources \
/Applications/jamovi.app/Contents/MacOS/python -B -S tools/check-concordance-points.py
```

The R reference needs existing DescTools/jsonlite developer packages; the engine
uses NumPy and the existing runtime error type. It installs no dependencies.
