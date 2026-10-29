"""Observed categorical prefixes, using one complete-case cohort throughout."""
import numpy as np
from cpj_runtime import Factor, InputError


def calculate(data, options):
    names=options.get('vars') or []
    if not isinstance(names,list) or not 1<=len(names)<=4 or len(set(names))!=len(names):
        raise InputError('Select one to four distinct categorical variables, in branching order.')
    columns=[];lengths=set();observed=[];unused=0
    for name in names:
        column=data.get(name)
        if not isinstance(column,Factor):raise InputError('Tree variables must be nominal or ordinal.')
        levels=column.levels;codes=np.asarray(column.codes)
        text=[v for v in levels if v is not None]
        if (any(not isinstance(v,str) for v in text) or len(set(text))!=len(text) or
                codes.ndim!=1 or codes.dtype.kind not in 'iu' or np.any(codes < -1) or np.any(codes>=len(levels))):
            raise InputError('Invalid factor levels or category codes.')
        lengths.add(len(codes));valid=codes>=0
        valid &= ~np.isin(codes,[j for j,v in enumerate(levels) if v is None])
        observed.append(valid);columns.append(column)
        unused+=sum(not np.any(codes[valid]==j) for j,v in enumerate(levels) if v is not None)
    if len(lengths)!=1:raise InputError('Selected variables must have equal lengths.')
    total=lengths.pop()
    if not 1<=total<=10000:raise InputError('The core accepts one to 10,000 input rows; it does not sample rows.')
    keep=np.logical_and.reduce(observed);n=int(keep.sum())
    if not n:raise InputError('No complete cases across the selected tree variables.')
    matrix=np.column_stack([c.codes[keep] for c in columns])
    counts={():n}
    for row in matrix:
        for depth in range(1,len(names)+1):
            key=tuple(int(v) for v in row[:depth]);counts[key]=counts.get(key,0)+1
            if len(counts)>201:raise InputError('The tree exceeds 200 observed non-root nodes. Select fewer variables or combine categories explicitly.')
    # Lexicographic code tuples give depth-first traversal in declared factor-level order.
    keys=sorted(counts);ids={key:i for i,key in enumerate(keys)};nodes=[]
    for key in keys:
        depth=len(key);parent=key[:-1];count=counts[key]
        path=[[names[j],columns[j].levels[code]] for j,code in enumerate(key)]
        nodes.append(dict(node=ids[key],parent=ids[parent] if depth else None,depth=depth,
                          variable=names[depth-1] if depth else '',level=path[-1][1] if depth else 'Complete cohort',
                          path=path,n=count,cohortPercent=count/n,parentPercent=count/counts[parent] if depth else 1.,
                          leaf=depth==len(names)))
    return dict(names=names,total=total,n=n,excluded=total-n,unused=unused,nodes=nodes,sourceRows=np.flatnonzero(keep).tolist())


def _mean_sd(values):
    """Scaled, anchored moments avoid overflow and preserve small within-node spreads."""
    if not len(values):return None,None
    anchor=float(values[0])
    with np.errstate(over='ignore',invalid='ignore',under='ignore'):
        shifted=values-anchor
        if np.isfinite(shifted).all():
            scale=float(np.max(np.abs(shifted)))
            if not scale:return anchor,0. if len(values)>1 else None
            scaled=shifted/scale
            mean=float(anchor+float(np.mean(scaled))*scale)
        else:
            scale=float(np.max(np.abs(values)));scaled=values/scale
            mean=float(np.mean(scaled)*scale)
        sd=float(np.std(scaled,ddof=1)*scale) if len(values)>1 else None
    if not np.isfinite(mean) or (sd is not None and not np.isfinite(sd)):
        raise InputError('The summary mean or SD exceeds numerical limits. Rescale the summary variable.')
    return mean,sd


def node_summaries(data,result,variable,location='leafonly'):
    if location not in ('leafonly','allnodes'):raise InputError('Unknown summary location.')
    if variable in result['names']:raise InputError('The continuous summary variable must differ from the categorical tree variables.')
    column=data.get(variable)
    if (not isinstance(column,np.ndarray) or column.ndim!=1 or column.dtype.kind not in 'fiu' or
            len(column)!=result['total']):raise InputError('Choose a numeric summary variable with one value per input row.')
    values=column.astype(float)
    if np.isinf(values).any():raise InputError('The summary variable contains infinite values. Recode them as missing or rescale before analysis.')
    indices=np.asarray(result['sourceRows'],dtype=int);values=values[indices];rows=[]
    for node in result['nodes']:
        if location=='leafonly' and not node['leaf']:continue
        keep=np.ones(result['n'],dtype=bool)
        for name,level in node['path']:
            factor=data[name];keep &= factor.codes[indices]==factor.levels.index(level)
        selected=values[keep];observed=selected[np.isfinite(selected)]
        mean,sd=_mean_sd(observed)
        rows.append(dict(node=node['node'],variable=variable,nodeN=node['n'],valid=len(observed),
                         missing=len(selected)-len(observed),mean=mean,sd=sd))
    return rows


def reference_summaries(data,result,variable,level):
    """Match/valid-reference percentage, independently of tree node percentages."""
    if not isinstance(variable,str) or not variable:raise InputError('Choose a categorical reference variable.')
    column=data.get(variable)
    if not isinstance(column,Factor):raise InputError('The reference variable must be categorical and separate from the numeric summary role.')
    codes=np.asarray(column.codes);labels=column.levels;text=[v for v in labels if v is not None]
    if (codes.ndim!=1 or codes.dtype.kind not in 'iu' or len(codes)!=result['total'] or
            np.any(codes < -1) or np.any(codes>=len(labels)) or any(not isinstance(v,str) for v in text) or len(set(text))!=len(text)):
        raise InputError('Invalid reference factor labels or codes.')
    if level is None or level not in text:raise InputError('Choose an existing, nonmissing reference level explicitly.')
    indices=np.asarray(result['sourceRows'],dtype=int);selected=codes[indices]
    valid=(selected>=0)&~np.isin(selected,[j for j,v in enumerate(labels) if v is None]);matches=selected==labels.index(level)
    rows=[]
    for node in result['nodes']:
        keep=np.ones(result['n'],dtype=bool)
        for name,label in node['path']:
            factor=data[name];keep &= factor.codes[indices]==factor.levels.index(label)
        n=int(np.sum(keep&valid));matched=int(np.sum(keep&matches))
        rows.append(dict(node=node['node'],variable=variable,level=level,nodeN=node['n'],valid=n,
                         missing=node['n']-n,matches=matched,percent=matched/n if n else None))
    return rows
