"""Grouped right-censored KM/log-rank numerical engine; native presentation is separate."""
import math

import numpy as np
from scipy.stats import chi2

from cpj_barstats import _factor
from cpj_estimation import _confidence, _ids, _numeric
from cpj_kaplan_meier import _effective_times, _fit, _summarize_queries
from cpj_runtime import InputError


def _logrank(times, events, groups, active):
    """Unweighted pooled risk sets with finite-population tie covariance."""
    k=len(active)
    dense=np.searchsorted(active,groups)
    risk=np.bincount(dense,minlength=k).astype(np.int64)
    observed=np.bincount(dense,weights=events,minlength=k)
    expected=np.zeros(k);variance=np.zeros((k,k));trace=[];event_times=0
    order=np.argsort(times,kind='stable');ordered=times[order]
    grid,starts,totals=np.unique(ordered,return_index=True,return_counts=True)
    for at,start,total in zip(grid,starts,totals):
        ids=order[start:start+total]
        counts=np.bincount(dense[ids],minlength=k)
        deaths=np.bincount(dense[ids],weights=events[ids],minlength=k)
        d=int(deaths.sum());n=int(risk.sum())
        if d:
            probabilities=risk/n
            contribution=d*probabilities
            expected+=contribution
            if n>1:
                scale=d*(n-d)/(n-1)
                variance+=scale*(np.diag(probabilities)-np.outer(probabilities,probabilities))
            event_times+=1
            if len(trace)<1000:
                trace.append(dict(time=float(at),n_risk=n,events=d,group_risk=risk.tolist(),
                    group_events=deaths.astype(int).tolist(),group_expected=contribution.tolist()))
        # Event/censor ties share the risk set before both are removed.
        risk-=counts
    eligible=np.flatnonzero(expected>0)
    result=dict(method='logrank',rho=0,status='available',n_groups=k,
        observed=observed.tolist(),expected=expected.tolist(),score=(observed-expected).tolist(),
        variance=variance.tolist(),eligible_codes=[int(active[i]) for i in eligible],
        statistic=None,df=None,p=None,trace=trace,trace_truncated=max(0,event_times-1000))
    if k<2:result['status']='unavailable_one_group'
    elif int(events.sum())==0:result['status']='unavailable_no_events'
    elif len(eligible)<2:result['status']='unavailable_no_between_group_information'
    else:
        # One redundant contrast is removed, matching survdiff; no ridge or
        # pseudoinverse is substituted when the covariance cannot support a test.
        delta=(observed-expected)[eligible][1:]
        vv=variance[np.ix_(eligible,eligible)][1:,1:]
        try:statistic=float(delta @ np.linalg.solve(vv,delta))
        except np.linalg.LinAlgError:
            result['status']='unavailable_singular_variance'
        else:
            p=float(chi2.sf(statistic,len(eligible)-1))
            if not all(math.isfinite(x) for x in (statistic,p)) or statistic<0:
                result['status']='unavailable_numeric_range'
            else:result.update(statistic=statistic,df=len(eligible)-1,p=p)
    return result


def grouped_survival_core(time,event,group,*,queries=(),confidence=.95,timefix=True,
                          unit='months',subject_ids=None):
    """Common complete cases; explicit 0/1 event; declared factor order/units.

    Log-scale intervals and strict group-specific horizon support preserve the
    released grouped baseline. Single-cohort log-log behavior is not changed.
    """
    _confidence(confidence)
    if not isinstance(timefix,bool):raise InputError('Enable or disable near-tie normalization explicitly.')
    if not isinstance(unit,str) or unit not in ('days','weeks','months','years'):
        raise InputError('Declare one time unit: days, weeks, months or years.')
    t,e=_numeric(time,'Elapsed time'),_numeric(event,'Binary event indicator')
    codes,labels=_factor(group,'Groups')
    if len(t)!=len(e) or len(t)!=len(codes):raise InputError('Time, event and grouping roles must align.')
    if np.any(t[~np.isnan(t)]<0):raise InputError('Elapsed times must be nonnegative or missing.')
    if np.any(~np.isin(e[~np.isnan(e)],[0.,1.])):
        raise InputError('Explicitly code 0=censored and 1=event. Competing events require a different analysis.')
    if np.ma.isMaskedArray(queries):raise InputError('Requested times must be unmasked numeric values.')
    try:q=np.asarray(queries)
    except (TypeError,ValueError):raise InputError('Supply at most 200 finite nonnegative requested times.') from None
    if q.ndim!=1 or len(q)>200:raise InputError('Supply at most 200 finite nonnegative requested times.')
    q=_numeric(queries,'Requested times') if len(q) else np.array([],dtype=float)
    if np.any(np.isnan(q)) or np.any(q<0):raise InputError('Requested times must be finite and nonnegative.')
    q=np.unique(q)
    keep=~np.isnan(t)&~np.isnan(e)&(codes>=0)
    indices=np.flatnonzero(keep)
    if not len(indices):raise InputError('No complete time/event/group triples remain.')
    ids=_ids(subject_ids,len(t),keep)
    tt,ee,gc=t[keep],e[keep].astype(np.int64),codes[keep]
    active=np.unique(gc)
    if len(active)>20:raise InputError('The grouped survival core supports at most 20 retained groups.')
    # Both grouped KM and log-rank normalize the common cohort, not each group
    # separately: cross-group near ties can change event-time risk sets.
    effective=_effective_times(tt,timefix)
    groups=[]
    for code in active:
        members=np.flatnonzero(gc==code)
        curve,median,ordered=_fit(effective[members],ee[members],confidence,
            confidence_method='log',suppress_boundaries=False)
        selected,omitted=_summarize_queries(curve,ordered,float(tt[members].max()),q,
            extend_terminal_zero=False,initial_bounds=1.)
        groups.append(dict(code=int(code),label=labels[code],n=len(members),events=int(ee[members].sum()),
            censored=int(np.sum(1-ee[members])),source_indices=indices[members].tolist(),
            maximum=float(tt[members].max()),effective_maximum=float(effective[members].max()),
            normalized=int(np.sum(tt[members]!=effective[members])),curve=curve,median=median,
            selected=selected,omitted_timepoints=omitted))
    return dict(schema_version=1,status='ok',confidence=float(confidence),confidence_method='log',
        timefix=timefix,unit=unit,n_source=len(t),n_complete=len(indices),excluded_missing=int(np.sum(~keep)),
        missing_time=int(np.sum(np.isnan(t))),missing_event=int(np.sum(np.isnan(e))),
        missing_group=int(np.sum(codes<0)),retained_indices=indices.tolist(),retained_subject_ids=ids,
        active_codes=active.tolist(),inactive_codes=[i for i,v in enumerate(labels) if v is not None and i not in active],
        events=int(ee.sum()),censored=int(np.sum(1-ee)),timefix_changed_rows=int(np.sum(tt!=effective)),
        effective_times=effective.tolist(),groups=groups,logrank=_logrank(effective,ee,gc,active))
