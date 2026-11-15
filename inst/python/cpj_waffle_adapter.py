"""Native tables and bounded drawing state for descriptive waffle charts."""
import json

from cpj_estimation_adapter import _numeric
from cpj_identity import audit
from cpj_runtime import InputError, md_escape
from cpj_waffle import waffle_core


def run(data, options, out):
    allowed = {'groups','counts','facet','subject','rows','flip','showPlot','show_legend',
               'showCases','showExplanations','mytitle','legendtitle','showConsole'}
    if set(options)-allowed:
        raise InputError('Unsupported options for the bounded waffle core.')
    group, counts, facet, subject = (options.get(k) for k in ('groups','counts','facet','subject'))
    roles = [group]+[v for v in (counts,facet,subject) if v]
    if any(not isinstance(v,str) or v not in data for v in roles) or len(set(roles))!=len(roles):
        raise InputError('Select available distinct category, frequency, panel and subject columns.')
    for key in ('showPlot','show_legend','showCases','showExplanations'):
        if not isinstance(options.get(key,key=='showPlot'),bool):
            raise InputError('Enable or disable each output explicitly.')
    titles = [options.get(key,'') for key in ('mytitle','legendtitle')]
    if any(not isinstance(v,str) or len(v)>200 for v in titles):
        raise InputError('Plot and legend titles must be text of at most 200 characters.')
    n = len(data[group].codes) if hasattr(data[group],'codes') else 0
    identity = audit(data,subject,n) if subject else None
    result = waffle_core(data[group],weights=_numeric(data,counts) if counts else None,
        facet=data[facet] if facet else None,rows=options.get('rows',5),flip=options.get('flip',False),
        subject_ids=identity['values'] if identity else None)
    out.row('cohort',source=result['n_source'],complete=result['n_complete'],
        excluded=result['excluded_missing'],zero=result['zero_frequency'],
        contributing=result['n_contributing'],total=result['n_total'])
    out.note('cohort','Complete rows include zero frequencies; N sums positive complete observation frequencies, not aggregated source rows.')
    for role,variable,key in [('Categories',group,'missing_group'),('Frequency',counts,'missing_frequency'),
                              ('Panels',facet,'missing_facet')]:
        if variable:out.row('missing',role=role,variable=variable,missing=result[key])
    out.note('missing','Role counts overlap. Excluded rows count their union. Literal NA labels remain categories; genuine missing factor levels are excluded.')
    for panel in result['panels']:
        out.row('panels',panel=panel['label'],total=panel['n_total'],
            sourceRows=len(panel['retained_indices']),tiles=100,status='Active')
        for cell in panel['cells']:
            out.row('allocation',panel=panel['label'],category=cell['label'],count=cell['count'],
                denominator=panel['n_total'],proportion=cell['proportion'],tiles=cell['tiles'],
                represented=cell['represented_proportion'],error=cell['allocation_error'],
                status='Positive count; no tile' if cell['omitted_positive'] else
                       'Zero count' if not cell['count'] else 'Represented')
    for code in result['inactive_facet_codes']:
        out.row('panels',panel=data[facet].levels[code],total=0,sourceRows=0,tiles=0,
            status='No positive complete frequency')
    out.note('panels','Each active panel has its own denominator and 100 tiles. Equal-size grids do not imply equal sample sizes. Inactive declared panels are not drawn.')
    out.note('allocation','One tile represents 1% of its own panel after rounding. Exact counts and proportions remain available for unused and rare categories. Allocation error is tile proportion minus exact proportion (multiply by 100 for percentage points).')
    if any(c['omitted_positive'] for p in result['panels'] for c in p['cells']):
        out.warn('Some positive categories receive no tiles after rounding. Consult exact counts and proportions in the allocation table.')
    if options.get('showCases',False):
        source_ids = list(out.row_ids) if out.row_ids is not None else [str(i+1) for i in range(n)]
        for j,i in enumerate(result['retained_indices'][:1000]):
            out.row('cases',sourceID=source_ids[i],subjectID=result['retained_subject_ids'][j] if identity else None,
                category=data[group].levels[int(data[group].codes[i])],
                panel=data[facet].levels[int(data[facet].codes[i])] if facet else 'All observations',
                frequency=data[counts][i] if counts else 1)
        if result['n_contributing']>1000:
            out.note('cases','First 1,000 contributing rows shown; every positive complete row contributes to the calculation.')
    if options.get('showExplanations',False):
        out.markdown('explanation','Exact integer largest remainders allocate 100 tiles per panel; later declared categories win tied remainders. This avoids the floating-point tile truncation observed in waffle 1.0.2. No inferential test or clinical classification is supplied.')
    if options.get('showPlot',True):
        payload = dict(schema_version=1,rows=result['rows'],flip=result['flip'],
            panels=[{k:v for k,v in p.items() if k!='retained_indices'} for p in result['panels']],
            legend=options.get('show_legend',False),title=titles[0],legend_title=titles[1])
        encoded = json.dumps(payload,allow_nan=False)
        if len(encoded)>1000000:
            raise InputError('Waffle drawing payload exceeds 1 MB; shorten category/panel labels or disable the chart.')
        out.plot('wafflePlot',[dict(payload=encoded)])
    out.markdown('summary',md_escape(f'{result["n_contributing"]} contributing source rows; frequency N={result["n_total"]}. '
        'Each active panel represents its own denominator with 100 rounded tiles. Frequencies are integer observation counts, not survey weights. '
        +'Exact tables retain rare and zero categories. '
        +('Known unique subject IDs were checked; this does not establish independent observations. ' if identity else '')
        +'Fractional weights, interactive inspection, palette presets and inferential/clinical interpretation are omitted.'))
