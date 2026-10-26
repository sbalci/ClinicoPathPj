# Python execution comparison

Install the single `ClinicoPathPj_0.3.8.jmo` module. Open **Python Lab → Execution services →
Python bridge comparison**. Pj >=1.3.0 is optional and needed only for its service routes.
Use a fresh jamovi engine after replacing loaded modules.

Select a numeric measurement, a binary reference and its explicit positive level.
The default route uses ClinicoPathPj processx with bundled Python. The other routes use
Pj with bundled or System Python; a System interpreter must already provide the required
scientific packages. Missing/incompatible Pj produces a targeted error.

All routes use identical cutoff calculations and native outputs. Set direction, criterion,
weights and intervals in the native options. Dragging, numeric preview and ROC selection
change the local preview. **Apply cutoff to jamovi** persists the cutoff option and reruns
the selected route. Restore returns to the applied cutoff. Opening the result must not
silently rerun a model. Existing D3 and Observable analyses retain local-only Apply.

The timing reports calculation/transport work, including service preparation, and excludes
static image rendering. It does not measure pure process-launch overhead. Pj is synchronous;
see the [review and limitations](pj-service-review.md).

## Menus

| Group | Topic subgroups |
|---|---|
| Descriptives Py | Distributions; Data quality; Transformations; Contingency tables; Summaries |
| Stats Plots Py | Group comparisons |
| MedDecide Py | Diagnostic accuracy; Decision analysis; Exact tests; Agreement sample size |
| Python Lab | Runtime; Cutoff explorers; Execution services |

Menu assignments and compact display titles come from the registry; source SPECs and
compiled manifest are checked against it. Existing `py…` identifiers, including kappa IDs,
remain unchanged. Planned Survival Py and OncoPath Py groups contain no placeholder analyses.

## Acceptance limits

Numerical route comparison and compiler checks are separate from GUI installation,
interaction, saved-file reopening and export evidence. This experiment does not resolve
the previously documented native SVG saved-analysis issue or complete the 61-analysis migration.

Native GUI: both modules were sideloaded successfully and jamovi restarted. The four
family groups, topic subgroups, short explorer titles and comparison route selector
were visible in the fresh session. Further save/reopen/export acceptance remains separate.
