"""Single-variable descriptive screening; frozen checkdata formulas, no quality grade."""
import numpy as np
from cpj_runtime import Factor, InputError


def screen(column, transform='none', rare_threshold=5, cv_min_mean=.01, assess=True):
    if transform not in ('none','log','sqrt'):
        raise InputError('Unknown outlier transformation.')
    for value,lo,hi,label in [(rare_threshold,.1,20,'Rare category threshold'),(cv_min_mean,0,10,'Minimum mean for CV')]:
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not np.isfinite(value) or not lo<=value<=hi:
            raise InputError(f'{label} is outside its supported range.')
    numeric=isinstance(column,np.ndarray) and np.issubdtype(column.dtype,np.number)
    if isinstance(column,Factor):
        if np.any(column.codes < -1) or np.any(column.codes>=len(column.levels)):
            raise InputError('Invalid factor codes.')
        values=np.array([column.levels[i] if i>=0 else None for i in column.codes],object)
        missing=column.codes<0;kind='Ordinal' if column.ordered else 'Categorical'
    elif numeric:
        values=np.asarray(column,float);missing=np.isnan(values);kind='Numeric'
        if np.isinf(values).any():raise InputError('Infinite values must be recoded as missing before screening.')
    else:
        values=np.asarray(column,object);missing=np.array([v is None for v in values]);kind='Text'
    if values.ndim!=1 or not 0<len(values)<=1_000_000:
        raise InputError('Select a nonempty scalar variable with at most 1,000,000 rows.')
    clean=values[~missing];n=len(clean);total=len(values)
    distinct,counts=np.unique(clean,return_counts=True)
    frequencies=[dict(value=str(v),n=int(c),proportion=float(c/n),rare=bool(c < rare_threshold*n/100)) for v,c in zip(distinct,counts)]
    frequencies.sort(key=lambda r:-r['n'])
    result=dict(values=values,missing=missing,kind=kind,total=total,n=n,distinct=len(distinct),
                repeats=n-len(distinct),frequencies=frequencies,stats={},transform='none',warnings=[],assessed=False)
    full=np.full(total,np.nan);flags=np.zeros((total,3),bool)
    result.update(z=full.copy(),modified=full.copy(),flags=flags,votes=np.zeros(total,int),selected=np.zeros(total,bool),mad_available=False)
    lengths=[]
    for value in missing:
        if lengths and lengths[-1][0]==value:lengths[-1][1]+=1
        else:lengths.append([bool(value),1])
    result['runs']=len(lengths)
    result['longest_missing']=max([c for m,c in lengths if m],default=0)
    result['trailing_missing']=lengths[-1][1] if lengths[-1][0] else 0
    if not numeric or not n:return result
    x=clean.astype(float);mean=float(np.mean(x));sd=float(np.std(x,ddof=1)) if n>1 else None
    q1,median,q3=np.quantile(x,[.25,.5,.75],method='linear');mad=1.4826*float(np.median(np.abs(x-median)))
    m2=np.mean((x-mean)**2)
    skew=float(np.mean((x-mean)**3)/m2**1.5) if n>=3 and m2>0 else 0.
    stats=dict(mean=mean,median=float(median),sd=sd,mad=mad,q1=float(q1),q3=float(q3),iqr=float(q3-q1),minimum=float(min(x)),maximum=float(max(x)),skewness=skew,
               cv=abs(sd/mean) if sd is not None and mean!=0 and abs(mean)>=cv_min_mean else None)
    if any(v is not None and not np.isfinite(v) for v in stats.values()):
        raise InputError('Numeric range is too extreme for reliable screening; rescale the source variable.')
    result['stats']=stats
    if not assess or n<3:return result
    y=x.copy()
    if transform=='log':
        if np.all(x>0):y=np.log(x);result['transform']='log'
        else:result['warnings'].append('Log transformation was not applied because zero or negative values are present; screening used raw values.')
    if transform=='sqrt':
        if np.all(x>=0):y=np.sqrt(x);result['transform']='sqrt'
        else:result['warnings'].append('Square-root transformation was not applied because negative values are present; screening used raw values.')
    spread=np.std(y,ddof=1);z=(y-np.mean(y))/spread if spread>0 else np.full(n,np.nan)
    a,b=np.quantile(y,[.25,.75],method='linear');fence=1.5*(b-a)
    sigma=1.4826*np.median(np.abs(y-np.median(y)));available=n>3 and sigma>0
    modified=(y-np.median(y))/sigma if available else np.full(n,np.nan)
    matrix=np.column_stack([np.abs(z)>3,(y<a-fence)|(y>b+fence),np.abs(modified)>3.5])
    votes=matrix.sum(axis=1);selected=votes >= (1 if n<10 else 2)
    result['z'][~missing]=z;result['modified'][~missing]=modified;result['flags'][~missing]=matrix
    result['votes'][~missing]=votes;result['selected'][~missing]=selected
    result.update(assessed=True,mad_available=bool(available),informative=n<10,lower=float(a-fence),upper=float(b+fence))
    return result
