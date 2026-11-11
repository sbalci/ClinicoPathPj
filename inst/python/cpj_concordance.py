"""Lin concordance point estimates for complete independent measurement pairs.

Prototype engine only: no public SPEC, confidence intervals or interpretation bands.
Variance/covariance divisors are n, not n-1. Callers own units, case-ID validation
and the distinction between independent cases and repeated observations.
"""
import math

import numpy as np

from cpj_runtime import InputError


def _numeric(values):
    if np.ma.isMaskedArray(values) or (isinstance(values, (list, tuple)) and
            any(isinstance(value, (bool, np.bool_)) for value in values)):
        raise InputError('Use numeric measurements with NaN missing cells, not masks or booleans.')
    try:
        array = np.asarray(values)
    except (TypeError, ValueError):
        raise InputError('Supply aligned one-dimensional numeric measurements.') from None
    if array.ndim != 1 or array.dtype.kind not in 'fiu':
        raise InputError('Measurements must be one-dimensional numeric values, not codes or booleans.')
    if array.dtype.kind in 'iu':
        outside = array > 2**53
        if array.dtype.kind == 'i':
            outside = outside | (array < -(2**53))
        if np.any(outside):
            raise InputError('Integer measurements exceed the exact supported range of plus/minus 2^53.')
    with np.errstate(over='ignore', invalid='ignore'):
        array = array.astype(np.float64)
    if np.isinf(array).any():
        raise InputError('Measurements must be finite or missing; infinite values are unsupported.')
    return array


def _bounded(value, lower, upper):
    tolerance = 64 * np.finfo(float).eps
    if not math.isfinite(value) or value < lower - tolerance or value > upper + tolerance:
        raise InputError('Concordance moments are numerically unresolved; check ranges and units.')
    return min(upper, max(lower, value))


def concordance(x, y):
    """Return CCC, Pearson precision, bias correction and complete-pair audit.

    Supports 3–5,000 complete pairs within at most 5,000 input rows. NaN denotes
    missingness; whole pairs are removed. Returned indices are zero-based source
    positions. Identical constants yield an explicitly undefined CCC (0/0).
    A constant versus another column has CCC=0 but undefined Pearson precision.
    """
    try:
        aligned = len(x) == len(y) and 1 <= len(x) <= 5000
    except TypeError:
        aligned = False
    if not aligned:
        raise InputError('Supply one to 5,000 aligned source rows.')
    x, y = _numeric(x), _numeric(y)
    missing_x, missing_y = np.isnan(x), np.isnan(y)
    retained = np.flatnonzero(~(missing_x | missing_y))
    n = len(retained)
    if n < 3:
        raise InputError('Concordance requires at least three complete independent measurement pairs.')
    result = dict(n_input=len(x), n_complete=n, missing_x=int(missing_x.sum()),
                  missing_y=int(missing_y.sum()), missing_either=len(x)-n,
                  missing_both=int((missing_x & missing_y).sum()),
                  retained_indices=retained.tolist(), moment_divisor='n',
                  ccc=None, precision=None, bias_correction=None,
                  undefined_reason='', precision_undefined_reason='', confidence_interval=None)
    a, b = x[retained], y[retained]
    varying_a, varying_b = bool(np.any(a != a[0])), bool(np.any(b != b[0]))
    # Translate before scaling to preserve small differences at a large common
    # offset. If subtraction overflows, scale first, then use a common origin.
    with np.errstate(over='ignore', invalid='ignore'):
        u, v = a - a[0], b - a[0]
    if not np.isfinite(u).all() or not np.isfinite(v).all():
        scale = max(float(np.max(np.abs(a))), float(np.max(np.abs(b))))
        u, v = a / scale, b / scale
        origin = float(u[0])
        u, v = u - origin, v - origin
    scale = max(float(np.max(np.abs(u))), float(np.max(np.abs(v))))
    if scale == 0:
        result['undefined_reason'] = 'Both complete measurement columns are identical constants (0/0).'
        result['precision_undefined_reason'] = 'Both complete measurement columns are constant.'
        return result
    u, v = u / scale, v / scale
    mu, mv = math.fsum(u) / n, math.fsum(v) / n
    du, dv = u - mu, v - mv
    vx = math.fsum(float(z) * float(z) for z in du) / n if varying_a else 0.
    vy = math.fsum(float(z) * float(z) for z in dv) / n if varying_b else 0.
    covariance = (math.fsum(float(p) * float(q) for p, q in zip(du, dv)) / n
                  if varying_a and varying_b else 0.)
    if (varying_a and vx == 0) or (varying_b and vy == 0):
        raise InputError('Measurement variation is numerically unresolved; check ranges and units.')
    denominator = math.fsum((vx, vy, (mu-mv)**2))
    if denominator <= 0:
        raise InputError('Concordance denominator is numerically unresolved; check ranges and units.')
    result['ccc'] = _bounded(2 * covariance / denominator, -1., 1.)
    product_sd = math.sqrt(vx) * math.sqrt(vy)
    result['bias_correction'] = _bounded(2 * product_sd / denominator, 0., 1.)
    if not varying_a or not varying_b:
        result['precision_undefined_reason'] = 'At least one complete measurement column is constant.'
    elif product_sd == 0:
        raise InputError('Precision is numerically unresolved; check ranges and units.')
    else:
        result['precision'] = _bounded(covariance / product_sd, -1., 1.)
    return result
