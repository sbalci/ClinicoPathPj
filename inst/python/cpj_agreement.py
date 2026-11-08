"""Conventional raw-scale Bland-Altman core for independent measurement pairs."""
import math
import numpy as np
from scipy.stats import norm, t
from cpj_runtime import InputError
from cpj_identity import audit


def calculate(data, options, row_ids=None):
    variables=options.get('vars') or []
    if len(variables)<2 or any(v not in data for v in variables):
        return dict(pending='Choose exactly two numeric measurement columns; one row must represent one independent case.')
    if len(variables)!=2 or len(set(variables))!=2:
        raise InputError('Choose two distinct measurement columns; categorical and multi-rater methods are not implemented in this core.')
    columns=[]
    for name in variables:
        x=data[name];meta=getattr(data,'metadata',{}).get(name,{})
        if (not isinstance(x,np.ndarray) or x.ndim!=1 or x.dtype.kind not in 'fiu'
                or meta.get('dimensions') or set(meta.get('classes') or [])-{'numeric','integer'}):
            raise InputError('Measurements must be scalar numeric values in the same units, not dates or categorical codes.')
        if np.isinf(x).any():raise InputError('Measurements must be finite or missing; infinite values are unsupported.')
        columns.append(x)
    x,y=columns;n=len(x)
    if not 1<=n<=5000 or len(y)!=n:raise InputError('Supply one to 5,000 aligned source rows without display sampling.')
    coverage=options.get('baConfidenceLevel',.95);confidence=options.get('confLevel',.95)
    for value,low,label in [(coverage,.50,'LoA coverage'),(confidence,.80,'CI confidence')]:
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not low<=value<=.99:
            raise InputError(label+' is outside its supported range.')
    ids=[str(i+1) for i in range(n)] if row_ids is None else list(row_ids)
    if len(ids)!=n or any(not isinstance(v,str) or not v for v in ids) or len(set(ids))!=n:
        raise InputError('Original source-row identities must be distinct strings aligned with the input.')
    present=~(np.isnan(x)|np.isnan(y));indices=np.flatnonzero(present);m=len(indices)
    if m<3:raise InputError('Bland-Altman analysis requires at least three complete independent measurement pairs.')
    labels=ids
    subject=options.get('subject')
    if subject:
        if subject not in data:return dict(pending='Choose an available case identifier or clear the optional role.')
        identity=audit(data,subject,n);labels=identity['values']
        retained=[labels[i] for i in indices]
        if any(v is None for v in retained) or len(set(retained))!=m:
            raise InputError('Complete pairs require known, unique case IDs. Repeated-measurement agreement is not implemented.')
    with np.errstate(over='ignore',invalid='ignore'):
        differences=x[present]-y[present];means=x[present]/2+y[present]/2
    if not np.isfinite(differences).all() or not np.isfinite(means).all():
        raise InputError('Measurement differences exceed finite numeric range; rescale the measurement units.')
    scale=float(np.max(np.abs(differences))) or 1.
    standardized=differences/scale
    bias=float(np.mean(standardized))*scale;sd=float(np.std(standardized,ddof=1))*scale
    z=float(norm.ppf((1+coverage)/2));critical=float(t.ppf((1+confidence)/2,m-1))
    lower=bias-z*sd;upper=bias+z*sd
    bias_half=critical*sd/math.sqrt(m)
    loa_half=critical*sd*math.sqrt(1/m+z*z/(2*(m-1)))
    values=[bias,sd,lower,upper,bias-bias_half,bias+bias_half,lower-loa_half,
            lower+loa_half,upper-loa_half,upper+loa_half]
    if not all(math.isfinite(v) for v in values):
        raise InputError('Agreement estimates exceed finite numeric range; rescale the measurement units.')
    rows=[dict(sourceID=ids[i],case=labels[i],first=float(x[i]),second=float(y[i]),
               mean=float(means[j]),difference=float(differences[j])) for j,i in enumerate(indices)]
    return dict(pending='',input=n,n=m,excluded=n-m,
                firstOnlyMissing=int((np.isnan(x)&~np.isnan(y)).sum()),
                secondOnlyMissing=int((~np.isnan(x)&np.isnan(y)).sum()),
                bothMissing=int((np.isnan(x)&np.isnan(y)).sum()),
                bias=bias,sd=sd,lower=lower,upper=upper,
                biasLower=bias-bias_half,biasUpper=bias+bias_half,
                lowerLower=lower-loa_half,lowerUpper=lower+loa_half,
                upperLower=upper-loa_half,upperUpper=upper+loa_half,
                coverage=coverage,confidence=confidence,rows=rows)
