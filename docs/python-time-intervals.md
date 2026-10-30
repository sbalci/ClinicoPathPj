# UTC elapsed and calendar-anniversary intervals

`pytimeinterval` is under **Survival Py → Data preparation → Time intervals (UTC core)**.
This partial Python port freezes umbrella `timeinterval` 1.0.81.01 at commit
`9fae7c5c7af84e65dfff9262d3bb2a031618753e`; source hashes remain in the registry.
The original R analysis is unchanged. NumPy/SciPy are bundled; no network or package
installation is needed.

| Feature | Status |
|---|---|
| Explicit four-digit text dates and UTC clocks | Implemented using the datetime core |
| Days / weeks / fixed months / fixed years | Implemented: 1 / 7 / 30.4375 / 365.25 days |
| Optional negative and extreme exclusions | Implemented with raw and removed counts |
| Follow-up landmark | Retain raw interval ≥ landmark, then subtract landmark |
| Summary and arithmetic-mean confidence interval | Native tables; sample SD and Student t |
| Raw date-quality and source preview | Optional quality tables; bounded preview |
| Saved interval | Continuous, full supplied-row alignment, named Calculated interval |
| Calendar-aware months/years | Implemented in 0.3.47; corrected R feature reference below |
| Auto parsing, numeric packed/epoch dates, two-digit years | Pending; rejected rather than guessed |
| System/named timezones, DST and R Date/POSIX input | Pending; UTC text only |
| Baseline clinical plausibility bands and glossary | Omitted in this core |
| Full parity, broader platforms and clinical/release review | Open |

Under the standardized default, months and years are fixed durations. For example, January 31
to February 29, 2024 is 29 days, or 29/30.4375 standardized months. Both source columns
must parse at least 80% of their nonmissing values; missing and invalid pairs stay
missing in saved output. The visible initial format is YMD in UTC, differing from
the baseline's automatic parsing default. Review the original/parsed preview before
using ambiguous day/month orders. Numeric encodings are not inferred.

Negative raw intervals cause an error by default. Explicit exclusion is required;
they never subtract from summed record-time. Potential extremes use the **raw**
type-7 99th percentile multiplied by the selected factor (default 2), before either
exclusions or landmark. Only a positive quantile enables this rule; strict exceedance
is required. Small samples can make this rule unable to flag any interval, which is
disclosed. Negative, extreme and below-landmark exclusions occur in that order.

The optional landmark defaults to 6 selected units. Equality is retained and becomes
zero after subtraction. This requires observed follow-up length, with no event input:
it cannot establish event-free survival at the landmark. Rows are records, not deduplicated
patients. Summed record-time is person-time only for appropriate nonoverlapping records.
No incidence or censoring-adjusted survival estimate is calculated.

The mean CI defaults to 95%, using n−1 degrees of freedom and sample SD. The lower
bound is intersected with zero; the raw bound and clipping flag remain visible.
This assumes independent observations and a suitable t approximation. Singleton
SD/CI and empty-cohort summaries are unavailable. Constant intervals produce a point
CI with a warning. These intervals do not quantify survival uncertainty.

The synthetic **UTC Interval Examples** dataset has ten complete intervals and two
missing pairs. Choose Start date / End date, YMD and days: total 871, n=10. A 6-day
landmark retains seven intervals and yields total 826. End with reversal introduces
one negative interval; exclude negatives to get n=9 and total 861 (without landmark).
No real patient data are included.

## Standardized 0.3.46 evidence and remaining gates

- Focused Python: eight tests pass, including analytic t(1) CI, independent date fixtures,
  type-7 thresholds, landmark ties, errors and runtime saved-row identities.
- Native base-R numerical checks and R6 lifecycle: **45 assertions pass**, no testthat
  failures, errors, warnings or skips. Initial harness failures were corrected to expect
  jamovi's rejection exception and inspect `rowCount` for an emptied table; no backend
  change was needed. Host subprocess checks emit `Operation not permitted` messages
  under the sandbox; these are separate from numerical assertion results.
- Generator/status freshness and compiler/build: pass. The built archive contains one
  ClinicoPathPj namespace; **26 packaged-runtime cases pass**, including interval output
  naming, source IDs and values. Installed manifest/R database/registry/interval helper
  bytes match the archive.
- Full Python regression suite: **362 tests pass** in 591.084 seconds for 0.3.46.
- Native jamovi 28.13 macOS arm64: **Sideload** update and full application restart pass.
  Baseline days: n=10/total=871; landmark 6: n=7/total=826; reversed interval rejects and
  clears every saved value; explicit negative exclusion recovers n=9/total=861.
  Four saved OMV states retain the source data and correctly aligned named output.
  Native HTML export includes the expected summary and all 12 preview rows. Fresh-engine
  reopening restores the excluded state, and toggling report output recalculates it.
  `tools/check-interval-artifacts.py` independently checks source data, saved values and HTML.
- Static plot export: not applicable; this preparation core has no plot.
- Platform qualification beyond macOS arm64, full baseline parity and clinical review: pending.

The prior full native inventory run was 3852 passing assertions for 0.3.44. It is
historical evidence, not a full 0.3.46 native qualification claim.

Reproduce from the repository with `tools/generate.py --check`,
`tools/migration-status.py --check`, the bundled-Python unittest discovery command
in `tools/check.sh`, the focused `tests/testthat/test-intervals-python.R` against the
built library, `tools/check-core-package.py` and `tools/check-interval-artifacts.py`.
Counts, limits and archive/source/artifact hashes are recorded in
[the qualification record](validation-exports/python-interval-0.3.46-checks.json).

## Calendar anniversaries — 0.3.47

The **Time basis** selector now offers Standardized elapsed units (the unchanged
default) and Calendar rollback anniversaries. Days and weeks remain elapsed units
under both bases. Calendar months count whole monthly anniversaries from the
original start date, rolling invalid days back to month end and preserving the
clock. The remainder is divided by the actual span to the next anniversary in
the interval's direction. Calendar years are these months divided by 12.

Examples starting 31 January 2024 at the same UTC clock:
28 February = 28/29 months; 29 February = 1 month; 1 March = 1 + 1/31 months.
The direction matters: swapping dates need not negate a fractional calendar result.
Use standardized durations when a constant unit of exposure is required. The
landmark and extreme-flag rules use the selected unit and basis; changing basis
can therefore change retention. Column metadata and the native scope identify
the basis and landmark used. No local display interaction or hidden refit is added.

The feature reference is the **recent corrected R method** at umbrella commit
`381df71e98e4fb460d44e5a6cc439a04289acfdd`, frozen in
`tests/fixtures/timeinterval-calendar-reference.R`. Full-source SHA256 is
`991bc0053ccbfb4a52132ffd27ae462969b34f783a3bb8c08ad8882f275c14e2`.
The original migration baseline remains recorded unchanged. Its calendar remainder
divisor used days in the rollback month: for 31 January → 1 March 2024 it gives
1 + 1/29, whereas the corrected adjacent-anniversary method gives 1 + 1/31. This
new option intentionally follows the corrected method; it is not claimed to match
the original formula. Existing 0.3.46 saved analyses omit `time_basis` and continue
with the standardized default.

Evidence: ten focused Python tests pass, with 408 frozen R date-pair references
(months and years), analytic month-end expectations, year 0001/9999 bounds and
full supplied-row saved output. The R fixture generator fixes its sampling indices
through a local seed and records lubridate's version; the resulting JSON fixture
is committed as the oracle input. The 65 focused native R assertions, 364-test Python regression run, compiler and
26 packaged-runtime cases pass. Desktop macOS arm64 jamovi 28.13 Sideload/restart,
standardized/calendar comparison, named aligned saved values, native HTML and fresh-engine
calendar reopen/rerun pass. The previous 0.3.46 file defaults to standardized and reruns
without changing source/saved values; its compatibility result is saved separately.
A final label-only rebuild removes fixed day lengths from the unit selector; the
selected basis and scope supply those definitions. Numerical-engine hashes are checked
unchanged across that rebuild. No new full native
inventory, platform or clinical qualification is claimed.

The **Calendar Anniversary Examples** dataset contains five complete synthetic
month-end pairs and one missing end date. Select Start date / End date, months,
then switch the time basis and inspect raw/used values and the saved column.

Reproduce additional checks with `data-raw/generate-calendar-reference.R`, the
focused Python/R interval tests, `tools/check-core-package.py` and
`tools/check-calendar-artifacts.py`. The latter reads native OMV/HTML without importing
the interval engine. This extension's machine-readable qualification record is
`docs/validation-exports/python-calendar-0.3.47-checks.json`.

The final label-only build passes 42 interval/generator checks. The numerical
engine hash matches the one used by the 364-test full run and 65 native assertions.
Final installed manifest, R database, registry and interval-engine bytes match the
archive; fresh restart/reopen shows **Months** with **Calendar rollback anniversaries**.
The full 0.3.47 native inventory was not rerun; other platforms and clinical review
remain unqualified.
