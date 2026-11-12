"""Source-only two-group/paired raw-mean estimation; no public SPEC or menu entry.

Contrast is first minus second. Advanced baseline methods and standardized
effects remain outside this bounded core; see docs/python-estimation-core.md.
"""
from numbers import Real
import math

import numpy as np
from scipy.stats import t

from cpj_runtime import Factor, InputError

MAX_ROWS = 100_000


def _numeric(values, name):
    if np.ma.isMaskedArray(values):
        raise InputError(f'{name}: masked values are unsupported; use NaN for missing cells.')
    if isinstance(values, (list, tuple)) and any(isinstance(v, (bool, np.bool_)) for v in values):
        raise InputError(f'{name}: use numeric measurements, not boolean values.')
    try:
        raw = np.asarray(values)
    except (TypeError, ValueError):
        raise InputError(f'{name}: supply a one-dimensional numeric vector.') from None
    if raw.ndim != 1 or raw.dtype.kind not in 'iufO':
        raise InputError(f'{name}: supply a one-dimensional numeric vector.')
    if raw.dtype.kind == 'O' and any(v is not None and
            (not isinstance(v, Real) or isinstance(v, (bool, np.bool_))) for v in raw):
        raise InputError(f'{name}: only numeric measurements and missing cells are supported.')
    with np.errstate(over='ignore', invalid='ignore'):
        try:
            result = raw.astype(float)
        except (TypeError, ValueError, OverflowError):
            raise InputError(f'{name}: measurements exceed the supported numeric range.') from None
    if np.isinf(result).any():
        raise InputError(f'{name}: infinite values are invalid; they are not missing observations.')
    if not 1 <= len(result) <= MAX_ROWS:
        raise InputError('The source estimation core accepts 1–100,000 source rows.')
    return result


def _confidence(value):
    if (not isinstance(value, Real) or isinstance(value, (bool, np.bool_))
            or not math.isfinite(value) or not .5 <= value <= .999):
        raise InputError('Confidence must be a finite number between 0.50 and 0.999.')


def _ids(subject_ids, n, keep):
    if subject_ids is None:
        return None
    if np.ma.isMaskedArray(subject_ids):
        raise InputError('Subject IDs must be aligned strings or missing cells.')
    try:
        ids = np.asarray(subject_ids, dtype=object)
    except (TypeError, ValueError):
        raise InputError('Subject IDs must be aligned strings or missing cells.') from None
    if (ids.ndim != 1 or len(ids) != n or
            any(x is not None and (not isinstance(x, str) or not x.strip()) for x in ids)):
        raise InputError('Subject IDs must be aligned nonempty strings or missing cells.')
    retained = ids[keep].tolist()
    if any(x is None for x in retained):
        raise InputError('Every retained case needs a known subject ID when IDs are supplied.')
    if len(set(retained)) != len(retained):
        raise InputError('Retained subject IDs must be unique; repeated cases need a different design.')
    return retained


def _summary(values):
    with np.errstate(over='ignore', invalid='ignore'):
        centered = values-values[0]
        mean = float(values[0]+np.mean(centered))
        sd = float(np.std(centered, ddof=1))
    if not math.isfinite(mean) or not math.isfinite(sd):
        raise InputError('Derived means or variances exceed the supported numeric range.')
    if sd == 0 and np.any(values != values[0]):
        raise InputError('Measurement variance underflows the supported numeric range.')
    return dict(n=len(values), mean=mean, sd=sd)


def _inference(a, b, confidence, method, summaries):
    first, second = summaries['first'], summaries['second']
    n1, n2 = first['n'], second['n']
    with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
        if method == 'paired_t':
            differences = a-b
            difference = float(np.mean(differences))
            se = float(np.std(differences, ddof=1)/np.sqrt(n1))
            df = n1-1.
            scale = abs(difference)
        else:
            difference = first['mean']-second['mean']
            v1, v2 = np.float64(first['sd'])**2, np.float64(second['sd'])**2
            if method == 'student':
                df = n1+n2-2.
                pooled = ((n1-1)*v1+(n2-1)*v2)/df
                se = float(np.sqrt(pooled*(1/n1+1/n2)))
            else:
                u, v = v1/n1, v2/n2
                se = float(np.sqrt(u+v))
                # Normalize before squaring: direct fourth moments can overflow.
                df = float(1/((u/(u+v))**2/(n1-1)+(v/(u+v))**2/(n2-1))) if u+v > 0 else None
            scale = max(abs(first['mean']), abs(second['mean']))
    if not math.isfinite(difference) or not math.isfinite(se):
        raise InputError('The difference or its standard error exceeds the supported numeric range.')
    if se == 0 and (np.any(differences != differences[0]) if method == 'paired_t'
                    else first['sd'] > 0 or second['sd'] > 0):
        raise InputError('The standard error underflows the supported numeric range.')
    result = dict(difference=difference, stderr=None, df=None, statistic=None,
                  p=None, lower=None, upper=None, status='degenerate')
    if se == 0 or se < 10*np.finfo(float).eps*scale:
        return result
    statistic = difference/se
    half = float(t.ppf((1+confidence)/2, df))*se
    lower, upper = difference-half, difference+half
    if not all(math.isfinite(v) for v in (df, statistic, lower, upper)):
        raise InputError('Inferential results exceed the supported numeric range.')
    result.update(stderr=se, df=float(df), statistic=statistic,
                  p=float(2*t.sf(abs(statistic), df)), lower=lower, upper=upper, status='ok')
    return result


def between_estimation(values, group, first_level, second_level, *,
                       equal_variances=False, confidence=.95, subject_ids=None):
    """Independent samples, explicit first-minus-second contrast; Welch by default."""
    _confidence(confidence)
    if not isinstance(equal_variances, bool):
        raise InputError('Choose explicitly whether to assume equal variances.')
    y = _numeric(values, 'Outcome')
    if (not isinstance(group, Factor) or not isinstance(group.levels, (list, tuple))
            or not all(isinstance(x, str) for x in group.levels)
            or len(set(group.levels)) != len(group.levels)):
        raise InputError('Group must be a factor with distinct string labels.')
    if (not isinstance(first_level, str) or not isinstance(second_level, str)
            or first_level not in group.levels or second_level not in group.levels
            or first_level == second_level):
        raise InputError('Choose distinct first and second group levels explicitly.')
    if (np.ma.isMaskedArray(group.codes) or isinstance(group.codes, (list, tuple))
            and any(isinstance(v, (bool, np.bool_)) for v in group.codes)):
        raise InputError('Use integer group codes and -1 for missing cells.')
    try:
        g = np.asarray(group.codes)
    except (TypeError, ValueError):
        raise InputError('Use aligned valid integer group codes and -1 for missing cells.') from None
    if (g.ndim != 1 or len(g) != len(y) or g.dtype.kind not in 'iu'
            or np.any(g < -1) or np.any(g >= len(group.levels))):
        raise InputError('Use aligned valid integer group codes and -1 for missing cells.')
    keep = ~np.isnan(y) & (g >= 0)
    first, second = group.levels.index(first_level), group.levels.index(second_level)
    if np.any(keep & (g != first) & (g != second)):
        raise InputError('This core requires exactly two groups with complete outcome data.')
    a_indices, b_indices = np.flatnonzero(keep & (g == first)), np.flatnonzero(keep & (g == second))
    if len(a_indices) < 2 or len(b_indices) < 2:
        raise InputError('Each selected group needs at least two complete independent observations.')
    ids = _ids(subject_ids, len(y), keep)
    a, b = y[a_indices], y[b_indices]
    summaries = dict(first=_summary(a), second=_summary(b))
    method = 'student' if equal_variances else 'welch'
    return dict(schema_version=1, design='independent', method=method, confidence=float(confidence),
        n_source=len(y), n_complete=int(keep.sum()), excluded_missing=int((~keep).sum()),
        missing_by_role=dict(outcome=int(np.isnan(y).sum()), group=int((g < 0).sum())),
        retained_indices=np.flatnonzero(keep).tolist(), first_indices=a_indices.tolist(),
        second_indices=b_indices.tolist(), mapping=dict(first=first_level, second=second_level),
        retained_subject_ids=ids, summaries=summaries, **_inference(a,b,confidence,method,summaries))


def within_estimation(first, second, *, confidence=.95, subject_ids=None):
    """Two wide measurements paired by original row; minimum three complete subjects."""
    _confidence(confidence)
    a, b = _numeric(first, 'First measurement'), _numeric(second, 'Second measurement')
    if len(a) != len(b):
        raise InputError('Paired measurements must have aligned source rows.')
    keep = ~np.isnan(a) & ~np.isnan(b)
    if keep.sum() < 3:
        raise InputError('Paired estimation needs at least three complete independent subjects.')
    ids = _ids(subject_ids, len(a), keep)
    summaries = dict(first=_summary(a[keep]), second=_summary(b[keep]))
    indices = np.flatnonzero(keep).tolist()
    return dict(schema_version=1, design='paired', method='paired_t', confidence=float(confidence),
        n_source=len(a), n_complete=int(keep.sum()), excluded_missing=int((~keep).sum()),
        missing_by_role=dict(first=int(np.isnan(a).sum()), second=int(np.isnan(b).sum())),
        retained_indices=indices, first_indices=indices[:], second_indices=indices[:],
        retained_subject_ids=ids, summaries=summaries, **_inference(a[keep],b[keep],confidence,'paired_t',summaries))
