"""Native tables and static stacked bars for the validated independent categorical core."""
from cpj_barstats import bar_core
from cpj_estimation_adapter import _numeric
from cpj_identity import audit
from cpj_runtime import InputError,md_escape

DEFAULTS=dict(resultssubtitle=False,showCells=True,showCases=False,showPlot=True)
ALLOWED=set(DEFAULTS)|{'dep','group','counts','subject','barScale','label','digitsperc',
    'typestatistics','paired','showConsole'}


def run(data,options,out):
    unknown=set(options)-ALLOWED
    if unknown:raise InputError('Unsupported options in this partial bar core: '+', '.join(sorted(unknown))+'.')
    if options.get('typestatistics','parametric')!='parametric' or options.get('paired',False) is not False:
        raise InputError('This core supports independent frequentist comparisons only; paired and Bayesian analyses are unavailable.')
    flags={key:options.get(key,value) for key,value in DEFAULTS.items()}
    if any(not isinstance(v,bool) for v in flags.values()):raise InputError('Enable or disable each output explicitly.')
    names=options.get('dep') or []
    if not isinstance(names,(list,tuple)) or len(names)!=1:raise InputError('Choose exactly one categorical outcome.')
    outcome,group,counts,subject=names[0],options.get('group'),options.get('counts'),options.get('subject')
    roles=[outcome,group]+([counts] if counts else [])+([subject] if subject else [])
    if any(not isinstance(k,str) or k not in data for k in roles) or len(set(roles))!=len(roles):
        raise InputError('Select available distinct columns for outcome, group, optional frequency and subject roles.')
    if counts and subject:raise InputError('Subject-ID auditing is unavailable for aggregated frequency rows.')
    scale=options.get('barScale','percentage');label=options.get('label','percentage');digits=options.get('digitsperc',0)
    if scale not in ('percentage','count') or label not in ('percentage','counts','both'):
        raise InputError('Choose a supported bar scale and segment label.')
    if isinstance(digits,bool) or not isinstance(digits,int) or not 0<=digits<=2:
        raise InputError('Percentage labels require 0–2 decimal places.')
    n=len(data[outcome].codes) if hasattr(data[outcome],'codes') else 0
    identity=audit(data,subject,n) if subject else None
    ids=identity['values'] if identity else None
    result=bar_core(data[outcome],data[group],weights=_numeric(data,counts) if counts else None,
                    inference=flags['resultssubtitle'],subject_ids=ids)
    out.row('cohort',source=result['n_source'],complete=result['n_complete'],excluded=result['excluded_missing'],
        zero=result['zero_frequency'],contributing=result['n_contributing'],total=result['n_total'])
    out.note('cohort','Complete rows can have zero frequency. Positive complete rows contribute; total N is the sum of their frequencies, not the number of aggregated rows.')
    for role,key,name in [('Outcome','missing_outcome',outcome),('Group','missing_group',group)]+(
            [('Frequency','missing_frequency',counts)] if counts else []):
        out.row('missing',role=role,variable=name,missing=result[key])
    out.note('missing','Missing-by-role counts overlap; excluded rows count their union. Actual missing levels are excluded, while a literal NA label is a category.')
    for g in result['group_codes']:
        cells=[c for c in result['cells'] if c['group']==g]
        out.row('groups',group=result['group_labels'][g],total=cells[0]['group_total'])
    if flags['showCells']:
        for c in result['cells']:
            out.row('cells',outcome=result['outcome_labels'][c['outcome']],group=result['group_labels'][c['group']],
                **{k:c[k] for k in ('count','expected','group_total','group_proportion','overall_proportion')})
        out.note('cells','Within-group proportion = cell count / complete-data group total; overall proportion = cell count / total N. Zero cells remain in the full active grid.')
    for role,codes,labels in [('Outcome',result['dropped_outcome_codes'],result['outcome_labels']),
                              ('Group',result['dropped_group_codes'],result['group_labels'])]:
        for code in codes:out.row('dropped',role=role,code=code,label=labels[code],reason='Actual missing level' if labels[code] is None else 'Unused or zero complete margin')
    association=result['association']
    if flags['resultssubtitle']:
        fisher=association['primary_method']=='fisher_exact'
        out.row('association',method='Fisher exact (two-sided)' if fisher else 'Pearson chi-square',
                p=association['primary_p'],status='exact' if fisher else 'approximation')
        out.row('pearson',statistic=association['pearson_statistic'],df=association['df'],p=association['pearson_p'])
        out.note('pearson','Uncorrected Pearson audit; when Fisher is primary, do not attach this statistic or df to the Fisher p-value.')
        out.row('effects',raw=association['cramers_v_raw'],corrected=association['cramers_v_corrected'],
            status=association['corrected_unavailable_reason'] or 'points_only')
        out.note('effects','Both points use the uncorrected Pearson statistic. The corrected point uses the Bergsma finite-sample correction. No confidence intervals, effect-size tests or interpretation bands are supplied.')
        if association['sparse_warning']:
            out.warn('Some expected counts are below 5 in a table larger than 2×2. Pearson inference is approximate; no larger exact or Monte Carlo replacement is supplied.')
        if fisher:out.info('Sparse 2×2 expected counts: the primary result is two-sided Fisher exact. Pearson and effect points are separately labelled audit quantities.')
        if association['corrected_unavailable_reason']:
            out.warn('The corrected effect denominator is nonpositive; that point is unavailable. No replacement value was manufactured.')
    if flags['showCases']:
        row_ids=list(out.row_ids) if out.row_ids is not None else [str(i+1) for i in range(n)]
        for j,i in enumerate(result['retained_indices'][:1000]):
            out.row('cases',sourceID=row_ids[i],subjectID=result['retained_subject_ids'][j] if ids else None,
                outcome=data[outcome].levels[int(data[outcome].codes[i])],group=data[group].levels[int(data[group].codes[i])],
                frequency=data[counts][i] if counts else 1)
        if result['n_contributing']>1000:out.note('cases','Only the first 1,000 contributing source rows are displayed; all positive complete rows contribute to calculation.')
    if flags['showPlot']:
        rows=[]
        for c in result['geometry'][scale]:
            percent=f'{100*c["group_proportion"]:.{digits}f}%';count=f'{c["count"]:,}'
            annotation=(percent if label=='percentage' else count if label=='counts' else count+'\n('+percent+')') if c['count'] else None
            rows.append(dict(group=result['group_labels'][c['group']],outcome=result['outcome_labels'][c['outcome']],
                x=c['x'],lower=c['lower'],upper=c['upper'],scale=scale,annotation=annotation))
        out.plot('barPlot',rows,xlab=group,ylab='Within-group percentage' if scale=='percentage' else 'Frequency count')
    out.markdown('summary',md_escape(f'{result["n_contributing"]} contributing source rows; total frequency N={result["n_total"]}. '
        'Independent observations are required; aggregated frequencies represent observation counts, not survey weights or repeated-patient inference. '
        +('Supplied contributing subject IDs are known and unique, which does not establish independence. ' if subject else '')
        +('The 100% scale has equal total bar heights by design; segment heights use within-group denominators. ' if scale=='percentage' else 'The count scale shows unequal group totals directly. ')
        +('Association results are in native tables. ' if flags['resultssubtitle'] else 'Association results are off; no test or effect points were computed. ')
        +'Unused/zero-margin levels are audited and removed. This partial core omits confidence intervals, paired/Bayesian models, split/multiple outcomes, per-bar proportion tests, clinical presets, balloon plots and interactive inspection.'))
