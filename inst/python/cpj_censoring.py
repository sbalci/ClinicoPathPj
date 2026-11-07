"""Numeric interval2 endpoint preparation; no survival fit or status-variable recoding."""
import numpy as np
from cpj_runtime import InputError

KINDS=['Right-censored','Exact','Left-censored','Interval-censored']


def numeric_column(data,name):
    if name not in data:raise InputError('Select both numeric endpoint variables.')
    column=data[name];metadata=getattr(data,'metadata',{}).get(name,{})
    if metadata.get('dimensions') or set(metadata.get('classes') or [])-{'numeric','integer'}:
        raise InputError('Endpoints must be scalar numeric columns in the same units and from the same origin; convert date classes explicitly first.')
    if not isinstance(column,np.ndarray) or column.ndim!=1 or column.dtype.kind not in 'fiu':
        raise InputError('Endpoints must be numeric, not factor level indices or text.')
    return column.astype(float)


def display(value):
    if np.isnan(value):return None
    if np.isposinf(value):return 'Inf'
    if np.isneginf(value):return '-Inf'
    return str(float(value))


def calculate(data,options):
    left=numeric_column(data,options.get('left'));right=numeric_column(data,options.get('right'))
    if len(left)!=len(right):raise InputError('Endpoint columns must have equal supplied row counts.')
    n=len(left)
    if not 1<=n<=10000:raise InputError('Interval preparation accepts one to 10,000 rows without sampling.')
    limit=options.get('preview_rows',20)
    if isinstance(limit,bool) or not isinstance(limit,int) or not 10<=limit<=100:
        raise InputError('Preview rows must be an integer from 10 to 100.')
    # Match Surv's order: compare the original bounds BEFORE mapping nonfinite values to NA.
    backwards=~np.isnan(left)&~np.isnan(right)&(left>right)
    finite_left=np.isfinite(left);finite_right=np.isfinite(right)
    unknown=~finite_left&~finite_right&~backwards
    codes=[];lower=[];upper=[];rows=[]
    for i,(a,b) in enumerate(zip(left,right)):
        if backwards[i]:code=None;kind='Invalid: reversed bounds'
        elif unknown[i]:code=None;kind='Uninformative: both open/missing'
        elif not finite_left[i]:code=2;kind=KINDS[code]
        elif not finite_right[i]:code=0;kind=KINDS[code]
        elif a==b:code=1;kind=KINDS[code]
        else:code=3;kind=KINDS[code]
        lo=float(a) if code is not None and finite_left[i] else None
        hi=float(b) if code is not None and finite_right[i] else None
        codes.append(code);lower.append(lo);upper.append(hi)
        rows.append(dict(rawLeft=display(a),rawRight=display(b),left=lo,right=hi,code=code,kind=kind))
    retained=sum(v is not None for v in codes)
    counts=[dict(code=i,kind=kind,n=codes.count(i),percent=codes.count(i)/retained if retained else None) for i,kind in enumerate(KINDS)]
    return dict(n=n,retained=retained,invalid=int(backwards.sum()),unknown=int(unknown.sum()),
                counts=counts,codes=codes,left=lower,right=upper,rows=rows,limit=limit,
                infinite=int((np.isinf(left)|np.isinf(right)).sum()),negative=int(((finite_left&(left<0))|(finite_right&(right<0))).sum()))
