"""Source-only RMS-variance standardized effects; approximate opt-in inference.

No native adapter imports this prototype. See the frozen method/coverage contract
in docs/python-welch-standardized-effects.md. Existing mean engines are unchanged.
"""
import math
import warnings

from scipy.special import gammaln
from scipy.optimize import brentq
from scipy.stats import nct, norm

from cpj_estimation import between_estimation
from cpj_runtime import InputError
from cpj_standardized import MAX_INTERVAL_T


def _plugin_interval(statistic, df, confidence):
    """Checked inversion; tolerate only eight ULPs of CDF boundary roundoff."""
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
            # For negative NCP and positive t, evaluate the small upper tail.
            # Bundled SciPy CDF can return NaN here even when SF is finite.
            value = float(1-nct.sf(observed, df, ncp) if ncp < 0
                          else nct.cdf(observed, df, ncp))
            tolerance = 8*math.ulp(1.)
            if not math.isfinite(value) or not -tolerance <= value <= 1+tolerance:
                raise ArithmeticError('Noncentral-t CDF evaluation failed.')
            return min(1., max(0., value))
        def solve(probability):
            bound = max(8., observed*2+8)
            for _ in range(12):
                if cdf(-bound) >= probability >= cdf(bound):
                    root, info = brentq(lambda nc: cdf(nc)-probability, -bound, bound,
                        xtol=1e-11, rtol=1e-12, maxiter=200, full_output=True, disp=False)
                    if not info.converged or abs(cdf(root)-probability) > 2e-10:
                        raise ArithmeticError('Noncentral-t inversion failed its convergence/probability check.')
                    return float(root)
                bound *= 2
            raise ArithmeticError('Noncentral-t inversion could not bracket an endpoint.')
        lower, upper = solve(1-tail), solve(tail)
    if not all(math.isfinite(v) for v in (lower, upper)) or lower >= upper:
        raise ArithmeticError('Noncentral-t limits are not finite and ordered.')
    return (lower, upper) if statistic > 0 else (-upper, -lower)


def between_welch_standardized(values, group, first_level, second_level, *,
                               standardizer, interval='none', confidence=.95,
                               subject_ids=None):
    """First-minus-second RMS-SD effect; optional Welch NCT plug-in delta limits."""
    if not isinstance(standardizer, str) or standardizer != 'rms_variance':
        raise InputError('Choose explicit rms_variance standardization for this source prototype.')
    if not isinstance(interval, str) or interval not in ('none', 'welch_nct_plugin'):
        raise InputError('Choose none or the approximate welch_nct_plugin interval explicitly.')
    raw = between_estimation(values, group, first_level, second_level,
                             equal_variances=False, confidence=confidence, subject_ids=subject_ids)
    result = dict(schema_version=1, standardizer='rms_variance', estimand='population_delta_RMS',
        interval_method=interval, interval_is_approximate=interval != 'none',
        correction_method='J_observed_welch_df', correction_exact=False,
        assumptions=['Independent observations and groups', 'Normal populations; unequal variances allowed'],
        d_rms=None, standardizer_sd=None, welch_df=None, sd_moment_df=None,
        welch_J=None, welch_J_point=None, correction_reason=None,
        ncp_lower=None, ncp_upper=None, delta_lower=None, delta_upper=None,
        status='degenerate', reason='Raw inference is degenerate; no standardized inference.')
    if raw['status'] != 'ok':
        return dict(schema_version=1, raw=raw, standardized=result)
    a, b = raw['summaries']['first'], raw['summaries']['second']
    sd = math.hypot(a['sd'], b['sd'])/math.sqrt(2)
    # Normalize before fourth powers; this df describes the RMS denominator,
    # and differs from the Welch SE df when group sizes differ.
    scale = max(a['sd'], b['sd'])
    v1, v2 = (a['sd']/scale)**2, (b['sd']/scale)**2
    w1, w2 = v1/(v1+v2), v2/(v1+v2)
    sd_df = 1/(w1*w1/(a['n']-1)+w2*w2/(b['n']-1))
    d, df = raw['difference']/sd, raw['df']
    if not all(math.isfinite(v) for v in (sd, sd_df, d)) or sd <= 0:
        raise InputError('Standardized estimates exceed the supported numeric range.')
    result.update(d_rms=d, standardizer_sd=sd, welch_df=df, sd_moment_df=sd_df,
                  status='point_only', reason=None)
    if df > 1:
        correction = float(math.exp(gammaln(df/2)-gammaln((df-1)/2)-math.log(df/2)/2))
        point = correction*d
        if not all(math.isfinite(v) for v in (correction, point)):
            raise InputError('The plug-in correction exceeds the supported numeric range.')
        result.update(welch_J=correction, welch_J_point=point)
    else:
        result['correction_reason'] = 'J requires degrees of freedom greater than one.'
    if interval != 'none':
        result['status'] = 'interval_unavailable'
        try:
            lower, upper = _plugin_interval(raw['statistic'], df, raw['confidence'])
            factor = raw['stderr']/sd
            delta_lower, delta_upper = lower*factor, upper*factor
            if not all(math.isfinite(v) for v in (delta_lower, delta_upper)):
                raise ArithmeticError('Approximate delta limits exceed the supported numeric range.')
            result.update(ncp_lower=lower, ncp_upper=upper, delta_lower=delta_lower,
                          delta_upper=delta_upper, status='ok')
        except (ArithmeticError, ValueError, RuntimeWarning) as error:
            result['reason'] = str(error)
    return dict(schema_version=1, raw=raw, standardized=result)
