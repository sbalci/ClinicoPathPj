"""Standardized UTC elapsed intervals with auditable exclusions and row-aligned output."""
import math
import numpy as np
from scipy.stats import t
from cpj_runtime import InputError
from cpj_datetime import calculate as prepare_dates, ORDERS
from cpj_tree import _mean_sd
from cpj_crosstable import quantiles

DAYS_PER_UNIT={'days':1.,'weeks':7.,'months':30.4375,'years':365.25}


def number(value,name,minimum,maximum=math.inf):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not minimum<=value<=maximum:
        raise InputError(f'{name} must be finite and between {minimum} and {maximum}.')
    return float(value)


def calculate(data,options,row_ids=None):
    start=options.get('dx_date');end=options.get('fu_date')
    if start not in data or end not in data:raise InputError('Select both start and end date variables.')
    fmt=options.get('time_format','ymd');unit=options.get('output_unit','months')
    if fmt not in ORDERS:raise InputError('Choose a supported explicit text date format; numeric encodings and automatic detection are not available in this core.')
    if unit not in DAYS_PER_UNIT:raise InputError('Unknown elapsed-time unit.')
    if options.get('time_basis','standardized')!='standardized':raise InputError('Calendar-aware months/years are not implemented; this core uses standardized elapsed units.')
    if options.get('timezone','utc')!='utc':raise InputError('This explicit-format interval core supports UTC only.')
    flags={name:options.get(name,False) for name in ('remove_negative','remove_extreme','use_landmark')}
    if any(not isinstance(v,bool) for v in flags.values()):raise InputError('Exclusion and landmark choices must be true or false.')
    confidence=number(options.get('confidence_level',95),'Confidence level',90,99)
    multiplier=number(options.get('extreme_multiplier',2),'Extreme multiplier',1.5,5)
    landmark=number(options.get('landmark_time',6),'Landmark',0) if flags['use_landmark'] else 0.
    limit=options.get('preview_rows',20)
    if isinstance(limit,bool) or not isinstance(limit,int) or not 10<=limit<=100:raise InputError('Preview rows must be an integer from 10 to 100.')
    a=prepare_dates(data,dict(datetime_var=start,datetime_format=fmt))
    b=prepare_dates(data,dict(datetime_var=end,datetime_format=fmt))
    if a['total']!=b['total']:raise InputError('Start and end columns must have equal row counts.')
    n=a['total']
    if row_ids is not None and len(row_ids)!=n:raise InputError('Source row IDs must match the supplied rows.')
    quality=[]
    for role,name,parsed in [('Start',start,a),('End',end,b)]:
        if parsed['success'] is None or parsed['parsed']==0 or parsed['success']<.8:
            raise InputError(f'{role} column {name}: at least 80% of nonmissing dates must parse; {parsed["parsed"]} parsed, {parsed["invalid"]} invalid, {parsed["missing"]} missing/blank. Check the explicit format.')
        quality.append(dict(role=role,variable=name,parsed=parsed['parsed'],invalid=parsed['invalid'],missing=parsed['missing'],success=parsed['success']))
    raw=np.array([np.nan if x is None or y is None else (y-x).total_seconds()/86400/DAYS_PER_UNIT[unit]
                  for x,y in zip(a['dates'],b['dates'])],dtype=float)
    complete=np.isfinite(raw)
    if not complete.any():raise InputError('No complete date pairs remain after parsing.')
    invalid=np.array([x['status']=='Invalid' or y['status']=='Invalid' for x,y in zip(a['rows'],b['rows'])])
    missing=~complete & ~invalid
    negative=complete & (raw<0);zero=complete & (raw==0)
    if negative.any() and not flags['remove_negative']:
        indexes=np.flatnonzero(negative)[:3]
        examples=', '.join(row_ids[i] if row_ids is not None else str(i+1) for i in indexes)
        context='source row IDs' if row_ids is not None else 'supplied-row positions'
        raise InputError(f'Negative intervals detected in {int(negative.sum())} of {n} rows ({context}: {examples}). Correct the date order/format or enable negative-interval exclusion; negative values cannot subtract from record-time.')
    q99=float(np.quantile(raw[complete],.99,method='linear'))
    threshold=q99*multiplier if q99>0 else None
    extreme=complete & (raw>threshold) if threshold is not None else np.zeros(n,dtype=bool)
    keep=complete.copy();reasons=['Retained' if ok else 'Invalid date' if bad else 'Missing date' for ok,bad in zip(complete,invalid)]
    removed_negative=negative if flags['remove_negative'] else np.zeros(n,dtype=bool)
    keep[removed_negative]=False
    removed_extreme=keep & extreme if flags['remove_extreme'] else np.zeros(n,dtype=bool)
    keep[removed_extreme]=False
    below=keep & (raw<landmark) if landmark>0 else np.zeros(n,dtype=bool)
    keep[below]=False
    for mask,reason in [(removed_negative,'Excluded negative interval'),(removed_extreme,'Excluded extreme interval'),(below,'Below follow-up landmark')]:
        for i in np.flatnonzero(mask):reasons[i]=reason
    values=[float(v-landmark) if ok else None for v,ok in zip(raw,keep)]
    used=np.array([v for v in values if v is not None],dtype=float)
    count=len(used);mean,sd=_mean_sd(used)
    q1,median,q3=quantiles(used) if count else (None,None,None)
    lower=upper=raw_lower=None;clipped=False
    if count>1:
        margin=float(t.ppf((1+confidence/100)/2,count-1))*sd/math.sqrt(count)
        raw_lower=mean-margin;lower=max(0.,raw_lower);upper=mean+margin;clipped=raw_lower<0
    statistics=dict(n=count,unit=unit,total=float(math.fsum(used)) if count else None,mean=mean,sd=sd,
                    minimum=float(used.min()) if count else None,q1=q1,median=median,q3=q3,maximum=float(used.max()) if count else None)
    uncertainty=dict(confidence=confidence,n=count,df=count-1 if count>1 else None,lower=lower,upper=upper,rawLower=raw_lower,clipped='Yes' if clipped else 'No')
    rows=[dict(start=x['original'],end=y['original'],unit=unit,raw=float(v) if np.isfinite(v) else None,value=final,status=reason)
          for x,y,v,final,reason in zip(a['rows'],b['rows'],raw,values,reasons)]
    warnings=[]
    if invalid.any():warnings.append(f'{int(invalid.sum())} pair(s) contain an invalid date; saved intervals remain missing.')
    if missing.any():warnings.append(f'{int(missing.sum())} pair(s) are missing a date; saved intervals remain missing.')
    if flags['remove_extreme'] and threshold is None:warnings.append('Extreme exclusion is disabled because the raw 99th percentile is not positive; no interval was removed by this rule.')
    if flags['remove_extreme'] and threshold is not None and int(complete.sum())<101 and multiplier*(101-int(complete.sum()))>=100:
        warnings.append('At this sample size and multiplier, the interpolated 99th-percentile rule cannot flag an interval; review the longest intervals directly.')
    if clipped:warnings.append('The t interval has a negative raw lower bound; the reported lower limit is intersected with zero. The raw bound is shown; assess the t approximation for skewed intervals.')
    if count>1 and sd==0:warnings.append('All used intervals are identical; the t interval collapses to a point and does not establish absence of population uncertainty.')
    if count and statistics['total']==0:warnings.append('Summed record-time is zero and cannot be used as an incidence-rate denominator.')
    return dict(total=n,complete=int(complete.sum()),invalid=int(invalid.sum()),missing=int(missing.sum()),
                negative=int(negative.sum()),zero=int(zero.sum()),extreme=int(extreme.sum()),
                negativeRemoved=int(removed_negative.sum()),extremeRemoved=int(removed_extreme.sum()),landmarkRemoved=int(below.sum()),
                n=count,q99=q99,threshold=threshold,multiplier=multiplier,landmark=landmark,preview_limit=limit,
                quality=quality,rows=rows,values=values,statistics=statistics,uncertainty=uncertainty,warnings=warnings,unit=unit,fmt=fmt)
