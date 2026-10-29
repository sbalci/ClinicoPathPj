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
    return dict(names=names,total=total,n=n,excluded=total-n,unused=unused,nodes=nodes)
