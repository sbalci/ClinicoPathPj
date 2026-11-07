# Two-component first-event preparation

`pyfirstevent` is a standalone Python utility under **Survival Py → Data preparation**,
introduced in 0.3.51. It prepares one composite time/status pair per supplied record.
It does not implement a clinical RFS, PFS or DFS definition or fit a survival model.
The existing outcome status analyses retain their contracts and defaults.

## Inputs and policy

Select a nominal/ordinal status variable and a scalar numeric time for each component.
Choose each component's **event** and **event-free** levels explicitly. The selections
must be distinct and declared; any other observed status must be recoded first.
Unused factor levels are retained in the source and do not become observations.

Times must be nonnegative durations with the same origin and units. A component
event status means time **to that event**. Event-free means time **through which
that component is known event-free**, not an arbitrary last-contact date. Zero is
permitted. Dates require explicit conversion; infinite times are rejected.

The utility uses a conservative common observation horizon:

1. Composite time is the minimum of the two component event/follow-up times.
2. Status is Event if a component event occurs at that minimum; otherwise Censored.
3. An exact event/censor tie favors Event. Two events at the same minimum are
   labelled Both components in the audit source.
4. An event after the other component's event-free observation ends does not count
   as an observed first composite event. Censor at the earlier common horizon.
5. Missing status or time in either component makes all three saved outputs missing.
   A known event alone cannot establish the first event when another component is unknown.
6. A negative duration invalidates the record. It is counted separately from other
   incomplete records; all three outputs remain missing.

For example, A event at 8 and B event-free through 2 produces time 2, Censored.
A event at 2 and B event-free through 8 produces time 2, Event, Component A.
These rules are displayed in the native results. They are a chosen representation
policy, not proof that censoring is independent or that follow-up is sufficient.

## Outputs and interface

Essential component roles and level definitions stay expanded. Results include
component mappings, row accounting, status counts and a bounded source-row preview.
Optional controls show a descriptive report and a static native count plot.
Saved **Composite time**, **Composite status** and **Determining component** preserve
original row identities, including missing/invalid rows. Status uses Censored/Event
labels (logical codes 0/1); determining component is an audit label, not a competing-risk
or cause-specific indicator. Plot and report settings do not change the endpoint rule.

The typed **Two-Component First-Event Examples** Data Library dataset contains twelve
synthetic records and literal expected outputs: nine usable records, six events,
three censored, two incomplete and one negative-duration record. Three exact
event/censor ties and two events beyond common follow-up illustrate the policy.
No patient data are included. Generation scripts are under `data-raw/`.

## Qualification

- Literal fixtures and independent chronological grouping cover event/censor order,
  simultaneous events, exact ties, zero, missingness and negative durations.
- Component-swapping and time-scaling identities, strict storage/level validation,
  bounded previews and sparse source-row outputs are covered in Python tests.
- 46 focused Python tests and all 391 full Python tests pass. The focused total includes
  eight first-event tests, six registry tests and 32 generator checks. The full run
  took 385.961 seconds. A subsequently corrected plot-option label and registry GUI
  evidence are presentation/metadata changes; final generator freshness is checked.
- 96 focused native R assertions pass: 22 first-event oracle/lifecycle checks, 29
  interval2 checks and 45 existing composite-status checks. This is not the full
  native R inventory. Sandbox `Operation not permitted` diagnostics occurred in
  the native log; testthat records zero failures, warnings or skipped assertions.
- Compiler and all 28 packaged-runtime cases pass, including first-event saved
  time/status/source and sparse row IDs. Source/archive integrity is checked separately.
- macOS arm64 jamovi 28.13: Modules → Sideload, fresh-engine reopening and forced
  recalculation pass. The typed example was opened with jamovi's file chooser.
  Essential event definitions remain visible; the final plot option is labelled
  Composite status counts. Installed files match the archive byte-for-byte.
- Three GUI-saved OMV states (valid, missing-role, recovered/fresh-engine reopened)
  preserve all original columns and expected row-aligned outputs. Missing-role
  outputs are all missing. Native HTML audit, count and preview tables match the
  literal fixtures. Its embedded 1437 × 798 PNG has unequal 3/6 bars and was visually
  inspected. This is HTML embedded-image export, not a direct Save Image test.
- Evidence: [qualification record](validation-exports/python-firstevent-0.3.51-checks.json).
  Recheck saved bytes with `python3 tools/check-first-event-artifacts.py`.
- No clinical review, independent-censoring validation, repeated-patient inference,
  fitted survival model, full outcome-organizer parity, accessibility certification
  or additional-platform qualification is claimed.

Patient-level hierarchy, more than two components, interval-censored components,
delayed entry and recurrent-event histories remain out
of scope. Do not pass multiple patient rows as independent survival observations
without an appropriate design and model. This utility does not deduplicate them.

## Optional administrative cutoff — 0.3.52

Administrative censoring is **off by default**, with an initially empty cutoff.
Enabling it requires an explicitly entered finite nonnegative duration. Zero and
scientific notation are accepted. The value must use the same origin and units
as both component times; it is not a calendar date or a recommended follow-up limit.

First prepare the unadjusted composite using the policy above. For each usable
record with composite time **strictly greater** than the cutoff, set time to the
cutoff, status to Censored and audit source to Administrative cutoff. Records
at or before the cutoff retain time, status and audit source. In particular,
an event exactly at the cutoff remains Event. Incomplete/invalid component
records remain missing; do not infer follow-up from a known partial record.

The expanded Administrative Censoring panel contains the switch and a cutoff
field enabled only when the switch is on. Native results add a cutoff audit
(shortened records, events changed to censored, censored records shortened and
events exactly at cutoff) plus conditional preview columns for unadjusted
time/status and whether the cutoff applied. The existing count plot uses adjusted
statuses. Row-accounting event/censor ties and events beyond common follow-up
refer to the unadjusted component stage; the separate cutoff audit counts
administrative adjustments. Python output descriptors include the current cutoff; see the persisted-description limitation below. Original
source codes 0–3 retain their meaning; code 4 (Administrative cutoff) is appended
only when censoring is enabled. Disabling it restores the four original source levels.

In the existing twelve-row typed example, cutoff 2 leaves nine usable records,
with three events and six censored. Four records shorten: three events and one
already censored record. Two events exactly at cutoff remain events. Cutoff 0
retains the single time-zero event and shortens the other eight usable records.
No component source columns are changed. Existing 0.3.51 OMVs open with censoring
disabled and can be recalculated with the original result contract.

Current checks: 45 focused first-event/generator tests and all 396 full Python
regression tests pass. Independent three-timepoint chronological enumeration covers
180 configurations, explicit cutoff validation, zero/exact ties, disabled-route
identity and sparse output alignment. The final full run took 560.849 seconds.

130 focused native R assertions pass against an isolated copy of the completed
package: 56 first-event/cutoff checks, 29 interval2 checks and 45 status-preparation
checks. An earlier run was invalidated by rebuilding its library while tests were
running; its missing-package errors are preserved separately and are not evidence
of a statistical defect. The isolated rerun has no failures, warnings or skips;
sandbox `Operation not permitted` diagnostics remain visible in its log.

Compiler, generator/status freshness and all 28 packaged-runtime cases pass,
including an explicit administrative request against the extracted archive.
macOS arm64 jamovi 28.13 Sideload, installed/archive byte comparison, reopening an
existing 0.3.51 OMV, disabled recalculation, cutoff 2, pending cutoff, cutoff 0,
recovery and fresh-engine reopen/rerun pass. Six saved OMV states retain every
source column and match the literal endpoint expectations. The pending state clears
all three output columns. Native HTML audit/preview and its embedded 1437 × 798
PNG match the fixture; this is not a direct Save Image qualification.

**Persisted description limitation:** jamovi retains existing dataset-column
descriptions from the older 0.3.51 file, even though Python sends updated output
descriptors and values update correctly. Those descriptions do not identify the
applied cutoff. The saved analysis's native cutoff audit and unadjusted preview
are authoritative. When taking these columns outside the analysis, carry the cutoff
policy with them. Recreating all three generated columns by switching their Save
and Export controls off, then on, was tested in the synthetic copy: the new
`freshoutputs` OMV retains all source values and has current cutoff-2 descriptions
for time/status. Manually annotating exported metadata is another option.
Automatic description refresh is not qualified. This limitation prevents claiming
a self-describing standalone dataset export from the older saved analysis.

Evidence: [0.3.52 qualification record](validation-exports/python-admin-0.3.52-checks.json).
Recheck persisted values and metadata with
`python3 tools/check-administrative-artifacts.py`.
Administrative censoring does not establish independent censoring, a clinical
endpoint definition, an appropriate cutoff, patient independence or model fit.

## Subject identity audit — 0.3.53

The optional **Subject identity audit** starts off. Enable it and select a text-ID
or nominal/ordinal column in the Data and roles supplier. The **Subject Identity**
section exposes **Require one record per subject**. Audit tables and subject preview
columns appear only while auditing is enabled. Selecting an ID does not aggregate,
remove, reorder or combine records, and does not alter endpoint or cutoff calculations.

ID comparison uses exact text/factor labels. Leading zeros and nonblank labels'
leading/trailing spaces are preserved: `001`, `01` and `1` are different IDs, as are
`S`, ` S` and `S `. Literal `NA` is known; actual missing values and wholly blank
labels are unknown. Numeric identifiers require explicit conversion to text or a
labelled factor; no automatic formatting or rounding is used. Scalar labels are
limited to 256 characters without control characters. Unused factor levels do
not create subjects. These rules are stated in the native identity policy.

Identity accounting covers **all supplied records**, including rows with missing
or invalid endpoint components. Counts distinguish records with IDs, missing IDs,
distinct known IDs, repeated IDs and records belonging to repeated IDs. The table
lists the first 20 repeated IDs in first-appearance order; the summary includes
all repeats. The bounded endpoint preview adds subject labels and full-input
record counts for each known ID.

Without the strict requirement, preparation continues per source row and warns
about repeated/missing IDs. With it enabled, any missing/blank or repeated ID
blocks preparation and clears previous outputs. A selected unique-ID column
restores preparation. Requiring uniqueness with the audit disabled, or enabling
an audit without selecting an ID, gives a pending configuration message.
Unique labels do not establish independent observations or validate a clinical
patient definition. Resolve patient histories and the intended observational
unit explicitly before downstream inference.

The typed **First-Event Subject Identity Examples** dataset contains twelve
synthetic timelines with eleven known ID records, nine distinct known IDs, two
repeated IDs across four records and one missing ID. The original endpoint
fixture still has nine usable record results. IDs `001`, `01` and `1` remain
distinct. No real patient data are included.

Qualification: Python, isolated native R, compiler/archive and desktop gates are
tracked separately below as they complete. Patient aggregation, repeated-event
history reconstruction, clinical review, full native inventory, other platforms
and accessibility certification remain open.

### 0.3.53 qualification status — 2026-11-07

The optional identity audit is qualified for this synthetic record-level workflow
on macOS arm64 jamovi 28.13. Six identity and three dependency-staging tests pass.
The final selector regression asserts that both the supplier and subject role
accept ID-measure columns; the role explicitly permits factor/ID inputs. Numeric
identifier storage remains rejected by the Python engine.

The full Python run completed 405 tests in 867.800 seconds: 402 passed and three
unrelated runtime subprocesses reached their unchanged SIGALRM limit. All three
passed on isolated rerun in 8.765 seconds. This is not a clean all-green full-suite
run. Runtime/resource limits were not relaxed. All nine final focused tests passed
in 11.042 seconds with bounded numerical-library threads.

All 76 focused native R assertions pass against the final completed build,
including independent label-frequency counts, exact-label transport, sparse source
rows and strict output clearing/recovery. The standalone harness initializes
jmvcore's protobuf constructor and sets the bundled PYTHONHOME. Earlier harness
runs omitted these setup steps and failed before completing serialization; their
logs are retained. Sandbox Operation not permitted diagnostics remain visible;
testthat records zero failures, warnings or skips. The full native inventory was
not run.

The final full compiler build and all 28 extracted packaged-runtime cases pass.
An interrupted earlier dependency refresh omitted Pillow; extraction now stages
and verifies a complete pinned tree before replacing the live bundle. Three tests
cover replacement, extraction failure and checksum failure. All ten pinned wheels
are restored. The incomplete archive remains quarantined, and the older candidate
is retained separately. The final archive uses the standard filename
`ClinicoPathPj_0.3.53.jmo`.

GUI Sideload installation, a fresh engine, text-ID selection, repeated/missing-ID
warnings, strict rejection, switching to a unique Record ID, restoring the original
ID, save/reopen and forced backend recalculation pass. Five saved OMV states retain
all nine source columns and the expected three aligned outputs. Pending and strict
states contain all-missing outputs; valid, unique and reopened states retain six
events, three censored and three unusable records. Exact labels 001, 01 and 1 stay
distinct. Native HTML contains the expected 12/11/1/9/2/4 audit, repeated-ID rows and
source-row annotations. Its embedded 1437 × 798 PNG was visually inspected and
shows unequal 3/6 bars. This verifies HTML embedded-image export, not direct Save
Image. Installed manifest, UI, R database, Python sources/registry, Pillow and typed
example match the final archive byte-for-byte.

See the [qualification record](validation-exports/python-identity-0.3.53-checks.json).
Recheck saved artifacts with `python3 tools/check-identity-artifacts.py`.
Patient aggregation, repeated-event histories, clinical review, broader platforms,
accessibility certification and full migration parity remain unqualified.
