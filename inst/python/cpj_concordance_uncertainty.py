"""Source-only Lin CCC interval prototype; no public SPEC or automatic fallback."""
import math
from numbers import Real
from decimal import Decimal, localcontext

import numpy as np
from scipy.stats import norm

from cpj_concordance import concordance, _numeric
from cpj_runtime import InputError


def _location_share(x, y):
    """Compute Cb*u^2 as 2*(mean difference)^2/CCC denominator.

    A common translation/scaling leaves this dimensionless quantity unchanged.
    Keeping the product together avoids huge u^2 times tiny Cb arithmetic.
    """
    with np.errstate(over='ignore', invalid='ignore'):
        a, b = x-x[0], y-x[0]
    if not np.isfinite(a).all() or not np.isfinite(b).all():
        scale = max(float(np.max(np.abs(x))), float(np.max(np.abs(y))))
        a, b = x/scale, y/scale
        origin = float(a[0])
        a, b = a-origin, b-origin
    scale = max(float(np.max(np.abs(a))), float(np.max(np.abs(b))))
    if scale == 0:
        return None
    a, b = a/scale, b/scale
    n = len(a)
    ma, mb = math.fsum(a)/n, math.fsum(b)/n
    vx = math.fsum(float(v)*float(v) for v in a-ma)/n
    vy = math.fsum(float(v)*float(v) for v in b-mb)/n
    shift = (ma-mb)**2
    denominator = math.fsum((vx, vy, shift))
    if not math.isfinite(denominator) or denominator <= 0:
        return None
    return 2*shift/denominator


def _decimal_limits(x, y, critical, method):
    """Resolve cancellation near |CCC|=1 on exact supplied binary floats.

    The reference formula and inference method are unchanged. Decimal is from the
    standard library; this path does not require mpmath or a system package.
    """
    with localcontext() as context:
        context.prec = 80
        a = [Decimal.from_float(float(v)) for v in x]
        b = [Decimal.from_float(float(v)) for v in y]
        n = Decimal(len(a))
        ma, mb = sum(a)/n, sum(b)/n
        da, db = [v-ma for v in a], [v-mb for v in b]
        vx, vy = sum(v*v for v in da)/n, sum(v*v for v in db)/n
        covariance = sum(v*w for v,w in zip(da,db))/n
        denominator = vx+vy+(ma-mb)**2
        rho = 2*covariance/denominator
        r = covariance/(vx*vy).sqrt()
        u2 = (ma-mb)**2/(vx*vy).sqrt()
        variance = (rho**2*(1-r**2)*(1-rho**2)/r**2
                    +2*rho**3*(1-rho)*u2/r-rho**4*u2**2/(2*r**2))/(n-2)
        if variance <= 0 or abs(rho) >= 1:
            return None
        se = variance.sqrt()
        q = Decimal.from_float(critical)
        if method == 'z-transform':
            center = ((1+rho)/(1-rho)).ln()/2
            transformed_se = se/(1-rho**2)
            limits = []
            for v in (center-q*transformed_se, center+q*transformed_se):
                e = (2*v).exp()
                limits.append((e-1)/(e+1))
        else:
            transformed_se = None
            limits = [rho-q*se,rho+q*se]
        return (float(variance),float(se),
                float(transformed_se) if transformed_se is not None else None,
                float(limits[0]),float(limits[1]))


def concordance_interval(x, y, confidence=.95, method='z-transform'):
    """Return explicit transformed or normal Lin CCC inference, or an empty status.

    Supports 10–5,000 complete independent pairs in at most 5,000 supplied rows.
    Confidence is .80–.99. Normal/Wald limits are not clipped to the parameter
    space. The two methods are never substituted for each other. The public
    concordance() point helper and installed jamovi analysis remain unchanged.
    """
    if (isinstance(confidence, (bool, np.bool_)) or not isinstance(confidence, Real)
            or not math.isfinite(confidence) or not .8 <= confidence <= .99):
        raise InputError('CCC confidence must be a finite number between 0.80 and 0.99.')
    if not isinstance(method, str) or method not in ('z-transform', 'asymptotic'):
        raise InputError('Choose z-transform or asymptotic explicitly; no fallback is applied.')
    point = concordance(x, y)
    n = point['n_complete']
    if n < 10:
        raise InputError('CCC intervals require at least 10 complete independent measurement pairs.')
    result = dict(estimate=point['ccc'], lower=None, upper=None, se=None, variance=None,
                  transformed_se=None, confidence=float(confidence), method=method,
                  status='unavailable', reason='', n_complete=n, point=point)
    p, r, cb = point['ccc'], point['precision'], point['bias_correction']
    if p is None or r is None:
        result['reason'] = 'CCC or Pearson precision is undefined for constant measurement columns.'
        return result
    if r == 0:
        result['reason'] = 'The referenced Lin variance is undefined at exact zero Pearson correlation.'
        return result
    if abs(p) == 1:
        result['reason'] = 'CCC is on the parameter boundary; a nondegenerate interval is unavailable.'
        return result
    indices = point['retained_indices']
    a, b = _numeric(x)[indices], _numeric(y)[indices]
    critical = float(norm.ppf((1+float(confidence))/2))
    arithmetic = 'float64_scaled'
    if abs(p) > .99:
        precise = _decimal_limits(a,b,critical,method)
        if precise is None:
            result['reason'] = 'High-precision Lin variance is nonpositive or unresolved.'
            return result
        variance,se,transformed_se,lower,upper = precise
        arithmetic = 'decimal80_boundary'
    else:
        location = _location_share(a, b)
        if location is None:
            result['reason'] = 'The standardized location shift is numerically unresolved.'
            return result
        # With p=r*Cb and location=Cb*u^2, the corrected Lin variance is
        # Cb^2 * [(1-r^2)(1-p^2) + 2*r^2*(1-p)*location
        #          - r^2*location^2/2] / (n-2).
        bracket = math.fsum(((1-r)*(1+r)*(1-p)*(1+p),
                             2*r*r*(1-p)*location, -.5*r*r*location*location))
        if not math.isfinite(bracket) or bracket <= 0:
            result['reason'] = 'Lin variance is nonpositive or numerically unresolved; no interval is reported.'
            return result
        se = cb*math.sqrt(bracket/(n-2))
        variance = se*se
        if method == 'z-transform':
            transformed_se = se/((1-p)*(1+p))
            center = math.atanh(p)
            lower = math.tanh(center-critical*transformed_se)
            upper = math.tanh(center+critical*transformed_se)
        else:
            transformed_se = None
            lower, upper = p-critical*se, p+critical*se
    if not math.isfinite(variance) or variance <= 0:
        result['reason'] = 'Lin variance is outside the resolved finite numeric range.'
        return result
    if not all(math.isfinite(v) for v in (se, lower, upper)) or not lower < p < upper:
        result['reason'] = 'Interval limits are nonfinite or their width is numerically unresolved.'
        return result
    result.update(lower=lower, upper=upper, se=se, variance=variance,
                  transformed_se=transformed_se, arithmetic=arithmetic, status='ok', reason='')
    return result
