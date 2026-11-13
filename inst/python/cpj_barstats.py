"""Independent categorical bar counts, explicit denominators and point-only association."""
import math
import numpy as np

from cpj_crosstable import categorical
from cpj_estimation import _ids, _numeric
from cpj_runtime import Factor, InputError

MAX_TOTAL = 2**53-1
MAX_LEVELS = 20


def _factor(value, name):
    if not isinstance(value,Factor) or np.ma.isMaskedArray(value.codes):
        raise InputError(f'{name}: select a labelled factor without masked codes.')
    if not isinstance(value.levels,(list,tuple)) or len(value.levels)>1000:
        raise InputError(f'{name}: supply at most 1,000 declared factor levels.')
    return categorical(value,name)


def _association(table, expected, n, enabled):
    sparse = bool(np.any(expected<5))
    result = dict(enabled=enabled,primary_method='disabled',primary_p=None,
        pearson_statistic=None,df=None,pearson_p=None,cramers_v_raw=None,
        cramers_v_corrected=None,corrected_unavailable_reason=None,
        sparse_warning=sparse and table.shape!=(2,2),minimum_expected=float(expected.min()),
        expected_below5=int(np.count_nonzero(expected<5)))
    if not enabled:return result
    from scipy.stats import chi2, fisher_exact
    statistic = float(np.sum((table-expected)**2/expected))
    r,c = table.shape
    df = (r-1)*(c-1)
    p = float(chi2.sf(statistic,df))
    fisher = table.shape==(2,2) and sparse
    primary = float(fisher_exact(table,alternative='two-sided').pvalue) if fisher else p
    phi2 = statistic/n
    raw = math.sqrt(phi2/min(r-1,c-1))
    corrected_phi = max(0.,phi2-(r-1)*(c-1)/(n-1))
    denominator = min(r-(r-1)**2/(n-1)-1,c-(c-1)**2/(n-1)-1)
    corrected = math.sqrt(corrected_phi/denominator) if denominator>0 else None
    if not all(math.isfinite(v) for v in (statistic,p,primary,raw)) or (corrected is not None and not math.isfinite(corrected)):
        raise InputError('Association calculations exceed the supported numeric range.')
    result.update(primary_method='fisher_exact' if fisher else 'pearson_chi_square',primary_p=primary,
        pearson_statistic=statistic,df=df,pearson_p=p,cramers_v_raw=raw,
        cramers_v_corrected=corrected,
        corrected_unavailable_reason='nonpositive_corrected_denominator' if corrected is None else None)
    return result


def bar_core(outcome, group, *, weights=None, inference=False, subject_ids=None):
    """One independent factor pair; frequencies are integer observations, never expanded."""
    if not isinstance(inference,bool):
        raise InputError('Enable or disable association results explicitly.')
    a,a_labels = _factor(outcome,'Outcome')
    b,b_labels = _factor(group,'Group')
    n = len(a)
    if not 1<=n<=100000 or len(b)!=n:
        raise InputError('Supply 1–100,000 aligned source rows for both factors.')
    if weights is not None and subject_ids is not None:
        raise InputError('Subject-ID auditing is unavailable for aggregated frequency rows.')
    w = np.ones(n) if weights is None else _numeric(weights,'Frequencies')
    if len(w)!=n:
        raise InputError('Frequencies must align with the factor source rows.')
    known = ~np.isnan(w)
    if np.any(w[known]<0) or np.any(w[known]!=np.floor(w[known])):
        raise InputError('Frequencies must be nonnegative whole numbers or missing.')
    if np.any(w[known]>MAX_TOTAL):
        raise InputError('Frequency total must not exceed 2^53 - 1.')
    complete = (a>=0)&(b>=0)&known
    positive = complete&(w>0)
    if not np.any(positive):
        raise InputError('No complete positive-frequency observations remain.')
    total = sum(int(v) for v in w[positive])
    if total>MAX_TOTAL:
        raise InputError('Frequency total must not exceed 2^53 - 1.')
    ac,bc = [int(v) for v in np.unique(a[positive])],[int(v) for v in np.unique(b[positive])]
    if min(len(ac),len(bc))<2:
        raise InputError('Both roles require at least two levels with positive complete frequency.')
    if max(len(ac),len(bc))>MAX_LEVELS:
        raise InputError('This core supports at most 20 active levels in either factor.')
    indices = np.flatnonzero(positive).tolist()
    ids = _ids(subject_ids,n,positive)
    ai,bi = {v:i for i,v in enumerate(ac)},{v:i for i,v in enumerate(bc)}
    table = np.zeros((len(ac),len(bc)),dtype=np.int64)
    for i in indices:table[ai[int(a[i])],bi[int(b[i])]]+=int(w[i])
    outcome_totals,group_totals = table.sum(axis=1),table.sum(axis=0)
    expected = np.array([[int(v)*int(g)/total for g in group_totals] for v in outcome_totals])
    cells=[]; geometry=dict(percentage=[],count=[])
    for j,g in enumerate(bc):
        group_n = int(group_totals[j])
        above = group_n
        for i,o in enumerate(ac):
            count = int(table[i,j]); lower = above-count
            cell=dict(outcome=o,group=g,count=count,expected=float(expected[i,j]),
                group_total=group_n,outcome_total=int(outcome_totals[i]),
                group_proportion=count/group_n,overall_proportion=count/total)
            cells.append(cell)
            for scale in ('percentage','count'):
                lo,hi = (lower/group_n,above/group_n) if scale=='percentage' else (lower,above)
                geometry[scale].append(dict(cell,x=j+1,xmin=j+1-.45,xmax=j+1+.45,
                                           lower=lo,upper=hi,center=(lo+hi)/2))
            above = lower
    return dict(schema_version=1,status='ok',n_source=n,n_complete=int(np.sum(complete)),
        excluded_missing=int(np.sum(~complete)),missing_outcome=int(np.sum(a<0)),
        missing_group=int(np.sum(b<0)),missing_frequency=int(np.sum(~known)),
        zero_frequency=int(np.sum(complete&(w==0))),n_contributing=len(indices),n_total=total,
        retained_indices=indices,retained_subject_ids=ids,outcome_codes=ac,group_codes=bc,
        outcome_labels=a_labels,group_labels=b_labels,
        dropped_outcome_codes=[i for i in range(len(a_labels)) if i not in ac],
        dropped_group_codes=[i for i in range(len(b_labels)) if i not in bc],
        cells=cells,association=_association(table,expected,total,inference),geometry=geometry)
