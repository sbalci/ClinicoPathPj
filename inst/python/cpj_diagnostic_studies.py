"""Raw diagnostic-study review; no pooling, weighting or continuity correction."""
import math
import numpy as np
from scipy.stats import norm
from cpj_runtime import InputError
from cpj_identity import audit

ROLES = ('true_positives','false_positives','false_negatives','true_negatives')


def wilson(successes, total, confidence):
    p=successes/total
    z=float(norm.ppf((1+confidence)/2));z2=z*z
    denominator=1+z2/total
    center=(p+z2/(2*total))/denominator
    radius=z*math.sqrt(p*(1-p)/total+z2/(4*total*total))/denominator
    return max(0.,center-radius),min(1.,center+radius)


def calculate(data, options, row_ids=None):
    for role in ('study',)+ROLES:
        if options.get(role) not in data:
            return dict(pending='Select a study ID and all four count variables (TP, FP, FN and TN).')
    columns=[]
    for role in ROLES:
        name=options[role];x=data[name]
        meta=getattr(data,'metadata',{}).get(name,{})
        if (not isinstance(x,np.ndarray) or x.ndim!=1 or x.dtype.kind not in 'fiu'
                or meta.get('dimensions') or set(meta.get('classes') or [])-{'numeric','integer'}):
            raise InputError('Count variables must contain scalar numeric participant counts, not dates or factor codes.')
        if np.isinf(x).any():raise InputError('Counts must be finite or missing; infinite counts are unsupported.')
        columns.append(x)
    n=len(columns[0])
    if not 1<=n<=200 or any(len(x)!=n for x in columns):
        raise InputError('Supply one to 200 aligned study rows without sampling.')
    width=options.get('confidence_level',95)
    limit=options.get('plot_limit',20)
    if isinstance(width,bool) or not isinstance(width,int) or not 50<=width<=99:
        raise InputError('Confidence level must be an integer from 50 to 99 percent.')
    if isinstance(limit,bool) or not isinstance(limit,int) or not 5<=limit<=100:
        raise InputError('Forest plot rows must be an integer from 5 to 100.')
    strict=options.get('reject_invalid',False)
    if not isinstance(strict,bool):raise InputError('Invalid-count rejection must be enabled or disabled explicitly.')
    identity=audit(data,options['study'],n)
    ids=[str(i+1) for i in range(n)] if row_ids is None else list(row_ids)
    if len(ids)!=n:raise InputError('Study source-row identities must align with all input rows.')
    studies=[];excluded=[];zero=0
    for i,values in enumerate(zip(*columns)):
        label=identity['values'][i]
        shown=label if label is not None else 'Unnamed study'
        reason=''
        if any(np.isnan(v) for v in values):reason='Missing count'
        elif any(v<0 for v in values):reason='Negative count'
        elif any(float(v)!=math.floor(v) for v in values):reason='Fractional count'
        elif any(v>2**53-1 for v in values) or sum(int(v) for v in values)>2**53-1:
            reason='Count total exceeds exact integer transport limit'
        else:
            tp,fp,fn,tn=map(int,values)
            if tp+fn==0 or tn+fp==0:reason='No diseased or no non-diseased participants'
        if reason:
            excluded.append(dict(sourceID=ids[i],study=shown,reason=reason));continue
        se=tp/(tp+fn);sp=tn/(tn+fp)
        se_low,se_high=wilson(tp,tp+fn,width/100)
        sp_low,sp_high=wilson(tn,tn+fp,width/100)
        zero+=int(0 in (tp,fp,fn,tn))
        studies.append(dict(sourceID=ids[i],study=shown,tp=tp,fp=fp,fn=fn,tn=tn,
                            sensitivity=se,seLower=se_low,seUpper=se_high,
                            specificity=sp,spLower=sp_low,spUpper=sp_high))
    if strict and excluded:
        raise InputError(f'{len(excluded)} study row(s) have missing or invalid counts. Review the four count variables or disable invalid-count rejection to inspect the exclusion audit.')
    return dict(pending='',input=n,studies=studies,excluded=excluded,zero=zero,
                identity=identity,confidence=width,limit=limit)
