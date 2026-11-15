"""Native lollipop presentation, using the independently validated core."""
from cpj_estimation_adapter import _numeric
from cpj_lollipop import lollipop_core
from cpj_runtime import InputError, md_escape


def run(data, options, out):
    allowed={'dep','group','aggregation','sortBy','orientation','baseline','showMean',
             'showValues','showPlot','showPoints','showCases','showConsole'}
    if set(options)-allowed:
        raise InputError('Unsupported lollipop options: '+', '.join(sorted(set(options)-allowed))+'.')
    dep,group=options.get('dep'),options.get('group')
    if any(not isinstance(k,str) or k not in data for k in (dep,group)) or dep==group:
        raise InputError('Select distinct available measurement and grouping columns.')
    flags={k:options.get(k,v) for k,v in [('showMean',False),('showValues',False),
        ('showPlot',True),('showPoints',True),('showCases',False)]}
    if any(not isinstance(v,bool) for v in flags.values()):
        raise InputError('Enable or disable each output explicitly.')
    r=lollipop_core(_numeric(data,dep),data[group],aggregation=options.get('aggregation','mean'),
        sorting=options.get('sortBy','original'),orientation=options.get('orientation','vertical'),
        baseline=options.get('baseline',0))
    out.row('cohort',source=r['n_source'],complete=r['n_complete'],excluded=r['excluded_missing'],
        groups=len(r['active_codes']),points=len(r['points']))
    out.row('missing',role='Measurement',variable=dep,missing=r['missing_values'])
    out.row('missing',role='Group',variable=group,missing=r['missing_group'])
    out.note('missing','Role counts overlap; excluded rows count their union. Genuine missing levels are excluded; literal NA labels remain categories.')
    for basis,key in [('Raw complete observations','raw_summary'),('Plotted values','plotted_summary')]:
        out.row('descriptives',basis=basis,**r[key])
    out.note('descriptives','Sample SD uses n - 1; quartiles use type 7. Under aggregation, the plotted mean is the unweighted mean of group values, not the grand mean. No intervals or hypothesis tests are supplied.')
    counts={c:0 for c in r['active_codes']}; membership={}
    for j,p in enumerate(r['points']):
        counts[p['code']]+=len(p['source_indices'])
        for i in p['source_indices']:membership[i]=(j+1,p)
        if flags['showPoints'] and j<1000:
            out.row('points',point=j+1,category=p['label'],value=p['value'],
                sourceRows=len(p['source_indices']),slot=p['slot'],baseline=p['stem_start'])
    for c,label in enumerate(data[group].levels):
        if label is not None:
            out.row('groups',category=label,sourceRows=counts.get(c,0),
                status='retained' if c in counts else 'no_complete_observations')
    if flags['showPoints'] and len(r['points'])>1000:
        out.note('points','Only the first 1,000 plotted values are listed; all points contribute and are drawn.')
    if flags['showCases']:
        ids=list(out.row_ids) if out.row_ids is not None else [str(i+1) for i in range(r['n_source'])]
        for i in r['retained_indices'][:1000]:
            j,p=membership[i]
            out.row('cases',sourceID=ids[i],category=p['label'],value=data[dep][i],point=j,plotted=p['value'])
        if r['n_complete']>1000:
            out.note('cases','Only the first 1,000 complete source rows are listed; all complete rows contribute.')
    if r['overplotting']:
        out.warn('Without aggregation, repeated categories share a stem position and points may overlap. Visible points do not show observation counts; consult source rows or choose aggregation.')
    if flags['showPlot']:
        horizontal=options.get('orientation','vertical')=='horizontal'
        out.plot('lollipopPlot',[dict(label=p['label'],slot=p['slot'],value=p['value'],baseline=p['stem_start'],
            orientation=options.get('orientation','vertical'),annotation=f'{p["value"]:.4g}' if flags['showValues'] else None)
            for p in r['points']],xlab=dep if horizontal else group,ylab=group if horizontal else dep,
            reference=r['reference_mean'] if flags['showMean'] else None)
    out.markdown('summary',md_escape(f'{r["n_complete"]} complete observations; {len(r["points"])} plotted values. '
        f'Aggregation: {options.get("aggregation","mean")}. The optional reference line is the mean of plotted values. '
        'Raw/plotted summaries and source membership are separate. Descriptive calculations do not establish independent patients or clinical importance. '
        'Alphabetic sorting uses Unicode order; infinities are rejected. Highlighting, conditional colors, inferential uncertainty and interactive inspection are omitted.'))
