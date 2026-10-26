"""Bounded native SVG markup with a complete initial graphic and local lookup payload."""
import html
import json
import math
from cpj_runtime import InputError
from cpj_cutoff import select


def svg_document(p):
    def esc(value):
        return html.escape(str(value), quote=True)

    values = [r['value'] for r in p['rows']]
    lo, hi = min(values + [p['initial'], p['automatic']]), max(values + [p['initial'], p['automatic']])
    span = max(hi - lo, abs(lo) * .1, 1)
    domain = [lo - .08 * span, hi + .08 * span]
    if not all(math.isfinite(v) for v in domain) or not math.isfinite(domain[1] - domain[0]):
        raise InputError('Measurement range is too extreme for the SVG preview.')
    p = dict(p, domain=domain)
    point = select(p['curves'][p['direction']]['points'], p['initial'], p['direction'])
    def y(v):
        return 475 - (v-domain[0]) / (domain[1]-domain[0]) * 340
    def text(x, yy, value, cls='', extra=''):
        return f'<text x="{x}" y="{yy}" class="{cls}" {extra}>{esc(value)}</text>'
    counts = lambda c: f"TP {c['tp']} · FP {c['fp']} · FN {c['fn']} · TN {c['tn']}"
    rule = '≥' if p['direction'] == 'ge' else '≤'
    parts = ['<div class="cpj-svg-cutoff">',
             '<p>Display-only preview. Drag the line, use its arrow keys, edit the numeric field, or select a ROC point. Native tables use saved jamovi options.</p>',
             f'<label>Preview cutoff <input class="cutoff-input" type="number" step="any" value="{p["initial"]!r}" /></label> ',
             '<button type="button" class="automatic">Automatic cutoff</button> ',
             '<button type="button" class="apply">Apply to SVG snapshot</button> ',
             '<button type="button" class="reset">Reset to native rule</button>',
             '<span class="feedback" role="status" aria-live="polite"></span>',
             f'<svg xmlns="http://www.w3.org/2000/svg" width="980" height="650" viewBox="0 0 980 650" class="jmv-results-svg-content" role="img" aria-label="Linked measurements and empirical ROC" data-payload="{esc(json.dumps(p, allow_nan=False, ensure_ascii=True))}">',
             '<style>text{font:14px system-ui,sans-serif;fill:#202b38}.title{font-size:20px;font-weight:600}.small{font-size:12px}.axis{stroke:#667;fill:none}.curve{stroke:#3975b8;stroke-width:2;fill:none}.roc-point{fill:#3975b8;cursor:pointer}.roc-point:focus{stroke:#111;stroke-width:3}.handle{cursor:ns-resize;stroke:transparent;stroke-width:22}.handle:focus{stroke:#3975b844}.cut-line{stroke:#bf4d29;stroke-width:2;stroke-dasharray:6 4}.paper{fill:white}.cut-label{font-weight:600}</style>',
             '<rect class="paper" width="980" height="650" />',
             text(30,32,'Native SVG cutoff lab','title'),
             text(30,57,f"N = {len(values)}; excluded = {p['excluded']}; Python threshold-state lookup",'small'),
             text(30,82,f"Native applied rule: {p['measurement']} {rule} {p['initial']!r}",'native-rule'),
             text(30,108,'Measurements by reference group'), text(535,108,'Empirical ROC'),
             '<path class="axis" d="M65 135V475H455 M535 135V475H935" />',
             '<path stroke="#aaa" stroke-dasharray="4 4" d="M535 475L935 135" fill="none" />']
    for i in range(6):
        value=domain[0]+i/5*(domain[1]-domain[0]); yy=y(value)
        parts += [text(58,yy+4,f'{value:.4g}','small','text-anchor="end"')]
        yy=475-i/5*340;xx=535+i/5*400
        parts += [text(528,yy+4,f'{i/5:.1f}','small','text-anchor="end"'),text(xx,495,f'{i/5:.1f}','small','text-anchor="middle"')]
    parts += [text(165,498,p['negative'],'small','text-anchor="middle"'),text(355,498,p['positive'],'small','text-anchor="middle"'),text(735,520,'False positive rate','small','text-anchor="middle"'),text(30,125,p['measurement'],'small')]
    for i,r in enumerate(p['rows']):
        xx=(355 if r['positive'] else 165)+((i*17%29)/28-.5)*55
        correct=(r['value']>=p['initial'] if p['direction']=='ge' else r['value']<=p['initial'])==r['positive']
        tip = esc("Original row {}: {!r}".format(r["row"], r["value"]))
        parts += [f'<circle class="observation" data-index="{i}" cx="{xx}" cy="{y(r["value"])}" r="4" fill="{"#3975b8" if correct else "#c25a2d"}"><title>{tip}</title></circle>']
    points=p['curves'][p['direction']]['points']
    parts += ['<path class="curve" d="'+' '.join(f'{"M" if i==0 else "L"}{535+c["fpr"]*400},{475-c["tpr"]*340}' for i,c in enumerate(sorted(points,key=lambda c:(c['fpr'],c['tpr']))))+'" />']
    for i,c in enumerate(points):
        parts += [f'<circle class="roc-point" data-point="{i}" cx="{535+c["fpr"]*400}" cy="{475-c["tpr"]*340}" r="3" tabindex="0" role="button" aria-label="Preview cutoff {c["cutoff"]!r}"><title>Cutoff {c["cutoff"]!r}</title></circle>']
    parts += [f'<circle class="operating" cx="{535+point["fpr"]*400}" cy="{475-point["tpr"]*340}" r="7" fill="#c25a2d" stroke="white" pointer-events="none" />',
              f'<line class="cut-line" x1="65" x2="455" y1="{y(p["initial"])}" y2="{y(p["initial"])}" />',
              f'<line class="handle" x1="65" x2="455" y1="{y(p["initial"])}" y2="{y(p["initial"])}" tabindex="0" role="slider" aria-label="Preview cutoff line" aria-valuemin="{domain[0]}" aria-valuemax="{domain[1]}" aria-valuenow="{p["initial"]}" />',
              text(30,550,f"Preview cutoff {p['initial']!r}: {counts(point)}",'preview cut-label'),
              text(30,578,f"Local snapshot cutoff {p['initial']!r}: {counts(point)}",'snapshot'),
              text(30,605,f"AUC {p['curves'][p['direction']]['auc']:.4g}; blue = correct, orange = classification error",'small'),
              text(30,629,'Export captures this displayed preview. Apply changes only the local snapshot; native options remain unchanged.','small'),
              '</svg></div>']
    content=''.join(parts)
    if len(content.encode())>1_500_000:
        raise InputError('The native SVG payload exceeds 1.5 MB. Filter to fewer observations.')
    return content
