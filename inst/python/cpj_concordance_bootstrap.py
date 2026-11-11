"""Source-only paired percentile CCC bootstrap; no public jamovi integration."""
import hashlib
import math
from numbers import Integral, Real

import numpy as np

from cpj_concordance import concordance, _numeric
from cpj_runtime import InputError


def _integer(value, minimum, maximum, label):
    if (isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral)
            or not minimum <= value <= maximum):
        raise InputError(f'{label} must be an integer from {minimum} to {maximum}.')
    return int(value)


def _replicates(x, y, indices):
    """Paired resamples, centered separately; constants have their exact meaning."""
    a, b = x[indices], y[indices]
    origin = a[:, :1].copy()
    a, b = a-origin, b-origin
    scale = np.maximum(np.max(np.abs(a), axis=1), np.max(np.abs(b), axis=1))
    scale = np.where(scale > 0, scale, 1.)
    a, b = a/scale[:, None], b/scale[:, None]
    ma, mb = a.mean(axis=1), b.mean(axis=1)
    da, db = a-ma[:, None], b-mb[:, None]
    denominator = np.mean(da*da, axis=1)+np.mean(db*db, axis=1)+(ma-mb)**2
    numerator = 2*np.mean(da*db, axis=1)
    with np.errstate(divide='ignore', invalid='ignore'):
        rho = numerator/denominator
    invalid = (~np.isfinite(rho)) | (np.abs(rho) > 1+32*np.finfo(float).eps)
    # Resolve only arithmetic overshoot at the mathematical parameter boundary.
    rho = np.minimum(1., np.maximum(-1., rho))
    rho[invalid] = np.nan
    return rho


def bootstrap_concordance_interval(x, y, confidence=.95, resamples=1999,
                                   seed=20261111, indices=None,
                                   return_distribution=False, checkpoint=None):
    """Equal-tailed paired percentile bootstrap with explicit failed-draw policy.

    Assumes iid complete measurement pairs. A local PCG64 generator leaves global
    RNG state unchanged. Explicit indices address the retained cohort, not source
    row positions, and allow cross-language replay without RNG equivalence claims.
    No degenerate draw is dropped or redrawn; any undefined draw withholds the CI.
    """
    if (isinstance(confidence, (bool, np.bool_)) or not isinstance(confidence, Real)
            or not math.isfinite(confidence) or not .8 <= confidence <= .99):
        raise InputError('CCC confidence must be a finite number between 0.80 and 0.99.')
    count = _integer(resamples, 199, 9999, 'Bootstrap resamples')
    seed = _integer(seed, 0, 4294967295, 'Bootstrap seed')
    if not isinstance(return_distribution, (bool, np.bool_)):
        raise InputError('return_distribution must be boolean.')
    if checkpoint is not None and not callable(checkpoint):
        raise InputError('checkpoint must be callable when supplied.')
    point = concordance(x, y)
    n = point['n_complete']
    if n < 10:
        raise InputError('CCC intervals require at least 10 complete independent pairs.')
    if n*count > 10000000:
        raise InputError('Bootstrap work exceeds 10,000,000 resampled pairs; reduce resamples.')
    supplied = indices is not None
    if supplied:
        try:
            indices = np.asarray(indices)
        except (TypeError, ValueError) as error:
            raise InputError('Bootstrap indices must be a rectangular integer matrix.') from error
        if (indices.shape != (count, n) or indices.dtype.kind not in 'iu'
                or np.any(indices < 0) or np.any(indices >= n)):
            raise InputError('Bootstrap indices must be integers shaped (resamples, complete pairs), '
                             'between zero and complete pairs minus one.')
    result = dict(estimate=point['ccc'], lower=None, upper=None, se=None,
                  confidence=float(confidence), method='paired-percentile',
                  quantile_method='linear (R type 7)', n_complete=n, resamples=count,
                  resamples_evaluated=0, undefined_resamples=0, index_sha256=None,
                  seed=None if supplied else seed,
                  index_source='supplied' if supplied else 'NumPy PCG64',
                  distribution=None, status='unavailable', reason='', point=point)
    if point['ccc'] is None or abs(point['ccc']) == 1:
        result['reason'] = 'Source CCC is undefined or on the parameter boundary.'
        return result
    retained = point['retained_indices']
    a, b = _numeric(x)[retained], _numeric(y)[retained]
    with np.errstate(over='ignore', invalid='ignore'):
        u, v = a-a[0], b-a[0]
    if not np.isfinite(u).all() or not np.isfinite(v).all():
        scale = max(float(np.max(np.abs(a))), float(np.max(np.abs(b))))
        u, v = a/scale, b/scale
        origin = float(u[0])
        u, v = u-origin, v-origin
    scale = max(float(np.max(np.abs(u))), float(np.max(np.abs(v))))
    u, v = u/scale, v/scale
    rng = np.random.Generator(np.random.PCG64(seed))
    digest = hashlib.sha256()
    draws = np.empty(count)
    for start in range(0, count, 64):
        if checkpoint is not None:
            checkpoint()
        end = min(start+64, count)
        batch = (indices[start:end] if supplied else
                 rng.integers(0, n, size=(end-start, n), dtype=np.int64))
        digest.update(np.asarray(batch, dtype='<i8').tobytes(order='C'))
        draws[start:end] = _replicates(u, v, batch)
    if checkpoint is not None:
        checkpoint()
    invalid = int(np.count_nonzero(~np.isfinite(draws)))
    result.update(resamples_evaluated=count, undefined_resamples=invalid,
                  index_sha256=digest.hexdigest())
    if return_distribution:
        result['distribution'] = [float(z) if math.isfinite(z) else None for z in draws]
    if invalid:
        result['reason'] = 'At least one bootstrap CCC is undefined or numerically unresolved; '
        result['reason'] += 'no resamples were dropped or redrawn.'
        return result
    tail = (1-float(confidence))/2
    lower, upper = np.quantile(draws, (tail, 1-tail), method='linear')
    se = float(np.std(draws, ddof=1))
    if not (math.isfinite(se) and se > 0 and lower < upper):
        result['reason'] = 'Bootstrap distribution or percentile interval is degenerate.'
        return result
    result.update(lower=float(lower), upper=float(upper), se=se, status='ok', reason='')
    return result
