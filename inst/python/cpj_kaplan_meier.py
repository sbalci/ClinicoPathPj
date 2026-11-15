"""Unweighted right-censored single-cohort survival; source-only numerical core."""
import math

import numpy as np
from scipy.stats import chi2, norm

from cpj_estimation import _confidence, _ids, _numeric
from cpj_runtime import InputError

TOLERANCE = math.sqrt(np.finfo(float).eps)


def _effective_times(times, enabled):
    if not enabled:
        return times.copy()
    values = np.unique(times)
    scale = math.fsum(float(v)/len(values) for v in values)
    differences = np.diff(values)
    tied = differences <= TOLERANCE
    if scale > 0:
        tied |= differences/scale <= TOLERANCE
    cuts = values[np.r_[True, ~tied]]
    return cuts[np.searchsorted(cuts, times, side='right')-1]


def _median(times, values):
    candidates = [(t,y) for t,y in zip(times,values) if y is not None and y < .5+TOLERANCE]
    if not candidates:
        return None
    first_time, first_value = candidates[0]
    if abs(first_value-.5) < TOLERANCE:
        later = next((t for t,y in candidates if y < first_value), None)
        if later is not None:
            return first_time/2 + later/2
    return first_time


def _fit(times, events, confidence):
    order = np.argsort(times, kind='stable')
    ordered = times[order]
    grid, starts, totals = np.unique(ordered, return_index=True, return_counts=True)
    deaths = np.add.reduceat(events[order], starts)
    risk = len(times)
    survival, greenwood = 1., 0.
    cumulative_events = cumulative_censored = 0
    z = float(norm.ppf((1+confidence)/2))
    curve, raw_lower, raw_upper = [], [], []
    for at, count, death in zip(grid, totals, deaths):
        at, count, death = float(at), int(count), int(death)
        censored = count-death
        cumulative_events += death
        cumulative_censored += censored
        survival *= (risk-death)/risk
        if death == risk:
            greenwood = None
            se = lo = hi = None
        else:
            greenwood += death/(risk*(risk-death))
            se = survival*math.sqrt(greenwood)
            if survival == 1:
                lo = hi = 1.
            else:
                log_hazard = math.log(-math.log(survival))
                spread = z*math.sqrt(greenwood)/(-math.log(survival))
                lo = math.exp(-math.exp(log_hazard+spread))
                hi = math.exp(-math.exp(log_hazard-spread))
        raw_lower.append(lo)
        raw_upper.append(hi)
        boundary = survival in (0.,1.)
        curve.append(dict(time=at, n_risk=risk, events=death, censored=censored,
            cumulative_events=cumulative_events, cumulative_censored=cumulative_censored,
            survival=survival, greenwood=greenwood, se=se,
            lower=None if boundary else lo, upper=None if boundary else hi))
        risk -= count
    median = dict(estimate=_median(grid.tolist(),[r['survival'] for r in curve]),
        lower=_median(grid.tolist(),raw_lower), upper=_median(grid.tolist(),raw_upper))
    return curve, median, ordered


def kaplan_meier_core(time, event, *, queries=(), confidence=.95, timefix=True,
                      unit='months', subject_ids=None):
    """0=censored, 1=event; no orientation guessing or competing-event recoding.

    Times/units are supplied explicitly. No weights, entry times or repeated-case
    inference. Reverse KM uses censoring as its event, with no observed-time fallback.
    """
    _confidence(confidence)
    if not isinstance(timefix,bool):
        raise InputError('Enable or disable near-tie normalization explicitly.')
    if not isinstance(unit,str) or unit not in ('days','weeks','months','years'):
        raise InputError('Declare one time unit: days, weeks, months or years.')
    t, e = _numeric(time,'Elapsed time'), _numeric(event,'Binary event indicator')
    if len(t) != len(e):
        raise InputError('Elapsed times and binary event indicators must align.')
    if np.any(t[~np.isnan(t)] < 0):
        raise InputError('Elapsed times must be nonnegative or missing.')
    if np.any(~np.isin(e[~np.isnan(e)],[0.,1.])):
        raise InputError('Explicitly code 0=censored and 1=event. Competing events require a different analysis.')
    if np.ma.isMaskedArray(queries):
        raise InputError('Requested times must be an unmasked numeric vector.')
    try:
        q = np.asarray(queries)
    except (TypeError,ValueError):
        raise InputError('Supply at most 200 finite nonnegative requested times.') from None
    if q.ndim != 1 or len(q)>200:
        raise InputError('Supply at most 200 finite nonnegative requested times.')
    q = _numeric(queries,'Requested times') if len(q) else np.array([],dtype=float)
    if np.any(np.isnan(q)) or np.any(q<0):
        raise InputError('Requested times must be finite and nonnegative; missing times are invalid.')
    q = np.unique(q)
    keep = ~np.isnan(t) & ~np.isnan(e)
    indices = np.flatnonzero(keep).tolist()
    if not indices:
        raise InputError('No complete time/event pairs remain.')
    ids = _ids(subject_ids,len(t),keep)
    tt, ee = t[keep], e[keep].astype(np.int64)
    try:
        exposure = math.fsum(float(v) for v in tt)
    except OverflowError:
        raise InputError('Total person-time exceeds the supported numeric range.') from None
    if not math.isfinite(exposure):
        raise InputError('Total person-time exceeds the supported numeric range.')
    effective = _effective_times(tt,timefix)
    confidence = float(confidence)
    curve, median, ordered = _fit(effective,ee,confidence)
    reverse_curve, reverse_median, _ = _fit(effective,1-ee,confidence)
    max_time = float(tt.max())
    omitted = [float(v) for v in q if v>max_time and curve[-1]['survival']!=0]
    supported = [float(v) for v in q if v<=max_time or curve[-1]['survival']==0]
    grid = np.array([r['time'] for r in curve])
    selected = []
    previous_events = previous_censored = 0
    for at in supported:
        position = int(np.searchsorted(grid,at,side='right'))-1
        point = curve[position] if position>=0 else dict(survival=1.,se=0.,lower=None,upper=None,
            cumulative_events=0,cumulative_censored=0)
        deaths, censors = point['cumulative_events'], point['cumulative_censored']
        selected.append(dict(time=at,n_risk=len(ordered)-int(np.searchsorted(ordered,at,side='left')),
            events=deaths-previous_events,censored=censors-previous_censored,
            cumulative_events=deaths,cumulative_censored=censors,
            **{k:point[k] for k in ('survival','se','lower','upper')},
            status='terminal_zero_extension' if at>max_time else 'within_followup'))
        previous_events, previous_censored = deaths, censors
    events = int(ee.sum())
    rate = dict(person_time=exposure,events=events,estimate=None,lower=None,upper=None,
        status='unavailable_zero_person_time')
    if exposure>0:
        alpha = (1-confidence)/2
        estimate = events/exposure
        lower = 0. if not events else float(chi2.ppf(alpha,2*events))/2/exposure
        upper = float(chi2.ppf(1-alpha,2*(events+1)))/2/exposure
        if all(math.isfinite(v) for v in (estimate,lower,upper)):
            rate.update(estimate=estimate,lower=lower,upper=upper,status='available')
        else:
            rate['status'] = 'unavailable_numeric_range'
    return dict(schema_version=1,status='ok',confidence=confidence,timefix=timefix,unit=unit,
        n_source=len(t),n_complete=len(indices),excluded_missing=int(np.sum(~keep)),
        missing_time=int(np.sum(np.isnan(t))),missing_event=int(np.sum(np.isnan(e))),
        retained_indices=indices,retained_subject_ids=ids,events=events,censored=len(indices)-events,
        event_proportion=events/len(indices),max_time=max_time,effective_max_time=float(effective.max()),
        timefix_changed_rows=int(np.sum(tt!=effective)),effective_times=effective.tolist(),
        curve=curve,median=median,selected=selected,omitted_timepoints=omitted,
        reverse=dict(curve=reverse_curve,median=reverse_median),rate=rate,
        assumptions=['Independent subjects; independent right censoring.',
            'Declared units, event orientation and origin must be supplied correctly.',
            'Pointwise log-log limits; no simultaneous band or treatment-effect inference.'])
