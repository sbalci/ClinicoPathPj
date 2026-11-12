# Independent and paired estimation — source contract

Started 2026-11-11; validation and roadmap update 2026-11-12.

`inst/python/cpj_estimation.py` provides the bounded raw-mean calculation core for
`pyjjbetweenstats` and `pyjjwithinstats`. They now have [native partial adapters](python-estimation-native.md), organized
interfaces, tables and a raw-difference plot; their registry status is **partial**.
These native adapters are packaged and locally desktop-qualified in **ClinicoPathPj 0.3.67**;
see the native evidence record for bounded macOS acceptance. The inventory
is now 32 partial targets, 29 planned targets and 15 retained utilities.

## Frozen baseline and first scope

The frozen `jjstatsplot` 1.0.82.03 source is commit
`4c3cbe8de39d6259ee61d5fde28704f45e9cc8ed`. The archived backend SHA-256 values are:

- `jjbetweenstats`: `0c93805b31adac65d59d29f54cbebdf9b374c34f4fd140e0c8283ac7d98bd9f0`
- `jjwithinstats`: `a32fecc07edce644ed57f305181f5e39b255fd0cf407f706a6cf539fbe7cafc2`

`tools/check-estimation-core.py` verifies all eight archived backend/YAML hashes
against the registry. Mutable sibling checkouts are not resnapshotted.
The baseline defaults to parametric statistics and 95% confidence; independent
comparisons default to unequal variances (`varequal=false`). Within-subject data
are wide, one row per subject, with at least three complete subjects required.
The first calculation scope preserves those choices, with an explicit
**first minus second** contrast. This is a narrower foundation than either full
plotting analysis, whose statistical subtitles include standardized effects.

| Core | Inputs | Computation and unit |
|---|---|---|
| `between_estimation` | One numeric outcome, factor, explicit distinct first/second labels; optional subject IDs | Two independent samples; Welch t by default, pooled Student t only with explicit equal variances. At least two complete observations per group. |
| `within_estimation` | Two aligned numeric measurement columns; optional subject IDs | Paired t on source-row differences; at least three complete independent subjects. The two columns are never independently sorted. |

Both return raw mean difference, standard error, t, degrees of freedom,
two-sided p-value and a t-based confidence interval; per-role N, mean and sample
SD; missingness audit; and retained original zero-based source positions.
The versioned result is a plain JSON-compatible dictionary (`schema_version=1`).
The confidence range is 0.50–0.999, default 0.95.

For Welch, SE is `sqrt(s1²/n1+s2²/n2)` and degrees of freedom use the
Satterthwaite formula with normalized variance contributions before squaring.
Student uses the sample-size-weighted pooled variance and `n1+n2-2` degrees of
freedom. Paired inference uses the sample SD of within-row differences and
`n-1` degrees of freedom. Independent rows and the chosen t-model assumptions
remain required; no normality pretest selects or switches methods.

## Cohorts, labels and identifiers

- NaN/None are missing. Independent outcomes require a nonmissing group;
  paired columns use one common complete-pair cohort. Missing-role counts can
  overlap, but excluded-row totals use the union.
- Unused factor levels do not create empty groups. Selected labels, including
  the literal `NA` or Unicode text, are returned verbatim. A third group with
  complete outcome data is rejected, rather than silently excluded.
- Infinity, complex/boolean/string measurements, masked arrays, matrices,
  malformed factor codes and unsupported derived numeric ranges are errors.
  The source core is bounded to 100,000 rows.
- Optional subject IDs must be aligned strings/None. Every retained ID must be
  known and unique; excluded-row IDs do not change the inferential cohort.
  Leading-zero labels such as `001`, `01` and `1` stay distinct. IDs neither
  merge rows nor establish that the observations are independent.

Zero SE or R's scale-dependent essentially-constant guard leaves the raw means
and difference available, with **all inferential fields null** and
`status=degenerate`. It does not produce infinite significance or a zero-width
interval. At the limit of floating-point resolution even descriptive mean
contrasts can lose information; no equivalence conclusion is supported.
Nonconstant variance/SE underflow is reported as an unsupported numeric range,
not relabelled as constant data. No automatic alternative test is used.

## Independent numerical evidence

`tests/reference/estimation-core.R` freezes base-R `stats::t.test` results and
explicit source-row indexing before the target Python engine. The final fixture
contains **32 datasets and 255 method/confidence configurations**, covering
confidence levels 0.50, 0.80, 0.95, 0.99 and 0.999; unequal N/variance, one constant
sample, constant/identical differences, two-observation groups, the public
three-subject paired minimum, missing alignment, unused/Unicode/literal-NA
labels, normal/skewed data, offsets and extreme scales.

Two numerical limitations of the initial raw-R reference were identified:

1. Welch's fourth-power denominator under/overflows at scales of `1e-100` and
   `1e100`. The independent R oracle now divides both samples by a common scale
   below `1e-50` or above `1e50`, then restores units to SE/CI endpoints. The
   scale-invariant t, df and p come from base R.
2. Raw R `sd()` loses precision near `1e15` with `0.125` increments. Summary SD is
   independently evaluated after translation by the first value. A separate
   literal four-value fixture checks the exact variance `5/192`. The Python
   core also centers summary moments; inference remains guarded at that offset.

The initial raw reference is preserved locally in the ignored validation directory;
no target Python values generate R targets. The final reference replays
byte-for-byte, SHA-256:
`f38a02fc06d2c65a08a9d7e8003f6a6302be2201c1f7edfb17477339138cf8aa`.

The source checker passes **20,380 comparisons** with maximum relative
difference `4.9478241112140007e-14`; the prespecified relative tolerance is
`1e-11`, p-value absolute tolerance `1e-12`, and zero targets require exact zero.
Seventeen focused tests cover the oracle plus invalid inputs, subject-ID policy,
contrast reversal, paired covariance, missing alignment, degeneracy, scale
invariance and numeric-range guards. Five temporary in-memory mutations are caught by the frozen numerical oracle:
substituting Student for Welch, reversing the independent contrast, using population
SD, using an independent SE for paired data, and independently sorting paired
columns. The repository implementation remains unchanged by these probes.
All **582 Python regression tests** pass. Generator and registry-status freshness
checks pass; the independently replayed R fixture remains byte-identical. Numerical
agreement does not qualify native/UI, clinical interpretation or an installed analysis.

Reproduce with bundled Python `tools/check-estimation-core.py`,
`tests/python/test_estimation.py`, and base R `tests/reference/estimation-core.R`.
Generated validation JSON/logs remain local and ignored.

## Remaining implementation gates

| Feature | Current boundary |
|---|---|
| Two-group Welch/Student and two-measurement paired raw estimates | Independently checked engine and native partial adapters. |
| Standardized effects and their intervals | Separate pooled/difference-SD source contract and independent oracles; native integration and unequal-variance effects remain pending. |
| More than two groups/measurements, ANOVA and repeated-measures corrections | Pending. |
| Rank-based, robust and Bayesian methods | Pending independent method contracts and reviewed dependencies. |
| Split-by/multiple outcomes and multiplicity | Pending; source core is one endpoint/one contrast. |
| Box/violin geometry, subject paths, statistical annotations, interaction | Pending; no plot-parity claim. |
| Native SPEC, organized UI and lifecycle | Implemented; see the separate native evidence record. |
| Packaging and GUI save/reopen/export | 0.3.67 bounded macOS arm64 qualification passes; see native record. |
| Clinical review and broader platform qualification | Pending. |

The adapters use the preallocated `py…` identifiers with visible
contrast/cohort/inferential-unit controls, native tables and static figures.
The next [standardized-effect source increment](python-standardized-effects.md)
explicitly separates pooled and difference-SD estimands, point corrections and
population-delta intervals. Its native integration remains pending. Preserve the
frozen supported defaults and expose no unvalidated rank/robust/Bayesian branch. Existing `pywelch`, R analyses,
utility entries and the qualified installed package remain unchanged.
