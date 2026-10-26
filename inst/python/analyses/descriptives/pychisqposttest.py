"""Chi-Square Post-Tests (Python). Validated core; see docs/python-core-analyses.md for limits."""
from cpj_runtime import InputError, md_escape

SPEC = {'name': 'pychisqposttest',
 'title': 'Chi-Square Post-Tests',
 'menuGroup': 'Descriptives Py',
 'menuSubgroup': 'Contingency tables',
 'version': '0.2.0',
 'options': [{'name': 'rows',
              'title': 'Row factor',
              'type': 'Variable',
              'permitted': ['factor'],
              'suggested': ['nominal'],
              'required': True},
             {'name': 'cols',
              'title': 'Column factor',
              'type': 'Variable',
              'permitted': ['factor'],
              'suggested': ['nominal'],
              'required': True},
             {'name': 'counts',
              'title': 'Optional frequency counts',
              'type': 'Variable',
              'permitted': ['numeric'],
              'suggested': ['continuous']},
             {'name': 'adjustment',
              'title': 'Pairwise p-value adjustment',
              'type': 'List',
              'default': 'bonferroni',
              'options': [{'name': 'bonferroni', 'title': 'Bonferroni'},
                          {'name': 'holm', 'title': 'Holm'},
                          {'name': 'bh', 'title': 'Benjamini-Hochberg'},
                          {'name': 'none', 'title': 'Disable pairwise tests'}]},
             {'name': 'alpha',
              'title': 'Significance level',
              'type': 'Number',
              'default': 0.05,
              'min': 0.001,
              'max': 0.1}],
 'results': [{'name': 'summary', 'title': 'Interpretation', 'type': 'Text'},
             {'name': 'overall',
              'title': 'Overall Association',
              'type': 'Table',
              'columns': [{'name': 'n', 'title': 'Total Frequency', 'type': 'number'},
                          {'name': 'statistic', 'title': 'Pearson Chi-Square', 'type': 'number'},
                          {'name': 'df', 'title': 'df', 'type': 'integer'},
                          {'name': 'p', 'title': 'p', 'type': 'number', 'format': 'zto,pvalue'},
                          {'name': 'cramersV', 'title': 'Cramers V', 'type': 'number'}]},
             {'name': 'cells',
              'title': 'Cell Counts and Adjusted Residual Tests',
              'type': 'Table',
              'columns': [{'name': 'row', 'title': 'Row', 'type': 'text'},
                          {'name': 'column', 'title': 'Column', 'type': 'text'},
                          {'name': 'observed', 'title': 'Observed', 'type': 'number'},
                          {'name': 'expected', 'title': 'Expected', 'type': 'number'},
                          {'name': 'residual', 'title': 'Adjusted Residual', 'type': 'number'},
                          {'name': 'p',
                           'title': 'Cell p',
                           'type': 'number',
                           'format': 'zto,pvalue'},
                          {'name': 'adjusted',
                           'title': 'Bonferroni p',
                           'type': 'number',
                           'format': 'zto,pvalue'},
                          {'name': 'significant', 'title': 'Significant', 'type': 'text'}]},
             {'name': 'pairs',
              'title': 'Pairwise Comparisons',
              'type': 'Table',
              'columns': [{'name': 'dimension', 'title': 'Compared Dimension', 'type': 'text'},
                          {'name': 'first', 'title': 'First Level', 'type': 'text'},
                          {'name': 'second', 'title': 'Second Level', 'type': 'text'},
                          {'name': 'method', 'title': 'Method', 'type': 'text'},
                          {'name': 'statistic', 'title': 'Pearson Chi-Square', 'type': 'number'},
                          {'name': 'df', 'title': 'df', 'type': 'integer'},
                          {'name': 'p', 'title': 'p', 'type': 'number', 'format': 'zto,pvalue'},
                          {'name': 'adjusted',
                           'title': 'Adjusted p',
                           'type': 'number',
                           'format': 'zto,pvalue'}]}],
 'ui': {'children': [{'type': 'VariableSupplier',
                      'persistentItems': False,
                      'stretchFactor': 1,
                      'children': [{'type': 'TargetLayoutBox',
                                    'label': 'Row factor',
                                    'children': [{'type': 'VariablesListBox',
                                                  'name': 'rows',
                                                  'isTarget': True,
                                                  'maxItemCount': 1}]},
                                   {'type': 'TargetLayoutBox',
                                    'label': 'Column factor',
                                    'children': [{'type': 'VariablesListBox',
                                                  'name': 'cols',
                                                  'isTarget': True,
                                                  'maxItemCount': 1}]},
                                   {'type': 'TargetLayoutBox',
                                    'label': 'Optional frequency counts',
                                    'children': [{'type': 'VariablesListBox',
                                                  'name': 'counts',
                                                  'isTarget': True,
                                                  'maxItemCount': 1}]}]},
                     {'type': 'CollapseBox',
                      'label': 'Analysis and Model',
                      'collapsed': False,
                      'children': [{'type': 'LayoutBox',
                                    'margin': 'large',
                                    'children': [{'name': 'adjustment', 'type': 'ComboBox'}]}]},
                     {'type': 'CollapseBox',
                      'label': 'Uncertainty and Validation',
                      'collapsed': True,
                      'children': [{'type': 'LayoutBox',
                                    'margin': 'large',
                                    'children': [{'name': 'alpha',
                                                  'type': 'TextBox',
                                                  'format': 'number'}]}]},
                     {'type': 'CollapseBox',
                      'label': 'Advanced Settings',
                      'collapsed': True,
                      'children': [{'type': 'CheckBox', 'name': 'showConsole'}]}]}}


def adjust_p(values, method):
    import numpy as np
    p=np.asarray(values,dtype=float)
    m=len(p)
    if not m:
        return p
    if method=='bonferroni':
        return np.minimum(1,p*m)
    order=np.argsort(p,kind='stable')
    ranked=p[order]
    if method=='holm':
        adjusted=np.maximum.accumulate(ranked*(m-np.arange(m)))
    elif method=='bh':
        adjusted=np.minimum.accumulate((ranked*m/(np.arange(m)+1))[::-1])[::-1]
    else:
        raise InputError('Unknown p-value adjustment.')
    answer=np.empty(m)
    answer[order]=np.minimum(1,adjusted)
    return answer


def run(data, options, out):
    import itertools
    import math
    import numpy as np
    from scipy.stats import chi2_contingency, fisher_exact, norm
    from cpj_runtime import Factor
    from cpj_accuracy import finite_number
    a,b=data[options['rows']],data[options['cols']]
    if not isinstance(a,Factor) or not isinstance(b,Factor):
        raise InputError('Rows and columns must be factors.')
    weights=np.ones(len(a.codes))
    keep=(a.codes>=0)&(b.codes>=0)
    if options.get('counts'):
        weights=np.asarray(data[options['counts']],dtype=float)
        if np.any(np.isinf(weights)) or np.any(weights[np.isfinite(weights)]<0) or np.any(
                weights[np.isfinite(weights)]!=np.floor(weights[np.isfinite(weights)])):
            raise InputError('Frequencies must be finite nonnegative whole numbers, or missing.')
        keep &= np.isfinite(weights)
    if not keep.any():
        raise InputError('No complete rows remain.')
    observed_rows=np.unique(a.codes[keep & (weights>0)])
    observed_cols=np.unique(b.codes[keep & (weights>0)])
    if len(observed_rows)<2 or len(observed_cols)<2:
        raise InputError('Both factors need at least two levels with positive frequency.')
    if len(observed_rows)*len(observed_cols)>10000:
        raise InputError('The contingency table exceeds 10,000 cells; combine levels first.')
    row_index={int(v):i for i,v in enumerate(observed_rows)}
    col_index={int(v):i for i,v in enumerate(observed_cols)}
    tab=np.zeros((len(observed_rows),len(observed_cols)))
    for r,c,w in zip(a.codes[keep],b.codes[keep],weights[keep]):
        if w:
            tab[row_index[int(r)],col_index[int(c)]] += w
    n=tab.sum()
    if not math.isfinite(n) or n>2**53-1:
        raise InputError('Total frequency must not exceed 2^53 - 1.')
    overall=chi2_contingency(tab,correction=False)
    expected=overall.expected_freq
    out.row('overall',n=n,statistic=overall.statistic,df=overall.dof,p=overall.pvalue,
            cramersV=np.sqrt(overall.statistic/(n*min(tab.shape[0]-1,tab.shape[1]-1))))
    if np.any(expected<5):
        out.warn('Some overall expected counts are below 5. The Pearson p-value is an asymptotic approximation; '
                 'this core does not provide an overall Fisher or Monte Carlo test.')
    residual=(tab-expected)/np.sqrt(expected*(1-tab.sum(axis=1)[:,None]/n)*(1-tab.sum(axis=0)[None,:]/n))
    cell_p=2*norm.sf(np.abs(residual))
    adj=np.minimum(1,cell_p*tab.size)
    alpha=finite_number(options.get('alpha',.05),'Significance level')
    if not 0<alpha<1:
        raise InputError('Significance level must lie strictly between 0 and 1.')
    for i,r in enumerate(observed_rows):
        for j,c in enumerate(observed_cols):
            out.row('cells',row=a.levels[r],column=b.levels[c],observed=tab[i,j],expected=expected[i,j],
                    residual=residual[i,j],p=cell_p[i,j],adjusted=adj[i,j],
                    significant='Yes' if adj[i,j]<alpha else 'No')
    method=options.get('adjustment','bonferroni')
    if method not in ('bonferroni','holm','bh','none'):
        raise InputError('Unknown pairwise adjustment.')
    count=sum(math.comb(d,2) for d in tab.shape if d>=3)
    if method=='none':
        out.note('pairs','Pairwise comparisons are disabled. Cell residual tests remain a separate Bonferroni family.')
    elif count>500:
        out.warn('Pairwise comparisons exceed the 500-comparison limit and were disabled. Overall and cell results remain available.')
    else:
        pairs=[]
        sparse_large=False
        for axis,levels,labels in ((0,observed_rows,a.levels),(1,observed_cols,b.levels)):
            if len(levels)<3:
                continue
            for i,j in itertools.combinations(range(len(levels)),2):
                sub=tab[[i,j],:] if axis==0 else tab[:,[i,j]]
                sub=sub[sub.sum(axis=1)>0,:]
                sub=sub[:,sub.sum(axis=0)>0]
                if min(sub.shape)<2:
                    continue
                test=chi2_contingency(sub,correction=False)
                sparse=np.any(test.expected_freq<5)
                fisher=sparse and sub.shape==(2,2)
                sparse_large |= sparse and not fisher
                p=fisher_exact(sub.astype('int64')).pvalue if fisher else test.pvalue
                pairs.append(dict(dimension='Rows' if axis==0 else 'Columns',first=labels[levels[i]],
                    second=labels[levels[j]],method='Fisher exact (2x2)' if fisher else 'Pearson (uncorrected)',
                    statistic=test.statistic,df=test.dof,p=p))
        for row,padj in zip(pairs,adjust_p([p['p'] for p in pairs],method)):
            out.row('pairs',**row,adjusted=padj)
        if sparse_large:
            out.warn('Some larger pairwise tables have expected counts below 5. Their Pearson p-values are approximate; '
                     'no larger-table Fisher result is claimed.')
        out.note('pairs',f'Adjustment: {method}; one family across all {len(pairs)} valid row/column comparisons. '
                 'Zero margins are removed within each comparison. Two-level dimensions are not retested.')
    out.note('cells','Adjusted standardized residuals account for row and column margins. Cell p-values are '
             'two-sided normal approximations, Bonferroni-adjusted across all retained cells independently of pairwise tests.')
    out.markdown('summary',md_escape(f'{int(keep.sum())} complete input rows; {int((~keep).sum())} excluded; '
        f'total frequency {n:g}. Frequencies represent independent observations, not sampling weights. '
        'Unused and zero-frequency levels are removed. No bootstrap intervals or power calculations are included.'))
