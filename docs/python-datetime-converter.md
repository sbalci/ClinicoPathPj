# Explicit-format UTC datetime conversion

`pydatetimeconverter` lives in **Survival Py → Data preparation → Datetime converter
(UTC core)**. It is a partial port of the frozen jsurvival 1.1.1 source at commit
`283a8275e3dd6704f6bba2164215442d3d293b8c`; the original R analysis is unchanged.
All conversion and component calculations run in bundled Python without new packages.

## Interpretation and feature boundary

| Feature | UTC core |
|---|---|
| Explicit YMD, DMY, MDY, YDM, MYD, DYM dates | Implemented, four-digit years |
| YMD/DMY/MDY hours-minutes or hours-minutes-seconds | Implemented; seconds may have up to six decimal places |
| Excel 1900 / Excel 1904 / Unix numeric encodings | Implemented, selected explicitly |
| Quality accounting and original/converted preview | Native tables; failed and missing rows remain distinct |
| Calendar components and numeric/text saved outputs | Implemented with original row identities |
| Automatic format/epoch detection | Pending |
| System/named timezones, timezone conversion and DST | Pending; UTC is fixed and visible |
| Two-digit-year/past-date policy | Pending; two-digit years are rejected |
| Native R Date/POSIX classes | Pending; convert these explicitly to text or numeric first |
| Locale-dependent parsing and glossary | Pending; extracted names use fixed English labels |
| Full baseline parity, broader platforms/accessibility and clinical/release review | Open |

This explicit-format subset starts at **YMD in UTC**, rather than exposing the original
analysis's `auto` and `system` defaults with incomplete implementations. The original
R defaults are preserved in their module. No day/month order or epoch is guessed in
this port. For ambiguous `01/02/2024`, DMY means 1 February and MDY means 2 January;
choosing the wrong format can produce a valid but wrong date. Review the preview.

Text dates require matching hyphen or slash separators. Time-bearing formats accept
a space or `T` before the clock and an optional terminal `Z`. Offsets, localized month
names, compact dates, two-digit years, leap seconds and invalid calendars are rejected;
invalid dates do not roll into another month. Date-only values mean midnight UTC.
Text/Unix conversion preserves microseconds within floating-point output precision.
Supported calendar bounds are years 0001–9999.

Excel conversions reproduce the frozen R arithmetic:

- 1900 system: UTC origin **1899-12-30**.
- 1904 system: UTC origin **1904-01-01**, 1,462 days later for the same serial.
- Day fractions are multiplied by 86,400 and rounded to whole seconds, ties to even.
- Early 1900 serials below 61 produce an explicit warning. The origin convention
  does not reproduce Excel's pre-March-1900 calendar, including its fictitious
  29 February 1900; serial 60 becomes 1900-02-28 under the frozen R convention.

Unix values are seconds from 1970-01-01 00:00:00 UTC, including negative/fractional
values. The converter does not infer whether a number is an Excel serial, Unix seconds,
milliseconds or a measurement. Out-of-range numeric dates are invalid. No clinical
plausibility bands or automatic century correction are applied.

## Accounting, components and saved output

Missing values and blank/whitespace text are counted as missing. Literal `NA`, `Unknown`
and other nonblank unparseable labels are invalid, not silently converted to missing.
Genuine factor missing levels are normalized while literal labels remain values. The
success denominator is nonmissing input: parsed / (parsed + invalid). An all-missing
column has an undefined success rate; an all-invalid nonmissing column has rate zero.

The core accepts 1–10,000 supplied rows without sampling. The preview displays the
first 10–100 source rows (default 20), disclosing any display truncation. Full counts
and saved values use every supplied row in its original order, retaining failed rows
as missing output. Independent numeric columns in the sample are teaching fixtures,
not paired clinical event dates or a follow-up history.

Optional components are year, month, month name, day, hour, minute, second, weekday
name, week, quarter and day of year. Week is **lubridate::week()** style: seven-day
blocks from 1 January, not ISO-8601 or epidemiological weeks. Thus 2021-01-01 has week
1 here, despite being ISO week 53 of 2020. Quarter and day of year use the Gregorian
calendar. English month/day labels do not depend on the machine locale.

Saved numeric output is Unix seconds; numeric component outputs are continuous numeric
columns. The standardized ISO-UTC text output is a nominal column carrying datetime
labels, not a native jamovi date class. Month/day names are nominal with fixed labels.
Only enabled Output controls append columns. All-unparsed output stays entirely
missing; an unused structural text level does not fabricate a parsed value.

The existing explicit `clearOnInputError` policy is enabled for this transformation.
Successful all-invalid results and incomplete selections clear prior saved values;
Python input validation clears native payloads. Pre-launch/transport failure paths and
actual desktop filtering remain separate lifecycle qualification limits.

## Synthetic example and independent checks

**UTC Date Conversion Examples** contains twelve PII-free source profiles. With
`Calendar text` and YMD, expected accounting is **7 parsed, 4 invalid, 1 missing**.
The ambiguous slash date is invalid under YMD; changing to DMY/MDY is a deliberate
reinterpretation. Separate Excel/Unix columns illustrate origins, minute fractions,
pre-epoch instants and bounds. Regenerate with
`python3 data-raw/generate-datetime-examples.py`.

Python tests use independent calendar/epoch fixtures, all 1,440 minute positions in an
Excel day, invalid leap dates, explicit ambiguity, true/literal missingness, numeric
limits and sparse saved-row IDs. Native R checks compare the supported formats with
`lubridate` parsers/components in UTC and numeric conversion with base R `as.POSIXct`
and `round`. Numerical, compiler, packaged runtime, native lifecycle, desktop
persistence/export and clinical/release gates are tracked separately below.

## Qualification

Recorded on 2026-10-29 / 0.3.45:

- The full Python suite passed **354 tests**. The native GUI subsequently exposed
  blank saved-column names when an output supplied a measure type without an explicit
  title. Every saved output now supplies its title and description; conversion values
  did not change. After that correction, **41 focused converter/generator checks** and
  **163 native assertions** passed again. The initial unnamed-output .omv is retained
  as failure evidence, not as a usable example.
- Native R comparisons cover twelve explicit text orders/time formats, Excel/Unix
  epochs, all 1,440 minute positions in an Excel day, components, genuine/literal
  missingness, sparse original row IDs and valid → unparsed → restored/unselected
  lifecycle. The R test framework reports no failed/error/warning/skip assertions;
  nonfatal OS-permission messages in its log are tracked separately.
- Compiler, generator/status freshness and **25 packaged-runtime cases** pass.
  Bundled Python is **3.11.9**; no zoneinfo/tzdata or extra packages were installed.
- macOS arm64 / jamovi 28.13: install via **Modules → Sideload**, start a fresh engine,
  load the Data Library CSV, select the source and enable saved outputs. Calendar
  accounting is **7 parsed / 4 invalid / 1 missing**; Excel is **11 / 0 / 1**.
  Requiring time-bearing text on the date-only column gives **0 / 11 / 1** and all
  four enabled saved outputs become missing. A correct source/format restores them.
- Saved `.omv` files contain the four explicitly named outputs (epoch, UTC labels,
  year and Jan-1-block week), all original profiles/columns and the original row order.
  Fresh-engine reopening preserves roles, formats and output settings; explanation
  on/off forces a rerun and clears optional text. Native HTML tables and saved values
  agree with independent CSV/calendar arithmetic through
  `python3 tools/check-datetime-artifacts.py`.
- This analysis adds no plot, so no plot-export claim is made. Actual GUI filtering,
  pre-launch/transport recovery, broader platforms/accessibility, omitted methods and
  clinical/release review remain open.

The prior 0.3.44 package separately passed a clean full native rerun with **3,852
assertions** before the new converter was added. That result is not a claim that the
entire 0.3.45 native inventory was rerun; the new converter has the independent
163-assertion native evidence above. See the
[machine-readable evidence](validation-exports/python-datetime-0.3.45-checks.json).
