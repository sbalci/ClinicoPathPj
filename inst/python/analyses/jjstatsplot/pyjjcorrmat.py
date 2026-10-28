"""Validated-core correlation matrix; full released R feature parity is pending."""
import json,uuid
from pathlib import Path
from cpj_runtime import md_escape
from cpj_correlation import calculate

SPEC = {'name': 'pyjjcorrmat',
 'title': 'Correlation Matrix (Python Core)',
 'menuGroup': 'Stats Plots Py',
 'menuSubgroup': 'Associations',
 'version': '0.3.24',
 'options': [{'name': 'dep',
              'title': 'Numeric variables',
              'type': 'Variables',
              'permitted': ['numeric'],
              'suggested': ['continuous'],
              'required': True},
             {'name': 'typestatistics',
              'title': 'Correlation method',
              'type': 'List',
              'options': [{'name': 'parametric', 'title': 'Pearson'},
                          {'name': 'nonparametric', 'title': 'Spearman (asymptotic p values)'}],
              'default': 'parametric'},
             {'name': 'partial', 'title': 'Partial Pearson (adjust for all other selected variables)', 'type': 'Bool', 'default': False},
             {'name': 'naHandling',
              'title': 'Missing values',
              'type': 'List',
              'options': [{'name': 'listwise', 'title': 'One common complete-case cohort'},
                          {'name': 'pairwise', 'title': 'Available pairs; report n for each pair'}],
              'default': 'listwise'},
             {'name': 'padjustmethod',
              'title': 'Multiplicity adjustment',
              'type': 'List',
              'options': [{'name': 'holm', 'title': 'Holm'},
                          {'name': 'bonferroni', 'title': 'Bonferroni'},
                          {'name': 'BH', 'title': 'Benjamini-Hochberg'},
                          {'name': 'BY', 'title': 'Benjamini-Yekutieli'},
                          {'name': 'hochberg', 'title': 'Hochberg'},
                          {'name': 'hommel', 'title': 'Hommel'},
                          {'name': 'none', 'title': 'None'}],
              'default': 'holm'},
             {'name': 'conflevel',
              'title': 'Pearson confidence level (proportion)',
              'type': 'Number',
              'min': 0.5,
              'max': 0.999,
              'default': 0.95},
             {'name': 'interactive',
              'title': 'Local matrix inspection',
              'type': 'Bool',
              'default': True}],
 'results': [{'name': 'summary', 'title': 'Correlation Cohort and Methods', 'type': 'Text'},
             {'name': 'correlations',
              'title': 'Unique Variable Pairs',
              'type': 'Table',
              'columns': [{'name': 'first', 'title': 'Variable 1', 'type': 'text'},
                          {'name': 'second', 'title': 'Variable 2', 'type': 'text'},
                          {'name': 'n', 'title': 'Complete Pairs', 'type': 'integer'},
                          {'name': 'excluded', 'title': 'Excluded Rows', 'type': 'integer'},
                          {'name': 'controls', 'title': 'Controls', 'type': 'integer'},
                          {'name': 'df', 'title': 'Test df', 'type': 'integer'},
                          {'name': 'estimate', 'title': 'Correlation', 'type': 'number'},
                          {'name': 'lower', 'title': 'CI Lower', 'type': 'number'},
                          {'name': 'upper', 'title': 'CI Upper', 'type': 'number'},
                          {'name': 'p', 'title': 'p', 'type': 'number', 'format': 'pvalue'},
                          {'name': 'adjusted',
                           'title': 'Adjusted p',
                           'type': 'number',
                           'format': 'pvalue'},
                          {'name': 'reason', 'title': 'Unavailable Reason', 'type': 'text'}]},
             {'name': 'matrix',
              'title': 'Correlation Matrix',
              'type': 'Image',
              'plot': 'ihcheatmap',
              'width': 800,
              'height': 650},
             {'name': 'explorer',
              'title': 'Local Correlation Inspector',
              'type': 'Html',
              'visible': '(interactive)'}],
 'ui': {'children': [{'type': 'VariableSupplier',
                      'persistentItems': True,
                      'stretchFactor': 1,
                      'children': [{'type': 'TargetLayoutBox',
                                    'label': 'Numeric variables',
                                    'children': [{'type': 'VariablesListBox',
                                                  'name': 'dep',
                                                  'isTarget': True}]}]},
                     {'type': 'CollapseBox',
                      'label': 'Analysis and Model',
                      'collapsed': False,
                      'children': [{'type': 'ComboBox', 'name': 'typestatistics'},
                                   {'type': 'ComboBox', 'name': 'naHandling'},
                                   {'type': 'CheckBox', 'name': 'partial'}]},
                     {'type': 'CollapseBox',
                      'label': 'Uncertainty and Validation',
                      'collapsed': False,
                      'children': [{'type': 'ComboBox', 'name': 'padjustmethod'},
                                   {'type': 'TextBox',
                                    'name': 'conflevel',
                                    'format': 'number',
                                    'enable': '(typestatistics:parametric)'}]},
                     {'type': 'CollapseBox',
                      'label': 'Plots and Interaction',
                      'collapsed': True,
                      'children': [{'type': 'CheckBox', 'name': 'interactive'}]},
                     {'type': 'CollapseBox',
                      'label': 'Advanced Settings',
                      'collapsed': True,
                      'children': [{'type': 'CheckBox', 'name': 'showConsole'}]}]}}


def run(data, options, out):
    p=calculate(data,options)
    for row in p['pairs']:out.row('correlations',**row)
    cells=[dict(row=first,label=first[:80],variable=second,value=p['matrix'][i][j]) for i,first in enumerate(p['names']) for j,second in enumerate(p['names'])]
    out.plot('matrix',cells,xlab='Correlation (fixed -1 to 1 when a diagonal is available)',ylab='Variable')
    method='Pearson' if p['method']=='parametric' else 'Spearman'
    out.markdown('summary',md_escape(
        f"Input rows: {p['inputRows']}; common complete rows: {p['commonRows']}. "
        f"Partial: {p['partial']}; controls per pair: {p['controls']}. Method: {method}; missingness: {p['missing']}; adjustment: {p['adjustment']}. "
        f"Multiplicity family: all {len(p['pairs'])} unique pairs, including unavailable tests. "
        "Zero-order coefficients and tests require at least three nonconstant complete pairs. Partial Pearson controls all other selected variables on a common complete-case cohort; t-test df = n - controls - 2. Singular systems remain unavailable. "
        f"Pearson {100*p['confidence']:g}% Fisher-z intervals require n - controls >= 4; no Spearman intervals in this core. "
        "Intervals are pointwise and unadjusted; p-value adjustment does not adjust intervals. "
        "Spearman p values use the asymptotic t approximation, including ties. "
        "Holm/Bonferroni control family-wise error under arbitrary dependence; Hochberg/Hommel require independent or suitably positively dependent tests. BH controls false discovery rate under independence or suitable positive dependence; BY allows arbitrary dependence. "
        "Rows must represent independent observations; repeated specimens need a separate clustered method. "
        "Pairwise deletion can produce a non-positive-semidefinite matrix. "
        "Gray cells are unavailable estimates, not zero associations. Robust, Bayesian, partial Spearman and grouped methods are omitted. Classical partial t/Fisher-z inference assumes independent observations and an appropriate multivariate-normal linear model. Partial correlation does not establish causality or eliminate unmeasured confounding."))
    unavailable=sum(row['estimate'] is None for row in p['pairs'])
    if unavailable:out.warn(f'{unavailable} pair(s) have unavailable estimates; see per-pair sample sizes and reasons.')
    if p['method']=='nonparametric':out.warn('Spearman p values are asymptotic; small samples need separate exact or permutation inference, which is not implemented in this core.')
    if options.get('interactive',True):
        encoded=json.dumps(p,allow_nan=False,ensure_ascii=True)
        for char,safe in (('<','\\u003c'),('>','\\u003e'),('&','\\u0026')):encoded=encoded.replace(char,safe)
        template=(Path(__file__).resolve().parents[2]/'templates/correlation.html').read_text()
        out.html('explorer',template.replace('__ROOT__','cpjcorr'+uuid.uuid4().hex).replace('__PAYLOAD__',encoded))
