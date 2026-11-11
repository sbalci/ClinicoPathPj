# Word and LaTeX export checks for the execution examples

Verified on **2026-11-10**, using ClinicoPathPj 0.3.62, Pj 1.5.0 and jamovi
28.17 on the current macOS arm64 setup. These are export checks for the saved
summary and age-pyramid comparisons. Analysis calculations and GUI save/reopen
checks have separate evidence in their respective guides.

| Comparison | Word tables | Word plots | LaTeX tables | LaTeX figure assets |
|---|---|---|---|---|
| Own/Pj summary | Two identical eight-column summaries | No plot defined | Both expected summaries | None expected |
| Own/Pj age pyramid | Two exclusion audits and two population tables | Two readable drawings | All four expected tables | Two referenced, rendered PDF figures |

All four exports were produced through **jamovi → File → Export**, starting from
the saved reopened comparisons. The original `.omv` files and module source were
not edited. No package rebuild or dependency installation was needed.

## Ready-to-inspect artifacts

- Summary [Word document](validation-exports/python-summary-service-0.3.62-reopened.docx),
  [Word rendering](validation-exports/python-summary-service-0.3.62-word-render.pdf),
  and [LaTeX bundle](validation-exports/python-summary-service-0.3.62-reopened-latex.zip).
- Age-pyramid [Word document](validation-exports/python-age-pyramid-0.3.62-reopened.docx),
  [Word rendering](validation-exports/python-age-pyramid-0.3.62-word-render.pdf),
  and [LaTeX bundle](validation-exports/python-age-pyramid-0.3.62-reopened-latex.zip).
- [Structural checks](validation-exports/python-service-office-artifacts-20261110.json)
  and [rendering/compilation evidence](validation-exports/python-service-office-qualification-20261110.json).

The Word renderings were generated with **LibreOffice 26.8.1.1 AARCH64**, using a
temporary isolated profile, then visually reviewed across all six pages. Both
summary rows, all age-pyramid tables, legends, axes and unequal bar lengths were
readable. Native Microsoft Word was not used. The first sandboxed conversion
exited without output; retrying outside the sandbox produced both documents.
The successful conversion reported fontconfig cache warnings, retained in the log.

Both Word drawings reference one deduplicated embedded PNG because the two
age-pyramid images are identical. One media file does not mean a plot is missing.
The LaTeX figures are separate PDFs with valid references; both render to identical
pixels and show the expected unequal bar lengths. These are native static Image
outputs; these checks do not qualify the interactive SVG experiment.

## Remaining LaTeX limitations

The two full-document compilation attempts stopped at **`apa7.cls` not found**.
The local TeX environment therefore cannot establish full compilation acceptance.
The exported sources were preserved unchanged; the required TeX class was not
installed as part of this check. See the [summary compile log](validation-exports/python-summary-service-latex-20261110.log)
and [age-pyramid compile log](validation-exports/python-age-pyramid-latex-20261110.log).

The jamovi exporter also reuses labels for repeated result titles: `tbl:Table_Summary`
in the summary comparison, and `tbl:Table_Data_Summary`, `tbl:Table_Population_Data`
and `fig:Figure_Age_Pyramid` in the age comparison. Figures and tables are present,
but manuscript cross references require distinct labels. This is observed export
structure, not a statistical difference between execution routes. Full compilation
and cross-reference checks remain open.

## Reproduce the structural checks

```sh
python3 tools/check-service-office-exports.py
```

The checker reads ZIP/XML/TeX without executing their contents. It checks exact
displayed counts, percentages and summary values; drawing relationships; nonempty
referenced figure assets; service identity; CRCs; and duplicate labels. It uses
only the standard library and existing artifact-inspection helpers. It does not
compile TeX or render office pages. Four separate corrupted-archive probes were
rejected: a changed Word mean, removed Word media, a changed LaTeX SD and a missing
LaTeX PDF figure. Rendering and compilation remain in the separate dated record.

No inference, statistical defaults, analysis identifiers or module menus changed.
Other platforms, clean-machine dependencies, new-example System Python and GUI
long-job cancellation remain separate qualification gates.
