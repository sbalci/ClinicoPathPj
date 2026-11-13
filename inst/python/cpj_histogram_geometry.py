"""Bounded ggstatsplot-width/ggplot2-bin geometry; no silent observation loss."""
import math
from numbers import Real

import numpy as np

from cpj_histogram import MAX_BINS, _cohort
from cpj_runtime import InputError


def histogram_geometry(values, *, width=None, subject_ids=None):
    """Construct right-closed fuzzy counting bins and unfuzzed drawing bounds."""
    automatic = width is None
    if not automatic and (not isinstance(width,Real) or isinstance(width,(bool,np.bool_))
                          or not math.isfinite(width) or width<=0):
        raise InputError('Manual histogram width must be a positive finite real number.')
    x,result = _cohort(values,subject_ids)
    if automatic:
        width = (float(np.max(x))-float(np.min(x)))/math.sqrt(len(x))
    width = float(width)
    result.update(automatic=automatic,width=width,raw_edges=[],fuzzy_edges=[],bins=[],
                  geometry_status='ok',reason=None)
    if automatic and width==0:
        result.update(geometry_status='constant_auto',
            reason='Automatic width is zero for constant data; select a positive manual bin width to draw a histogram.')
        return result
    if not math.isfinite(width) or width<=0:
        raise InputError('Automatic histogram width exceeds the supported numeric range.')
    lo,hi = float(np.min(x)),float(np.max(x))
    boundary = width/2
    shift = (lo-boundary)/width
    upper = hi+(1-1e-8)*width
    if not all(math.isfinite(v) for v in (boundary,shift,upper)):
        raise InputError('Histogram edge placement exceeds the supported numeric range.')
    origin = boundary+math.floor(shift)*width
    span = upper-origin
    steps = span/width
    if not math.isfinite(steps) or steps>MAX_BINS+1:
        raise InputError('Histogram requires more than 2,000 bins; select a larger manual width.')
    # R seq treats almost-equal endpoints at a large offset as identical. Its
    # ensuing two-edge fallback can silently lose cases. Refuse that geometry.
    if span<=100*np.finfo(float).eps*max(abs(origin),abs(upper)):
        raise InputError('Histogram edge spacing is unsafe at this numeric offset; rescale or center the measurement explicitly.')
    if steps<0:
        raise InputError('Histogram edges do not span the retained measurements.')
    # R seq's integer-length allowance; clamp a rounding overshoot to its endpoint.
    nsteps = math.floor(steps+1e-10)
    edges = origin+np.arange(nsteps+1,dtype=float)*width
    if edges[-1]>upper:edges[-1]=upper
    if len(edges)==1:edges=np.array([edges[0],edges[0]+width])
    widths = np.diff(edges)
    if (len(widths)>MAX_BINS or not np.all(np.isfinite(edges))
            or not np.all(np.isfinite(widths)) or np.any(widths<=0)):
        raise InputError('Histogram edges collapse or exceed the supported 2,000-bin numeric range.')
    fuzz = 1e-8*float(np.median(widths))
    fuzzy = edges+np.r_[-fuzz,np.repeat(fuzz,len(widths))]
    if not np.all(np.isfinite(fuzzy)) or np.any(np.diff(fuzzy)<=0):
        raise InputError('Histogram counting edges are not finite and strictly increasing.')
    if np.any(x<fuzzy[0]) or np.any(x>fuzzy[-1]):
        raise InputError('Histogram geometry would lose retained observations; rescale or select another explicit manual width.')
    indices = np.searchsorted(fuzzy,x,side='left')-1
    indices[x==fuzzy[0]]=0
    if np.any(indices<0) or np.any(indices>=len(widths)):
        raise InputError('Histogram counting failed to assign every retained observation exactly once.')
    counts = np.bincount(indices,minlength=len(widths))
    with np.errstate(over='ignore',under='ignore',invalid='ignore'):
        centers = (edges[:-1]+edges[1:])/2
        lower,upper_bounds = centers-widths/2,centers+widths/2
        proportions = counts/len(x)
        density = counts/widths/len(x)
    if (not all(np.all(np.isfinite(v)) for v in (centers,lower,upper_bounds,density))
            or np.any(upper_bounds<=lower) or np.any((counts>0)&(density==0))):
        raise InputError('Histogram display bounds or density exceed the supported numeric range.')
    result.update(raw_edges=edges.tolist(),fuzzy_edges=fuzzy.tolist(),bins=[dict(
        center=float(center),width=float(w),lower=float(a),upper=float(b),
        count=int(count),proportion=float(proportion),density=float(d))
        for center,w,a,b,count,proportion,d in zip(centers,widths,lower,upper_bounds,counts,proportions,density)])
    return result
