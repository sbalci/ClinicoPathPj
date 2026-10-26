"""Categorical summaries: native tables, complete denominators and descriptive reporting."""
from cpj_runtime import Factor, InputError, md_escape

SPEC = {'name': 'pyreportcat',
 'title': 'Summary of Categorical Variables',
 'menuGroup': 'Descriptives Py',
 'menuSubgroup': 'Summaries',
 'version': '0.3.0',
 'options': [{'name': 'vars',
              'title': 'Categorical variables',
              'type': 'Variables',
              'permitted': ['factor'],
              'suggested': ['nominal', 'ordinal'],
              'required': True}],
 'results': [{'name': 'overview',
              'title': 'Variable Summary',
              'type': 'Table',
              'columns': [{'name': 'variable', 'title': 'Variable', 'type': 'text'},
                          {'name': 'total', 'title': 'Rows', 'type': 'integer'},
                          {'name': 'valid', 'title': 'Valid', 'type': 'integer'},
                          {'name': 'missing', 'title': 'Missing', 'type': 'integer'},
                          {'name': 'missingRate',
                           'title': 'Missing (%)',
                           'type': 'number',
                           'format': 'pc'},
                          {'name': 'declared', 'title': 'Declared Levels', 'type': 'integer'},
                          {'name': 'observed', 'title': 'Observed Levels', 'type': 'integer'},
                          {'name': 'mode', 'title': 'Most Frequent Categories', 'type': 'text'},
                          {'name': 'modeN', 'title': 'Count per Mode', 'type': 'integer'}]},
             {'name': 'frequencies',
              'title': 'Category Frequencies',
              'type': 'Table',
              'columns': [{'name': 'variable', 'title': 'Variable', 'type': 'text'},
                          {'name': 'level', 'title': 'Category', 'type': 'text'},
                          {'name': 'n', 'title': 'Count', 'type': 'integer'},
                          {'name': 'validPercent',
                           'title': 'Valid (%)',
                           'type': 'number',
                           'format': 'pc'},
                          {'name': 'totalPercent',
                           'title': 'All Rows (%)',
                           'type': 'number',
                           'format': 'pc'}]},
             {'name': 'clinicalSummary', 'title': 'Data Completeness', 'type': 'Text'},
             {'name': 'reportSentences', 'title': 'Copy-Ready Summary', 'type': 'Text'},
             {'name': 'assumptions', 'title': 'Data Quality and Assumptions', 'type': 'Text'},
             {'name': 'distribution',
              'title': 'Category Distributions',
              'type': 'Image',
              'plot': 'bar',
              'width': 650,
              'height': 450}],
 'ui': {'children': [{'type': 'VariableSupplier',
                      'persistentItems': False,
                      'stretchFactor': 1,
                      'children': [{'type': 'TargetLayoutBox',
                                    'label': 'Categorical variables',
                                    'children': [{'type': 'VariablesListBox',
                                                  'name': 'vars',
                                                  'isTarget': True}]}]},
                     {'type': 'CollapseBox',
                      'label': 'Advanced Settings',
                      'collapsed': True,
                      'children': [{'type': 'CheckBox', 'name': 'showConsole'}]}]}}


def percent(value):
    return '<0.1' if 0 < value < .05 else f'{value:.1f}'


def summarize(column):
    import numpy as np
    if not isinstance(column, Factor): raise InputError('Select categorical variables.')
    if any(not isinstance(v,str) for v in column.levels): raise InputError('Invalid category labels.')
    if np.any(column.codes >= len(column.levels)): raise InputError('Invalid category codes.')
    n = len(column.codes); valid = int(np.sum(column.codes >= 0))
    counts = np.bincount(column.codes[column.codes >= 0], minlength=len(column.levels))
    order = list(range(len(counts))) if column.ordered else sorted(range(len(counts)),key=lambda i:-int(counts[i]))
    modes = [column.levels[i] for i in range(len(counts)) if valid and counts[i] == counts.max()]
    return n, valid, counts, order, modes


def run(data, options, out):
    variables = options.get('vars') or []
    if not variables: raise InputError('Select categorical variables.')
    results = [(name, summarize(data[name])) for name in variables]
    if not results or not results[0][1][0]: raise InputError('The dataset has no rows.')
    empty = [name for name,(n,valid,*_) in results if valid == 0]
    if len(empty) == len(results): raise InputError('Every selected variable is empty or all missing.')
    if empty: out.warn('Variables with no observed categories were excluded: '+', '.join(empty)+'.')
    sentences=[]; missing=[]; plot=[]
    for name,(n,valid,counts,order,modes) in results:
        if not valid:continue
        observed=int(sum(counts>0)); absent=int(sum(counts==0)); mode_n=int(max(counts))
        out.row('overview',variable=name,total=n,valid=valid,missing=n-valid,missingRate=(n-valid)/n,
                declared=len(counts),observed=observed,mode=', '.join(modes),modeN=mode_n)
        for i in order:
            out.row('frequencies',variable=name,level=data[name].levels[i],n=int(counts[i]),
                    validPercent=int(counts[i])/valid,totalPercent=int(counts[i])/n)
            plot.append(dict(label=name+' / '+data[name].levels[i],value=int(counts[i]),group=name))
        missing.append((name,100*(n-valid)/n))
        labels=', '.join("'"+v+"'" for v in modes)
        if len(modes)>1:
            sentence=f'For {name}, {labels} were equally the most frequent categories (n = {mode_n} of {valid} valid cases each, {100*mode_n/valid:.1f}% each).'
        else:
            sentence=f'For {name}, the most common category was {labels} (n = {mode_n} of {valid} valid cases, {100*mode_n/valid:.1f}%).'
        if n-valid:sentence+=f' Missing data: {n-valid} of {n} cases ({percent(100*(n-valid)/n)}%).'
        if absent:sentence+=f' {absent} declared categories had no observations.'
        sentences.append(md_escape(sentence))
        if observed>20:out.warn(f'{name} has {observed} observed categories; consider whether recoding is appropriate.')
        sparse=int(sum((counts>0)&(counts<5)))
        if observed>1 and sparse:out.warn(f'{name} has {sparse} of {observed} observed categories with fewer than 5 cases. Sparse cells can make subsequent inference unstable.')
        if (n-valid)/n>.2:out.warn(f'{name} has {percent(100*(n-valid)/n)}% missing data.')
    rates=[r for _,r in missing]; worst=max(rates)
    if worst==0: quality='No missing values in any of the retained variables.'
    else:
        worst_names=', '.join(name for name,r in missing if r==worst)
        quality=f'Missing values range from {percent(min(rates))}% to {percent(worst)}% (mean {percent(sum(rates)/len(rates))}%); highest: {worst_names}.'
    out.markdown('clinicalSummary',md_escape(f'{len(missing)} categorical variables from {results[0][1][0]} rows. '+quality))
    out.markdown('reportSentences','\n\n'.join(sentences))
    out.markdown('assumptions','Descriptive summaries do not establish clinical validity. Valid percentages exclude missing values; all-row percentages include them in the denominator. Declared unused categories remain visible. Ordinal categories retain their level order; nominal categories are sorted by frequency. Tied modes are reported together. One row should represent the intended observation unit. Missingness may bias descriptive results.')
    out.note('frequencies','Missing values are reported separately and are never treated as categories. No inferential tests or confidence intervals are calculated.')
    if len(plot)<=2000:out.plot('distribution',plot,xlab='Variable / category',ylab='Count')
    else:out.warn('The native distribution plot is omitted above 2,000 variable/category rows; frequency tables retain every category.')
