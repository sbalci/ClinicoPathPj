"""Exact complete-case set memberships; missing values are never negative membership."""
import numpy as np
from cpj_runtime import Factor,InputError


def calculate(data,options):
    selected=[(options.get(f'var{i}'),options.get(f'var{i}true')) for i in range(1,5) if options.get(f'var{i}')]
    if not options.get('var1') or not options.get('var2') or not 2<=len(selected)<=4:
        raise InputError('Choose two to four sets, including Variable 1 and Variable 2.')
    names=[name for name,_ in selected]
    if len(set(names))!=len(names):raise InputError('Each set must use a distinct variable.')
    members=[];observed=[];sets=[];lengths=set()
    for index,(name,positive) in enumerate(selected):
        column=data[name]
        if not isinstance(column,Factor):raise InputError('Set variables must be nominal or ordinal.')
        labels=column.levels;codes=np.asarray(column.codes)
        if any(v is not None and not isinstance(v,str) for v in labels) or len({v for v in labels if v is not None})!=sum(v is not None for v in labels):
            raise InputError('Set levels must be distinct text labels.')
        if codes.ndim!=1 or codes.dtype.kind not in 'iu' or np.any(codes>=len(labels)):
            raise InputError('Invalid set category codes.')
        if positive is None or positive not in labels:raise InputError('Choose every selected set positive level explicitly.')
        lengths.add(len(codes));present=codes>=0
        if any(v is None for v in labels):present&=~np.isin(codes,[i for i,v in enumerate(labels) if v is None])
        observed.append(present);members.append(codes==labels.index(positive))
        sets.append(dict(position=index+1,variable=name,positive=positive))
    if len(lengths)!=1:raise InputError('Set variables must have equal lengths.')
    total=lengths.pop()
    if total==0:raise InputError('There are no input rows.')
    complete=np.logical_and.reduce(observed);retained=int(complete.sum())
    if not retained:raise InputError(f'No complete cases across selected sets (input rows: {total}; excluded: {total}); missing values are not negative membership.')
    bits=np.column_stack(members);masks=np.sum(bits*np.array([1<<i for i in range(len(names))]),axis=1).astype(int)
    counts=np.bincount(masks[complete],minlength=1<<len(names))
    patterns=[]
    for mask,count in enumerate(counts):
        signature=''.join('1' if mask&(1<<i) else '0' for i in range(len(names)))
        included=[name for i,name in enumerate(names) if mask&(1<<i)]
        patterns.append(dict(code=mask,pattern=signature,members=' + '.join(included) if included else 'None',n=int(count),percent=float(count/retained)))
    for i,record in enumerate(sets):record.update(n=retained,members=int(bits[complete,i].sum()),missing=int((~observed[i]).sum()))
    return dict(names=names,sets=sets,patterns=patterns,inputRows=total,retained=retained,excluded=total-retained,
                masks=[int(v) if keep else None for v,keep in zip(masks,complete)],
                bits=[[int(v) for v in row] if keep else None for row,keep in zip(bits,complete)],
                union=retained-int(counts[0]),allSets=int(counts[-1]))
