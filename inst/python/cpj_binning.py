"""Validated interval construction and categorical assignment; no R execution."""
import math
import numpy as np
from cpj_runtime import InputError


def fisher_jenks(x, k):
    """Exact weighted 1-D least-squares partition via monotone divide-and-conquer DP."""
    values,weights=np.unique(x,return_counts=True)
    m=len(values)
    if m<2:raise InputError('Natural breaks need at least two different values.')
    if len(x)>20000 and m>3000:
        raise InputError('Large-sample seeded Jenks subsampling is not yet implemented. Use at most 20,000 observations, at most 3,000 distinct values, or choose another method.')
    k=min(k,m)
    if k==m:
        half=np.mean(np.diff(values))/2
        return np.r_[values[0]-half,values[:-1]+np.diff(values)/2,values[-1]+half]
    # Scaling avoids cancellation when measurements have a large common offset.
    z=values.astype(np.longdouble)
    z=(z-z[0])/(z[-1]-z[0])
    w=np.r_[np.longdouble(0),np.cumsum(weights,dtype=np.longdouble)]
    sx=np.r_[0,np.cumsum(weights*z)];sx2=np.r_[0,np.cumsum(weights*z*z)]
    previous=np.full(m+1,np.inf,dtype=np.longdouble);previous[0]=0
    splits=np.zeros((k+1,m+1),dtype=np.int32)
    for group in range(1,k+1):
        current=np.full(m+1,np.inf,dtype=np.longdouble)
        def solve(left,right,lo,hi):
            if left>right:return
            mid=(left+right)//2
            candidates=np.arange(lo,min(hi,mid-1)+1)
            count=w[mid]-w[candidates];total=sx[mid]-sx[candidates]
            sse=np.maximum(0,sx2[mid]-sx2[candidates]-total*total/count)
            costs=previous[candidates]+sse
            minimum=np.min(costs)
            # Equal-objective partitions choose the first boundary, as classInt does.
            # Only values within an arithmetic-roundoff bound are treated as ties.
            tolerance=8*np.finfo(np.longdouble).eps*max(1,sx2[mid],abs(minimum))
            best=int(candidates[np.flatnonzero(costs<=minimum+tolerance)[0]])
            current[mid]=costs[np.flatnonzero(candidates==best)[0]];splits[group,mid]=best
            solve(left,mid-1,lo,best);solve(mid+1,right,best,hi)
        solve(group,m,group-1,m-1)
        previous=current
    cuts=[];end=m
    for group in range(k,1,-1):
        cut=int(splits[group,end]);cuts.append(values[cut-1]+(values[cut]-values[cut-1])/2);end=cut
    return np.r_[values[0],sorted(cuts),values[-1]]


def make_breaks(x,method='quantile',nbins=4,manual='',sdmult=1,exclude_outside=False):
    if len(x)<2 or min(x)==max(x):raise InputError('At least two non-missing observations with nonzero variability are needed.')
    if isinstance(nbins,bool) or not isinstance(nbins,int) or not 2<=nbins<=20:raise InputError('Number of categories must be an integer from 2 to 20.')
    if isinstance(sdmult,bool) or not isinstance(sdmult,(int,float)) or not math.isfinite(sdmult) or not .5<=sdmult<=3:raise InputError('SD multiplier must lie between 0.5 and 3.')
    notes=[]
    if method=='equal':b=np.linspace(min(x),max(x),nbins+1)
    elif method=='quantile':b=np.unique(np.quantile(x,np.linspace(0,1,nbins+1),method='linear'))
    elif method=='manual':
        try:
            pieces=manual.split(',')
            if not manual.strip() or any(not p.strip() for p in pieces):raise ValueError()
            b=np.array([float(p.strip()) for p in pieces])
        except (ValueError,AttributeError):raise InputError('Enter finite comma-separated numeric break points.') from None
        if not np.all(np.isfinite(b)):raise InputError('Break points must be finite.')
        b=np.unique(b)
    elif method=='meansd':
        mean=float(np.mean(x));sd=float(np.std(x,ddof=1));lo=mean-sdmult*sd;hi=mean+sdmult*sd
        b=[min(x),mean,max(x)]
        if lo>min(x):b.append(lo)
        else:notes.append('The lower mean/SD band was dropped because its boundary lies at or below the data minimum.')
        if hi<max(x):b.append(hi)
        else:notes.append('The upper mean/SD band was dropped because its boundary lies at or above the data maximum.')
        b=np.unique(b)
    elif method=='median':
        med=float(np.median(x))
        if med==min(x) or med==max(x):raise InputError('The median equals a data endpoint; a median split cannot form two nonzero-width intervals.')
        b=np.array([min(x),med,max(x)])
    elif method=='jenks':
        b=fisher_jenks(x,nbins)
        notes.append('Fisher-Jenks breaks use the full observed data; no random seed is used in this exact branch.')
    else:raise InputError('Unknown binning method.')
    if method!='manual' or not exclude_outside:b=np.unique(np.r_[min(min(b),min(x)),b,max(max(b),max(x))])
    if len(b)<2 or not np.all(np.isfinite(b)) or np.any(np.diff(b)<=0):raise InputError('Break points must contain at least two distinct finite boundaries.')
    if np.min(np.diff(b))/(b[-1]-b[0])<1e-10:raise InputError('Break points are too close together relative to their range.')
    if method in ('quantile','jenks') and len(b)-1!=nbins:notes.append(f'Ties/distinct values produced {len(b)-1} categories instead of the requested {nbins}.')
    return b,notes


def interval_labels(b,include_lowest=True,right=True):
    digits=max(1,int(math.ceil(-math.log10(float(np.min(np.diff(b))))))+1)
    digits=min(digits,12)
    while digits<12 and len(set(f'{v:.{digits}f}' for v in b))<len(b):digits+=1
    fmt=(lambda v:f'{v:.{digits}f}') if len(set(f'{v:.{digits}f}' for v in b))==len(b) else (lambda v:f'{v:.17g}')
    return [('[' if not right or (i==0 and include_lowest) else '(')+fmt(a)+', '+fmt(z)+
            (']' if right or (i==len(b)-2 and include_lowest) else ')') for i,(a,z) in enumerate(zip(b[:-1],b[1:]))]


def labels_for(b,style='auto',custom='',include_lowest=True,right=True):
    k=len(b)-1;fallback=[f'Category {i+1}' for i in range(k)];warning=None
    if style=='auto':labels=interval_labels(b,include_lowest,right)
    elif style=='semantic':
        labels={2:['Low','High'],3:['Low','Medium','High'],4:['Low','Medium-Low','Medium-High','High'],5:['Very Low','Low','Medium','High','Very High']}.get(k,
          ['Very Low','Low','Medium-Low','Medium','Medium-High','High','Very High'][:k] if k<=7 else [f'Level {i+1}' for i in range(k)])
    elif style=='numbered':labels=[str(i+1) for i in range(k)]
    elif style=='lettered':labels=[chr(65+i) for i in range(k)] if k<=26 else fallback
    elif style=='custom':
        labels=[p.strip() for p in custom.split(',')]
        if not custom or len(labels)!=k or len(set(labels))!=k:
            labels=fallback;warning='Custom labels were empty, duplicated or did not match the number of categories; numbered category labels were used.'
    else:raise InputError('Unknown category-label style.')
    return labels,warning


def assign(values,b,include_lowest=True,right=True):
    code=np.searchsorted(b,values,side='left' if right else 'right')-1
    if include_lowest:code[values==(b[0] if right else b[-1])]=0 if right else len(b)-2
    code[(code<0)|(code>=len(b)-1)|np.isnan(values)]=-1
    return code
