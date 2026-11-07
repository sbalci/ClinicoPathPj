# Explicit numeric dates — 0.3.48

`pydatetimeconverter` and `pytimeinterval` remain under **Survival Py → Data preparation**.
The converter gains **Packed YYYYMMDD (eight digits)**; intervals now expose that
format and the converter's existing Excel1900/1904 and Unix formats. YMD in UTC
and standardized interval units remain the defaults. Existing identifiers, options
and output names are retained.

| Input | Explicit meaning |
|---|---|
| Excel1900 | Origin 1899-12-30; day fractions round to whole seconds, ties to even |
| Excel1904 | Origin 1904-01-01; same rounding; 1,462-day origin difference |
| Unix | Seconds since 1970-01-01 UTC; fractional/negative seconds supported |
| Packed YYYYMMDD | Finite integer numeric value or exactly eight ASCII text digits; calendar validated |

Packed `20240229` is valid; `20230229`, `20240230`, fractions and six-digit years
are invalid. Numeric `20240229.0` is integral and valid; text `20240229.0` is not
eight digits. Eight-digit text supports leading-zero years; numeric inputs with
fewer than eight digits are rejected. Outer whitespace is trimmed. There is no
automatic origin, format or century choice. Native R Date/POSIX classes and named
timezones remain unsupported.

Both interval roles use the same selected encoding and origin. The per-column
80% parse guard, exclusion order, follow-up landmark and saved-row contracts remain
unchanged. Calendar units are computed after conversion to UTC. Excel1900 serials
below 61 carry an explicit warning: the frozen origin does not reproduce Excel's
fictitious 29 February 1900. Interval saved-column descriptions state the format,
unit, basis and landmark; review these before downstream use.

The **Numeric Date Encoding Examples** dataset has five complete equivalent pairs
and one missing start. Select matching Start/End columns, the corresponding format
and days: n=5 and total=456. The separate Malformed packed end column contains
`20240230`: with Start packed, it yields n=4, one invalid pair and one missing pair,
total=91 days. It meets the exact 80% nonmissing end-column parse boundary. All
records are synthetic.

## Qualification

- 25 focused Python tests pass, including existing datetime/interval regressions,
  450 packed Gregorian dates, explicit integer/text rules, origins/fractions,
  parse-boundary failures, source IDs and named saved output.
- Full Python: **370 tests pass**, 344.956 seconds. Compiler/build, generator and registry
  freshness pass; archive integrity and **26 packaged-runtime analysis cases** pass,
  including additional packed converter and interval requests.
- Native base-R/lifecycle: **261 assertions pass** (33 new numeric-date, 163 converter,
  65 interval assertions), no testthat failures/errors/warnings/skips. The sandbox
  separately emits `Operation not permitted` subprocess messages; they are not counted
  as numerical failures.
- Native jamovi 28.13 macOS arm64: Modules → Sideload, full restart and installed
  manifest/R database/registry/date-engine archive-byte checks pass. Packed pairs yield
  n=5/456 days; malformed end n=4/91 days; incompatible YMD clears all saved intervals;
  Excel pairs recover n=5/456 days. The packed converter reports 5 parsed/1 invalid.
  Named numeric and nominal saved outputs retain original source positions.
- Combined native HTML export and fresh-engine OMV reopening/recalculation pass.
  `tools/check-numeric-date-artifacts.py` independently reads all five saved states and
  HTML without importing the date/interval engines; it verifies source data, quality,
  summaries, epoch arithmetic, labels and output alignment.
- Static plot export is not applicable to these preparation analyses.
- No full native inventory, broader platform, full parity or clinical review claim.

The original registry baseline hashes remain intact. This extension adds explicit
format contracts; it does not enable permissive automatic/two-digit parsing or
infer follow-up origin, independent censoring or event-time validity.

Reproduce with the bundled-Python test discovery command in `tools/check.sh`,
`tests/testthat/test-numeric-dates-python.R`, `test-datetime-python.R` and
`test-intervals-python.R` against the built library, `tools/check-core-package.py`,
`tools/generate.py --check`, `tools/migration-status.py --check` and
`tools/check-numeric-date-artifacts.py`. The qualification record is
`docs/validation-exports/python-numeric-dates-0.3.48-checks.json`.
