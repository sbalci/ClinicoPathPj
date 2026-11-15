"""Bounded descriptive waffle allocation and static plot-ready tile geometry."""
import numpy as np

from cpj_barstats import MAX_TOTAL, _factor
from cpj_estimation import _ids, _numeric
from cpj_runtime import InputError


def waffle_core(group, *, weights=None, facet=None, rows=5, flip=False, subject_ids=None):
    """Allocate exactly 100 tiles per retained panel, using integer remainders.

    Later factor levels win tied remainders, following waffle's stable ordering.
    Frequencies represent observations, not fractional or survey weights.
    Geometry fills a column bottom-to-top before moving right (swapped if flipped).
    """
    if isinstance(rows, (bool, np.bool_)) or not isinstance(rows, (int, np.integer)) or not 1 <= rows <= 100:
        raise InputError('Choose a whole number of tile rows from 1 to 100.')
    if not isinstance(flip, bool):
        raise InputError('Enable or disable flipped geometry explicitly.')
    rows = int(rows)
    codes, labels = _factor(group, 'Groups')
    n = len(codes)
    if not 1 <= n <= 100000:
        raise InputError('Supply 1–100,000 source rows for the grouping factor.')
    categories = [i for i, label in enumerate(labels) if label is not None]
    if not 1 <= len(categories) <= 20:
        raise InputError('This waffle core supports 1–20 declared nonmissing categories.')
    if facet is None:
        facets, facet_labels = np.zeros(n, dtype=int), ['All observations']
    else:
        facets, facet_labels = _factor(facet, 'Facets')
    facet_codes = [i for i, label in enumerate(facet_labels) if label is not None]
    if len(facets) != n or not 1 <= len(facet_codes) <= 8:
        raise InputError('Supply aligned facets with 1–8 declared nonmissing levels.')
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
    complete = (codes >= 0) & (facets >= 0) & known
    positive = complete & (frequency > 0)
    indices = np.flatnonzero(positive).tolist()
    if not indices:
        raise InputError('No complete positive-frequency observations remain.')
    totals = {f: {c: 0 for c in categories} for f in facet_codes}
    membership = {f: [] for f in facet_codes}
    for i in indices:
        f, c = int(facets[i]), int(codes[i])
        totals[f][c] += int(frequency[i])
        membership[f].append(i)
    total = sum(sum(counts.values()) for counts in totals.values())
    if total > MAX_TOTAL:
        raise InputError('Frequency total must not exceed 2^53 - 1.')
    ids = _ids(subject_ids, n, positive)
    panels, inactive = [], []
    for f in facet_codes:
        counts = totals[f]
        panel_n = sum(counts.values())
        if not panel_n:
            inactive.append(f)
            continue
        tiles = {c: 100 * counts[c] // panel_n for c in categories}
        remainders = {c: 100 * counts[c] % panel_n for c in categories}
        additions = 100 - sum(tiles.values())
        if additions:
            for c in sorted(categories, key=lambda c: (remainders[c], c))[-additions:]:
                tiles[c] += 1
        cells, geometry = [], []
        for c in categories:
            proportion = counts[c] / panel_n
            cells.append(dict(code=c, label=labels[c], count=counts[c], proportion=proportion,
                tiles=tiles[c], represented_proportion=tiles[c] / 100,
                allocation_error=tiles[c] / 100 - proportion,
                omitted_positive=counts[c] > 0 and tiles[c] == 0))
            for _ in range(tiles[c]):
                k = len(geometry)
                x, y = k // rows + 1, k % rows + 1
                if flip:
                    x, y = y, x
                geometry.append(dict(code=c, x=x, y=y, xmin=x-.5, xmax=x+.5,
                    ymin=y-.5, ymax=y+.5))
        panels.append(dict(code=f, label=facet_labels[f], n_total=panel_n,
            retained_indices=membership[f], cells=cells, geometry=geometry))
    return dict(schema_version=1, status='ok', rows=rows, flip=flip,
        n_source=n, n_complete=int(np.sum(complete)), excluded_missing=int(np.sum(~complete)),
        missing_group=int(np.sum(codes < 0)), missing_facet=int(np.sum(facets < 0)),
        missing_frequency=int(np.sum(~known)), zero_frequency=int(np.sum(complete & (frequency == 0))),
        n_contributing=len(indices), n_total=total, retained_indices=indices,
        retained_subject_ids=ids, inactive_facet_codes=inactive, panels=panels,
        allocation_method='exact_integer_largest_remainder_later_ties',
        notices=['Each panel represents its own population with exactly 100 tiles.',
                 'Rounded tile areas can omit positive categories; use exact counts and proportions.',
                 'Integer allocation avoids the known waffle 1.0.2 floating-point tile truncation.'])
