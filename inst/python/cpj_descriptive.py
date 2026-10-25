"""Numeric summaries and distribution checks shared by the descriptive ports."""
import numpy as np
from scipy import stats
from cpj_runtime import InputError


def numeric(values, name):
    if not isinstance(values, np.ndarray) or values.ndim != 1:
        raise InputError(f'{name}: select a numeric variable.')
    if np.any(np.isinf(values)):
        raise InputError(f'{name}: infinite observations must be recoded before analysis.')
    return values[~np.isnan(values)]


def summarize(values, diagnostics=False, outliers=False):
    x=np.asarray(values,dtype=float);n=len(x)
    if not n: return {'n':0}
    q1,median,q3=np.quantile(x,[.25,.5,.75],method='linear')
    result=dict(n=n,mean=float(np.mean(x)),sd=float(np.std(x,ddof=1)) if n>1 else None,
                minimum=float(min(x)),q1=float(q1),median=float(median),q3=float(q3),maximum=float(max(x)))
    if diagnostics:
        unique=len(np.unique(x)); eligible=3<=n<=5000 and unique>1
        sw=stats.shapiro(x) if eligible else None
        result.update(w=float(sw.statistic) if sw else None,p=float(sw.pvalue) if sw else None,
            skewness=float(stats.skew(x,bias=True)) if n>=3 and unique>1 else None,
            kurtosis=float(stats.kurtosis(x,bias=True,fisher=False)) if n>=3 and unique>1 else None,
            diagnostic_status='available' if eligible else 'constant' if n>=3 and unique==1 else 'sample size outside 3-5000')
    if outliers:
        result.update(lower=float(q1-1.5*(q3-q1)) if n>=4 else None,
                      upper=float(q3+1.5*(q3-q1)) if n>=4 else None)
    return result


def histogram(values, group):
    counts,edges=np.histogram(values,bins='auto')
    return [dict(group=group,lower=float(a),upper=float(b),count=int(c))
            for a,b,c in zip(edges[:-1],edges[1:],counts)]


def display_p(p):
    if p is None:return 'unavailable'
    if p<.001:return '< 0.001'
    digits=3
    while p!=.05 and digits<15 and round(p,digits)==.05:digits+=1
    return f'{p:.{digits}f}'
