# ClinicoPathPj 0.2.0 validation — 2026-10-25

## Result

The six implemented Python cores passed their independent numerical checks, native GUI use,
`.omv` cold-reopen and native PDF export. They ship in the existing ClinicoPathPj module.
This is an experimental core implementation with the limitations documented in
[methods and feature matrix](python-core-analyses.md).

| Evidence | Result |
|---|---|
| Full Python suite, jamovi's bundled Python | **152 tests passed**, no failures |
| Independent new-core R tests | **98 assertions passed**, no failures/warnings/skips |
| Full R suite | **411 assertions passed; 5 errors**, all in existing bridge process-lifecycle tests |
| Metadata regression after adding the example | **5 assertions passed**, no failures/warnings/skips |
| Generator freshness and existing dotplot event tests | Passed |
| Compiler and package build | Passed; standard ClinicoPathPj 0.2.0 archive |
| Final extracted-package smoke | All six analyses returned successful native table results; plot payloads present where applicable |
| Native GUI installation | Passed; one ClinicoPathPj 0.2.0 entry, all six new menu items |
| Native GUI calculations | All six ran on synthetic inputs without analysis errors |
| Native `.omv` save and cold-reopen | Passed; six analyses and all three native plots restored in a fresh app session |
| Native PDF export | Passed; 12 pages, all analysis sections, exactly 3 embedded plot image objects |
| Data Library | Verified Python Core Examples under ClinicoPathPj; opened the packaged example |

The five full-suite errors are `Operation not permitted` from `ps::ps_pids()` / recursive
child-process enumeration in existing `test-bridge.R` lifecycle tests (lines 29, 37, 46, 54 and 75).
The restricted environment therefore does **not** give a full-green R suite or prove those
process-cleanup assertions. No such error occurred in the 98 new-core assertions.

## Independent numerical references

- Diagnostic proportions and exact intervals: base R `binom.test()`; interior accuracy and
  likelihood-ratio/DOR/Youden values and proportion intervals: `epiR::epi.tests(method='exact')`.
  Row-data and count interfaces matched for the same counts; zero margins, infinite/undefined
  ratios and supplied-prevalence separation were checked separately.
- Sequential rules: independent enumeration of all test-result combinations within both disease
  groups, including workload and testing costs. Extreme probabilities were checked without
  inventing undefined predictive values.
- Contingency analysis: base R `chisq.test(correct=FALSE)` statistics, expected counts and
  standardized residuals; `fisher.test()` on sparse 2x2 sub-tables; `p.adjust()` for Bonferroni,
  Holm and BH across the defined families. Degenerate comparisons and the 500-pair cap were checked.
- Benford: independently specified leading-digit counts for one through three digits, base R
  chi-square calculations, and `benford.analysis` digit frequencies/MAD. Ordinary decimal
  boundaries, subnormal magnitudes and excluded nonpositive/missing values were checked.
- Decision curves: independent brute-force threshold classification and `dcurves::dca()` on
  the same complete-case cohort. Tests include exact threshold ties, missingness differing by
  model, invalid probabilities and a model name colliding with a reference-strategy label.
- Native plots: restored plot state rendered without source data. The new bar renderer retained
  all digit categories and followed jamovi's global palette.

## GUI example and artifacts

The GUI workbook uses 36 synthetic observations and eight columns. It contains these analyses:
`pydecisioncalculator`, `pysequentialtests`, `pybenford`, `pydecision`, `pychisqposttest` and
`pydecisioncurve`. The contingency example was checked both unweighted and with Frequency
(total frequency 106); the decision curves compare RiskA and RiskB on 36 common complete cases.

- [Native workbook](../data/python_core_examples.omv)
- [Synthetic CSV](../data/python_core_examples.csv)
- [Native 12-page PDF export](validation-exports/python_core_examples.pdf)
- [Sequential-testing plot](validation-exports/pysequentialtests.png)
- [Benford plot](validation-exports/pybenford.png)
- [Decision-curve plot](validation-exports/pydecisioncurve.png)
- [Final archive smoke results](validation-exports/package-smoke.json)

The workbook passed ZIP integrity checking and an independent `jmvReadWrite::read_omv()` read
confirmed 36 rows and the eight expected column names. The final installed Python helper,
runtime and example archive were compared byte-for-byte with the distributed package.

The module is `ClinicoPathPj`; no alternate module namespace was created. Previous root packages
are preserved as ZIP backups under `build/previous-artifacts/`. Final package:
`ClinicoPathPj_0.2.0.jmo`; SHA-256:
`2f625fa8d9fd455f47a8607123ab91600e6bdbda49c6cfb00ff75c61ccade315`.

## Reproduce

1. `python3 tools/generate-core-examples.py` regenerates the synthetic CSV.
2. `Rscript --vanilla tools/build.R --build-only` builds without installing. It reads the installed
   app's version from its plist for the compiler's explicit version argument. This bypasses the
   unreliable app-version probe in this shell; it does not stand in for the separate GUI evidence.
3. `tools/check.sh` runs Python and installed-module R tests in the engine-like environment;
   expect the described process-enumeration restrictions when using the same restricted shell.
4. Run `tools/check-core-package.py` with jamovi's bundled Python to inspect and execute the
   archive itself; it checks all six analyses and the bundled `.omv`.
5. Open Data Library > ClinicoPathPj > Python Core Examples in a fresh jamovi session, rerun,
   save, close and reopen. Export to PDF to check native image persistence.

Numerical agreement and GUI lifecycle tests do not establish population validity, independent
external validation, repeated-patient inference or clinical decision suitability. The omitted
advanced features are intentional and are listed in the methods document.
