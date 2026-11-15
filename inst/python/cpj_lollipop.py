"""Source-only lollipop summaries, memberships and stem geometry; no inference."""
import math
from numbers import Real

import numpy as np

from cpj_barstats import _factor
from cpj_estimation import _numeric
from cpj_runtime import InputError


def _mean(values):
    scale = max(abs(float(v)) for v in values)
    return (math.fsum(float(v)/scale for v in values)/len(values))*scale if scale else 0.


def _summary(values):
    values = np.asarray(values, dtype=float)
    mean = _mean(values)
    with np.errstate(over='ignore', invalid='ignore', under='ignore'):
        delta = values-mean
        scale = float(np.max(np.abs(delta)))
        sd = (scale*math.sqrt(math.fsum(float(v)**2 for v in delta/scale)/(len(values)-1))
              if len(values)>1 and scale>0 else 0. if len(values)>1 else None)
        quartiles = np.quantile(values,[.25,.5,.75],method='linear').tolist()
        span = float(values.max()-values.min())
    result = dict(n=len(values),mean=mean,median=quartiles[1],sd=sd,
        minimum=float(values.min()),maximum=float(values.max()),range=span,
        q1=quartiles[0],q3=quartiles[2])
    if any(v is not None and not math.isfinite(v) for v in result.values()):
        raise InputError('Derived lollipop summaries exceed the supported numeric range.')
    if sd == 0 and np.any(values != values[0]):
        raise InputError('Lollipop dispersion underflows the supported numeric range.')
    return result


def lollipop_core(values, group, *, aggregation='mean', sorting='original',
                  orientation='vertical', baseline=0.):
    """Return raw/plotted summaries separately, preserving contributing source rows."""
    if not isinstance(aggregation,str) or aggregation not in ('mean','median','sum','none'):
        raise InputError('Aggregation must be mean, median, sum or none.')
    if not isinstance(sorting,str) or sorting not in ('original','value_asc','value_desc','group_alpha'):
        raise InputError('Choose original, value_asc, value_desc or group_alpha sorting.')
    if not isinstance(orientation,str) or orientation not in ('vertical','horizontal'):
        raise InputError('Orientation must be vertical or horizontal.')
    if (not isinstance(baseline,Real) or isinstance(baseline,(bool,np.bool_))
            or not math.isfinite(baseline)):
        raise InputError('The stem baseline must be a finite numeric value.')
    numbers = _numeric(values,'Values')
    codes,labels = _factor(group,'Groups')
    if len(numbers)!=len(codes) or len(numbers)<2:
        raise InputError('Supply 2–100,000 aligned source rows.')
    keep = (codes>=0) & ~np.isnan(numbers)
    indices = np.flatnonzero(keep).tolist()
    active = sorted(set(int(codes[i]) for i in indices))
    if not 2<=len(active)<=50:
        raise InputError('Supply 2–50 groups with complete observations.')
    if aggregation=='none' and len(indices)>10000:
        raise InputError('Unaggregated lollipops are limited to 10,000 complete points.')
    members = {c:[] for c in active}
    for i in indices:
        members[int(codes[i])].append(i)
    points = []
    if aggregation=='none':
        points = [dict(code=int(codes[i]),label=labels[int(codes[i])],
            value=float(numbers[i]),source_indices=[i]) for i in indices]
    else:
        for code in active:
            x = numbers[members[code]]
            try:
                with np.errstate(over='ignore',invalid='ignore'):
                    value = (_mean(x) if aggregation=='mean' else
                             float(np.quantile(x,.5,method='linear')) if aggregation=='median' else math.fsum(x))
            except (ValueError,OverflowError):
                raise InputError('Aggregated lollipop values exceed the supported numeric range.') from None
            if not math.isfinite(value):
                raise InputError('Aggregated lollipop values exceed the supported numeric range.')
            points.append(dict(code=code,label=labels[code],value=value,source_indices=members[code]))
    if sorting=='value_asc':
        points.sort(key=lambda p:p['value'])
    elif sorting=='value_desc':
        points.sort(key=lambda p:-p['value'])
    elif sorting=='group_alpha':
        points.sort(key=lambda p:p['label'])
    axis = ([labels[c] for c in active] if sorting=='original' else
            list(dict.fromkeys(p['label'] for p in points)))
    if sorting!='original' and orientation=='horizontal':
        axis.reverse()
    slots = {label:i+1 for i,label in enumerate(axis)}
    for p in points:
        p.update(slot=slots[p['label']],stem_start=float(baseline),stem_end=p['value'])
        if not math.isfinite(p['value']-baseline):
            raise InputError('The stem span exceeds the supported numeric range.')
    raw = _summary(numbers[keep])
    plotted = _summary([p['value'] for p in points])
    return dict(schema_version=1,n_source=len(numbers),n_complete=len(indices),
        excluded_missing=len(numbers)-len(indices),missing_values=int(np.isnan(numbers).sum()),
        missing_group=int((codes<0).sum()),retained_indices=indices,active_codes=active,
        unused_codes=[i for i,label in enumerate(labels) if label is not None and i not in active],
        axis_levels=axis,points=points,raw_summary=raw,plotted_summary=plotted,
        reference_mean=plotted['mean'],
        overplotting=aggregation=='none' and any(len(m)>1 for m in members.values()),
        highest_groups=list(dict.fromkeys(p['label'] for p in points if p['value']==plotted['maximum'])),
        lowest_groups=list(dict.fromkeys(p['label'] for p in points if p['value']==plotted['minimum'])))
