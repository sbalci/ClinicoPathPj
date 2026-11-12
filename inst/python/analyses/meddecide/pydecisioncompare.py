"""Native paired binary-test partial core; paired-difference intervals are omitted."""
from cpj_runtime import InputError, md_escape

SPEC = {'name': 'pydecisioncompare',
 'title': 'Paired Binary Test Comparison',
 'menuGroup': 'MedDecide Py',
 'menuSubgroup': 'Test comparisons',
 'version': '0.1.0',
 'clearOnInputError': True,
 'options': [
  {'name': 'gold', 'title': 'Reference or comparator', 'type': 'Variable',
   'permitted': ['factor'], 'suggested': ['nominal'], 'required': True},
  {'name': 'test1', 'title': 'Test 1', 'type': 'Variable',
   'permitted': ['factor'], 'suggested': ['nominal'], 'required': True},
  {'name': 'test2', 'title': 'Test 2', 'type': 'Variable',
   'permitted': ['factor'], 'suggested': ['nominal'], 'required': True},
  {'name': 'test3', 'title': 'Test 3 (optional)', 'type': 'Variable',
   'permitted': ['factor'], 'suggested': ['nominal']},
  {'name': 'goldPositive', 'title': 'Reference positive level', 'type': 'Level', 'variable': '(gold)', 'role': 'event'},
  {'name': 'goldNegative', 'title': 'Reference negative level', 'type': 'Level', 'variable': '(gold)', 'role': 'event'},
  {'name': 'test1Positive', 'title': 'Test 1 positive level', 'type': 'Level', 'variable': '(test1)', 'role': 'event'},
  {'name': 'test1Negative', 'title': 'Test 1 negative level', 'type': 'Level', 'variable': '(test1)', 'role': 'event'},
  {'name': 'test2Positive', 'title': 'Test 2 positive level', 'type': 'Level', 'variable': '(test2)', 'role': 'event'},
  {'name': 'test2Negative', 'title': 'Test 2 negative level', 'type': 'Level', 'variable': '(test2)', 'role': 'event'},
  {'name': 'test3Positive', 'title': 'Test 3 positive level', 'type': 'Level', 'variable': '(test3)', 'role': 'event'},
  {'name': 'test3Negative', 'title': 'Test 3 negative level', 'type': 'Level', 'variable': '(test3)', 'role': 'event'},
  {'name': 'referenceType', 'title': 'Reference interpretation', 'type': 'List',
   'options': [{'name': 'legacy', 'title': 'Not specified (diagnostic terminology)'},
               {'name': 'disease', 'title': 'Disease reference'},
               {'name': 'consensus', 'title': 'Expert consensus comparator'},
               {'name': 'method', 'title': 'Comparative method'}], 'default': 'legacy'},
  {'name': 'excludeIndeterminate', 'title': 'Exclude results outside selected level pairs', 'type': 'Bool', 'default': False},
  {'name': 'statComp', 'title': 'Statistical comparisons', 'type': 'Bool', 'default': False},
  {'name': 'mcnemarMethod', 'title': 'McNemar method', 'type': 'List',
   'options': [{'name': 'midp', 'title': 'Mid-p'},
               {'name': 'asymptotic', 'title': 'Asymptotic (no continuity correction)'}], 'default': 'midp'},
  {'name': 'ci', 'title': 'Per-test exact confidence intervals', 'type': 'Bool', 'default': False},
  {'name': 'confLevel', 'title': 'Confidence level', 'type': 'Number', 'default': .95, 'min': .8, 'max': .99},
  {'name': 'showPairCounts', 'title': 'Paired discordance counts', 'type': 'Bool', 'default': False},
  {'name': 'showCases', 'title': 'Retained source rows', 'type': 'Bool', 'default': False},
  {'name': 'plot', 'title': 'Per-test proportion plot', 'type': 'Bool', 'default': False}],
 'results': [
  {'name': 'summary', 'title': 'Cohort and Interpretation', 'type': 'Text'},
  {'name': 'cohort', 'title': 'Common Complete Determinate Cohort', 'type': 'Table',
   'columns': [{'name': 'source', 'title': 'Source Rows', 'type': 'integer'},
               {'name': 'retained', 'title': 'Retained', 'type': 'integer'},
               {'name': 'missing', 'title': 'Excluded Missing', 'type': 'integer'},
               {'name': 'outside', 'title': 'Excluded Outside Pairs', 'type': 'integer'},
               {'name': 'positive', 'title': 'Reference Positive', 'type': 'integer'},
               {'name': 'negative', 'title': 'Reference Negative', 'type': 'integer'}]},
  {'name': 'mapping', 'title': 'Selected Levels and Source Exclusions', 'type': 'Table',
   'columns': [{'name': 'role', 'title': 'Role', 'type': 'text'},
               {'name': 'variable', 'title': 'Variable', 'type': 'text'},
               {'name': 'positive', 'title': 'Positive Level', 'type': 'text'},
               {'name': 'negative', 'title': 'Negative Level', 'type': 'text'},
               {'name': 'missing', 'title': 'Missing Rows', 'type': 'integer'},
               {'name': 'outside', 'title': 'Outside-Pair Rows', 'type': 'integer'}]},
  {'name': 'counts', 'title': 'Per-Test Classification Counts', 'type': 'Table',
   'columns': [{'name': 'test', 'title': 'Test', 'type': 'text'},
               {'name': 'pp', 'title': 'Reference + / Test +', 'type': 'integer'},
               {'name': 'np', 'title': 'Reference - / Test +', 'type': 'integer'},
               {'name': 'pn', 'title': 'Reference + / Test -', 'type': 'integer'},
               {'name': 'nn', 'title': 'Reference - / Test -', 'type': 'integer'}]},
  {'name': 'estimates', 'title': 'Sample Proportions on the Common Cohort', 'type': 'Table',
   'columns': [{'name': 'test', 'title': 'Test', 'type': 'text'},
               {'name': 'metric', 'title': 'Metric', 'type': 'text'},
               {'name': 'successes', 'title': 'Numerator', 'type': 'integer'},
               {'name': 'n', 'title': 'Denominator', 'type': 'integer'},
               {'name': 'estimate', 'title': 'Estimate', 'type': 'number', 'format': 'pc'},
               {'name': 'lower', 'title': 'Lower CI', 'type': 'number', 'format': 'pc', 'visible': '(ci)'},
               {'name': 'upper', 'title': 'Upper CI', 'type': 'number', 'format': 'pc', 'visible': '(ci)'},
               {'name': 'status', 'title': 'Status', 'type': 'text'}]},
  {'name': 'comparisons', 'title': 'Paired Differences and McNemar Tests', 'type': 'Table', 'visible': '(statComp)',
   'columns': [{'name': 'first', 'title': 'First Test', 'type': 'text'},
               {'name': 'second', 'title': 'Second Test', 'type': 'text'},
               {'name': 'metric', 'title': 'Metric', 'type': 'text'},
               {'name': 'n', 'title': 'Paired N', 'type': 'integer'},
               {'name': 'difference', 'title': 'First Minus Second', 'type': 'number', 'format': 'pc'},
               {'name': 'p', 'title': 'Unadjusted p', 'type': 'number', 'format': 'pvalue'},
               {'name': 'adjusted', 'title': 'Holm p (Accuracy Only)', 'type': 'number', 'format': 'pvalue'},
               {'name': 'status', 'title': 'Test Status', 'type': 'text'}]},
  {'name': 'discordance', 'title': 'Paired Success and Discordance Counts', 'type': 'Table', 'visible': '(statComp && showPairCounts)',
   'columns': [{'name': 'first', 'title': 'First Test', 'type': 'text'},
               {'name': 'second', 'title': 'Second Test', 'type': 'text'},
               {'name': 'metric', 'title': 'Metric', 'type': 'text'},
               {'name': 'both', 'title': 'Both Succeed', 'type': 'integer'},
               {'name': 'firstOnly', 'title': 'First Only', 'type': 'integer'},
               {'name': 'secondOnly', 'title': 'Second Only', 'type': 'integer'},
               {'name': 'neither', 'title': 'Neither Succeeds', 'type': 'integer'},
               {'name': 'discordant', 'title': 'Discordant N', 'type': 'integer'}]},
  {'name': 'cases', 'title': 'Retained Original Source Rows', 'type': 'Table', 'visible': '(showCases)',
   'columns': [{'name': 'sourceID', 'title': 'Source Row', 'type': 'text'},
               {'name': 'reference', 'title': 'Reference', 'type': 'text'},
               {'name': 'test1', 'title': 'Test 1', 'type': 'text'},
               {'name': 'test2', 'title': 'Test 2', 'type': 'text'},
               {'name': 'test3', 'title': 'Test 3', 'type': 'text'}]},
  {'name': 'proportionPlot', 'title': 'Per-Test Proportions', 'type': 'Image', 'plot': 'interval',
   'width': 700, 'height': 450, 'visible': '(plot)'}],
 'ui': {'children': [
  {'type': 'VariableSupplier', 'persistentItems': False, 'stretchFactor': 1, 'children': [
   {'type': 'TargetLayoutBox', 'label': 'Reference or comparator', 'children': [
    {'type': 'VariablesListBox', 'name': 'gold', 'isTarget': True, 'maxItemCount': 1},
    {'type': 'LevelSelector', 'name': 'goldPositive', 'enable': '(!(!gold))'},
    {'type': 'LevelSelector', 'name': 'goldNegative', 'enable': '(!(!gold))'}]},
   {'type': 'TargetLayoutBox', 'label': 'Test 1', 'children': [
    {'type': 'VariablesListBox', 'name': 'test1', 'isTarget': True, 'maxItemCount': 1},
    {'type': 'LevelSelector', 'name': 'test1Positive', 'enable': '(!(!test1))'},
    {'type': 'LevelSelector', 'name': 'test1Negative', 'enable': '(!(!test1))'}]},
   {'type': 'TargetLayoutBox', 'label': 'Test 2', 'children': [
    {'type': 'VariablesListBox', 'name': 'test2', 'isTarget': True, 'maxItemCount': 1},
    {'type': 'LevelSelector', 'name': 'test2Positive', 'enable': '(!(!test2))'},
    {'type': 'LevelSelector', 'name': 'test2Negative', 'enable': '(!(!test2))'}]},
   {'type': 'TargetLayoutBox', 'label': 'Test 3 (optional)', 'children': [
    {'type': 'VariablesListBox', 'name': 'test3', 'isTarget': True, 'maxItemCount': 1},
    {'type': 'LevelSelector', 'name': 'test3Positive', 'enable': '(!(!test3))'},
    {'type': 'LevelSelector', 'name': 'test3Negative', 'enable': '(!(!test3))'}]}]},
  {'type': 'CollapseBox', 'label': 'Analysis and Model', 'collapsed': False, 'children': [
   {'type': 'ComboBox', 'name': 'referenceType'},
   {'type': 'Label', 'label': 'Independent cases; tests paired within each row'},
   {'type': 'Label', 'label': 'One common complete determinate cohort for all selected tests'},
   {'type': 'CheckBox', 'name': 'excludeIndeterminate'},
   {'type': 'CheckBox', 'name': 'statComp'},
   {'type': 'ComboBox', 'name': 'mcnemarMethod', 'enable': '(statComp)'}]},
  {'type': 'CollapseBox', 'label': 'Uncertainty and Validation', 'collapsed': False, 'children': [
   {'type': 'CheckBox', 'name': 'ci'},
   {'type': 'TextBox', 'name': 'confLevel', 'format': 'number', 'enable': '(ci)'}]},
  {'type': 'CollapseBox', 'label': 'Results and Interpretation', 'collapsed': True, 'children': [
   {'type': 'CheckBox', 'name': 'showPairCounts', 'enable': '(statComp)'},
   {'type': 'CheckBox', 'name': 'showCases'}]},
  {'type': 'CollapseBox', 'label': 'Plots and Interaction', 'collapsed': True, 'children': [
   {'type': 'CheckBox', 'name': 'plot'}]},
  {'type': 'CollapseBox', 'label': 'Advanced Settings', 'collapsed': True, 'children': [
   {'type': 'CheckBox', 'name': 'showConsole'}]}]}}


def run(data, options, out):
    from cpj_paired_decision import paired_decision
    reference = options.get('gold')
    roles = [(role, options.get(role)) for role in ('test1', 'test2', 'test3') if options.get(role)]
    if not reference or not options.get('test1') or not options.get('test2'):
        raise InputError('Choose the reference and two test columns with explicit positive/negative levels.')
    columns = [reference]+[name for _, name in roles]
    if len(set(columns)) != len(columns):
        raise InputError('Choose distinct reference and test columns; duplicate-valued tests may use distinct columns.')
    method = options.get('mcnemarMethod', 'midp')
    interpretation = options.get('referenceType', 'legacy')
    if method not in ('midp', 'asymptotic'):
        raise InputError('The public core offers mid-p or uncorrected asymptotic McNemar only.')
    if interpretation not in ('legacy', 'disease', 'consensus', 'method'):
        raise InputError('Choose a supported reference interpretation.')
    mappings = {role: (options.get(role+'Positive'), options.get(role+'Negative')) for role, _ in roles}
    result = paired_decision(data[reference], {role: data[name] for role, name in roles},
        (options.get('goldPositive'), options.get('goldNegative')), mappings,
        exclude_indeterminate=options.get('excludeIndeterminate', False), method=method,
        confidence=options.get('confLevel', .95), adjustment='holm', difference_intervals=False)
    names = dict(roles)
    comparator = interpretation in ('consensus', 'method')
    labels = (['Positive agreement (reference positives)', 'Negative agreement (reference negatives)',
               'Reference-positive agreement (test positives)', 'Reference-negative agreement (test negatives)',
               'Overall agreement'] if comparator else
              ['Sensitivity', 'Specificity', 'Positive predictive value', 'Negative predictive value', 'Accuracy'])
    pair_labels = dict(zip(('accuracy', 'sensitivity', 'specificity'), (labels[4], labels[0], labels[1])))
    out.row('cohort', source=result['n_source'], retained=result['n_complete'],
            missing=result['excluded_missing'], outside=result['excluded_indeterminate'],
            positive=result['n_positive'], negative=result['n_negative'])
    for role, variable in [('reference', reference)]+roles:
        levels = result['mappings'][role]
        out.row('mapping', role='Reference' if role == 'reference' else 'Test '+role[-1],
                variable=variable, positive=levels[0], negative=levels[1],
                missing=result['missing_by_role'][role], outside=result['indeterminate_by_role'][role])
    out.note('mapping', 'Source missing/outside-pair counts may overlap between roles. '
             'Cohort exclusions are mutually exclusive, with missingness counted first. Unused levels are not pooled as negative.')
    plot_rows = []
    for role, model in result['models'].items():
        pp, np_, pn, nn = model['counts']
        out.row('counts', test=names[role], pp=pp, np=np_, pn=pn, nn=nn)
        numerators = (pp, nn, pp, nn, pp+nn)
        denominators = (pp+pn, nn+np_, pp+np_, nn+pn, pp+np_+pn+nn)
        for index, row in enumerate(model['proportions']):
            lower, upper = (row['lower'], row['upper']) if options.get('ci', False) else (None, None)
            out.row('estimates', test=names[role], metric=labels[index], successes=numerators[index],
                    n=denominators[index], estimate=row['estimate'], lower=lower, upper=upper,
                    status='Undefined: zero denominator' if not denominators[index] else
                           'Exact per-test interval' if options.get('ci', False) else 'Point estimate')
            if index in (0, 1, 4) and row['estimate'] is not None:
                plot_rows.append(dict(label=names[role]+': '+labels[index],
                                      estimate=row['estimate'], lower=lower, upper=upper))
    out.note('estimates', 'Every test uses the same retained cohort. Enabled per-test limits are '
             'Clopper-Pearson binomial intervals, not intervals for paired differences. Predictive values describe this sample.')
    if options.get('statComp', False):
        for pair in result['pairs']:
            for metric in ('accuracy', 'sensitivity', 'specificity'):
                row = pair[metric]
                status = ('No discordance: p=1 by convention; not equivalence' if row['status'] == 'no_discordance'
                          else 'Undefined: no reference cases in this class' if row['status'] == 'absent_class'
                          else 'Mid-p McNemar' if method == 'midp' else 'Asymptotic McNemar without correction')
                out.row('comparisons', first=names[pair['first_name']], second=names[pair['second_name']],
                        metric=pair_labels[metric], n=row['n'], difference=row['difference'], p=row['p'],
                        adjusted=row.get('p_adjusted') if metric == 'accuracy' else None, status=status)
                if options.get('showPairCounts', False):
                    out.row('discordance', first=names[pair['first_name']], second=names[pair['second_name']],
                            metric=pair_labels[metric], both=row['counts'][0], firstOnly=row['counts'][1],
                            secondOnly=row['counts'][2], neither=row['counts'][3], discordant=row['discordant'])
        out.note('comparisons', 'Differences are first minus second. Accuracy/overall-agreement tests compare '
                 'correctness relative to the reference, not raw positivity, and depend on sample case mix. '
                 'Holm includes only informative accuracy comparisons; no-discordance p=1 is conventional. '
                 'Sensitivity/positive-agreement and specificity/negative-agreement p-values are unadjusted. '
                 'Paired-difference confidence intervals are not provided in this core.')
        if any(0 < p[m]['discordant'] < 10 for p in result['pairs'] for m in ('accuracy', 'sensitivity', 'specificity')):
            out.warn('Some comparisons have fewer than 10 discordant pairs: information is limited; asymptotic approximation may be poor.')
    if options.get('showCases', False):
        for index in result['retained_indices']:
            values = {role: data[name].levels[int(data[name].codes[index])] for role, name in roles}
            out.row('cases', sourceID=str(out.row_ids[index] if out.row_ids is not None else index+1),
                    reference=data[reference].levels[int(data[reference].codes[index])], **values)
    if options.get('plot', False):
        out.plot('proportionPlot', plot_rows, xlab='Proportion'+(' (exact per-test intervals)' if options.get('ci', False) else ' (point estimates)'))
    if not result['n_positive'] or not result['n_negative']:
        out.warn('A reference class is absent; its conditional proportions and comparisons are undefined.')
    if interpretation == 'legacy':
        out.warn('Reference interpretation is not specified. Diagnostic terminology is retained; choose the comparator type before interpretation.')
    description = (f"{result['n_complete']} common complete determinate cases from {result['n_source']} rows. "
        'All selected tests use this cohort; adding Test 3 can change every estimate. '
        'Cases must be independent across rows and tests paired within each case; repeated specimens need a clustering-aware method. ')
    if comparator:
        description += ('Agreement with this comparator does not establish disease status. Positive and negative agreement '
                        'condition on the reference; they are not symmetric specific-agreement measures or disease-risk estimates. ')
    else:
        description += 'Accuracy and predictive values depend on this sample case mix; case-control samples do not establish population accuracy or predictive values. '
    if options.get('statComp', False):
        description += (f"Informative accuracy comparisons: {result['holm_family']}; "
                        f"Holm adjustment {'applied' if result['holm_applied'] else 'not applied (at most one informative pair)'}. "
                        'Mid-p and asymptotic tests are not exact size-controlled tests. ')
    description += ('This partial core omits paired-difference intervals, Cochran Q, OPA/non-inferiority, '
                    'stratification, prevalence scenarios and best-test recommendations.')
    out.markdown('summary', md_escape(description))
