# Cross tables: supported Python core

`pycrosstable` is **Descriptives Py → Contingency tables → Cross tables (core)**.
Select one to twenty numeric or nominal/ordinal summary variables and a separate
categorical grouping variable. Native tables report overall and grouped summaries,
valid/missing counts, methods, p-values and adjusted p-values. This increment introduces
no plots or HTML tables; the R baseline is a table analysis.

## Baseline and supported scope

The authoritative registry preserves ClinicoPathDescriptives 1.0.82.03 source hashes at
commit `7162149586afc8992f1ba17e56887e2fbcb0835d`. This implements a subset of the
default gtsummary behavior with native jamovi presentation. The established R module is
unchanged. Other styles are not exposed as working choices.

| Feature | Core behavior |
|---|---|
| Overall and grouped continuous summaries | Mean/sample SD or median/type-7 Q1/Q3 |
| Categorical summaries | Counts, valid denominator and valid percentage; missing count separately |
| Numeric typing | Baseline: ≤6 distinct nonmissing values becomes categorical |
| Explicit numeric override | Advanced Settings can keep all numeric variables continuous |
| Missingness | Per-variable by default; optional complete-case cohort across selections |
| Continuous inference | Two-sided Wilcoxon for two groups; Kruskal–Wallis for more groups |
| Categorical inference | Uncorrected Pearson when all expected cells ≥5; otherwise request exact |
| Fisher exact | Two-sided 2×2 supported; larger exact tables unavailable |
| Multiplicity | None, Bonferroni, Holm, BH, BY over available variable-level p-values |
| Variable and group labels | Literal labels and declared factor order retained |
| Other engines/styles, SMDs and copy-ready interpretation | Omitted |
| Full baseline parity, repeated patients/weights | Omitted |

## Denominators and typing

Rows with a missing grouping value are always excluded, including from Overall.
With complete-case exclusion, a row is removed if any selected variable or the group
is missing. Otherwise, each variable uses its own valid values within each group.
The cohort table reports retained rows; the continuous table reports valid/missing n;
categorical percentages use valid variable values within that stratum. Missing rows
have a count and no percentage, so they are not presented as recorded categories.

Factor levels with zero counts remain in categorical summaries. Zero-margin levels are
removed for tests. Unused grouping levels are omitted from the native core, unlike
empty columns that the R formatter may retain. A separate Scope field distinguishes
Overall from a recorded group literally named Overall. True missing factor levels are
missing; literal text NA remains a recorded category. CSV import may interpret NA as
missing before analysis. A generated `(Missing)` label increments its suffix if the
recorded variable already uses that text.

The default low-distinct-numeric typing rule is evaluated after optional complete-case
exclusion, before removing missing-group rows, as in the frozen backend's typing step.
Typing is fixed per variable, not separately within each group. Numeric category labels
use a round-trip representation rather than rounded numbers. The optional typing table
states each applied rule. The explicit continuous override is an additional core option;
it does not change the default or silently recode nominal/ordinal variables.

## Inference and uncertainty

Changing continuous summary display does not change p-values. For two groups, the
Wilcoxon rank-sum test is exact when both valid sample sizes are below 50, including ties through the conditional
label-permutation rank distribution in R 4.6. Untied exact tests use SciPy; tied exact
tests use bounded dynamic programming over doubled midrank sums, with floating-point
counts and no sampled permutations. Otherwise the normal approximation corrects for
ties and uses the default continuity correction. Its statistic is U for the first retained group in
declared factor order. Kruskal–Wallis uses the usual tie correction and chi-square
reference. Tests compare distributions, not specifically means or medians.

The default categorical selector requests exact inference if any expected cell is
below 5. Forced Fisher also requests exact inference. Only 2×2 exact tests are available;
larger tables retain their descriptive summaries but have no p-value and a warning.
No Pearson fallback or simulated exact p-value is supplied. Small two-group all-constant samples have exact p=1 under R 4.6; constant normal-approximation
or Kruskal–Wallis cases, degenerate categorical data and variable-specific single-group
observations have explicit unavailable reasons.

Adjustment uses available variable-level tests, excluding unavailable p-values, matching
base R `p.adjust()` with its default family size. The stated family size can therefore
change when missingness changes test availability. This is not adjustment across all
categorical cells. No effect-size intervals, SMD balance classifications or clinical
conclusions are supplied. All inference assumes independent observations; repeated
patients, matched designs, survey designs and weights need other methods.

## Interface and lifecycle

The generator accepts only a declared List choice in column visibility, such as
`(cont:mean)`. Mean/SD and median/quartile columns switch natively; test-detail columns
are optional. All values remain numeric; hidden values are retained in the result
contract. The main variable supplier contains both roles. Missing roles use the usual
bridge guidance. Clearing/restoring roles must clear/repopulate every result and match
a fresh object. No generated header or YAML is hand-edited.

## Synthetic example and evidence

**Data Library → ClinicoPathPj → Grouped Cross Table Examples** contains 25 synthetic
profiles: 12 Control, 12 Intervention, and one missing-group profile. Age has two missing
values and Marker has one; Code illustrates the default numeric-category rule. Default
retention is 24 rows, with per-variable denominators. Complete-case exclusion leaves
21 rows. No patient data are included. The Data Library uses a GUI-saved typed `.omv`, with Age
and Code explicitly Continuous and a preconfigured mean/SD, per-variable, Holm example.
The raw CSV is retained for independent oracles; regenerate it using
`python3 data-raw/generate-cross-table-examples.py`. Integer CSV columns may otherwise
import as nominal, so the typed file avoids relying on import heuristics.

Focused fixtures compare independent counts, exact rank probabilities, Pearson's
definition, type-7 quantiles, missing labels and unavailable-test adjustment behavior.
Native R checks compare `mean`, `sd`, `quantile`, `wilcox.test`, `kruskal.test`,
`chisq.test`, `fisher.test` and `p.adjust`, plus supported outputs from the installed
gtsummary version. Numerical, compiler, native GUI, saved-file, platform and clinical
qualification remain separate grades. Dated acceptance evidence is appended when ready.


## 0.3.42 bounded qualification

323 full Python tests (43 focused analysis/generator), 275 native R assertions, compiler
and 22 extracted-package cases pass. Oracles include base R 4.6.0 and the installed
gtsummary 2.6.1 default tests. The initial R test exposed R 4.6's exact conditional
handling of ties; the corrected engine matches independent label enumeration, ordinary
tied fixtures, all-constant exact p=1, and a 49+49 boundary p≈7.85×10⁻²⁹, including a
relative-error comparison. The other initial test failure was an expected-vector names
attribute. Initial failed-oracle evidence is retained separately. Native R emits
environment Operation not permitted messages despite exit 0, zero failed assertions
and zero test warnings.

Installed the final archive through jamovi GUI on macOS arm64 / jamovi 28.13 and
restarted the application. The installed typed Data Library file opens a preconfigured
mean/SD, per-variable, Holm example with 24 retained rows and the correct continuous
Age method. Both saved states reopen in the fresh engine with their roles and options.
The complete-case state forces 21 → 24 → 21 recalculation and median → mean → median
column reversal; hidden columns clear correctly. The categorical method changes to
Fisher where complete-case expected counts become sparse.

Native HTML exports independently match all summary/count/percentage rows and Holm
p-values at native display precision. The raw CSV, curated typed example and both
saved analysis copies retain all 25 source profiles in their original order. The final
example/registry rebuild preserves 1,384 Python-area assets excluding registry evidence.
There is no plot in this table-analysis increment, so no plot-export claim is made.

See [evidence](validation-exports/python-cross-tables-0.3.42-checks.json),
[available-case native export](validation-exports/python-cross-tables-0.3.42-available.html),
[complete-case native export](validation-exports/python-cross-tables-0.3.42-complete.html),
and [saved example](validation-exports/python-cross-tables-0.3.42-complete.omv). Recheck
with `python3 tools/check-cross-table-artifacts.py`. Broader platform/accessibility,
full baseline parity and clinical/release review remain open.
