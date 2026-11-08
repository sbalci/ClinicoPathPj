"""Balanced independent-case ICC numerical prototype, not yet a public analysis.

ICC(2,k) confidence limits are deliberately withheld pending interval-policy review.
Two named candidates expose the frozen irr formula and the transformed single-rater
interval for comparison; neither is selected automatically for presentation.
"""
import math
import numpy as np
from scipy.stats import f

MODELS = ('icc11', 'icc21', 'icc31', 'icc1k', 'icc2k', 'icc3k')


def _ratio(numerator, denominator):
    if denominator == 0:
        return None
    value = numerator / denominator
    return float(value) if math.isfinite(value) else None


def _interval(lower, upper):
    if lower is None or upper is None or not all(math.isfinite(v) for v in (lower, upper)):
        return None
    if lower > upper or upper > 1 + 1e-12:
        return None
    return [float(lower), float(upper)]


def _agreement_df(msc, mse, n, k, coefficient):
    a = k * coefficient / (n * (1 - coefficient))
    b = 1 + k * coefficient * (n - 1) / (n * (1 - coefficient))
    denominator = (a * msc)**2 / (k - 1) + (b * mse)**2 / ((n - 1) * (k - 1))
    v = _ratio((a * msc + b * mse)**2, denominator)
    return v


def calculate_icc(ratings, model='icc21', confidence=.95):
    """Return ANOVA-based ICC estimates and qualified intervals for a wide matrix.

    Columns are rater slots; each complete row is one independent case. This
    engine cannot infer the sampling design or prove independence from the data.
    Rows with any missing measurement are excluded together. No imputation,
    clipping of negative estimates, continuity corrections or clinical bands.
    """
    if model not in MODELS:
        raise ValueError('Choose one of the six declared balanced ICC forms')
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not .80 <= confidence <= .99:
        raise ValueError('ICC confidence must be between .80 and .99')
    x = np.asarray(ratings)
    if x.ndim != 2 or x.dtype.kind not in 'fiu' or not 2 <= x.shape[1] <= 20 or not 1 <= x.shape[0] <= 5000:
        raise ValueError('Supply a numeric case-by-rater matrix with 1–5000 rows and 2–20 columns')
    if np.isinf(x).any():
        raise ValueError('Ratings must be finite or missing')
    retained = np.flatnonzero(~np.isnan(x).any(axis=1))
    values = x[retained].astype(float)
    n, k = values.shape
    if n < 2:
        raise ValueError('At least two complete independent cases are required')
    # Work in common scaled units to avoid squaring huge/small measurements.
    scale = float(np.max(np.abs(values))) or 1.
    centered = values / scale
    centered = centered - np.mean(centered)
    rows = centered.mean(axis=1, keepdims=True)
    columns = centered.mean(axis=0, keepdims=True)
    msr = float(k * np.sum(rows**2) / (n - 1))
    msc = float(n * np.sum(columns**2) / (k - 1))
    mse = float(np.sum((centered - rows - columns)**2) / ((n - 1) * (k - 1)))
    msw = float(np.sum((centered - rows)**2) / (n * (k - 1)))
    family = int(model[3])
    average = model.endswith('k')
    error = msw if family == 1 else mse
    if family == 2:
        denominator = msr + (msc - mse) / n if average else msr + (k - 1)*mse + k*(msc - mse)/n
    else:
        denominator = msr if average else msr + (k - 1)*error
    estimate = _ratio(msr - error, denominator)
    raw_estimate = estimate
    inadmissible = estimate is not None and estimate > 1
    if inadmissible:
        estimate = None
    result = dict(model=model, confidence=confidence, input=int(x.shape[0]), n=n, raters=k,
                  excluded=int(x.shape[0] - n), retained_indices=retained.tolist(),
                  estimate=estimate, unconstrained_estimate=raw_estimate,
                  interval=None, candidate_intervals={}, notices=[],
                  normalized_anova=dict(subject=msr, rater=msc, error=mse, within=msw),
                  normalization_scale=scale, public_analysis=False)
    if inadmissible:
        result['notices'].append('ANOVA ratio exceeds one with an inadmissible variance estimate; coefficient withheld.')
    if estimate is not None and estimate < 0:
        result['notices'].append('Negative unconstrained ICC retained; no automatic clinical interpretation.')
    # Treat zero/numerically unresolved ANOVA components conservatively. A point
    # estimate of one from identical columns is not population certainty.
    tolerance = np.finfo(float).eps**2 * n * k
    if estimate is None or msr <= tolerance or error <= tolerance:
        result['notices'].append('Zero or numerically unresolved ANOVA component: inferential limits withheld.')
        return result
    q = (1 + confidence) / 2
    if family != 2:
        df = n*(k - 1) if family == 1 else (n - 1)*(k - 1)
        fl, fu = float(f.ppf(q, n - 1, df)), float(f.ppf(q, df, n - 1))
        if average:
            result['interval'] = _interval(1 - fl*error/msr, 1 - error/(fu*msr))
        else:
            result['interval'] = _interval(
                _ratio(msr - fl*error, msr + (k - 1)*fl*error),
                _ratio(fu*msr - error, fu*msr + (k - 1)*error))
        if result['interval'] is None:
            result['notices'].append('Finite ordered inferential limits could not be identified.')
        return result
    single = _ratio(msr - mse, msr + (k - 1)*mse + k*(msc - mse)/n)
    if single is None or single >= 1:
        result['notices'].append('Absolute-agreement interval could not be identified.')
        return result

    def limits(coefficient, averaged):
        if coefficient is None or coefficient >= 1:
            return None
        v = _agreement_df(msc, mse, n, k, coefficient)
        if v is None or v <= 0:
            return None
        fl, fu = float(f.ppf(q, n - 1, v)), float(f.ppf(q, v, n - 1))
        term = msc - mse if averaged else k*msc + (k*n - k - n)*mse
        return _interval(_ratio(n*(msr - fl*mse), fl*term + n*msr),
                         _ratio(n*(fu*msr - mse), term + n*fu*msr))

    single_interval = limits(single, False)
    if not average:
        result['interval'] = single_interval
        if single_interval is None:
            result['notices'].append('Finite ordered absolute-agreement limits could not be identified.')
    else:
        transformed = None
        if single_interval is not None and all(1 + (k - 1)*v > 0 for v in single_interval):
            transformed = _interval(*[k*v/(1 + (k - 1)*v) for v in single_interval])
        result['candidate_intervals'] = dict(frozen_irr=limits(estimate, True),
                                              transformed_single=transformed)
        result['notices'].append('ICC(2,k) interval policy unresolved: candidate formulas differ; public interval withheld.')
    return result
