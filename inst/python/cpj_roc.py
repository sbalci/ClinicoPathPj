"""Source-only empirical binary ROC and paired DeLong calculations.

Scores and hypotheses are supplied, never trained or automatically oriented here.
No SPEC/UI/public entry is created by this numerical engine.
"""
import math
from itertools import combinations
from numbers import Real

import numpy as np
from scipy.stats import norm

from cpj_concordance import _numeric
from cpj_runtime import Factor, InputError


def _curve(scores, truth, direction):
    oriented = scores if direction == 'higher' else -scores
    unique, bins = np.unique(oriented, return_inverse=True)
    positive = np.bincount(bins, weights=truth, minlength=len(unique)).astype(int)[::-1]
    negative = np.bincount(bins, weights=~truth, minlength=len(unique)).astype(int)[::-1]
    m, n = int(truth.sum()), int((~truth).sum())
    points = [dict(cutoff=None, rule='none positive', tp=0, fp=0, fn=m, tn=n,
                   tpr=0., fpr=0.)]
    tp, fp = 0, 0
    for score, a, b in zip(unique[::-1], positive, negative):
        tp, fp = tp+int(a), fp+int(b)
        points.append(dict(cutoff=float(score if direction == 'higher' else -score),
                           rule='>=' if direction == 'higher' else '<=',
                           tp=tp, fp=fp, fn=m-tp, tn=n-fp, tpr=tp/m, fpr=fp/n))
    return points


def _placements(scores, truth, direction):
    values = scores if direction == 'higher' else -scores
    positive, negative = values[truth], values[~truth]
    a, b = np.sort(positive), np.sort(negative)
    # P(case score > control score) + one half of exact ties.
    positive_placement = (np.searchsorted(b, positive, side='left')+
                          np.searchsorted(b, positive, side='right'))/(2*len(b))
    negative_placement = 1-(np.searchsorted(a, negative, side='left')+
                            np.searchsorted(a, negative, side='right'))/(2*len(a))
    return positive_placement, negative_placement


def roc_analysis(reference, markers, positive, directions=None, confidence=.95):
    """Full empirical ROC/AUC and paired DeLong inference on a common cohort.

    DeLong intervals/tests are asymptotic and assume independent cases. Zero or
    unestimable variance withholds uncertainty, retaining descriptive AUC/curves.
    Public integration and calibration qualification remain separate gates.
    """
    if (isinstance(confidence, (bool, np.bool_)) or not isinstance(confidence, Real)
            or not math.isfinite(confidence) or not .8 <= confidence <= .99):
        raise InputError('ROC confidence must be a finite number between 0.80 and 0.99.')
    if (not isinstance(reference, Factor) or not isinstance(reference.levels, (list, tuple))
            or len(reference.levels) != 2
            or not all(isinstance(v, str) for v in reference.levels)
            or len(set(reference.levels)) != 2):
        raise InputError('Choose a binary reference with exactly two distinct factor labels.')
    if not isinstance(positive, str) or positive not in reference.levels:
        raise InputError('Choose the reference positive level explicitly.')
    if np.ma.isMaskedArray(reference.codes):
        raise InputError('Reference codes must use -1 missing cells, not masked arrays.')
    try:
        codes = np.asarray(reference.codes)
    except (TypeError, ValueError):
        raise InputError('Reference codes must be an aligned integer vector.') from None
    if (codes.ndim != 1 or codes.dtype.kind not in 'iu'
            or np.any(codes < -1) or np.any(codes > 1)):
        raise InputError('Reference codes must be 0/1, with -1 for missing values.')
    if len(codes) > 5000:
        raise InputError('ROC prototype accepts at most 5,000 source rows.')
    if (not isinstance(markers, dict) or not 1 <= len(markers) <= 3
            or not all(isinstance(name, str) and name for name in markers)):
        raise InputError('Supply one to three named numeric score columns.')
    names = list(markers)
    if directions is None:
        directions = {name: 'higher' for name in names}
    if (not isinstance(directions, dict) or set(directions) != set(names)
            or any(not isinstance(v, str) or v not in ('higher', 'lower')
                   for v in directions.values())):
        raise InputError('Specify higher or lower for every marker; automatic orientation is unsupported.')
    arrays = [_numeric(markers[name]) for name in names]
    if any(len(a) != len(codes) for a in arrays):
        raise InputError('Reference and all score columns must have aligned source rows.')
    keep = codes >= 0
    missing = {name: int(np.isnan(a).sum()) for name, a in zip(names, arrays)}
    for array in arrays:
        keep &= np.isfinite(array)
    retained = np.flatnonzero(keep)
    truth = codes[keep] == reference.levels.index(positive)
    m, n = int(truth.sum()), int((~truth).sum())
    if not m or not n:
        raise InputError('Both reference groups require complete observations across all selected markers.')
    scores = [a[keep] for a in arrays]
    placements = [_placements(a, truth, directions[name]) for name, a in zip(names, scores)]
    v10, v01 = np.stack([p[0] for p in placements]), np.stack([p[1] for p in placements])
    aucs = v10.mean(axis=1)
    covariance = None
    if m >= 2 and n >= 2:
        centered_positive, centered_negative = v10-v10.mean(axis=1)[:, None], v01-v01.mean(axis=1)[:, None]
        covariance = ((centered_positive @ centered_positive.T)/(m*(m-1))+
                      (centered_negative @ centered_negative.T)/(n*(n-1)))
    q = float(norm.ppf((1+float(confidence))/2))
    models = []
    for i, (name, a) in enumerate(zip(names, scores)):
        variance = float(covariance[i, i]) if covariance is not None else None
        item = dict(name=name, direction=directions[name], auc=float(aucs[i]),
                    variance=variance, se=None, lower=None, upper=None,
                    raw_lower=None, raw_upper=None, inference_status='unavailable',
                    inference_reason='', positive_placements=v10[i].tolist(),
                    negative_placements=v01[i].tolist(), points=_curve(a, truth, directions[name]))
        if variance is None:
            item['inference_reason'] = 'DeLong variance requires at least two complete cases in each reference group.'
        elif not math.isfinite(variance) or variance <= 0:
            item['inference_reason'] = 'DeLong variance is zero or unresolved; no nondegenerate interval is reported.'
        else:
            se = math.sqrt(variance)
            raw_lower, raw_upper = float(aucs[i]-q*se), float(aucs[i]+q*se)
            item.update(se=se, lower=max(0., raw_lower), upper=min(1., raw_upper),
                        raw_lower=raw_lower, raw_upper=raw_upper, inference_status='ok')
        models.append(item)
    comparisons = []
    for a, b in combinations(range(len(names)), 2):
        delta = float(aucs[a]-aucs[b])
        contrast_variance = None
        if covariance is not None:
            # Compute contrast directly to avoid cancellation for nearly identical scores.
            contrast_variance = float(np.var(v10[a]-v10[b], ddof=1)/m+
                                      np.var(v01[a]-v01[b], ddof=1)/n)
        item = dict(first=names[a], second=names[b], difference=delta,
                    covariance=float(covariance[a, b]) if covariance is not None else None,
                    variance=contrast_variance, se=None, z=None, p=None, lower=None,
                    upper=None, status='unavailable', reason='')
        if contrast_variance is None:
            item['reason'] = 'Paired DeLong inference requires at least two complete cases in each reference group.'
        elif not math.isfinite(contrast_variance) or contrast_variance <= 0:
            item['reason'] = 'Paired DeLong difference variance is zero or unresolved; no test or interval is reported.'
        else:
            se = math.sqrt(contrast_variance)
            z = delta/se
            item.update(se=se, z=z, p=float(2*norm.sf(abs(z))), lower=delta-q*se,
                        upper=delta+q*se, status='ok')
        comparisons.append(item)
    return dict(method='empirical ROC / paired DeLong', confidence=float(confidence),
                auc_interval='normal, bounded at [0,1]; raw limits retained',
                difference_interval='unbounded normal', multiplicity='none',
                positive=positive, negative=reference.levels[1-reference.levels.index(positive)],
                reference_levels=list(reference.levels), n_source=len(codes),
                n_complete=m+n, n_positive=m, n_negative=n, n_excluded=len(codes)-m-n,
                retained_indices=retained.tolist(), missing_reference=int((codes < 0).sum()),
                missing_by_marker=missing, models=models, comparisons=comparisons,
                covariance=covariance.tolist() if covariance is not None else None)
