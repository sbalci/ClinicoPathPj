# Pie count and geometry core — frozen 2026-11-14

Reserved public identifier `pyjjpiestats`, released jjstatsplot 1.0.82.03 baseline
commit `4c3cbe8de39d6259ee61d5fde28704f45e9cc8ed`. Verify its four registry hashes
against the frozen archive before comparing results. This increment is a reusable
source engine, with no SPEC/menu entry, package replacement or GUI claim.

Accept one labelled factor and optional nonnegative integer frequencies, or
optional known unique subject IDs for unweighted contributing rows. Frequencies
are observation counts, not survey weights. Never expand frequencies. Bound source
rows to 1–100,000, declared levels to 1,000 and nonmissing declared categories to 20.
Total positive complete frequency must be in 1..2^53-1. Reject invalid known weights
even when another role is missing. Audit source/complete/excluded rows, overlapping
role missingness, zero-frequency rows, positive contributing rows and total N.

True missing factor codes and actual missing level labels are excluded; literal
`NA` labels remain categories. Preserve declared factor order, including unused or
zero-count categories. Return a frequency/proportion table for all nonmissing
declared categories. A zero-count category has a zero-angle slice, no slice label,
and remains available to a future legend/table. A single active category is a
valid descriptive full circle. All-zero/empty input is refused. Preserve original
contributing row indices and optional exact subject labels.

Geometry matches single-variable ggpiestats: stack the last category at zero,
then earlier categories above it. Fractional lower/upper bounds equal integer
cumulative counts divided by total N. Convert to radians from 12 o'clock,
clockwise, with theta=2*pi*fraction. Return middle angle and unit-circle label
anchor x=sin(theta), y=cos(theta), except a zero-count slice has no anchor. Work
from exact integer cumulative counts, never rounded display percentages. Require
full-circle closure, no gaps/overlap, and sum of slice fractions one.

The R oracle is written and frozen before the Python engine. Compare its table
aggregation and actual ggplot2 build geometry, with ggpiestats cross-checks on
ordinary supported cases. Cover uneven/reordered/ordinal/Unicode labels, literal
NA and true missing levels, unused levels, zero weights, a full circle, large exact
counts, frequencies missing only on a row, and invalid/resource/identity requests.
Use independent tiny arithmetic and expansion/permutation/scaling properties.
Reject corrupted count, denominator, missingness and slice-direction outputs.

No inferential statistic, confidence interval, default expected ratio, paired test,
group/split panel, donut, clinical preset, renderer or interactive view is supplied.
Those require separate contracts and qualification. In particular, zero-count
declared categories must not silently disappear from a future null hypothesis.
The released wrapper defaults results.subtitle/proportion.test/bf.message off;
the underlying ggpiestats defaults differ. Preserve wrapper defaults in a future
native interface. Python plotting must use serialized geometry without refitting.

Method references: [ggplot2 polar coordinates](https://ggplot2.tidyverse.org/reference/coord_polar.html)
defines the origin/direction; actual local ggstatsplot 1.1.1 and ggplot2 4.0.3 build
inspection supplies slice bounds and retained zero-level evidence. These checks
establish geometry, not inferential or clinical validity.


## Earlier source-only evidence (2026-11-14)

The frozen oracle covers 12 datasets and **757 comparisons**, with zero observed
scaled difference. It uses base-R categorical aggregation, actual ggplot2 fill
stack bounds/polar settings and the ggpiestats path for ordinary small tables.
Eleven focused Python tests pass: tiny exact arithmetic, expansion equivalence,
row permutation, frequency scaling, polar closure, preserved unused categories,
missing-code/level distinctions, exact IDs, integer totals at 2^53-1 and explicit
invalid/resource refusals. Four mutations (count, denominator, missingness and
angle direction) are rejected by the frozen checker. R replay is byte-identical.
No inference was tested or supplied.

The first oracle run uncovered a real baseline limit: ggpiestats calls
`tidyr::uncount()` and refuses the `large_exact` fixture when converting large
frequencies to integer expansion weights. The oracle retains that error message
in the fixture's `baseline_limit` field. For that case, independent aggregation
and the non-expanded ggplot2 build supply the reference. The Python core supports
those exact count totals without expansion; it does not claim the original
high-level ggpiestats path accepts them. The failed run remains under
`/private/tmp/cpj-pie-reference-20261114.log`.

Fixture SHA-256: `478ff7b66b88b6a01cfa414c63b9c1ec9db278fc246466bbacaea3bd924668b7`.
Oracle SHA-256: `9ab4fa6a43468600b3fe1cf5c66cedece767a332284690c598ea3d07b50f61ee`.
At that earlier milestone, the registry remained **planned** until a public native adapter.
Source inventory stays 34 partial / 27 planned / 15 utilities, with 49 entries.
The qualified 0.3.71 JMO and all 1,467 installed files are byte-identical after
this source work. Its SHA-256 remains
`145cbc164a84c4fc4bf75fdaac7336610d5eb5a954a8b0678f8cf8e8fb0d4b5e`.

Reproduce from the project root:

```sh
Rscript --vanilla tests/reference/pie-core.R /private/tmp/pie-replay.json
cmp tests/fixtures/pie-core.json /private/tmp/pie-replay.json
PYTHONHOME=/Applications/jamovi.app/Contents/Resources \
  /Applications/jamovi.app/Contents/MacOS/python -B tools/check-pie-core.py
PYTHONHOME=/Applications/jamovi.app/Contents/Resources \
  /Applications/jamovi.app/Contents/MacOS/python -B tests/python/test_pie_core.py
```

Next: native frequency/denominator/source-row tables, organized single-factor
controls, plot payload/renderer, and native clearing/state restoration/export.
Only then build the next package and qualify its installed runtime and desktop
lifecycle. Statistical tests/ratios, grouped panels, donut and interaction need
separate validated increments.

The final source suite passes **673 Python tests** in 273.392 seconds, with no
failures, errors or skips. Generator/status freshness and whitespace checks pass.


## Native source increment (2026-11-14)

The earlier frozen source-only milestone above now has a literal SPEC/run entry:
`pyjjpiestats`, **Pie Chart (Core, Python)**, under **Stats Plots Py → Categorical
comparisons**. The public source implementation is partial; the existing qualified
0.3.71 package has not been replaced. Registry is now 35 partial / 26 planned /
15 utilities, with 50 entries and no full-parity claim.

The native interface selects one factor and either integer frequency counts or an
optional unweighted subject ID. Essential data roles remain visible; mutually
exclusive optional roles disable each other. Native tables report cohort/zero and
missing rows, all declared nonmissing categories, counts, explicit total-frequency
denominators, proportions and optional original contributing rows (first 1,000).
Zero categories remain visible in the frequency table and legend. Percentage labels
remain the default, with zero decimals; count/combined labels and 0–2 percentage
decimals are display-only. There are no inactive statistical-method or interval
controls. Statistical inference and grouped/donut/interactive features are omitted.

The new typed pie payload is bounded to 20 categories and stores counts, total N,
fractional slice bounds and optional display labels. Python Matplotlib constructs
Wedge objects from those bounds, with origin at twelve o'clock and clockwise
mapping. Its input checks reject inconsistent integer totals, nonfinite/gapped/
misordered slices and duplicate categories. Rendering never calls the count engine.
R displays the completed PNG and supplies jamovi's global colors and theme. Repeated
palette colors receive a hatch; native styling differs from the R baseline.

Six focused adapter/renderer tests pass: all frozen datasets traverse the public
runtime; actual Wedge angles match the independent R bounds; factor/zero legend
order and no-refit behavior are checked; labels/off controls/identity roles are
exercised; six malformed drawing payloads are refused; the subprocess route works.
The isolated R library passes **172 native assertions**, without failures, errors,
warnings or skips. It checks all 12 fixtures, missing-level distinctions, source
identities, labels/off/required-role recovery, duplicate-ID failure recovery and
restored drawing state after setting analysis data to NULL, followed by PNG export.
Its five relevant Python files byte-match final source.

The first native run had two test-contract failures. The existing bridge protects
markup-looking native table labels by inserting a space after a leading less-than
sign (`<A & B>` displays as `< A & B>`). Raw category labels and the plot legend stay
exact. Separately, an absent zero-slice annotation becomes NA in the R data-frame
state. The tests now check these existing display/serialization conventions; no
count, factor encoding, geometry or tolerance changed. The initial failed log is
retained at /private/tmp/cpj-pie-native-20261114.log. Do not claim character-for-
character native table presentation for markup-looking labels.

The synthetic `data/python_pie_examples.csv` has six source rows: four complete,
two excluded, one zero-frequency and three positive contributing rows, with N=25.
Declared counts 12/8/5/0 correspond to 48%/32%/20%/0%. The native 1300×900 PNG
was exported and inspected: the zero category has no slice/label and stays in the
legend. PNG/JSON/log validation assets remain ignored. No new JMO, installed
replacement or desktop GUI gate is claimed for this increment.

Reproduce native checks after source installation into an isolated library:

```sh
PYTHONHOME=/Applications/jamovi.app/Contents/Resources \
  Rscript --vanilla tools/check-pie-native.R <library>
PYTHONHOME=/Applications/jamovi.app/Contents/Resources \
  Rscript --vanilla tools/render-pie-example.R <library> /private/tmp/pie.png
```

Next execute a new standard-version archive's runtime and native library, then
Sideload through jamovi's module menu and qualify fresh-engine saved-file and
export behavior. Keep broader methods/platform and clinical-review gates separate.

The initial full Python run identified a stale negative generator probe that used
`pie` as an unsupported plot kind. It now uses an actually unsupported sentinel;
the focused generator suite passes. The failed run is preserved separately from
the final full-suite rerun. No statistical or drawing tolerance changed.

Final native-source gate: **679 Python tests** pass in 265.601 seconds; existing
categorical bars also pass **390 native assertions** in the same isolated library.
Generator/status freshness and whitespace checks pass.


## Packaged and desktop qualification — 0.3.72 (2026-11-14)

The earlier source/native milestones above are now packaged without changing the
statistical or drawing implementation. The actual extracted JMO passes **4,428
pie checks / 77 configurations**, including every frozen dataset, all three label
modes, both default/two-decimal labels, table denominators/identities, actual Wedge
angles, legend order and output/unsupported-option gates. Archived existing routes
also pass **5,435 bar / 90 configurations**, **6,692 histogram / 270**, and **2,008
independent/paired mean / 102**. The built and GUI-installed native libraries each
pass **172 pie assertions**, with no failures, errors, warnings or skips. The frozen
679-test source gate is retained; packaging/validation tooling adds no calculation.

Installed via **Modules → Manage installed → Sideload**, with all **1,473 files**
byte-identical to the JMO and no extra installed files. Fresh sessions on macOS
arm64/jamovi 28.17.0 (ports 58282 and 58479) verify the Data Library entry, one pie
menu item, frequency selection, zero-category legend, percentage/combined labels,
0/2 decimals, optional rows/plot clearing and required-outcome clearing/recovery.
The CSV imports alphabetical factor order **No, Other, Yes, Zero**; its counts are
12/5/8/0 with a common denominator 25. The earlier source example deliberately
specified No/Yes/Other/Zero instead. Both preserve their actual input order.

Six desktop saves cover percentage, combined labels, outputs off, incomplete,
recovered and reopened states. A second fresh session reopens and recalculates the
result. Native HTML/PNG export succeeds. Independent base-R CSV counts/proportions
verify all saved/exported tables. All six saves preserve dataset/metadata bytes;
recovered/reopened tables and equivalent cached plot pixels agree. Label changes
alter the plot while retaining the same numerical tables. Four artifact corruptions
(count, denominator, source identity and missing plot) are rejected.

Direct PNG is **1300×900**, byte-identical to the separately rendered native CSV
example with matching imported order and two-decimal combined labels. Its SHA-256
is `6c4c07915c37a8008a892c14ac3deeb47daeb1c1ff8ba7fec291c6300ae64e78`.
PNG/JSON/log validation assets remain ignored. JMO is **23,631,757 bytes**, SHA-256
`09a03d5e18931dade3dcdef6a99b7f7bb4c9aecd3c667d53bf09122a3b973710`.
Qualified 0.3.71 is retained in packages/archive for rollback.

The first artifact checker expected a partial-input message copied from the
multi-role bar analysis. Removing this pie's only required role instead returns
quietly with empty tables/notes and no cached image, as intended for an unconfigured
analysis. The checker now verifies that cleared state and absence of stale summary;
no numbers, tolerances or implementation changed. The failed run is preserved at
/private/tmp/cpj-pie-artifacts-20261114.log.

Weighted-example desktop qualification does not establish the optional unweighted
subject-role GUI workflow, broader theme/accessibility support, other platforms,
full baseline methods or clinical review. No inference or interactive behavior is
claimed. The archived registry is a build-time snapshot; coverage fields in the
source registry record this subsequent qualification.

```sh
# Use jamovi's bundled Python environment for these checks.
python -B tools/check-pie-package.py ClinicoPathPj_0.3.72.jmo
Rscript --vanilla tools/render-pie-gui-example.R <library> docs/validation-exports/python-pie-0.3.72-native-source.png
python -B tools/check-pie-artifacts.py
```
