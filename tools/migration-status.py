"""Generate a truthful feature/status matrix from the authoritative registry."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
registry=json.loads((ROOT/'inst/python/registry.json').read_text())
rows=[e for e in registry['analyses'] if e.get('baseline')]
text='''# Python migration status

Generated from `inst/python/registry.json`; never infer full parity from a menu entry.
The frozen baseline contains 61 analyses across five families. Existing utility and
example analyses are retained separately. Every public identifier starts with `py`;
the original R identifier is provenance, not a second menu entry.

`partial` means an executable implementation exists with incomplete feature or acceptance
coverage. `planned` entries are not installed as placeholder analyses. Full supported
parity and GUI/platform acceptance remain separate gates.

| Python identifier | Original R analysis | Family | Wave | Implementation | Full parity | GUI |
|---|---|---|---:|---|---|---|
'''
for e in sorted(rows,key=lambda e:(e['wave'],e['family'],e['id'])):
 text+='| {} | {} | {} | {} | {} | {} | {} |\n'.format(e['id'],e['source_name'],e['family'],e['wave'],e['status'],'yes' if e['coverage']['full_parity'] else 'pending',e['coverage']['gui'])
text+='''
## Menus and optional execution service

Installed analyses use Descriptives Py, Stats Plots Py, MedDecide Py and Python Lab,
with registry-owned topic subgroups and compact experiment titles. Planned Survival Py
and OncoPath Py groups do not install placeholder entries. Existing identifiers remain stable.

`pybridgecompare` is a retained utility experiment, not another baseline port. It uses
the same cutoff engine through processx (default) or optional Pj >=1.3.0 service API 1.
Twelve bundled-interpreter route configurations passed matched native results and
independent R count/exact-interval checks. See [service review](pj-service-review.md).

## Foundation and next gates

Implemented: registry-based family routing, frozen baselines with file hashes,
generator-owned organized `u.yaml`, mixed-case-capable internal schema, stable existing
Python identifiers, Python static plotting through bundled Matplotlib Agg, categorical
factor ordering and original-row transport, and native saved-column payload validation.

The bridge supports Terms transport and Output payloads. Action options/UI are accepted;
analysis-specific Action result/file delivery and GUI tests are still required before
claiming those workflows complete.

Existing static interval, line, box, bar and diagnostic scatter plots are constructed in
Python. The diagnostic interactive dotplot also has an applied-cutoff static export.
The R bridge displays PNGs and supplies jamovi palette/theme settings. Existing saved
R plot-data states are translated into the same Python drawing input without model refits.

Pending: remaining method parity across all waves; advanced engines and independent
validation; broader interactive views; native saved-column/action GUI qualification;
SVG/PDF asset delivery; remaining save/reopen/export acceptance; and Windows/Linux support.

The current dependency lock targets CPython 3.11 on macOS arm64. Users install nothing.
Never label the entire 61-analysis migration complete from the foundation build.
'''
path=ROOT/'docs/python-migration-status.md'
if '--check' in sys.argv:
 sys.exit(0 if path.exists() and path.read_text()==text else 1)
path.write_text(text)
print(f'{len(rows)} targets; {sum(e["status"]=="partial" for e in rows)} partial implementations; {sum(e["coverage"]["full_parity"] for e in rows)} full-parity releases')
