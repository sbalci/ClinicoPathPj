"""Univariate screening flags; exact R type-7 quartiles, sample SD and scaled MAD."""
import numpy as np
from cpj_runtime import InputError


def calculate(data, options):
    names=options.get('vars') or []
    if not 1<=len(names)<=20 or len(set(names))!=len(names):
        raise InputError('Select one to twenty distinct numeric variables.')
    method=options.get('method','zscore_robust')
    if method not in ('zscore_robust','zscore','iqr'):raise InputError('Unknown screening method.')
    z=options.get('zscore_threshold',3.29);mult=options.get('iqr_multiplier',1.7)
    for value,lo,hi in ((z,1,5),(mult,1,3)):
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not np.isfinite(value) or not lo<=value<=hi:
            raise InputError('Screening threshold is outside its supported range.')
    arrays=[]
    for name in names:
        x=data.get(name)
        if not isinstance(x,np.ndarray) or not np.issubdtype(x.dtype,np.number) or x.ndim!=1:
            raise InputError('Screening requires numeric scalar variables.')
        arrays.append(np.asarray(x,float))
    total=len(arrays[0])
    if not 1<=total<=10000 or any(len(x)!=total for x in arrays):
        raise InputError('Use equal-length variables with 1 to 10,000 rows; this core never subsamples.')
    matrix=np.column_stack(arrays);keep=np.isfinite(matrix).all(axis=1);x=matrix[keep];n=len(x)
    if n<2:raise InputError('At least two finite complete rows are required across selected variables.')
    flags=np.full(x.shape,np.nan);summaries=[]
    for j,name in enumerate(names):
        v=x[:,j];q1,q3=np.quantile(v,[.25,.75],method='linear')
        if method=='iqr':
            center=float(np.median(v));spread=float(q3-q1);lower=float(q1-mult*spread);upper=float(q3+mult*spread)
            flags[:,j]=((v<lower)|(v>upper)).astype(float)
        else:
            center=float(np.mean(v)) if method=='zscore' else float(np.median(v))
            spread=float(np.std(v,ddof=1)) if method=='zscore' else float(1.4826*np.median(np.abs(v-center)))
            lower=center-z*spread;upper=center+z*spread
            if spread>0:flags[:,j]=(np.abs((v-center)/spread)>z).astype(float)
            else:
                # R's 0/0 is undefined; noncentral values / zero are infinite and flag.
                flags[v!=center,j]=1.
        if not np.isfinite([center,spread,lower,upper]).all():
            raise InputError('Numeric range is too extreme; rescale the source variables.')
        available=np.isfinite(flags[:,j]);count=int(np.nansum(flags[:,j]))
        summaries.append(dict(variable=name,n=n,evaluable=int(available.sum()),flagged=count,
                              unavailable=int((~available).sum()),center=center,spread=spread,
                              lower=float(lower),upper=float(upper)))
    full=np.full(total,np.nan);available=np.isfinite(flags).any(axis=1)
    aggregate=np.full(n,np.nan);aggregate[available]=(np.nan_to_num(flags[available],nan=0).max(axis=1)>0).astype(float)
    full[keep]=aggregate
    return dict(names=names,method=method,total=total,n=n,excluded=total-n,keep=keep,
                summaries=summaries,flags=flags,aggregate=full,
                variable_missing=np.sum(~np.isfinite(matrix),axis=0).tolist())
