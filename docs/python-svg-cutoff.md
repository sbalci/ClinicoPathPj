# Native SVG cutoff experiment — 0.3.7

`pysvgcutoff` appears under ClinicoPathPj → Medical Decisions alongside the existing
D3 and Observable experiments. Use `data/python_d3_cutoff_examples.csv`, Measurement,
Reference and the explicit Positive reference level. Set the native cutoff to 2 for
a tied-threshold comparison. The module identity and previous entry points are retained.

Python performs the complete-case selection, threshold enumeration, classification
counts, proportion intervals, AUC and optimization. All three experiments call the
same engine. Exact-threshold ties are positive according to the chosen ≥ or ≤ rule.
The existing 1,000-complete-row cap and a 1.5 MB SVG payload cap apply. No additional
packages or network resources are required.

A complete initial SVG is constructed in Python; a bundled local JavaScript file adds
interaction using browser SVG APIs. It has no D3 or Observable runtime dependency.
This experiment tests jamovi's native result container, not a different statistical
method. See the [official Svg API](https://dev.jamovi.org/api/svg).

## Interactions and persistence

- Drag the measurement cutoff line; a transparent wide handle makes it easier to grab.
- Focus the line and use arrow keys, Shift for larger steps, Home or End.
- Edit Preview cutoff, choose Automatic cutoff, or click/focus-and-Enter a ROC point.
- Live counts, point colors and ROC operating point use Python's precomputed states.
- Apply to SVG snapshot updates only the local snapshot label. It cannot modify native
  tables, analysis options, saved classifications or the dataset.
- Reset to native rule restores the saved option. Change native direction, criterion,
  weights, confidence or cutoff in the options panel to rerun Python.

The graphic distinguishes the native applied rule, live preview and local snapshot.
An exported SVG/PNG captures the displayed preview, including the current local
snapshot label; static Image counterparts and native tables use saved options.
Interactive reopening starts from saved options. Jamovi also stores a graphic snapshot
for viewing without the module; its preservation must be checked separately from
interactive reconstruction. Local preview is not a persisted analysis rule.

## Comparison scope

| Approach | Browser dependency | Native graphic export | Recalculation |
|---|---|---|---|
| D3 HTML | Local D3 | Separate native Images | Saved jamovi options |
| Observable HTML | Local D3, Plot, Inputs, htl | Separate native Images | Saved jamovi options |
| Native Svg | Local custom JavaScript | Current SVG/PNG plus native Images | Saved jamovi options |

SVG supports native copy/export and a saved snapshot in jamovi ≥ 28.3. The module
already requires 28.3, so this experiment does not raise its minimum version.
For dense plots SVG size grows with observations; keep the bounded experiment and
raster counterparts. ROC controls with coincident points can overlap; keyboard focus
provides access to each point. There is no claim that this frontend is universally
better than Observable's richer form and table controls.

Confidence intervals assume independent observations and a fixed cutoff; they exclude
selection uncertainty. AUC has no inferential interval. Error weights are simple FP/FN
weights, not an economic model. Select cutoffs in one cohort and validate separately.
