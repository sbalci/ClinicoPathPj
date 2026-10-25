# Multi-variable quality validation — 0.3.3

Recorded 2026-10-25 using jamovi 28.13 on macOS arm64 with bundled Python and the
installed R package. The evidence applies to the implemented core, not full baseline
parity, clinical clearance or all-platform qualification.

## Numerical checks

The frozen `dataquality.b.R` specification was inspected for denominators, constants,
cardinality, IQR eligibility, threshold comparisons and row/value duplicate semantics.
`tools/generate-quality-oracles.R` constructs independent base-R references rather than
calling the Python implementation. `tests/fixtures/quality-oracles.json` contains **32
fixtures**, including seeded random frames, ordered/unused levels, literal NA categories,
all-missing columns, numeric IQR flags, delimiter-bearing strings, and 251/2500 missing
values (10.04%, which must exceed a 10% threshold before rounding).

Python agrees with reference missing/observed/distinct/repeated counts, rates, constants,
cardinality, complete cases, missing cells and row-missingness distributions. Row-duplicate
counts and the first occurrence/count of the top groups match independent R row equality.
True missing codes stay distinct from literal text. Missing row signatures are included
in multi-variable row mode, while value mode excludes missing values.

## Integration and local interaction

- **192 Python tests passed**, including all prior analyses and seven new quality tests.
- **515 installed-package R expectations passed**, with zero failures, warnings or skips.
  The new R file contributes 23 expectations for native counts, true NA factor levels,
  original row IDs, threshold edges and valid -> changed selection -> incomplete -> valid
  transitions, including HTML and static-map clearing/restoration.
- All **20 entry points** compile. Generator/status freshness and whitespace checks pass.
- Package inspection confirms the single module identity, version, registered source and
  shared-helper/template bytes. **Ten packaged analysis runtimes** execute successfully.
- The offline Node DOM harness checks paging, filtering, cell click and keyboard-focus
  event handlers. Separate tests verify script-closing labels are escaped and that the
  template uses no network requests, innerHTML or jamovi option/refit hooks.
- Plot geometry tests check the exact missing/observed matrix, original-row axis labels
  and rejection of incomplete rectangular maps. Preview limits are checked independently.

The full suites ran against a stable build. No module calculations, statistical defaults
or existing utility/kappa identifiers were changed.

## Native jamovi evidence

Installed `ClinicoPathPj_0.3.3.jmo` with Modules -> Manage installed -> Sideload into the
existing module, then restarted jamovi to use a fresh engine. The installed analysis,
shared helper and interactive template were compared byte-for-byte with source.

Imported `data/python_dataquality_examples.csv` and selected its four variables:

- 24 input rows, 19 complete rows, three missing ages and two missing marker values.
- Row-level duplicate accounting found one excess repeated full row.
- Interactive missing-only filtering displayed five rows while native completeness
  stayed at 19. Clicking Row 4/Age reported missing; keyboard Tab moved to Row 4/Marker
  and reported observed. Paging to page 2 displayed row 11 onward.
- Native Missing Patterns plotted the expected cells at rows 4, 5, 10, 12 and 21.
- Saved `validation-exports/python-dataquality-0.3.3-validation.omv`, quit/restarted
  jamovi and reopened it. Tables, maps and the interactive controls restored. The
  reopened missing-only filter again displayed five rows. Selecting Age reduced the
  displayed columns while retaining that same missing-any-preview-variable row filter. Display filters/page reset
  as documented and do not change the cohort.
- Image -> Export -> PNG produced `validation-exports/pydataquality-0.3.3-native-export.png`.
  The PNG was decoded and visually checked. The `.omv` ZIP is valid and embeds two PNG
  map resources, alongside the interactive result content.

The final registry-evidence rebuild changes metadata only. Statistical, bridge, renderer,
UI and JavaScript files are identical to the GUI-tested candidate.

## Remaining gates

Little's MCAR test, parsing-based type guessing and the original heuristic quality grade
are omitted explicitly. Native overview/type-plot desktop transitions, GUI previews at
resource limits, exhaustive cancellation scenarios,
additional architectures/platforms and clinical review remain pending. None of these
counts establishes why data are missing or whether repeated records represent errors.
See [the function guide](python-dataquality.md) and the registry feature matrix.
