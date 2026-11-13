"""Source-only explicit-boundary histograms and two-sided one-sample mean tests.

No public SPEC/menu integration. See docs/python-histogram-core.md for the frozen
contract and differences from automatic gghistostats/normality behavior.
"""
import math
from numbers import Real

import numpy as np
from scipy.stats import t

from cpj_estimation import _confidence, _ids, _numeric, _summary
from cpj_runtime import InputError

MAX_BINS = 2000


def _cohort(values, subject_ids):
    y = _numeric(values, 'Measurement')
    keep = ~np.isnan(y)
    if not np.any(keep):
        raise InputError('At least one complete finite measurement is required.')
    x = y[keep]
    summary = _summary(x) if len(x)>1 else dict(n=1,mean=float(x[0]),sd=None)
    # Sum before division to retain small residual means under cancellation.
    # If the unscaled sum overflows, preserve the validated scaled-moment mean.
    try:
        summary['mean'] = math.fsum(float(v) for v in x)/len(x)
    except OverflowError:
        pass
    with np.errstate(over='ignore', invalid='ignore'):
        quantiles = np.quantile(x,[.25,.5,.75],method='linear')
    if not np.all(np.isfinite(quantiles)):
        raise InputError('Summary quantiles exceed the supported numeric range.')
    summary.update(minimum=float(np.min(x)),q1=float(quantiles[0]),median=float(quantiles[1]),
                   q3=float(quantiles[2]),maximum=float(np.max(x)))
    return x, dict(schema_version=1,n_source=len(y),n_complete=len(x),
        excluded_missing=int(np.sum(~keep)),retained_indices=np.flatnonzero(keep).tolist(),
        retained_subject_ids=_ids(subject_ids,len(y),keep),summary=summary)


def histogram_core(values, *, breaks, closure, subject_ids=None):
    """Count exact intervals with explicit closure; retain both outer endpoints."""
    if not isinstance(closure,str) or closure not in ('right','left'):
        raise InputError('Choose right or left histogram closure explicitly.')
    edges = _numeric(breaks, 'Histogram breaks')
    if not 2 <= len(edges) <= MAX_BINS+1 or not np.all(np.isfinite(edges)):
        raise InputError('Supply 2–2,001 finite histogram breaks.')
    with np.errstate(over='ignore', invalid='ignore'):
        widths = np.diff(edges)
    if not np.all(np.isfinite(widths)) or np.any(widths<=0):
        raise InputError('Histogram breaks must be strictly increasing with finite positive widths.')
    x, result = _cohort(values,subject_ids)
    if np.any(x<edges[0]) or np.any(x>edges[-1]):
        raise InputError('Histogram breaks must cover every retained measurement; no observations are discarded.')
    # searchsorted left puts internal-edge ties in the lower/right-closed bin;
    # right puts them in the upper/left-closed bin. Clamp only outer endpoints
    # already proved in range, never out-of-range observations.
    side = 'left' if closure=='right' else 'right'
    indices = np.searchsorted(edges,x,side=side)-1
    indices = np.clip(indices,0,len(widths)-1)
    counts = np.bincount(indices,minlength=len(widths))
    proportions = counts/len(x)
    with np.errstate(over='ignore', under='ignore', invalid='ignore'):
        density = proportions/widths
    if (not np.all(np.isfinite(density)) or np.any((counts>0)&(density==0))):
        raise InputError('Histogram density exceeds or underflows the supported numeric range.')
    result.update(closure=closure,bins=[dict(lower=float(a),upper=float(b),
        lower_closed=(closure=='left' or i==0),
        upper_closed=(closure=='right' or i==len(widths)-1),count=int(count),
        proportion=float(proportion),density=float(d))
        for i,(a,b,count,proportion,d) in enumerate(zip(edges[:-1],edges[1:],counts,proportions,density))])
    return result


def one_sample_core(values, *, reference=0., confidence=.95, subject_ids=None):
    """Independent normal one-sample Student mean inference; reference in data units."""
    if (not isinstance(reference,Real) or isinstance(reference,(bool,np.bool_))
            or not math.isfinite(reference)):
        raise InputError('The reference must be a finite real number in the measurement units.')
    _confidence(confidence)
    reference, confidence = float(reference), float(confidence)
    x, result = _cohort(values,subject_ids)
    n, mean, sd = len(x), result['summary']['mean'], result['summary']['sd']
    difference = mean-float(reference)
    if not math.isfinite(difference):
        raise InputError('The mean-minus-reference contrast exceeds the supported numeric range.')
    result.update(reference=float(reference),confidence=float(confidence),difference=difference,
        stderr=None,df=None,statistic=None,p=None,mean_lower=None,mean_upper=None,
        difference_lower=None,difference_upper=None,status='insufficient_n',
        assumptions=['Independent observations','Normal one-sample Student model'])
    if n<2:
        return result
    se = sd/math.sqrt(n)
    if se==0 and sd>0:
        raise InputError('The mean standard error underflows the supported numeric range.')
    if se==0 or se<10*np.finfo(float).eps*abs(mean):
        result['status']='degenerate'
        return result
    df, statistic = float(n-1), difference/se
    half = float(t.ppf((1+confidence)/2,df))*se
    mean_lower, mean_upper = mean-half, mean+half
    difference_lower, difference_upper = mean_lower-reference, mean_upper-reference
    p = float(2*t.sf(abs(statistic),df))
    if not all(math.isfinite(v) for v in (se,statistic,p,half,mean_lower,mean_upper,
                                          difference_lower,difference_upper)):
        raise InputError('One-sample inference exceeds the supported numeric range.')
    result.update(stderr=se,df=df,statistic=statistic,p=p,mean_lower=mean_lower,
        mean_upper=mean_upper,difference_lower=difference_lower,difference_upper=difference_upper,status='ok')
    return result
