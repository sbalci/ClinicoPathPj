"""Missingness and duplicate accounting without interpreting repeated values as errors."""
import numpy as np
from cpj_runtime import Factor, InputError


def profile(columns, threshold=10):
    if not isinstance(threshold,(int,float)) or isinstance(threshold,bool) or not np.isfinite(threshold) or not 0<=threshold<=100:
        raise InputError('Missing-data threshold must be between 0 and 100 percent.')
    if not columns:raise InputError('Choose variables to check.')
    if len(columns)>200:raise InputError('Select at most 200 variables per quality assessment.')
    summaries=[];masks=[];encodings=[];n=None
    for name,column in columns.items():
        if isinstance(column,Factor):
            values=column.codes
            if np.any(values>=len(column.levels)) or np.any(values < -1):raise InputError('Invalid factor codes.')
            mask=values<0;kind='Ordinal' if column.ordered else 'Categorical'
        elif isinstance(column,np.ndarray) and np.issubdtype(column.dtype,np.number):
            values=column;mask=np.isnan(values);kind='Numeric'
            if np.any(np.isinf(values)):raise InputError(f'{name}: infinite numeric values must be recoded as missing.')
        else:
            values=np.asarray(column,dtype=object);mask=np.array([v is None for v in values]);kind='Text'
        if values.ndim!=1:raise InputError('Only scalar columns are supported.')
        if n is None:
            n=len(values)
            if n*len(columns)>10_000_000:raise InputError('Quality assessment supports at most 10 million selected cells per run.')
        if len(values)!=n or not n:raise InputError('The dataset must have aligned, nonempty rows.')
        clean=values[~mask]
        # Missing codes share one sentinel; literal text such as NA remains an observed value.
        distinct,inverse=np.unique(clean,return_inverse=True)
        codes=np.full(n,-1,dtype=np.int64);codes[~mask]=inverse
        nonmissing=len(clean);unique=len(distinct);missing=n-nonmissing
        outliers=None
        if kind=='Numeric' and nonmissing>10:
            q1,q3=np.quantile(clean,[.25,.75],method='linear');iqr=q3-q1
            outliers=int(np.sum((clean<q1-1.5*iqr)|(clean>q3+1.5*iqr))) if iqr>0 else 0
        summaries.append(dict(variable=name,kind=kind,n=n,valid=nonmissing,missing=missing,
            missingRate=missing/n,unique=unique,repeats=nonmissing-unique,
            repeatRate=(nonmissing-unique)/nonmissing if nonmissing else None,
            constant=nonmissing>0 and unique<=1,highCardinality=kind!='Numeric' and unique>50 and unique>.5*nonmissing,
            aboveThreshold=missing>n*threshold/100,outliers=outliers,
            outlierRate=outliers/nonmissing if outliers is not None else None))
        masks.append(mask);encodings.append(codes)
    missing=np.column_stack(masks);codes=np.column_stack(encodings)
    per_row=missing.sum(axis=1)
    return dict(summaries=summaries,missing=missing,codes=codes,n=n,p=len(summaries),
        complete=int(np.sum(per_row==0)),missingCells=int(missing.sum()),rowMissing=per_row)


def duplicate_rows(codes):
    # Integer tuples avoid delimiter collisions and distinguish true missing from literal NA.
    _,first,counts=np.unique(codes,axis=0,return_index=True,return_counts=True)
    repeated=[(int(i),int(c)) for i,c in zip(first,counts) if c>1]
    repeated.sort(key=lambda item:(-item[1],item[0]))
    return dict(unique=len(counts),excess=len(codes)-len(counts),groups=len(repeated),patterns=repeated[:5])


def preview(result,names,row_ids=None):
    nr=min(result['n'],200);nc=min(result['p'],20)
    return dict(variables=list(names)[:nc],row_ids=[str(row_ids[i] if row_ids is not None else i+1) for i in range(nr)],
                missing=result['missing'][:nr,:nc].astype(int).tolist(),total_rows=result['n'],total_variables=result['p'])
