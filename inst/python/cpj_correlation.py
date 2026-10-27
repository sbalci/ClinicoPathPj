"""Unconditional Pearson/Spearman core; explicit cohorts and comparison family."""
import numpy as np
from scipy import stats
from cpj_runtime import Factor, InputError


def adjust(values, method):
    p=np.array([np.nan if v is None else v for v in values],dtype=float)
    family=len(p);indices=np.flatnonzero(np.isfinite(p));answer=np.full(family,np.nan)
    if method not in ('none','holm','bonferroni','BH'):
        raise InputError('Unsupported p-value adjustment.')
    if not len(indices):return [None]*family
    order=indices[np.argsort(p[indices],kind='stable')];ranked=p[order]
    if method=='none':q=ranked
    elif method=='bonferroni':q=ranked*family
    elif method=='holm':q=np.maximum.accumulate(ranked*(family-np.arange(len(order))))
    else:q=np.minimum.accumulate((ranked*family/np.arange(1,len(order)+1))[::-1])[::-1]
    answer[order]=np.minimum(1,q)
    return [float(v) if np.isfinite(v) else None for v in answer]


def calculate(data, options):
    names=options.get('dep') or []
    if not 2<=len(names)<=20 or len(set(names))!=len(names):
        raise InputError('Choose two to twenty distinct numeric variables.')
    columns=[]
    for name in names:
        c=data[name]
        if isinstance(c,Factor) or np.asarray(c).dtype.kind not in 'fiu':
            raise InputError('Correlation variables must be numeric.')
        columns.append(np.asarray(c,dtype=float))
    if len({len(c) for c in columns})!=1:raise InputError('Variables must have equal lengths.')
    x=np.column_stack(columns)
    if not len(x):raise InputError('There are no input observations.')
    if np.isinf(x).any():raise InputError('Infinite values are not supported.')
    method=options.get('typestatistics','parametric');missing=options.get('naHandling','listwise')
    if method not in ('parametric','nonparametric') or missing not in ('listwise','pairwise'):
        raise InputError('Unsupported correlation method or missingness rule.')
    try:confidence=float(options.get('conflevel',.95))
    except (TypeError,ValueError):raise InputError('Confidence level must be a numeric proportion.') from None
    if not .5<=confidence<=.999:raise InputError('Confidence level must be between 0.5 and 0.999.')
    common=np.isfinite(x).all(axis=1);matrix=np.full((len(names),len(names)),np.nan);pairs=[]
    for i in range(len(names)):
        own=x[common,i] if missing=='listwise' else x[np.isfinite(x[:,i]),i]
        if len(own)>=3 and np.ptp(own)>0:matrix[i,i]=1
        for j in range(i+1,len(names)):
            keep=common if missing=='listwise' else np.isfinite(x[:,i])&np.isfinite(x[:,j])
            a,b=x[keep,i],x[keep,j];n=len(a);r=p=lo=hi=None
            reason='Fewer than three complete pairs' if n<3 else 'Constant variable' if np.ptp(a)==0 or np.ptp(b)==0 else None
            if reason is None:
                result=stats.pearsonr(a,b) if method=='parametric' else stats.spearmanr(a,b)
                r,p=float(result.statistic),float(result.pvalue)
                if not np.isfinite(r) or not np.isfinite(p):raise InputError('Correlation is numerically unstable; check variable magnitudes.')
                r=float(np.clip(r,-1,1));matrix[i,j]=matrix[j,i]=r
                if method=='parametric' and n>=4:
                    if abs(r)==1:lo=hi=r
                    else:
                        delta=stats.norm.ppf((1+confidence)/2)/np.sqrt(n-3)
                        lo,hi=[float(v) for v in np.tanh([np.arctanh(r)-delta,np.arctanh(r)+delta])]
            pairs.append(dict(first=names[i],second=names[j],n=n,excluded=len(x)-n,estimate=r,lower=lo,upper=hi,p=p,reason=reason or ''))
    q=adjust([row['p'] for row in pairs],options.get('padjustmethod','holm'))
    for row,value in zip(pairs,q):row['adjusted']=value
    return dict(names=names,pairs=pairs,matrix=[[None if not np.isfinite(v) else float(v) for v in row] for row in matrix],inputRows=len(x),commonRows=int(common.sum()),method=method,missing=missing,confidence=confidence,adjustment=options.get('padjustmethod','holm'))
