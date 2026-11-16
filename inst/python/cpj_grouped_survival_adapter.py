"""Labelled role mapping and bounded native presentation for grouped survival."""
import json
import math
from numbers import Real

import numpy as np

from cpj_barstats import _factor
from cpj_estimation_adapter import _numeric
from cpj_identity import audit
from cpj_kaplan_meier_adapter import _queries
from cpj_grouped_survival import grouped_survival_core
from cpj_runtime import InputError, md_escape


def run(data, options, out):
    allowed={'elapsedtime','outcome','explanatory','subject','outcomeLevel','censorLevel',
        'timetypeoutput','cutp','ciWidth','showSteps','showCases','showExplanations',
        'sc','ci95','censored','timefix','showConsole'}
    if set(options)-allowed:raise InputError('Unsupported options for this grouped right-censored core.')
    time,outcome,group,subject=(options.get(k) for k in ('elapsedtime','outcome','explanatory','subject'))
    roles=[time,outcome,group]+([subject] if subject else [])
    if any(not isinstance(k,str) or k not in data for k in roles) or len(set(roles))!=len(roles):
        raise InputError('Select distinct available time, outcome, group and optional subject-ID columns.')
    flags={k:options.get(k,False) for k in ('showSteps','showCases','showExplanations','sc','ci95','censored')}
    if any(not isinstance(v,bool) for v in flags.values()):raise InputError('Enable or disable each output explicitly.')
    width=options.get('ciWidth',95)
    if not isinstance(width,Real) or isinstance(width,bool) or not math.isfinite(width) or not 50<=width<=99.9:
        raise InputError('Confidence level must be between 50 and 99.9 percent.')
    codes,labels=_factor(data[outcome],'Outcome')
    event,censor=options.get('outcomeLevel'),options.get('censorLevel')
    if any(not isinstance(v,str) or v not in labels for v in (event,censor)) or event==censor:
        raise InputError('Select distinct explicit event and censoring levels from the outcome.')
    ec,cc=labels.index(event),labels.index(censor)
    if np.any((codes>=0)&~np.isin(codes,[ec,cc])):
        raise InputError('An observed outcome is neither the selected event nor censoring level. Competing events require a different analysis.')
    binary=np.full(len(codes),np.nan);binary[codes==ec]=1;binary[codes==cc]=0
    raw=_numeric(data,time)
    identity=audit(data,subject,len(raw)) if subject else None
    r=grouped_survival_core(raw,binary,data[group],queries=_queries(options.get('cutp','12, 36, 60')),
        confidence=width/100,timefix=options.get('timefix',True),unit=options.get('timetypeoutput','months'),
        subject_ids=identity['values'] if identity else None)
    unit=r['unit'];groups=r['groups'];test=r['logrank']
    out.row('cohort',source=r['n_source'],complete=r['n_complete'],excluded=r['excluded_missing'],
        groups=len(groups),events=r['events'],censored=r['censored'],normalized=r['timefix_changed_rows'])
    out.row('mapping',variable=outcome,event=event,censor=censor,unit=unit,
        origin='Origin of supplied elapsed times',groupVariable=group)
    out.note('mapping','Units are declarations, not conversions. Only the two selected outcome levels may be observed. One record per independent subject; independent right censoring within groups is assumed.')
    for role,variable,key in [('Elapsed time',time,'missing_time'),('Outcome',outcome,'missing_event'),('Group',group,'missing_group')]:
        out.row('missing',role=role,variable=variable,missing=r[key])
    out.note('missing','Role counts overlap. Complete cases use the common time/outcome/group cohort; genuine missing levels are excluded, while literal NA labels remain categories.')
    steps=0;omitted=[]
    for g in groups:
        out.row('groups',group=g['label'],n=g['n'],events=g['events'],censored=g['censored'],
            maximum=g['maximum'],effective=g['effective_maximum'],normalized=g['normalized'])
        m=g['median']
        out.row('medians',group=g['label'],estimate=m['estimate'],lower=m['lower'],upper=m['upper'],
            confidence=r['confidence'],unit=unit,status='Available' if m['estimate'] is not None else 'Not reached / not estimable')
        for p in g['selected']:
            out.row('selectedTimes',group=g['label'],time=p['time'],unit=unit,risk=p['n_risk'],events=p['events'],
                censored=p['censored'],cumEvents=p['cumulative_events'],cumCensored=p['cumulative_censored'],
                survival=p['survival'],lower=p['lower'],upper=p['upper'],status=p['status'])
        if g['omitted_timepoints']:omitted.append(g['label']+': '+', '.join(f'{v:g}' for v in g['omitted_timepoints']))
        if flags['showSteps']:
            for p in g['curve'][:max(0,1000-steps)]:
                out.row('steps',group=g['label'],time=p['time'],risk=p['n_risk'],events=p['events'],
                    censored=p['censored'],survival=p['survival'],se=p['se'],lower=p['lower'],upper=p['upper']);steps+=1
    out.note('medians','Summary.survfit midpoint convention at a half-survival plateau. Limits invert pointwise log bands. Unreached medians or limits stay blank; a plateau does not establish cure.')
    out.note('selectedTimes','Post-event estimates at ties. At risk is immediately before the requested time; interval counts start after the preceding requested time. Every horizon beyond that group’s raw maximum is omitted, including terminal zero curves. Limits at survival 1 are [1,1]; at 0 they remain blank.')
    if omitted:out.info('Requested times beyond group follow-up omitted ('+unit+'): '+'; '.join(omitted)+'.')
    if r['inactive_codes']:
        _,gl=_factor(data[group],'Groups')
        out.note('groups','Unused declared levels excluded from inference: '+', '.join(gl[i] for i in r['inactive_codes'])+'.')
    out.row('logrank',method='Unweighted log-rank (rho = 0)',statistic=test['statistic'],df=test['df'],p=test['p'],status=test['status'])
    out.note('logrank','Asymptotic overall comparison of independent groups; finite-population covariance handles event ties. No pairwise comparisons, multiplicity adjustment, weights, stratification or proportional-hazards diagnostics are provided.')
    if test['status']!='available':out.info('Overall log-rank test unavailable: '+test['status'].removeprefix('unavailable_').replace('_',' ')+'. Group survival estimates are retained; no regularization or continuity correction is substituted.')
    for i,g in enumerate(groups):
        out.row('logrankGroups',group=g['label'],observed=test['observed'][i],expected=test['expected'][i],
            score=test['score'][i],eligible='Yes' if g['code'] in test['eligible_codes'] else 'No')
        if flags['showSteps']:
            for j,h in enumerate(groups):out.row('covariance',rowGroup=g['label'],columnGroup=h['label'],value=test['variance'][i][j])
    if flags['showSteps']:
        shown=0
        for point in test['trace']:
            for i,g in enumerate(groups):
                if shown>=1000:break
                out.row('riskSets',time=point['time'],group=g['label'],risk=point['group_risk'][i],
                    events=point['group_events'][i],expected=point['group_expected'][i],
                    totalRisk=point['n_risk'],totalEvents=point['events']);shown+=1
            if shown>=1000:break
        if len(test['trace'])*len(groups)>1000 or test['trace_truncated']:
            out.note('riskSets','First 1,000 group rows at pooled event times shown. All event times contribute to the overall test; no inference uses this display truncation.')
    if flags['showSteps'] and sum(len(g['curve']) for g in groups)>1000:
        out.note('steps','First 1,000 effective group times shown in declared group order. All complete observations contribute to every calculation.')
    if flags['showCases']:
        ids=list(out.row_ids) if out.row_ids is not None else [str(i+1) for i in range(len(raw))]
        lookup={i:g['label'] for g in groups for i in g['source_indices']}
        for j,i in enumerate(r['retained_indices'][:1000]):
            out.row('cases',group=lookup[i],sourceID=ids[i],subjectID=r['retained_subject_ids'][j] if identity else None,
                rawTime=raw[i],effectiveTime=r['effective_times'][j],status=labels[int(codes[i])],event=int(binary[i]))
        if r['n_complete']>1000:out.note('cases','First 1,000 retained source rows shown; all complete cases contribute.')
    if r['timefix_changed_rows']:out.info('Near-equal times were normalized globally on the complete cohort using the R survival convention before group risk sets were constructed.')
    chart='off'
    if flags['sc']:
        if sum(len(g['curve']) for g in groups)>5000:
            chart='omitted (more than 5,000 group times)'
            out.warn('The static chart is omitted above 5,000 effective group times. Tables and inference use all retained cases; no sampling was performed.')
        else:
            shorten=lambda s:s if len(s)<=120 else s[:117]+'...'
            payload=dict(schema_version=1,unit=unit,event_label=shorten(event),
                label_shortened=len(event)>120 or any(len(g['label'])>120 for g in groups),
                n=r['n_complete'],confidence=r['confidence'],maximum=max(g['maximum'] for g in groups),
                show_ci=flags['ci95'],show_censors=flags['censored'],confidence_method='log',
                series=[dict(code=g['code'],label=shorten(g['label']),n=g['n'],maximum=g['maximum'],
                    points=[{k:p[k] for k in ('time','n_risk','events','censored','survival','lower','upper')} for p in g['curve']]) for g in groups])
            encoded=json.dumps(payload,allow_nan=False)
            if len(encoded)>2000000:raise InputError('The bounded grouped survival drawing payload exceeds 2 MB; disable the plot.')
            out.plot('survivalPlot',[dict(payload=encoded)]);chart='on'
    if flags['showExplanations']:
        out.markdown('explanation','Independent subjects and independent right censoring within groups are assumed. Greenwood log limits are pointwise, not simultaneous bands. Global log-rank compares entire curves and does not establish proportional hazards or causality. Censor marks denote distinct times, not counts. Sparse events can limit asymptotic inference; inspect observed and expected group counts. No repeated-patient inference is performed.')
    out.markdown('summary',md_escape(f'{r["n_complete"]} complete subjects in {len(groups)} active groups; {r["events"]} events and {r["censored"]} censored. Event: {event}; censored: {censor}. Declared unit: {unit}; no conversion. Static chart: {chart}. Original source IDs preserved. Weighted/pairwise tests, Cox models, PH diagnostics, RMST, dates, landmarking, delayed entry, competing risks, weights and interactive exploration are omitted.'))
