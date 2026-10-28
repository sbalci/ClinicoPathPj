"""Partial univariate baseline port; composite and multivariate methods are omitted."""
import numpy as np
from cpj_runtime import md_escape
from cpj_outliers import calculate

SPEC = {'name': 'pyoutlierdetection',
 'title': 'Univariate Outlier Screening (Python Core)',
 'menuGroup': 'Descriptives Py',
 'menuSubgroup': 'Data quality',
 'version': '0.3.32',
 'options': [{'name': 'vars',
              'title': 'Numeric variables',
              'type': 'Variables',
              'permitted': ['numeric'],
              'suggested': ['continuous'],
              'required': True},
             {'name': 'method',
              'title': 'Univariate method',
              'type': 'List',
              'options': [{'name': 'zscore_robust', 'title': 'Robust Z-score (scaled MAD)'},
                          {'name': 'zscore', 'title': 'Standard Z-score (sample SD)'},
                          {'name': 'iqr', 'title': 'IQR fences'}],
              'default': 'zscore_robust'},
             {'name': 'zscore_threshold',
              'title': 'Absolute Z-score cutoff',
              'type': 'Number',
              'default': 3.29,
              'min': 1,
              'max': 5},
             {'name': 'iqr_multiplier',
              'title': 'IQR multiplier',
              'type': 'Number',
              'default': 1.7,
              'min': 1,
              'max': 3},
             {'name': 'showRows',
              'title': 'Row screening preview (first 1,000 rows)',
              'type': 'Bool',
              'default': False},
             {'name': 'showPlot', 'title': 'Per-variable flag counts', 'type': 'Bool', 'default': False},
             {'name': 'screenFlags', 'title': 'Save any-variable screening flag', 'type': 'Output'}],
 'results': [{'name': 'summary', 'title': 'Cohort and Screening Rules', 'type': 'Text'},
             {'name': 'variables',
              'title': 'Univariate Screening Summary',
              'type': 'Table',
              'columns': [{'name': 'variable', 'title': 'Variable', 'type': 'text'},
                          {'name': 'n', 'title': 'Complete Rows', 'type': 'integer'},
                          {'name': 'evaluable', 'title': 'Evaluable Rows', 'type': 'integer'},
                          {'name': 'flagged', 'title': 'Flagged', 'type': 'integer'},
                          {'name': 'unavailable', 'title': 'Undefined', 'type': 'integer'},
                          {'name': 'center', 'title': 'Center', 'type': 'number'},
                          {'name': 'spread', 'title': 'Spread', 'type': 'number'},
                          {'name': 'lower', 'title': 'Lower Limit', 'type': 'number'},
                          {'name': 'upper', 'title': 'Upper Limit', 'type': 'number'}]},
             {'name': 'rowPreview',
              'title': 'Row Screening Preview',
              'type': 'Table',
              'visible': '(showRows)',
              'columns': [{'name': 'row', 'title': 'Source Row', 'type': 'text'},
                          {'name': 'status', 'title': 'Status', 'type': 'text'},
                          {'name': 'drivers', 'title': 'Flagged Variables', 'type': 'text'},
                          {'name': 'undefined', 'title': 'Undefined Variables', 'type': 'text'}]},
             {'name': 'countPlot',
              'title': 'Per-Variable Screening Flags',
              'type': 'Image',
              'plot': 'bar',
              'width': 800,
              'height': 500,
              'visible': '(showPlot)'},
             {'name': 'screenFlags',
              'title': 'Screening Flag',
              'type': 'Output',
              'varTitle': 'Univariate screening flag',
              'varDescription': '1=at least one selected variable flagged; 0=evaluable without flags; '
                                'missing=excluded or all methods undefined',
              'measureType': 'nominal'}],
 'ui': {'children': [{'type': 'VariableSupplier',
                      'persistentItems': False,
                      'stretchFactor': 1,
                      'children': [{'type': 'TargetLayoutBox',
                                    'label': 'Numeric variables',
                                    'children': [{'type': 'VariablesListBox',
                                                  'name': 'vars',
                                                  'isTarget': True}]}]},
                     {'type': 'CollapseBox',
                      'label': 'Analysis and Method',
                      'collapsed': False,
                      'children': [{'type': 'ComboBox', 'name': 'method'},
                                   {'type': 'TextBox',
                                    'name': 'zscore_threshold',
                                    'format': 'number',
                                    'enable': '(method:zscore || method:zscore_robust)'},
                                   {'type': 'TextBox',
                                    'name': 'iqr_multiplier',
                                    'format': 'number',
                                    'enable': '(method:iqr)'}]},
                     {'type': 'CollapseBox',
                      'label': 'Results and Interpretation',
                      'collapsed': False,
                      'children': [{'type': 'CheckBox', 'name': 'showRows'}]},
                     {'type': 'CollapseBox',
                      'label': 'Plots and Interaction',
                      'collapsed': True,
                      'children': [{'type': 'CheckBox', 'name': 'showPlot'}]},
                     {'type': 'CollapseBox',
                      'label': 'Save and Export',
                      'collapsed': True,
                      'children': [{'type': 'Output', 'name': 'screenFlags'}]},
                     {'type': 'CollapseBox',
                      'label': 'Advanced Settings',
                      'collapsed': True,
                      'children': [{'type': 'CheckBox', 'name': 'showConsole'}]}]}}


def run(data,options,out):
    result=calculate(data,options)
    for row in result['summaries']:out.row('variables',**row)
    ids=out.row_ids if out.row_ids is not None else [str(i+1) for i in range(result['total'])]
    complete_index=0
    if options.get('showRows',False):
        for i,retained in enumerate(result['keep']):
            if i>=1000:break
            drivers=[];undefined=[]
            if retained:
                flags=result['flags'][complete_index];complete_index+=1
                drivers=[v for v,f in zip(result['names'],flags) if f==1]
                undefined=[v for v,f in zip(result['names'],flags) if not np.isfinite(f)]
            flag=result['aggregate'][i]
            status='Excluded: missing/nonfinite' if not retained else ('Undefined' if not np.isfinite(flag) else ('Flagged' if flag else 'Not flagged'))
            out.row('rowPreview',row=ids[i],status=status,drivers=', '.join(drivers),undefined=', '.join(undefined))
        if result['total']>1000:out.info('Only the first 1,000 source rows are shown; all rows contribute to summaries and saved flags.')
    if options.get('showPlot',False):
        out.plot('countPlot',[dict(label=r['variable'],value=r['flagged'],group='Flagged') for r in result['summaries']],xlab='Variable',ylab='Flagged complete rows')
    if out.row_ids is not None:
        values=[int(v) if np.isfinite(v) else None for v in result['aggregate']]
        out.column('screenFlags',values,levels=['Not flagged','Flagged'],measure_type='nominal',title='Univariate screening flag',description='Any selected variable flagged; excluded/all-undefined rows remain missing')
    out.markdown('summary',md_escape(f"Input rows: {result['total']}; finite complete cohort: {result['n']}; excluded: {result['excluded']}. Method: {result['method']}. Absolute Z cutoff: {options.get('zscore_threshold',3.29)}; IQR multiplier: {options.get('iqr_multiplier',1.7)} (only the selected method's cutoff applies). Z uses mean/sample SD; robust Z uses median/MAD scaled by 1.4826; IQR uses R type-7 quartiles. Flags use strict cutoffs and any-variable aggregation. Zero-spread Z scores at the center are undefined; noncentral values have infinite scores and flag. IQR zero-width fences remain evaluable. Missing/nonfinite values exclude a row across all selected variables. Rows are supplied observations; repeated subjects are not modeled. Flags prompt review, not automatic deletion or clinical classification. This core exposes univariate methods, rather than the baseline composite default. Composite/multivariate/interval methods, subsampling and automatic exclusion are omitted. No data values are changed."))
    if result['excluded']:out.warn(f"{result['excluded']} row(s) excluded for missing/nonfinite selected measurements.")
    if any(r['unavailable'] for r in result['summaries']):out.warn('Some zero-spread Z scores are undefined; missing flags distinguish these from not flagged.')
    if result['n']<30:out.warn('Small-sample screening is unstable; review flags in the original measurement context.')
