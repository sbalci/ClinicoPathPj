"""Explicit labelled event mapping and native single-cohort survival presentation."""
import json
import math
from numbers import Real

import numpy as np

from cpj_barstats import _factor
from cpj_estimation_adapter import _numeric
from cpj_identity import audit
from cpj_kaplan_meier import kaplan_meier_core
from cpj_runtime import InputError, md_escape


def _queries(text):
    if not isinstance(text,str) or len(text)>10000:
        raise InputError('Supply up to 200 requested times as comma-separated numbers.')
    if not text.strip():return []
    tokens=text.split(',')
    if len(tokens)>200 or any(not t.strip() for t in tokens):
        raise InputError('Supply up to 200 times without empty comma-separated entries.')
    try:return [float(t.strip()) for t in tokens]
    except ValueError:
        raise InputError('Requested times must be numbers, not labels or executable expressions.') from None


def run(data, options, out):
    allowed={'elapsedtime','outcome','subject','outcomeLevel','censorLevel','timetypeoutput','cutp',
        'ciWidth','showFollowup','person_time','showSteps','showCases','showExplanations',
        'sc','ci95','censored','timefix','showConsole'}
    if set(options)-allowed:
        raise InputError('Unsupported options for this right-censored single-cohort core.')
    time,outcome,subject=(options.get(k) for k in ('elapsedtime','outcome','subject'))
    roles=[time,outcome]+([subject] if subject else [])
    if any(not isinstance(k,str) or k not in data for k in roles) or len(set(roles))!=len(roles):
        raise InputError('Select distinct available time, outcome and optional subject-ID columns.')
    flags={k:options.get(k,k=='showFollowup') for k in
        ('showFollowup','person_time','showSteps','showCases','showExplanations','sc','ci95','censored')}
    if any(not isinstance(v,bool) for v in flags.values()):
        raise InputError('Enable or disable each output explicitly.')
    width=options.get('ciWidth',95)
    if not isinstance(width,Real) or isinstance(width,bool) or not math.isfinite(width) or not 50<=width<=99.9:
        raise InputError('Confidence level must be between 50 and 99.9 percent.')
    codes,labels=_factor(data[outcome],'Outcome')
    event,censor=options.get('outcomeLevel'),options.get('censorLevel')
    if any(not isinstance(v,str) or v not in labels for v in (event,censor)) or event==censor:
        raise InputError('Select distinct explicit event and censoring levels from the outcome.')
    event_code,censor_code=labels.index(event),labels.index(censor)
    if np.any((codes>=0)&~np.isin(codes,[event_code,censor_code])):
        raise InputError('An observed outcome is neither the selected event nor censoring level. Competing events require a different analysis.')
    binary=np.full(len(codes),np.nan)
    binary[codes==event_code]=1;binary[codes==censor_code]=0
    raw=_numeric(data,time)
    identity=audit(data,subject,len(raw)) if subject else None
    r=kaplan_meier_core(raw,binary,queries=_queries(options.get('cutp','12, 36, 60')),
        confidence=width/100,timefix=options.get('timefix',True),
        unit=options.get('timetypeoutput','months'),subject_ids=identity['values'] if identity else None)
    unit=r['unit']
    out.row('cohort',source=r['n_source'],complete=r['n_complete'],excluded=r['excluded_missing'],
        events=r['events'],censored=r['censored'],normalized=r['timefix_changed_rows'])
    out.row('mapping',variable=outcome,event=event,censor=censor,unit=unit,
        origin='Origin of supplied elapsed times',maximum=r['max_time'],effective=r['effective_max_time'])
    out.note('mapping','Units are declarations, not conversions. Only the two selected outcome levels may be observed; genuine missing levels are excluded, while literal NA labels remain valid categories.')
    for role,variable,key in [('Elapsed time',time,'missing_time'),('Outcome',outcome,'missing_event')]:
        out.row('missing',role=role,variable=variable,missing=r[key])
    out.note('missing','Role counts overlap; excluded rows count the union of missing time/outcome pairs.')
    for basis,m in [('Event-free survival',r['median'])]+([('Reverse-KM follow-up',r['reverse']['median'])] if flags['showFollowup'] else []):
        out.row('medians',basis=basis,estimate=m['estimate'],lower=m['lower'],upper=m['upper'],
            confidence=r['confidence'],unit=unit,status='Available' if m['estimate'] is not None else 'Not reached / not estimable')
    out.note('medians','Summary.survfit midpoint convention at a half-survival plateau; confidence limits invert its pointwise log-log band. Unreached limits stay blank. Reverse KM treats original censoring as the event; no observed-time median is substituted.')
    for p in r['selected']:
        out.row('selectedTimes',time=p['time'],unit=unit,risk=p['n_risk'],events=p['events'],
            censored=p['censored'],cumEvents=p['cumulative_events'],cumCensored=p['cumulative_censored'],
            survival=p['survival'],lower=p['lower'],upper=p['upper'],status=p['status'])
    out.note('selectedTimes','Post-event estimate at a tied time. At risk is immediately before that time; interval counts are since the preceding requested time, not cumulative. Limits are pointwise and blank at 0%/100%. Times beyond follow-up are omitted unless survival has reached zero.')
    if r['omitted_timepoints']:
        out.info('Requested times outside observed follow-up were omitted: '+', '.join(f'{v:g}' for v in r['omitted_timepoints'])+' '+unit+'. No positive survival plateau was extrapolated.')
    if flags['person_time']:
        rate=r['rate']
        out.row('personTime',events=rate['events'],exposure=rate['person_time'],estimate=rate['estimate'],
            lower=rate['lower'],upper=rate['upper'],unit=unit,status=rate['status'])
        out.note('personTime','Events per one declared unit of raw observation time. Exact two-sided Poisson count interval assumes a Poisson model conditional on the supplied exposure; KM does not validate that model. This is not a survival probability or fitted hazard.')
        if rate['status']!='available':out.info('Person-time rate is unavailable because exposure is zero or its rate interval exceeds the numeric range; survival estimates are retained.')
    if flags['showSteps']:
        for p in r['curve'][:1000]:
            out.row('steps',time=p['time'],risk=p['n_risk'],events=p['events'],censored=p['censored'],
                survival=p['survival'],se=p['se'],lower=p['lower'],upper=p['upper'])
        if len(r['curve'])>1000:out.note('steps','First 1,000 distinct effective times shown; all retained observations contribute to estimates.')
    if flags['showCases']:
        ids=list(out.row_ids) if out.row_ids is not None else [str(i+1) for i in range(len(raw))]
        for j,i in enumerate(r['retained_indices'][:1000]):
            out.row('cases',sourceID=ids[i],subjectID=r['retained_subject_ids'][j] if identity else None,
                rawTime=raw[i],effectiveTime=r['effective_times'][j],status=labels[int(codes[i])],event=int(binary[i]))
        if r['n_complete']>1000:out.note('cases','First 1,000 retained source rows shown; all complete pairs contribute.')
    if r['timefix_changed_rows']:
        out.info('Near-equal times were normalized using the R survival convention. Effective times and risk sets may differ from raw times; person-time still sums raw observations.')
    chart='off'
    if flags['sc']:
        if len(r['curve'])>5000:
            chart='omitted (more than 5,000 distinct times)'
            out.warn('The static chart is omitted above 5,000 distinct effective times. Tables and estimates use all retained cases; no display sampling was performed.')
        else:
            short=event if len(event)<=120 else event[:117]+'...'
            payload=dict(schema_version=1,unit=unit,event_label=short,label_shortened=short!=event,
                n=r['n_complete'],confidence=r['confidence'],maximum=r['max_time'],
                show_ci=flags['ci95'],show_censors=flags['censored'],
                points=[{k:p[k] for k in ('time','n_risk','events','censored','survival','lower','upper')} for p in r['curve']])
            encoded=json.dumps(payload,allow_nan=False)
            if len(encoded)>2000000:raise InputError('The bounded survival drawing payload exceeds 2 MB; disable the plot.')
            out.plot('survivalPlot',[dict(payload=encoded)]);chart='on'
    if flags['showExplanations']:
        out.markdown('explanation','Independent subjects and independent right censoring are assumed. Greenwood log-log limits are pointwise, not simultaneous bands. Limits at zero/one are blank. A late plateau or unreached median does not establish cure or good outcomes. Reverse KM describes follow-up; person-time rates use a separate Poisson count model. Censor ticks indicate distinct times, not individual counts. No repeated-subject or competing-risk inference is performed.')
    out.markdown('summary',md_escape(f'{r["n_complete"]} complete pairs; {r["events"]} events and {r["censored"]} censored. '
        f'Event: {event}; censored: {censor}. Elapsed times are declared in {unit}; no unit conversion. '
        f'Static chart: {chart}. Original source IDs are preserved. '
        'Dates, landmarking, delayed entry, competing risks, weights, RMST, regression and interactive exploration are omitted.'))
