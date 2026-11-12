"""Explicit pooled/difference-standardized effects shared by native partial adapters.

Cohen d/d_z and a Hedges-corrected point estimate share a population delta target.
Noncentral-t limits target delta, unscaled by J; no separately labelled g limits.
"""
import math
import warnings

from scipy.optimize import brentq
from scipy.special import gammaln
from scipy.stats import nct, norm

from cpj_estimation import between_estimation, within_estimation
from cpj_runtime import InputError

MAX_INTERVAL_T = 40.


def _noncentral_interval(statistic, df, confidence):
    """Equal-tail population NCP limits with checked residuals; no approximation."""
    if abs(statistic) > MAX_INTERVAL_T or not 2 <= df <= 100_000:
        raise ArithmeticError('Noncentral-t inversion is outside the qualified numerical range.')
    tail = (1-confidence)/2
    if statistic == 0:
        lower = float(norm.ppf(tail))
        return lower, -lower
    observed = abs(statistic)
    with warnings.catch_warnings():
        warnings.simplefilter('error', RuntimeWarning)

        def cdf(ncp):
            value = float(nct.cdf(observed, df, ncp))
            if not math.isfinite(value) or not 0 <= value <= 1:
                raise ArithmeticError('Noncentral-t CDF evaluation failed.')
            return value

        def solve(probability):
            bound = max(8., observed*2+8)
            for _ in range(12):
                if cdf(-bound) >= probability >= cdf(bound):
                    root, info = brentq(lambda nc: cdf(nc)-probability, -bound, bound,
                                        xtol=1e-11, rtol=1e-12, maxiter=200,
                                        full_output=True, disp=False)
                    if not info.converged:
                        raise ArithmeticError('Noncentral-t inversion did not converge.')
                    root = float(root)
                    if abs(cdf(root)-probability) > 2e-10:
                        raise ArithmeticError('Noncentral-t inversion failed its probability check.')
                    return root
                bound *= 2
            raise ArithmeticError('Noncentral-t inversion could not bracket an endpoint.')

        lower, upper = solve(1-tail), solve(tail)
    if not math.isfinite(lower) or not math.isfinite(upper) or lower >= upper:
        raise ArithmeticError('Noncentral-t limits are not finite and ordered.')
    return (lower, upper) if statistic > 0 else (-upper, -lower)


def _standardize(raw, standardizer):
    result = dict(schema_version=1, standardizer=standardizer,
        estimand='population_delta_z' if raw['design'] == 'paired' else 'population_delta',
        interval_method='equal_tail_noncentral_t_population_delta',
        assumptions=(['Independent subjects', 'Normally distributed within-subject differences']
            if raw['design'] == 'paired' else
            ['Independent observations and groups', 'Normal populations with a common variance']),
        cohens_d=None, hedges_g=None, correction=None, standardizer_sd=None, df=None,
        ncp_lower=None, ncp_upper=None, delta_lower=None, delta_upper=None,
        status='degenerate', reason='Raw inference is degenerate; no standardized inference.')
    if raw['status'] != 'ok':
        return dict(schema_version=1, raw=raw, standardized=result)
    first, second = raw['summaries']['first'], raw['summaries']['second']
    factor = (1/math.sqrt(first['n']) if raw['design'] == 'paired'
              else math.sqrt(1/first['n']+1/second['n']))
    df = raw['df']
    denominator = raw['stderr']/factor
    d = raw['statistic']*factor
    correction = float(math.exp(gammaln(df/2)-gammaln((df-1)/2)-math.log(df/2)/2))
    g = correction*d
    if not all(math.isfinite(v) for v in (denominator, d, correction, g)) or denominator <= 0:
        raise InputError('Standardized estimates exceed the supported numeric range.')
    result.update(cohens_d=d, hedges_g=g, correction=correction,
                  standardizer_sd=denominator, df=df, status='interval_unavailable', reason=None)
    try:
        lower, upper = _noncentral_interval(raw['statistic'], df, raw['confidence'])
        delta_lower, delta_upper = lower*factor, upper*factor
        if not all(math.isfinite(v) for v in (delta_lower, delta_upper)):
            raise ArithmeticError('Population-delta limits exceed the supported numeric range.')
        result.update(ncp_lower=lower, ncp_upper=upper, delta_lower=delta_lower,
                      delta_upper=delta_upper, status='ok')
    except (ArithmeticError, ValueError, RuntimeWarning) as error:
        result['reason'] = str(error)
    return dict(schema_version=1, raw=raw, standardized=result)


def between_standardized(values, group, first_level, second_level, *, standardizer,
                         confidence=.95, subject_ids=None):
    """Pooled-SD effects under an explicit equal-variance independent normal model."""
    if not isinstance(standardizer, str) or standardizer != 'pooled':
        raise InputError('Independent standardized effects require explicit pooled SD; Welch effects are not implemented.')
    raw = between_estimation(values, group, first_level, second_level, equal_variances=True,
                             confidence=confidence, subject_ids=subject_ids)
    return _standardize(raw, 'pooled')


def within_standardized(first, second, *, standardizer, confidence=.95, subject_ids=None):
    """d_z/g_z, standardized by within-row difference SD, independent normal subjects."""
    if not isinstance(standardizer, str) or standardizer != 'difference':
        raise InputError('Paired standardized effects require explicit difference SD; marginal-SD effects are not implemented.')
    raw = within_estimation(first, second, confidence=confidence, subject_ids=subject_ids)
    return _standardize(raw, 'difference')
