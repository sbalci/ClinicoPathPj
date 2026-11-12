# Paired binary tests — native partial integration, 2026-11-11

`pydecisioncompare` now has a literal Python SPEC and adapter, generator-owned
native tables, organized UI and a static Python-rendered proportion plot. The
registry owns its stable identifier and compact routing:
**MedDecide Py → Test comparisons → Paired Binary Tests**. It uses the
[independently checked common-cohort engine](python-paired-decision-core.md).

Version 0.3.66 is GUI-Sideloaded and has bounded local desktop acceptance on
macOS arm64 / jamovi 28.17.0. Source, built-library, installed-native and GUI
evidence are recorded separately below. The registry now has
30 partial targets, 31 planned targets, 15 retained utilities and no full-parity
releases. Existing R analyses, other module namespaces and utility entries are
unchanged.

## User interface and defaults

| Section | Controls and meaning |
|---|---|
| Data roles | Reference and two required tests, optional Test 3; explicit positive and negative level selectors beside every role in the first supplier. Unused selectors are disabled. |
| Analysis and Model | Reference interpretation, visible independent-case/common-cohort assumptions, explicit outside-pair exclusion, statistical comparisons and McNemar method. |
| Uncertainty and Validation | Per-test exact intervals and confidence level. These are binomial intervals for each proportion, not paired-difference intervals. |
| Results and Interpretation | Optional discordance counts and retained source rows. |
| Plots and Interaction | Optional static per-test sensitivity/positive agreement, specificity/negative agreement and accuracy/overall agreement points; enabled per-test intervals are drawn. |
| Advanced Settings | Optional Python console diagnostics. |

The frozen baseline defaults are preserved for the supported selectors:
reference interpretation **not specified**, outside-pair exclusion **off**,
statistical comparisons **off**, per-test intervals **off**, plot **off**, and
McNemar **mid-p**. Added confidence defaults to 95%, with an 80–99% range. The
asymptotic alternative has no continuity correction. The source-only exact
conditional method is not offered as a public selector.

All chosen tests use one common complete determinate cohort. This deliberately
narrower policy differs from the R baseline's per-test available cohorts and
pair-specific comparisons. Adding Test 3 can change all estimates. Genuine
missing factor levels are missing; the literal label `NA` remains a label.
Observed labels outside the selected positive/negative pair cause an error
unless exclusion is explicitly enabled; unused labels are not pooled as negative.
Rows must represent independent cases, with tests paired within each row.

## Results and interpretation

Native tables show the common cohort, selected mappings and source exclusions,
per-test classification counts, proportions with explicit numerators and
denominators, and optional paired differences/tests, discordance cells and
retained original row identifiers. With statistical comparisons enabled:

- Accuracy/overall agreement compares correctness against the reference, rather
  than raw positivity. Its case-mix dependence is stated.
- Sensitivity/positive agreement compares positive calls in reference-positive
  cases; specificity/negative agreement compares negative calls in the other class.
- Holm adjustment applies only across informative accuracy comparisons. The
  conditional-class tests are explicitly unadjusted.
- No discordance yields conventional p=1 and an explicit status, not equivalence.
  Absent classes have undefined estimates/tests. Few discordant pairs produce an
  information/approximation warning.

Consensus and comparative-method modes use agreement terminology and state that
the comparator does not establish disease status. Their conditional quantities
are not symmetric specific agreement. Unspecified interpretation retains the
frozen diagnostic terminology but displays a warning. No disease prevalence or
population-risk adjustment is introduced.

**Paired-difference intervals are not exposed.** The
[Newcombe prototype](python-paired-difference-intervals.md) remains source-only
after six coverage-screen failures. The adapter explicitly disables it even if
an undeclared extra option is supplied. Paired-difference interval columns and
controls do not exist. Per-test Clopper–Pearson intervals remain separate.

## Synthetic example

Data Library → ClinicoPathPj → **Paired Binary Test Examples** contains 20
synthetic rows. Choose Reference, Test_A, Test_B and optional Test_C, with each
positive level `Positive` and negative level `Negative`. For all three tests,
enable explicit outside-pair exclusion: 16 cases remain, with three missing-role
rows and one determinate outside-pair row excluded. That retained cohort matches
the independent hand fixture. With only the first two tests, 17 cases remain.
The extra label in Test_C must not silently become a negative result.

The example is regenerated by `data-raw/generate-python-paired-examples.py` from
the frozen synthetic fixture, without calling the target analysis engine.

## Feature boundary and next gates

| Feature | Current boundary |
|---|---|
| Explicit levels, common cohort, sample proportions | Python engine and native adapter implemented. |
| McNemar mid-p/asymptotic and informative-pair Holm | Implemented; independent numerical fixtures retained. |
| Exact per-test binomial intervals | Implemented, optional, with visible denominators. |
| Paired-difference intervals | Omitted from native analysis; source research only. |
| Static proportion plot | Implemented through the existing Python image contract. |
| Per-test available/pair-specific cohorts | Omitted; common cohort is explicit. |
| Cochran Q, OPA/non-inferiority, stratification | Omitted. |
| Supplied prevalence, ratios, radar/heatmap, full reports | Omitted. |
| Native installed GUI | Bounded 0.3.66 macOS arm64 acceptance below; no full-parity claim. |
| Broader platforms and clinical review | Pending. |

The baseline manifest and source hashes remain unchanged. Compiler preparation
passes. All **565 Python regression tests** pass. Eight focused adapter tests cover all 13 independently frozen datasets
under both public McNemar methods and three confidence levels, comparator labels,
missing/excluded rows, row IDs, optional outputs, unsupported methods and interval
omission. Native tests additionally exercise valid → incomplete/invalid → valid,
optional third-test transitions, genuine missing levels and rendering from
serialized state after clearing analysis data. Isolated-source, built-library and GUI-installed namespace
runs each pass **960 assertions with zero failures, warnings, errors or skips**. Native
numerical assertions use the prespecified `1e-12` absolute tolerance; an initial
relative-tolerance test near zero was corrected without changing calculations.

The actual JMO extracted runtime passes **1,984 checks across 13 independent
fixtures and 26 public-method configurations**, with maximum absolute difference
`4.813927034774679e-13`. Archive CRC, one namespace/analysis entry, eight compiled
level selectors, source-engine bytes, synthetic example and absent public
paired-interval controls are checked by `tools/check-paired-package.py`.
Test-only R references are not bundled.

Final standard archive: `ClinicoPathPj_0.3.66.jmo` (22,965,769 bytes), SHA-256
`82a4f42b10a26dbd76d3427258e1b2ca4c18c9effd556b49dcc12ef891c74fc8`.
The final archive's analysis/shared-engine bytes and registry implementation
contract match source. The source registry's GUI/platform evidence fields were
advanced after qualification; the immutable JMO retains their pre-installation
values. `tools/check-paired-package.py` allows only these two named evidence
fields to differ and rejects any implementation-contract difference. Deliberate
method-contract and full-parity mutations in temporary archives are rejected.
The qualified 0.3.65 rollback is preserved byte-for-byte in `packages/archive/`.
The package is available locally; it has not been committed, published or submitted.

The synthetic example static image was rendered natively and visually inspected:
unequal intervals and all nine test/metric labels are visible. It is available as
[the native plot example](validation-exports/python-paired-native-example-20261111.png).
This is a source-rendered image, not a desktop export or saved-file artifact.

## Local desktop qualification — 0.3.66

The earlier computer-use service startup failure was resolved in the follow-up.
Install through **Modules → Manage installed → Sideload** succeeded; the installed
modules panel shows 0.3.66. All **1,444 installed files** match the JMO bytes.
A fresh engine was used after installation, and another engine reopened the
saved example. No installation through Finder was used.

Observed desktop checks:

- One menu entry under the intended group; visible level pairs and common-cohort
  assumptions. Empty-role selectors disable; assigned-role selectors enable.
  Frozen comparison/interval/plot defaults remain off.
- Two-test cohort retains 17 rows. Adding Test 3 requires explicit exclusion of
  its outside-pair result; the resulting cohort is 16, with three missing rows
  and one outside-pair row excluded. The invalid state clears prior results.
- With statistical comparisons, per-test intervals, discordance/source-row
  tables and plot enabled, clearing Test 2's negative level clears computed
  tables and the cached PNG. Restoring it recovers the results.
- Removing Test 3 disables its level selectors and recalculates to 17 cases;
  restoring it restores the chosen levels and 16-case cohort.
- Save As works for valid, incomplete and recovered states. A second fresh
  engine reopens the recovered file with the plot visible. Per-test intervals
  were switched off, recalculated, restored and saved as a separate reopened file.
- Native HTML results and PNG image exports succeed after reopening.

Saved fixtures: [valid](validation-exports/python-paired-0.3.66-valid.omv),
[incomplete](validation-exports/python-paired-0.3.66-incomplete.omv),
[recovered](validation-exports/python-paired-0.3.66-recovered.omv), and
[fresh-engine recalculated](validation-exports/python-paired-0.3.66-reopened.omv).
Exports: [native HTML](validation-exports/python-paired-0.3.66-recovered.html) and
[native PNG](validation-exports/python-paired-0.3.66-native-plot.png).

`tools/check-paired-artifacts.py` checks all seven native tables against the
independent R hand fixture, original row IDs, confidence limits, raw/adjusted
p-values and discordance cells at displayed precision. Equivalent-input saved
and recalculated tables and cached plot pixels agree; HTML uses the same
1118×718 plot pixels. The 1400×900 native PNG is byte-identical to the same-size
source-rendered reference. All saved states preserve dataset bytes/metadata.
The incomplete file contains no computed rows or cached PNG. Four deliberate
artifact corruptions (cohort count, estimate, paired p-value and missing image)
are rejected. The checker normalizes export whitespace before comparing p-values.

This establishes bounded local acceptance of the partial core. Full baseline
parity, paired-difference intervals, clinical review, Windows/Linux/other Mac
architectures and additional export formats remain open. No library submission
or complete-migration claim is made. Next specify the independent/paired
estimation contracts for `pyjjbetweenstats` and `pyjjwithinstats`.
