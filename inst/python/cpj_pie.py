"""Single-factor pie counts and polar geometry; no inferential calculations."""
import math

import numpy as np

from cpj_barstats import MAX_TOTAL, _factor
from cpj_estimation import _ids, _numeric
from cpj_runtime import InputError


def pie_core(outcome, *, weights=None, subject_ids=None):
    """Accumulate integer observation frequencies without expanding source rows.

    Preserve nonmissing declared categories, including zero slices. Angles are
    radians clockwise from twelve o'clock, in reverse factor stacking order.
    """
    codes, labels = _factor(outcome, 'Outcome')
    n = len(codes)
    if not 1 <= n <= 100000:
        raise InputError('Supply 1–100,000 source rows for the categorical outcome.')
    categories = [i for i, label in enumerate(labels) if label is not None]
    if not 1 <= len(categories) <= 20:
        raise InputError('This pie core supports 1–20 declared nonmissing categories.')
    if weights is not None and subject_ids is not None:
        raise InputError('Subject-ID auditing is unavailable for aggregated frequency rows.')
    frequency = np.ones(n) if weights is None else _numeric(weights, 'Frequencies')
    if len(frequency) != n:
        raise InputError('Frequencies must align with the factor source rows.')
    known = ~np.isnan(frequency)
    if np.any(frequency[known] < 0) or np.any(frequency[known] != np.floor(frequency[known])):
        raise InputError('Frequencies must be nonnegative whole numbers or missing.')
    if np.any(frequency[known] > MAX_TOTAL):
        raise InputError('Frequency total must not exceed 2^53 - 1.')
    complete = (codes >= 0) & known
    positive = complete & (frequency > 0)
    if not np.any(positive):
        raise InputError('No complete positive-frequency observations remain.')
    indices = np.flatnonzero(positive).tolist()
    totals = {code: 0 for code in categories}
    for i in indices:
        totals[int(codes[i])] += int(frequency[i])
    total = sum(totals.values())
    if total > MAX_TOTAL:
        raise InputError('Frequency total must not exceed 2^53 - 1.')
    ids = _ids(subject_ids, n, positive)
    cells = []
    above = total
    for code in categories:
        count = totals[code]
        below = above - count
        lo, hi = below / total, above / total
        theta = math.tau * ((lo + hi) / 2)
        cells.append(dict(code=code, label=labels[code], count=count,
            proportion=count / total, lower=lo, upper=hi,
            theta_lower=math.tau * lo, theta_upper=math.tau * hi, theta_center=theta,
            anchor_x=math.sin(theta) if count else None,
            anchor_y=math.cos(theta) if count else None))
        above = below
    return dict(schema_version=1, status='ok', n_source=n,
        n_complete=int(np.sum(complete)), excluded_missing=int(np.sum(~complete)),
        missing_outcome=int(np.sum(codes < 0)), missing_frequency=int(np.sum(~known)),
        zero_frequency=int(np.sum(complete & (frequency == 0))),
        n_contributing=len(indices), n_total=total, retained_indices=indices,
        retained_subject_ids=ids, missing_level_codes=[i for i, v in enumerate(labels) if v is None],
        cells=cells)
