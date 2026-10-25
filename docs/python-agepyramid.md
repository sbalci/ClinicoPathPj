# Python age pyramid

`pyagepyramid` is under **ClinicoPathPj → Descriptives → Age Pyramid**. Calculations and
static figure construction run in bundled Python. No new Python dependencies are needed.

Import `data/python_agepyramid_examples.csv`, choose **Age** and **Gender**, and set
Female = Female and Male = Male. The 19 synthetic input rows produce 16 retained pairs:
one missing age, one negative age and one unselected gender level are excluded.
Try the WHO/UN preset, then switch to custom breaks `0,18,65,85` to inspect boundary ages.

## Implemented core

- Six named presets: WHO/UN standard, WHO abridged infants, pediatric, reproductive,
  geriatric and life course. Presets always use left-closed bands.
- Custom fixed widths (including fractional years) or sorted distinct custom boundaries,
  with an open final band. Custom bands allow left or right closure. The first lower
  endpoint is included. Custom boundaries override width; malformed tokens are disclosed.
- Female/male level selection, label-based defaults, explicit warnings for level-order or
  partial automatic assignment, and single-group cohorts. An absent group's within-group
  percentage is unavailable, rather than 0% of a nonexistent denominator.
- Native count/percentage tables and a Data Summary with disjoint exclusions. Percentages
  use either each retained gender separately or all retained observations.
- Numeric metadata is honored for age columns; factors without numeric metadata use their
  numeric level labels. Missing codes remain missing; unreadable labels and negative ages
  are counted as unusable. Infinite numeric inputs are rejected by the shared bridge and
  must be recoded as missing before running the analysis.
- Native static pyramid, count/percentage bars, literal plot title, global jamovi palette,
  symmetric horizontal scale, and saved aggregate plot state. No calculation reads the
  original dataset while rendering the figure.
- Resource limit of 200 requested bands; a warning above 25 occupied bands. Only occupied
  bands are displayed, in ascending age order (oldest at the top). Vertical spacing is
  categorical and does not encode time. Unequal-width bands are counts per band, not age
  densities; the output states this limitation.

The fixed-width path includes a final empty band when all ages are younger than the width,
as the R baseline does; empty bands are omitted from displayed tables/plots. Ages above
120 years are retained with a warning. No data are removed automatically from the sheet.

## Remaining differences and gates

The original ggcharts alternate renderer, custom theme/palette controls and its sorting
options are omitted. The new renderer follows jamovi's global palette. Empty-band tables,
interactive exploration, population standardization, confidence intervals and clinical
reference intervals are not provided. The table is displayed in ascending order rather
than the baseline's descending order. The existing R analysis remains untouched.

This is an independently checked descriptive core, not full baseline feature parity.
Validation evidence is in [python-agepyramid-validation.md](python-agepyramid-validation.md).
