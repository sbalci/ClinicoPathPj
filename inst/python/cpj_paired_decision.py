"""Source-only paired binary diagnostic comparisons on one audited common cohort.

No public SPEC/menu entry. See docs/python-paired-decision-core.md for the frozen
scope, baseline differences and gates before exposing inference in jamovi.
"""
import math
from itertools import combinations
from numbers import Real

import numpy as np
from scipy.stats import binom, binomtest, chi2

from cpj_accuracy import calculate
from cpj_correlation import adjust
from cpj_paired_interval import newcombe_interval
from cpj_runtime import Factor, InputError

MAX_ROWS = 100_000
MAX_DISCORDANCE = 1_000_000
METHODS = ('midp', 'asymptotic', 'exact')


def mcnemar_discordance(b, c, method='midp'):
    """McNemar for first-only/second-only counts; p=1 is flagged when m=0.

    Mid-p uses Fagerland et al. (2013), including equation (6) at b=c>0.
    Exact conditional is an explicitly named reference method, not a new UI option.
    """
    if not isinstance(method, str) or method not in METHODS:
        raise InputError('Use midp, asymptotic or exact for the source McNemar method.')
    counts = []
    for value in (b, c):
        if (isinstance(value, (bool, np.bool_)) or not isinstance(value, Real)
                or not math.isfinite(value) or not 0 <= value <= MAX_DISCORDANCE
                or int(value) != value):
            raise InputError('Discordant counts must be nonnegative finite integers.')
        counts.append(int(value))
    b, c = counts
    m = b+c
    if m > MAX_DISCORDANCE:
        raise InputError('The source McNemar helper accepts at most 1,000,000 discordant pairs.')
    if not m:
        return dict(statistic=None, p=1., discordant=0, status='no_discordance')
    statistic = None
    if method == 'asymptotic':
        statistic = (b-c)**2/m
        p = chi2.sf(statistic, 1)
    elif method == 'exact':
        p = binomtest(b, m, .5).pvalue
    else:
        mass = binom.pmf(min(b, c), m, .5)
        p = 1-mass/2 if b == c else min(1., 2*binom.cdf(min(b, c), m, .5))-mass
    return dict(statistic=statistic, p=float(np.clip(p, 0., 1.)),
                discordant=m, status='ok')


def _factor(role, mapping, name):
    if (not isinstance(role, Factor) or not isinstance(role.levels, (list, tuple))
            or not all(isinstance(x, str) for x in role.levels)
            or len(set(role.levels)) != len(role.levels)):
        raise InputError(f'{name}: supply a factor with distinct string labels.')
    if (not isinstance(mapping, (list, tuple)) or len(mapping) != 2
            or not all(isinstance(x, str) and x in role.levels for x in mapping)
            or mapping[0] == mapping[1]):
        raise InputError(f'{name}: choose distinct positive and negative levels explicitly.')
    if (np.ma.isMaskedArray(role.codes) or
            isinstance(role.codes, (list, tuple)) and
            any(isinstance(x, (bool, np.bool_)) for x in role.codes)):
        raise InputError(f'{name}: use integer factor codes and -1 for missing cells.')
    try:
        codes = np.asarray(role.codes)
    except (ValueError, TypeError):
        raise InputError(f'{name}: supply a one-dimensional integer factor vector.') from None
    if (codes.ndim != 1 or codes.dtype.kind not in 'iu'
            or np.any(codes < -1) or np.any(codes >= len(role.levels))):
        raise InputError(f'{name}: invalid factor codes; missing cells must use -1.')
    pos, neg = (role.levels.index(x) for x in mapping)
    return codes, codes == pos, (codes >= 0) & (codes != pos) & (codes != neg)


def _comparison(x, y, method):
    n = len(x)
    counts = [int(np.sum(x & y)), int(np.sum(x & ~y)),
              int(np.sum(~x & y)), int(np.sum(~x & ~y))]
    if not n:
        return dict(n=0, first=None, second=None, difference=None, counts=counts,
                    discordant=0, statistic=None, p=None, status='absent_class')
    return dict(n=n, first=float(x.mean()), second=float(y.mean()),
                difference=(counts[1]-counts[2])/n, counts=counts,
                **mcnemar_discordance(counts[1], counts[2], method))


def paired_decision(reference, tests, reference_levels, test_levels, *,
                    exclude_indeterminate=False, method='midp', confidence=.95,
                    adjustment='holm', difference_intervals=False):
    """Return audited cohort, per-test exact intervals and paired comparisons.

    mappings are (positive label, negative label), not inferred from factor order.
    Accuracy uses Holm across informative pairs; sensitivity/specificity remain
    unadjusted. Difference intervals require explicit opt-in and remain pointwise.
    """
    if (not isinstance(confidence, Real) or isinstance(confidence, (bool, np.bool_))
            or not math.isfinite(confidence) or not .8 <= confidence <= .99):
        raise InputError('Confidence must be a finite number between 0.80 and 0.99.')
    if not isinstance(exclude_indeterminate, bool):
        raise InputError('Choose explicitly whether to exclude outside-pair levels.')
    if not isinstance(difference_intervals, bool):
        raise InputError('Choose explicitly whether to calculate paired-difference intervals.')
    if not isinstance(method, str) or method not in METHODS:
        raise InputError('Unsupported source McNemar method.')
    if not isinstance(adjustment, str) or adjustment not in ('holm', 'none'):
        raise InputError('Use holm or none for accuracy p-value adjustment.')
    if (not isinstance(tests, dict) or not 2 <= len(tests) <= 3
            or not all(isinstance(x, str) and x and x != 'reference' for x in tests)):
        raise InputError('Supply two or three named test factors; reference is a reserved role name.')
    if not isinstance(test_levels, dict) or set(test_levels) != set(tests):
        raise InputError('Supply explicit positive/negative mappings for every selected test.')
    roles = {'reference': _factor(reference, reference_levels, 'reference')}
    roles.update({name: _factor(role, test_levels[name], name) for name, role in tests.items()})
    n_source = len(roles['reference'][0])
    if not 1 <= n_source <= MAX_ROWS:
        raise InputError('The paired source core accepts 1–100,000 source rows.')
    if any(len(v[0]) != n_source for v in roles.values()):
        raise InputError('All selected roles must have aligned source rows.')
    missing_by_role = {name: int(np.sum(v[0] < 0)) for name, v in roles.items()}
    indeterminate_by_role = {name: int(v[2].sum()) for name, v in roles.items()}
    if not exclude_indeterminate and any(indeterminate_by_role.values()):
        raise InputError('Observed levels outside the explicit positive/negative pairs require exclusion or recoding.')
    missing = np.logical_or.reduce([v[0] < 0 for v in roles.values()])
    outside = np.logical_or.reduce([v[2] for v in roles.values()])
    keep = ~(missing | outside)
    retained = np.flatnonzero(keep)
    if not len(retained):
        raise InputError('No common complete determinate cases remain across all selected roles.')
    truth = roles['reference'][1][keep]
    predictions = {name: roles[name][1][keep] for name in tests}
    models = {}
    for name, pred in predictions.items():
        counts = [int(np.sum(truth & pred)), int(np.sum(~truth & pred)),
                  int(np.sum(truth & ~pred)), int(np.sum(~truth & ~pred))]
        proportions, _ = calculate(counts, confidence*100)
        models[name] = dict(counts=counts, proportions=proportions)
    pairs = []
    for first, second in combinations(tests, 2):
        x, y = predictions[first], predictions[second]
        pairs.append(dict(first_name=first, second_name=second,
            accuracy=_comparison(x == truth, y == truth, method),
            sensitivity=_comparison(x[truth], y[truth], method),
            specificity=_comparison(~x[~truth], ~y[~truth], method)))
    active = [i for i, pair in enumerate(pairs) if pair['accuracy']['discordant'] > 0]
    adjusted = adjust([pairs[i]['accuracy']['p'] for i in active], adjustment)
    for pair in pairs:
        pair['accuracy']['p_adjusted'] = pair['accuracy']['p']
    for i, value in zip(active, adjusted):
        pairs[i]['accuracy']['p_adjusted'] = value
    if difference_intervals:
        for pair in pairs:
            for metric in ('accuracy', 'sensitivity', 'specificity'):
                row = pair[metric]
                interval = newcombe_interval(row['counts'], confidence)
                row.update(lower=interval['lower'], upper=interval['upper'],
                           interval_phi=interval['phi'],
                           interval_status='absent_class' if row['n'] == 0 else interval['status'],
                           interval_method='Newcombe method 10; approximate, pointwise, unadjusted')
    return dict(schema_version=1, cohort='common_complete_determinate',
        method=method, confidence=float(confidence), adjustment=adjustment,
        interval_method=('Clopper-Pearson per-test proportions; Newcombe method 10 paired differences'
                         if difference_intervals else
                         'Clopper-Pearson per-test proportions; paired-difference intervals omitted'),
        holm_family=len(active), holm_applied=adjustment == 'holm' and len(active) > 1,
        n_source=n_source, n_complete=len(retained),
        n_positive=int(truth.sum()), n_negative=int((~truth).sum()),
        retained_indices=retained.tolist(), excluded_missing=int(missing.sum()),
        excluded_indeterminate=int((~missing & outside).sum()),
        missing_by_role=missing_by_role, indeterminate_by_role=indeterminate_by_role,
        mappings={'reference': list(reference_levels), **{k: list(v) for k, v in test_levels.items()}},
        factor_levels={'reference': list(reference.levels), **{k: list(v.levels) for k, v in tests.items()}},
        models=models, pairs=pairs)
