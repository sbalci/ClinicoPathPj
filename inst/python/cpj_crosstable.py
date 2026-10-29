"""Grouped summaries and the supported default gtsummary test-selection subset."""
import math
import numpy as np
from scipy import stats
from cpj_runtime import Factor, InputError
from cpj_correlation import adjust
from cpj_tree import _mean_sd


def categorical(column, name):
    if not isinstance(column, Factor):
        raise InputError(f'{name}: select a nominal or ordinal grouping variable.')
    codes = np.asarray(column.codes)
    labels = column.levels
    text = [v for v in labels if v is not None]
    if (codes.ndim != 1 or codes.dtype.kind not in 'iu' or np.any(codes < -1) or
            np.any(codes >= len(labels)) or any(not isinstance(v, str) for v in text) or
            len(set(text)) != len(text)):
        raise InputError(f'{name}: invalid category labels or codes.')
    values = codes.copy()
    values[np.isin(codes, [j for j,v in enumerate(labels) if v is None])] = -1
    return values, list(labels)


def quantiles(values):
    """Type-7 interpolation avoiding an overflowing opposite-sign subtraction."""
    ordered = np.sort(values)
    answer = []
    for probability in (.25, .5, .75):
        index = (len(ordered)-1)*probability
        lo = int(np.floor(index)); hi = int(np.ceil(index)); fraction = index-lo
        a = float(ordered[lo]); b = float(ordered[hi])
        value = ((1-fraction)*a+fraction*b if a < 0 < b else a+fraction*(b-a))
        answer.append(value)
    return answer


def tied_rank_exact(values, first_n):
    """Conditional label-permutation distribution for R 4.6 small-sample tied ranks.

    Doubled midranks make integer sums. Dynamic-programming counts are float64;
    choose(98,49) fits comfortably, and no permutations are sampled.
    """
    ranks = np.rint(2*stats.rankdata(values)).astype(int)
    n = len(ranks)
    k = min(first_n, n-first_n)
    observed = int(ranks[:first_n].sum() if first_n == k else ranks[first_n:].sum())
    maximum = int(np.sort(ranks)[-k:].sum())
    counts = np.zeros((k+1,maximum+1),dtype=float)
    counts[0,0] = 1
    for seen,rank in enumerate(ranks):
        for used in range(min(seen+1,k),0,-1):
            counts[used,rank:] += counts[used-1,:-rank]
    denominator = math.comb(n,k)
    lower = float(counts[k,:observed+1].sum()/denominator)
    upper = float(counts[k,observed:].sum()/denominator)
    return min(1.,2*min(lower,upper))


def compare(values, group_codes, group_levels, kind, pcat):
    valid = (group_codes >= 0) & (np.isfinite(values) if kind == 'continuous' else values >= 0)
    x = values[valid]; g = group_codes[valid]
    groups = [code for code in group_levels if np.any(g == code)]
    row = dict(n=int(valid.sum()), groups=len(groups), method='', statistic=None,
               df=None, p=None, reason='')
    if len(groups) < 2:
        row['reason'] = 'Fewer than two groups with observed values'; return row
    if kind == 'continuous':
        samples = [x[g == code] for code in groups]
        unique = len(np.unique(x))
        if len(groups) == 2:
            exact = all(len(v) < 50 for v in samples)
            if exact and unique < len(x):
                ordered = np.concatenate(samples)
                statistic = float(stats.rankdata(ordered)[:len(samples[0])].sum()-len(samples[0])*(len(samples[0])+1)/2)
                row.update(method='Wilcoxon exact (ties)',statistic=statistic,
                           p=tied_rank_exact(ordered,len(samples[0])))
            elif not exact and unique < 2:
                row['reason'] = 'All observed values are identical; normal rank variance is zero'
            else:
                test = stats.mannwhitneyu(*samples, alternative='two-sided',
                                         method='exact' if exact else 'asymptotic', use_continuity=True)
                row.update(method='Wilcoxon exact' if exact else 'Wilcoxon normal',
                           statistic=float(test.statistic), p=float(test.pvalue))
        else:
            if unique < 2:
                row['reason'] = 'All observed values are identical'; return row
            test = stats.kruskal(*samples)
            row.update(method='Kruskal–Wallis', statistic=float(test.statistic),
                       df=len(groups)-1, p=float(test.pvalue))
    else:
        levels = sorted(set(int(v) for v in x))
        if len(levels) < 2:
            row['reason'] = 'Fewer than two observed categories'; return row
        table = np.array([[np.sum((x == level) & (g == code)) for code in groups] for level in levels])
        pearson = stats.chi2_contingency(table, correction=False)
        use_fisher = pcat == 'fisher' or np.any(pearson.expected_freq < 5)
        if use_fisher:
            if table.shape != (2,2):
                row.update(method='Exact RxC unavailable',
                           reason='Larger exact contingency tests are outside this core; no Pearson substitution')
            else:
                row.update(method='Fisher 2×2', p=float(stats.fisher_exact(table, alternative='two-sided').pvalue))
        else:
            row.update(method='Pearson χ²', statistic=float(pearson.statistic),
                       df=int(pearson.dof), p=float(pearson.pvalue))
    if row['p'] is not None and not np.isfinite(row['p']):
        row.update(p=None, reason='Test is numerically undefined')
    return row


def calculate(data, options):
    names = options.get('vars') or []; group = options.get('group')
    if (not isinstance(names, list) or not 1 <= len(names) <= 20 or
            any(not isinstance(v,str) or not v for v in names) or len(set(names)) != len(names)):
        raise InputError('Select one to twenty distinct summary variables.')
    if not isinstance(group,str) or not group or group in names:
        raise InputError('Choose a categorical grouping variable separate from summary variables.')
    g, group_labels = categorical(data.get(group), group)
    total = len(g)
    if not 1 <= total <= 10000:
        raise InputError('This core accepts one to 10,000 rows without sampling.')
    numeric_mode = options.get('numericMode','auto')
    if numeric_mode not in ('auto','continuous') or options.get('cont','mean') not in ('mean','median'):
        raise InputError('Unknown numeric typing or summary selection.')
    if options.get('pcat','chisq') not in ('chisq','fisher'):
        raise InputError('Unknown categorical test selection.')
    if options.get('p_adjust','none') not in ('none','bonferroni','holm','BH','BY'):
        raise InputError('Unknown multiplicity adjustment.')
    columns = {}; masks = []
    for name in names:
        column = data.get(name)
        if isinstance(column,Factor):
            values,labels = categorical(column,name)
            columns[name] = dict(values=values,labels=labels,numeric=False)
            valid = values >= 0
        else:
            if (not isinstance(column,np.ndarray) or column.ndim != 1 or
                    column.dtype.kind not in 'fiu'):
                raise InputError(f'{name}: use a numeric or nominal/ordinal variable.')
            values = np.asarray(column,dtype=float)
            if np.isinf(values).any():
                raise InputError(f'{name}: recode infinite values before analysis.')
            columns[name] = dict(values=values,numeric=True)
            valid = np.isfinite(values)
        if len(values) != total:
            raise InputError('Selected variables must have equal lengths.')
        masks.append(valid)
    common = (g >= 0) & np.logical_and.reduce(masks)
    exclude = options.get('excl',False)
    if not isinstance(exclude,bool): raise InputError('Missing-value exclusion must be true or false.')
    keep = common if exclude else g >= 0
    retained = int(keep.sum())
    if not retained: raise InputError('No rows remain with a recorded grouping value under the selected missingness policy.')
    group_levels = [j for j in range(len(group_labels)) if np.any(g[keep] == j)]
    if not 2 <= len(group_levels) <= 10:
        raise InputError('Two to ten observed groups are required after missingness handling.')
    missing_group = int(np.sum(g < 0))
    g = g[keep]
    strata = [('Overall','',np.ones(retained,dtype=bool))]+[
        ('Group',group_labels[code],g == code) for code in group_levels]
    result = dict(total=total,retained=retained,missingGroup=missing_group,
                  excluded=total-retained,group=group,continuous=[],categories=[],tests=[],typing=[],cohort=[])
    for scope,label,mask in strata:
        result['cohort'].append(dict(scope=scope,group=label,n=int(mask.sum()),percent=int(mask.sum())/retained))
    for name,column in columns.items():
        values = column['values'][keep]
        kind = 'continuous' if column['numeric'] else 'categorical'
        typing_values = column['values'][common] if exclude else column['values']
        auto = (column['numeric'] and numeric_mode == 'auto' and
                len(np.unique(typing_values[np.isfinite(typing_values)])) <= 6)
        if auto:
            unique = np.unique(typing_values[np.isfinite(typing_values)])
            codes = np.full(retained,-1,dtype=int)
            for j,value in enumerate(unique): codes[values == value] = j
            values = codes; column['labels'] = [format(float(v),'.17g') for v in unique]
            kind = 'categorical'
        valid = np.isfinite(values) if kind == 'continuous' else values >= 0
        result['typing'].append(dict(variable=name,kind=kind,
            rule='Numeric ≤6 distinct: categorical' if auto else 'Numeric: continuous' if column['numeric'] else 'Recorded factor',
            valid=int(valid.sum()),missing=int((~valid).sum())))
        if kind == 'categorical':
            labels = column['labels']
            levels = [j for j in range(len(labels)) if labels[j] is not None]
            if len(levels) > 20: raise InputError(f'{name}: at most twenty declared categories are supported; remove unused levels explicitly if needed.')
            missing_label = '(Missing)'; suffix = 1
            while missing_label in labels:
                suffix += 1; missing_label = f'(Missing {suffix})'
        for scope,label,mask in strata:
            selected = values[mask]; observed = selected[np.isfinite(selected)] if kind == 'continuous' else selected[selected>=0]
            n = len(observed); missing = len(selected)-n
            base = dict(variable=name,scope=scope,group=label)
            if kind == 'continuous':
                mean,sd = _mean_sd(observed)
                q1,median,q3 = quantiles(observed) if n else (None,None,None)
                result['continuous'].append(dict(base,n=n,missing=missing,mean=mean,sd=sd,q1=q1,median=median,q3=q3))
            else:
                for code in levels:
                    count = int(np.sum(observed == code))
                    result['categories'].append(dict(base,level=labels[code],n=count,valid=n,
                                                       percent=count/n if n else None))
                if missing:
                    result['categories'].append(dict(base,level=missing_label,n=missing,valid=n,percent=None))
        test = compare(values,g,group_levels,kind,options.get('pcat','chisq'))
        result['tests'].append(dict(variable=name,**test))
    # R p.adjust removes NA test values before its default n is evaluated. Use the
    # family of available variable-level tests, then restore unavailable rows.
    available = [i for i,t in enumerate(result['tests']) if t['p'] is not None]
    adjusted = adjust([result['tests'][i]['p'] for i in available],options.get('p_adjust','none'))
    for test in result['tests']: test['adjusted'] = None
    for i,p in zip(available,adjusted): result['tests'][i]['adjusted'] = p
    result['testFamily'] = len(available)
    return result
