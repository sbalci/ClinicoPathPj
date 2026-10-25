"""Shared diagnostic accuracy arithmetic; no continuity corrections or hidden level guessing."""
import math
from cpj_runtime import Factor, InputError, fmt_num


def finite_number(value, name, *, integer=False, minimum=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise InputError(f'{name} must be a finite number.')
    if integer and (not float(value).is_integer() or value > 2**53 - 1):
        raise InputError(f'{name} must be a whole number no greater than 2^53 - 1.')
    if minimum is not None and value < minimum:
        raise InputError(f'{name} must be at least {minimum}.')
    return int(value) if integer else float(value)


def probability(value, name):
    value = finite_number(value, name)
    if not 0 <= value <= 1:
        raise InputError(f'{name} must lie between 0 and 1.')
    return value


def divide(numerator, denominator):
    if numerator is None or denominator is None:
        return None
    if denominator == 0:
        return None if numerator == 0 else math.inf
    return numerator / denominator


def display(value):
    if value is None:
        return 'Undefined'
    if math.isinf(value):
        return 'Infinite'
    return fmt_num(value, digits=6)


def binary(group, positive, name):
    import numpy as np
    if not isinstance(group, Factor):
        raise InputError(f'The {name} column must be nominal or ordinal.')
    observed = np.unique(group.codes[group.codes >= 0])
    if len(observed) > 2:
        raise InputError(f'The {name} column contains more than two observed levels.')
    if positive not in group.levels:
        raise InputError(f'Choose the {name} positive level explicitly.')
    return group.codes == group.levels.index(positive)


def calculate(counts, ci_width=95):
    from scipy.stats import binomtest
    tp,fp,fn,tn = [finite_number(v,'Confusion counts',integer=True,minimum=0) for v in counts]
    n=tp+fp+fn+tn
    if n == 0:
        raise InputError('The confusion table must contain at least one observation.')
    width=finite_number(ci_width,'Confidence level')/100
    if not .5 <= width < 1:
        raise InputError('Confidence level must be at least 50% and below 100%.')
    proportions=[]
    for label,a,b in [('Sensitivity',tp,tp+fn),('Specificity',tn,tn+fp),
                      ('Positive predictive value',tp,tp+fp),('Negative predictive value',tn,tn+fn),
                      ('Accuracy',tp+tn,n)]:
        ci=binomtest(a,b).proportion_ci(confidence_level=width) if b else None
        proportions.append(dict(metric=label,estimate=a/b if b else None,
                                lower=ci.low if ci else None,upper=ci.high if ci else None))
    se,sp=proportions[0]['estimate'],proportions[1]['estimate']
    ratios=[('Positive likelihood ratio',divide(se,None if sp is None else 1-sp)),
            ('Negative likelihood ratio',divide(None if se is None else 1-se,sp)),
            ('Diagnostic odds ratio',divide(tp*tn,fp*fn)),
            ('Youden index',None if se is None or sp is None else se+sp-1)]
    return proportions,ratios


def report(counts, options, out):
    proportions,ratios=calculate(counts,options.get('ciWidth',95))
    tp,fp,fn,tn=counts
    for label,n in zip(('True positive','False positive','False negative','True negative'),counts):
        out.row('counts',cell=label,n=n)
    for row in proportions:
        out.row('accuracy',**row)
    for label,value in ratios:
        out.row('ratios',metric=label,estimate=value,display=display(value))
    if tp+fn == 0 or tn+fp == 0:
        out.warn('A reference group is absent. Metrics requiring that group are undefined.')
    out.note('accuracy',f"{options.get('ciWidth',95):g}% exact Clopper-Pearson intervals assume independent "
             'observations and a fixed classification rule. PPV, NPV and accuracy describe this sample, '
             'not population performance in a case-control sample.')
    out.note('ratios','No continuity correction is applied. Infinite means a positive numerator with a zero '
             'denominator; undefined includes zero divided by zero or a missing reference margin. Ratio intervals are omitted.')
    if options.get('usePrevalence',False):
        p=probability(options.get('prevalence',.3),'Supplied prevalence')
        if not 0 < p < 1:
            raise InputError('Supplied prevalence must be strictly between 0 and 1.')
        se,sp=proportions[0]['estimate'],proportions[1]['estimate']
        if se is None or sp is None:
            ppv=npv=None
        else:
            ppv=divide(p*se,p*se+(1-p)*(1-sp))
            npv=divide((1-p)*sp,(1-p)*sp+p*(1-se))
        for label,value in [('Supplied prevalence',p),('Derived PPV',ppv),('Derived NPV',npv)]:
            out.row('population',metric=label,estimate=value)
        out.note('population','Bayes calculations assume sample sensitivity and specificity transport to the '
                 'specified population. The supplied prevalence is treated as known; no derived intervals are provided.')
