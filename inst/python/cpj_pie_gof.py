"""Source-only fixed-null Pearson goodness-of-fit; no native interface change."""
import math
from numbers import Real

import numpy as np
from scipy.stats import chi2

from cpj_pie import pie_core
from cpj_runtime import InputError


def _probabilities(cells, ratios):
    labels = [c['label'] for c in cells]
    if ratios is None:
        values = [1.] * len(labels)
    else:
        if not isinstance(ratios, dict) or set(ratios) != set(labels):
            raise InputError('Expected ratios must map every declared nonmissing category label exactly once, with no extra labels.')
        values = []
        for label in labels:
            value = ratios[label]
            if not isinstance(value, Real) or isinstance(value, (bool, np.bool_)):
                raise InputError('Expected ratios must be positive finite numbers, not strings or booleans.')
            try:
                value = float(value)
            except (OverflowError, ValueError):
                raise InputError('Expected ratios exceed the supported numeric range.') from None
            if not math.isfinite(value) or value <= 0:
                raise InputError('Expected ratios must be positive and finite; structural zero probabilities are unsupported.')
            values.append(value)
    scale = max(values)
    scaled = [v / scale for v in values]
    denominator = math.fsum(scaled)
    probabilities = [v / denominator for v in scaled]
    if any(p <= 0 or not math.isfinite(p) for p in probabilities):
        raise InputError('Expected-ratio normalization underflowed; no null category was removed.')
    return probabilities


def pie_gof(outcome, *, weights=None, subject_ids=None, enabled=False, ratios=None):
    """Keep the descriptive cohort and test a prespecified multinomial null.

    All declared nonmissing categories define the support, including zero counts.
    Ratios are ignored while disabled. Sparse p-values are approximations, with an
    explicit warning flag; no exact test, continuity correction or fitted null.
    """
    if not isinstance(enabled, bool):
        raise InputError('Enable or disable goodness-of-fit results explicitly.')
    descriptive = pie_core(outcome, weights=weights, subject_ids=subject_ids)
    result = dict(enabled=enabled, status='disabled', reason=None, method=None,
        statistic=None, df=None, p=None, minimum_expected=None, expected_below5=None,
        sparse_warning=False, null=None, rows=[])
    if not enabled:
        return dict(schema_version=1, descriptives=descriptive, gof=result)
    cells = descriptive['cells']
    probabilities = _probabilities(cells, ratios)
    total = descriptive['n_total']
    rows = []
    for cell, probability in zip(cells, probabilities):
        expected = total * probability
        if expected <= 0 or not math.isfinite(expected):
            raise InputError('An expected count is outside the supported numeric range.')
        difference = cell['count'] - expected
        residual = difference / math.sqrt(expected)
        contribution = difference * difference / expected
        if not math.isfinite(residual) or not math.isfinite(contribution):
            raise InputError('Goodness-of-fit calculations exceed the supported numeric range.')
        rows.append(dict(code=cell['code'], label=cell['label'], observed=cell['count'],
            probability=probability, expected=expected, pearson_residual=residual,
            contribution=contribution))
    below = sum(r['expected'] < 5 for r in rows)
    result.update(null='equal' if ratios is None else 'labelled_ratios', rows=rows,
        minimum_expected=min(r['expected'] for r in rows), expected_below5=below,
        sparse_warning=bool(below))
    if len(cells) == 1:
        rows[0].update(pearson_residual=None, contribution=None)
        result.update(status='unavailable', reason='one_declared_category')
    else:
        try:
            statistic = math.fsum(r['contribution'] for r in rows)
        except OverflowError:
            raise InputError('Goodness-of-fit statistic exceeds the supported numeric range.') from None
        p = float(chi2.sf(statistic, len(cells)-1))
        if not math.isfinite(statistic) or not math.isfinite(p):
            raise InputError('Goodness-of-fit results exceed the supported numeric range.')
        result.update(status='sparse_approximation' if below else 'approximation',
            method='pearson_chi_square_gof', statistic=statistic, df=len(cells)-1, p=p)
    return dict(schema_version=1, descriptives=descriptive, gof=result)
