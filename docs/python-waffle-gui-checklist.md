# Waffle package and desktop acceptance — 0.3.76

Executed on 2026-11-15 with macOS arm64 / jamovi 28.17.0. GUI Sideload and two
fresh engines pass seven waffle OMV profiles, native HTML/PNG export and legacy
lollipop reopen/recalculation. All 1,487 installed files match the archive.
Built and installed libraries each pass 859 native assertions; actual packaged
runtime checks total 246,364 across waffle/lollipop/pie. Independent saved/exported
tables, data bytes and same-dimension pixels agree; four corruptions are rejected.
The original 0.3.75 lollipop file remains unchanged and its package is archived.
See [the detailed evidence and limitations](python-waffle-core.md).

The protocol below is retained for reproduction. Cached Results and direct
exports have different resolutions: compare each with a native reference at the
same dimensions. Normalize only numeric whitespace before % in proportion cells;
do not change digits or infer precision from formatting differences.

The source gate passed previously: 739 Python tests, 859 isolated native R
assertions, independent fixtures and restored-state PNG export. These do not
establish acceptance of a built or GUI-installed 0.3.76 module.

## Preparation

- Preserve verified `ClinicoPathPj_0.3.75.jmo` in `packages/archive/`.
- Build the standard `ClinicoPathPj_0.3.76.jmo` using
  `Rscript --vanilla tools/build.R --build-only`.
- Inspect archive paths, duplicate names, CRC, module version, single waffle
  menu entry, every registered analysis source, shared helpers, compiled UI and
  `python_waffle_examples.csv`. Execute `tools/check-waffle-package.py` against
  the actual archive using jamovi's bundled Python.
- Run the existing lollipop and pie package regressions, then the waffle native
  suite against the actual built R library. Compare that library with the JMO.
- Install only through jamovi Modules → Manage installed → Sideload. Verify
  every installed file against the archive, then restart for a fresh engine.

## Desktop protocol

1. Reopen the saved 0.3.75 lollipop example and force recalculation. Preserve
   its prior file; compare tables and dataset bytes with the older artifact.
2. Open Data Library → ClinicoPathPj → Waffle Panel Denominator Examples.
   Confirm one Waffle Charts entry under Stats Plots Py → Categorical comparisons.
3. Select Category, Frequency and Panel. Check source rows 9, complete 7,
   excluded 2, zero-frequency 2, contributing 5 and total N=1,004.
4. Check active panel N values 4 and 1,000, inactive panel N=0; each active
   grid has 100 tiles. Category counts are 1/3/0 and 899/100/1. Allocation is
   25/75/0 and 90/10/0. Rare remains in exact tables despite receiving no tile.
   Panel/category display order follows transported factor order.
5. Enable legend, source rows and explanations. Check the omission warning,
   visible panel N, exact table labels, mutually disabled subject/frequency
   roles and organized, readable controls.
6. Save a default profile; set seven rows and flip axes, save a second profile.
   Change title/legend title, disable plot/source/explanations and verify stale
   results clear. Save an off profile.
7. Remove the required Category role, verify incomplete tables/plot clear and
   save an incomplete profile. Restore it, verify recalculation and save a
   recovered profile. Test removal/restoration of the optional Panel role too.
8. Save As a separate reopened profile, restart jamovi and reopen that file.
   Force an option change and rerun. Export native HTML and PNG from the GUI.
9. Independently inspect every OMV index/table/options/image and exported HTML
   against R/reference counts. Verify dataset/metadata bytes are unchanged
   across option-only profiles. Compare direct PNG with the cached/restored
   drawing and a native reference render using the same factor order/options.
10. Recheck installed/archive bytes. Record GUI, numerical, compatibility,
    platform and remaining accessibility evidence separately. Archive the
    superseded root package only after the replacement is qualified.

Keep PNGs and generated report JSON/logs ignored. Retain meaningful synthetic
OMV/HTML fixtures and source/reference test fixtures. Full baseline parity,
fractional weights, interaction and other platforms remain separate gates.
