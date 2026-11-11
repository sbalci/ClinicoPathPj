"""Source-only empirical-moment delta CCC uncertainty; not Lin's normal-model SE."""
import math
from decimal import Decimal, localcontext
from numbers import Real

import numpy as np
from scipy.stats import norm

from cpj_concordance import concordance, _numeric
from cpj_runtime import InputError


def _scaled_influences(x, y, rho):
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
    da, db = a-ma, b-mb
    vx = math.fsum(float(v)*float(v) for v in da)/n
    vy = math.fsum(float(v)*float(v) for v in db)/n
    covariance = math.fsum(float(v)*float(w) for v,w in zip(da,db))/n
    delta = ma-mb
    denominator = math.fsum((vx,vy,delta*delta))
    if denominator <= 0 or not math.isfinite(denominator):
        return None
    influences = []
    for dx,dy in zip(da,db):
        covariance_if = float(dx)*float(dy)-covariance
        denominator_if = math.fsum((float(dx)*float(dx)-vx,float(dy)*float(dy)-vy,
                                    2*delta*(float(dx)-float(dy))))
        influences.append(math.fsum((2*covariance_if,-rho*denominator_if))/denominator)
    variance = math.fsum(v*v for v in influences)/(n*n)
    return variance, math.fsum(influences)/n


def _decimal_inference(x, y, critical, method):
    with localcontext() as context:
        context.prec = 80
        a = [Decimal.from_float(float(v)) for v in x]
        b = [Decimal.from_float(float(v)) for v in y]
        n = Decimal(len(a))
        ma, mb = sum(a)/n, sum(b)/n
        da, db = [v-ma for v in a], [v-mb for v in b]
        vx, vy = sum(v*v for v in da)/n, sum(v*v for v in db)/n
        covariance = sum(v*w for v,w in zip(da,db))/n
        delta = ma-mb
        denominator = vx+vy+delta*delta
        rho = 2*covariance/denominator
        influence = [(2*(dx*dy-covariance)-rho*(dx*dx-vx+dy*dy-vy+2*delta*(dx-dy)))/denominator
                     for dx,dy in zip(da,db)]
        variance = sum(v*v for v in influence)/(n*n)
        if variance <= 0 or abs(rho) >= 1:
            return None
        se = variance.sqrt()
        q = Decimal.from_float(critical)
        if method == 'empirical-z':
            center = ((1+rho)/(1-rho)).ln()/2
            transformed_se = se/(1-rho*rho)
            bounds = []
            for z in (center-q*transformed_se,center+q*transformed_se):
                e = (2*z).exp()
                bounds.append((e-1)/(e+1))
        else:
            transformed_se = None
            bounds = [rho-q*se,rho+q*se]
        return (float(variance),float(se),float(sum(influence)/n),
                float(transformed_se) if transformed_se is not None else None,
                float(bounds[0]),float(bounds[1]))


def empirical_concordance_interval(x, y, confidence=.95, method='empirical-z'):
    """Empirical influence variance for iid pairs with finite fourth moments.

    No normal-model Lin variance, n-2 correction, automatic fallback, clipping or
    outlier deletion. Exact zero Pearson correlation is supported when the
    empirical first-order variance is positive. Neither inference method is
    exposed by the installed point-only jamovi analysis.
    """
    if (isinstance(confidence,(bool,np.bool_)) or not isinstance(confidence,Real)
            or not math.isfinite(confidence) or not .8 <= confidence <= .99):
        raise InputError('CCC confidence must be a finite number between 0.80 and 0.99.')
    if not isinstance(method,str) or method not in ('empirical-z','empirical-normal'):
        raise InputError('Choose empirical-z or empirical-normal explicitly; no fallback is applied.')
    point = concordance(x,y)
    n = point['n_complete']
    if n < 10:
        raise InputError('CCC intervals require at least 10 complete independent measurement pairs.')
    p = point['ccc']
    result = dict(estimate=p,lower=None,upper=None,se=None,variance=None,
                  mean_influence=None,transformed_se=None,arithmetic=None,
                  confidence=float(confidence),method=method,n_complete=n,
                  variance_method='empirical moment delta',variance_divisor='n^2',
                  status='unavailable',reason='',point=point)
    if p is None:
        result['reason'] = 'CCC is undefined for identical constant measurement columns.'
        return result
    if abs(p) == 1:
        result['reason'] = 'CCC is on the parameter boundary; a nondegenerate interval is unavailable.'
        return result
    indices = point['retained_indices']
    a, b = _numeric(x)[indices], _numeric(y)[indices]
    critical = float(norm.ppf((1+float(confidence))/2))
    if abs(p) > .99:
        precise = _decimal_inference(a,b,critical,method)
        if precise is None:
            result['reason'] = 'Empirical first-order variance is zero or unresolved.'
            return result
        variance,se,mean_influence,transformed_se,lower,upper = precise
        arithmetic = 'decimal80_boundary'
    else:
        moments = _scaled_influences(a,b,p)
        if moments is None:
            result['reason'] = 'Empirical moments are numerically unresolved.'
            return result
        variance,mean_influence = moments
        if not math.isfinite(variance) or variance <= 0:
            result['reason'] = 'Empirical first-order variance is zero or unresolved.'
            return result
        se = math.sqrt(variance)
        if method == 'empirical-z':
            transformed_se = se/((1-p)*(1+p))
            center = math.atanh(p)
            lower = math.tanh(center-critical*transformed_se)
            upper = math.tanh(center+critical*transformed_se)
        else:
            transformed_se = None
            lower,upper = p-critical*se,p+critical*se
        arithmetic = 'float64_scaled'
    if (not all(math.isfinite(v) for v in (variance,se,lower,upper,mean_influence))
            or variance <= 0 or not lower < p < upper):
        result['reason'] = 'Empirical uncertainty or interval width is numerically unresolved.'
        return result
    result.update(variance=variance,se=se,lower=lower,upper=upper,
                  transformed_se=transformed_se,mean_influence=mean_influence,
                  arithmetic=arithmetic,status='ok',reason='')
    return result
