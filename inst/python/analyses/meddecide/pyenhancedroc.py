"""Empirical ROC / paired DeLong partial core; see docs/python-roc-native.md."""
from cpj_runtime import InputError, md_escape

SPEC = {'name': 'pyenhancedroc',
 'title': 'Clinical ROC Analysis',
 'menuGroup': 'MedDecide Py',
 'menuSubgroup': 'ROC and comparison',
 'version': '0.3.63',
 'clearOnInputError': True,
 'options': [{'name': 'reference',
              'title': 'Binary reference outcome',
              'type': 'Variable',
              'permitted': ['factor'],
              'suggested': ['nominal'],
              'required': True},
             {'name': 'positive',
              'title': 'Reference positive level',
              'type': 'Level',
              'variable': '(reference)',
              'role': 'event'},
             {'name': 'marker1',
              'title': 'Score 1 (required)',
              'type': 'Variable',
              'permitted': ['numeric'],
              'suggested': ['continuous'],
              'required': True},
             {'name': 'marker2',
              'title': 'Score 2 (optional)',
              'type': 'Variable',
              'permitted': ['numeric'],
              'suggested': ['continuous']},
             {'name': 'marker3',
              'title': 'Score 3 (optional)',
              'type': 'Variable',
              'permitted': ['numeric'],
              'suggested': ['continuous']},
             {'name': 'direction1',
              'title': 'Score 1 direction',
              'type': 'List',
              'options': [{'name': 'higher', 'title': 'Higher scores are positive (>=)'},
                          {'name': 'lower', 'title': 'Lower scores are positive (<=)'}],
              'default': 'higher'},
             {'name': 'direction2',
              'title': 'Score 2 direction',
              'type': 'List',
              'options': [{'name': 'higher', 'title': 'Higher scores are positive (>=)'},
                          {'name': 'lower', 'title': 'Lower scores are positive (<=)'}],
              'default': 'higher'},
             {'name': 'direction3',
              'title': 'Score 3 direction',
              'type': 'List',
              'options': [{'name': 'higher', 'title': 'Higher scores are positive (>=)'},
                          {'name': 'lower', 'title': 'Lower scores are positive (<=)'}],
              'default': 'higher'},
             {'name': 'confLevel',
              'title': 'Confidence level',
              'type': 'Number',
              'default': 0.95,
              'min': 0.8,
              'max': 0.99},
             {'name': 'showComparisons',
              'title': 'Paired AUC comparisons (unadjusted)',
              'type': 'Bool',
              'default': True},
             {'name': 'showThresholds',
              'title': 'Observed-threshold classifications',
              'type': 'Bool',
              'default': False},
             {'name': 'showCases',
              'title': 'Retained source rows',
              'type': 'Bool',
              'default': False},
             {'name': 'showROC', 'title': 'Empirical ROC plot', 'type': 'Bool', 'default': True}],
 'results': [{'name': 'summary', 'title': 'Method and Assumptions', 'type': 'Text'},
             {'name': 'cohort',
              'title': 'Common Complete-Case Cohort',
              'type': 'Table',
              'columns': [{'name': 'source', 'title': 'Source Rows', 'type': 'integer'},
                          {'name': 'retained', 'title': 'Retained', 'type': 'integer'},
                          {'name': 'excluded', 'title': 'Excluded', 'type': 'integer'},
                          {'name': 'cases', 'title': 'Reference Positive', 'type': 'integer'},
                          {'name': 'controls', 'title': 'Reference Negative', 'type': 'integer'}]},
             {'name': 'auc',
              'title': 'Empirical AUC and Approximate DeLong Intervals',
              'type': 'Table',
              'columns': [{'name': 'marker', 'title': 'Score', 'type': 'text'},
                          {'name': 'direction', 'title': 'Positive Rule', 'type': 'text'},
                          {'name': 'estimate', 'title': 'AUC', 'type': 'number', 'format': 'zto'},
                          {'name': 'se', 'title': 'SE', 'type': 'number'},
                          {'name': 'lower', 'title': 'Lower CI', 'type': 'number', 'format': 'zto'},
                          {'name': 'upper', 'title': 'Upper CI', 'type': 'number', 'format': 'zto'},
                          {'name': 'status', 'title': 'Uncertainty Status', 'type': 'text'}]},
             {'name': 'comparisons',
              'title': 'Paired AUC Differences (Unadjusted)',
              'type': 'Table',
              'visible': '(showComparisons)',
              'columns': [{'name': 'first', 'title': 'First Score', 'type': 'text'},
                          {'name': 'second', 'title': 'Second Score', 'type': 'text'},
                          {'name': 'difference', 'title': 'First Minus Second', 'type': 'number'},
                          {'name': 'se', 'title': 'SE', 'type': 'number'},
                          {'name': 'lower', 'title': 'Lower CI', 'type': 'number'},
                          {'name': 'upper', 'title': 'Upper CI', 'type': 'number'},
                          {'name': 'z', 'title': 'z', 'type': 'number'},
                          {'name': 'p',
                           'title': 'Unadjusted p',
                           'type': 'number',
                           'format': 'pvalue'},
                          {'name': 'status', 'title': 'Inference Status', 'type': 'text'}]},
             {'name': 'thresholds',
              'title': 'Observed Thresholds on the Common Cohort',
              'type': 'Table',
              'visible': '(showThresholds)',
              'columns': [{'name': 'marker', 'title': 'Score', 'type': 'text'},
                          {'name': 'rule', 'title': 'Rule', 'type': 'text'},
                          {'name': 'cutoff', 'title': 'Observed Cutoff', 'type': 'number'},
                          {'name': 'tp', 'title': 'TP', 'type': 'integer'},
                          {'name': 'fp', 'title': 'FP', 'type': 'integer'},
                          {'name': 'fn', 'title': 'FN', 'type': 'integer'},
                          {'name': 'tn', 'title': 'TN', 'type': 'integer'},
                          {'name': 'sensitivity',
                           'title': 'Sensitivity',
                           'type': 'number',
                           'format': 'pc'},
                          {'name': 'specificity',
                           'title': 'Specificity',
                           'type': 'number',
                           'format': 'pc'}]},
             {'name': 'cases',
              'title': 'Retained Source Rows',
              'type': 'Table',
              'visible': '(showCases)',
              'columns': [{'name': 'sourceID', 'title': 'Source Row', 'type': 'text'},
                          {'name': 'reference', 'title': 'Reference', 'type': 'text'},
                          {'name': 'score1', 'title': 'Score 1', 'type': 'number'},
                          {'name': 'score2', 'title': 'Score 2', 'type': 'number'},
                          {'name': 'score3', 'title': 'Score 3', 'type': 'number'}]},
             {'name': 'rocPlot',
              'title': 'Empirical ROC Curves',
              'type': 'Image',
              'plot': 'line',
              'width': 650,
              'height': 450,
              'visible': '(showROC)'}],
 'ui': {'children': [{'type': 'VariableSupplier',
                      'persistentItems': False,
                      'stretchFactor': 1,
                      'children': [{'type': 'TargetLayoutBox',
                                    'label': 'Binary reference outcome',
                                    'children': [{'type': 'VariablesListBox',
                                                  'name': 'reference',
                                                  'isTarget': True,
                                                  'maxItemCount': 1},
                                                 {'type': 'LevelSelector',
                                                  'name': 'positive',
                                                  'enable': '(reference)'}]},
                                   {'type': 'TargetLayoutBox',
                                    'label': 'Score 1 (required)',
                                    'children': [{'type': 'VariablesListBox',
                                                  'name': 'marker1',
                                                  'isTarget': True,
                                                  'maxItemCount': 1}]},
                                   {'type': 'TargetLayoutBox',
                                    'label': 'Score 2 (optional)',
                                    'children': [{'type': 'VariablesListBox',
                                                  'name': 'marker2',
                                                  'isTarget': True,
                                                  'maxItemCount': 1}]},
                                   {'type': 'TargetLayoutBox',
                                    'label': 'Score 3 (optional)',
                                    'children': [{'type': 'VariablesListBox',
                                                  'name': 'marker3',
                                                  'isTarget': True,
                                                  'maxItemCount': 1}]}]},
                     {'type': 'CollapseBox',
                      'label': 'Analysis and Model',
                      'collapsed': False,
                      'children': [{'type': 'LayoutBox',
                                    'margin': 'large',
                                    'children': [{'type': 'ComboBox',
                                                  'name': 'direction1',
                                                  'enable': '(!(!marker1))'},
                                                 {'type': 'ComboBox',
                                                  'name': 'direction2',
                                                  'enable': '(!(!marker2))'},
                                                 {'type': 'ComboBox',
                                                  'name': 'direction3',
                                                  'enable': '(!(!marker3))'}]}]},
                     {'type': 'CollapseBox',
                      'label': 'Uncertainty and Validation',
                      'collapsed': False,
                      'children': [{'type': 'LayoutBox',
                                    'margin': 'large',
                                    'children': [{'type': 'TextBox',
                                                  'name': 'confLevel',
                                                  'format': 'number'}]}]},
                     {'type': 'CollapseBox',
                      'label': 'Results and Interpretation',
                      'collapsed': True,
                      'children': [{'type': 'LayoutBox',
                                    'margin': 'large',
                                    'children': [{'type': 'CheckBox', 'name': 'showComparisons'},
                                                 {'type': 'CheckBox', 'name': 'showThresholds'},
                                                 {'type': 'CheckBox', 'name': 'showCases'}]}]},
                     {'type': 'CollapseBox',
                      'label': 'Plots and Interaction',
                      'collapsed': True,
                      'children': [{'type': 'LayoutBox',
                                    'margin': 'large',
                                    'children': [{'type': 'CheckBox', 'name': 'showROC'}]}]},
                     {'type': 'CollapseBox',
                      'label': 'Advanced Settings',
                      'collapsed': True,
                      'children': [{'type': 'CheckBox', 'name': 'showConsole'}]}]}}


def run(data, options, out):
    from cpj_roc import roc_analysis
    reference, first = options.get('reference'), options.get('marker1')
    if not reference or not first:
        raise InputError('Choose a binary reference, its positive level and Score 1.')
    roles = [(i, options.get(f'marker{i}')) for i in range(1, 4) if options.get(f'marker{i}')]
    names = [name for _, name in roles]
    if len(set(names)) != len(names):
        raise InputError('Choose distinct score columns; the same column cannot occupy two roles.')
    directions = {name: options.get(f'direction{i}', 'higher') for i, name in roles}
    result = roc_analysis(data[reference], {name: data[name] for name in names},
                          options.get('positive'), directions, options.get('confLevel', .95))
    out.row('cohort', source=result['n_source'], retained=result['n_complete'],
            excluded=result['n_excluded'], cases=result['n_positive'], controls=result['n_negative'])
    for model in result['models']:
        status = ('Approximate normal CI' if model['inference_status'] == 'ok'
                  else model['inference_reason'])
        out.row('auc', marker=model['name'], direction='>=' if model['direction'] == 'higher' else '<=',
                estimate=model['auc'], se=model['se'], lower=model['lower'], upper=model['upper'], status=status)
        if options.get('showThresholds', False):
            for point in model['points']:
                out.row('thresholds', marker=model['name'], rule=point['rule'], cutoff=point['cutoff'],
                        tp=point['tp'], fp=point['fp'], fn=point['fn'], tn=point['tn'],
                        sensitivity=point['tpr'], specificity=1-point['fpr'])
    if options.get('showComparisons', True):
        for pair in result['comparisons']:
            out.row('comparisons', **{field: pair[field] for field in
                    ('first','second','difference','se','lower','upper','z','p')},
                    status='Approximate paired DeLong test' if pair['status']=='ok' else pair['reason'])
        out.note('comparisons', 'Differences are first AUC minus second AUC on the same cases. '
                 'Two-sided normal tests and difference intervals are approximate; p-values are unadjusted. '
                 'Zero or unestimable contrast variance leaves inference empty. Select at least two scores for comparisons.')
    if options.get('showCases', False):
        for index in result['retained_indices']:
            values = {f'score{i}': float(data[name][index]) for i, name in roles}
            out.row('cases', sourceID=str(out.row_ids[index] if out.row_ids is not None else index+1),
                    reference=data[reference].levels[int(data[reference].codes[index])], **values)
        out.note('cases', 'Source rows retain original row identifiers; score slots follow the selected input roles.')
    if options.get('showROC', True):
        plot = [dict(x=p['fpr'], y=p['tpr'], group='Score: '+model['name'])
                for model in result['models'] for p in model['points']]
        plot.extend([dict(x=0.,y=0.,group='Reference: chance'),dict(x=1.,y=1.,group='Reference: chance')])
        out.plot('rocPlot', plot, xlab='False positive rate (1 - specificity)', ylab='Sensitivity')
    out.note('auc', 'AUC gives half credit to tied case/control scores. Confidence intervals use the normal '
             'DeLong approximation, bounded at 0 and 1. Constant/perfect scores or insufficient class sizes '
             'may have no estimable uncertainty; empty cells do not mean certainty.')
    if options.get('showThresholds', False):
        out.note('thresholds', 'Equality is positive (>= for higher, <= for lower). The none-positive endpoint '
                 'has an empty cutoff and an explicit rule. Thresholds are observed scores, not pROC midpoints. '
                 'No optimal cutoff is selected or validated.')
    small = min(result['n_positive'], result['n_negative'])
    text = (f"{result['n_complete']} common complete cases; {result['n_excluded']} source rows excluded. "
            f"Positive reference: {result['positive']}. Every score uses the same cohort and its stated direction; "
            'directions are never chosen from the observed AUC. Cases must be independent and scores measured '
            'on the same cases. DeLong uncertainty is a large-sample normal approximation; small classes can '
            'have materially inadequate coverage. The minimum of two observations per class only permits '
            'variance calculation and does not establish reliable inference. ')
    if small < 2:
        text += 'At least one class has fewer than two observations; uncertainty and paired tests are unavailable. '
    text += ('Comparisons are unadjusted for multiple testing. Scores are analyzed as supplied, without fitting, '
             'calibration or clinical acceptance bands. Bootstrap, partial/smoothed/multiclass ROC, cutoff '
             'optimization and interactive exploration are not implemented in this core.')
    out.markdown('summary', md_escape(text))
