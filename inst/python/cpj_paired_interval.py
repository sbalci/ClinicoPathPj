"""Source-only Newcombe method-10 limits for paired binary differences.

Counts are both-success, first-only, second-only and neither-success. Limits are
pointwise approximations, not multiplicity-adjusted or equivalence conclusions.
See docs/python-paired-difference-intervals.md for the pinned method contract.
"""
import math
from numbers import Real

import numpy as np
from scipy.stats import norm

from cpj_runtime import InputError

MAX_INTERVAL_N = 1_000_000


def _wilson(successes, n, z):
    p = successes/n
    denominator = n+z*z
    center = (successes+z*z/2)/denominator
    half = z*math.sqrt(successes*(n-successes)/n+z*z/4)/denominator
    # Roundoff guards preserve the known marginal estimate at exact boundaries.
    return min(p, max(0., center-half)), max(p, min(1., center+half))


def newcombe_interval(counts, confidence=.95):
    """Return method-10 estimate, limits, corrected phi, N, cells and status.

    Confidence accepts 80–99%; all-zero cells have explicitly undefined output.
    Positive AD-BC is reduced by n/2 and floored at zero; negative AD-BC is retained.
    """
    if (isinstance(confidence, (bool, np.bool_)) or not isinstance(confidence, Real)
            or not math.isfinite(confidence) or not .8 <= confidence <= .99):
        raise InputError('Paired-difference confidence must be between 0.80 and 0.99.')
    if np.ma.isMaskedArray(counts) or not isinstance(counts, (list, tuple, np.ndarray)):
        raise InputError('Supply four unmasked paired counts in a one-dimensional vector.')
    if isinstance(counts, np.ndarray) and counts.ndim != 1:
        raise InputError('Supply four paired counts in a one-dimensional vector.')
    if len(counts) != 4:
        raise InputError('Supply exactly four paired counts: both, first-only, second-only, neither.')
    cells = []
    for value in counts:
        if (isinstance(value, (bool, np.bool_)) or not isinstance(value, Real)
                or not math.isfinite(value) or not 0 <= value <= MAX_INTERVAL_N
                or int(value) != value):
            raise InputError('Paired counts must be nonnegative finite integers.')
        cells.append(int(value))
    a, b, c, d = cells
    n = sum(cells)
    if n > MAX_INTERVAL_N:
        raise InputError('Paired-difference intervals accept at most 1,000,000 observations.')
    result = dict(estimate=None, lower=None, upper=None, phi=None, n=n,
                  counts=cells, confidence=float(confidence), status='empty')
    if not n:
        return result
    z = float(norm.ppf((1+confidence)/2))
    first, second, estimate = (a+b)/n, (a+c)/n, (b-c)/n
    lower1, upper1 = _wilson(a+b, n, z)
    lower2, upper2 = _wilson(a+c, n, z)
    product = (a+b)*(c+d)*(a+c)*(b+d)
    numerator = a*d-b*c
    if numerator > 0:
        numerator = max(0., numerator-n/2)
    phi = numerator/math.sqrt(product) if product else 0.
    if not -1-1e-12 <= phi <= 1+1e-12:
        raise InputError('Paired correlation is numerically unresolved.')
    phi = min(1., max(-1., phi))
    lower_square = math.fsum(((first-lower1)**2, (upper2-second)**2,
                               -2*phi*(first-lower1)*(upper2-second)))
    upper_square = math.fsum(((upper1-first)**2, (second-lower2)**2,
                               -2*phi*(upper1-first)*(second-lower2)))
    if min(lower_square, upper_square) < -1e-14:
        raise InputError('Paired interval distances are numerically unresolved.')
    result.update(estimate=estimate, lower=max(-1., estimate-math.sqrt(max(0., lower_square))),
                  upper=min(1., estimate+math.sqrt(max(0., upper_square))),
                  phi=phi, status='ok')
    return result
