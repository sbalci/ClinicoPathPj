"""Explicit outcome and recurrence/progression status preparation."""
from cpj_runtime import md_escape
from cpj_outcomes import calculate

SPEC = {'name': 'pyoutcomeorganizer',
 'title': 'Outcome Organizer (Python Core)',
 'clearOnInputError': True,
 'menuGroup': 'Survival Py',
 'menuSubgroup': 'Data preparation',
 'version': '0.3.49',
 'options': [{'name': 'outcome',
              'title': 'Outcome variable',
              'type': 'Variable',
              'permitted': ['factor', 'numeric'],
              'required': True},
             {'name': 'outcomeLevel',
              'title': 'Event level (single-event coding)',
              'type': 'Level',
              'variable': '(outcome)',
              'optional': True},
             {'name': 'analysistype',
              'title': 'Outcome preparation type',
              'type': 'List',
              'options': [{'name': 'os', 'title': 'Single event / overall survival'},
                          {'name': 'cause', 'title': 'Cause-specific survival'},
                          {'name': 'compete', 'title': 'Competing risks'},
                          {'name': 'multistate', 'title': 'Multistate status'},
                          {'name': 'rfs', 'title': 'RFS status: event or recurrence'},
                          {'name': 'pfs', 'title': 'PFS status: event or progression'},
                          {'name': 'dfs', 'title': 'DFS status: event or recurrence'},
                          {'name': 'ttp', 'title': 'TTP status: progression only'}],
              'default': 'os'},
             {'name': 'multievent',
              'title': 'Multiple event levels',
              'type': 'Bool',
              'default': False},
             {'name': 'dod',
              'title': 'Dead of disease',
              'type': 'Level',
              'variable': '(outcome)',
              'optional': True},
             {'name': 'dooc',
              'title': 'Dead of other causes',
              'type': 'Level',
              'variable': '(outcome)',
              'optional': True},
             {'name': 'awd',
              'title': 'Alive with disease',
              'type': 'Level',
              'variable': '(outcome)',
              'optional': True},
             {'name': 'awod',
              'title': 'Alive without disease',
              'type': 'Level',
              'variable': '(outcome)',
              'optional': True},
             {'name': 'diagnostics',
              'title': 'Source-row preview',
              'type': 'Bool',
              'default': False},
             {'name': 'visualization',
              'title': 'Outcome distribution',
              'type': 'Bool',
              'default': False},
             {'name': 'showNaturalSummary',
              'title': 'Descriptive report',
              'type': 'Bool',
              'default': False},
             {'name': 'addOutcome', 'title': 'Recoded outcome', 'type': 'Output'},
             {'name': 'recurrence',
              'title': 'Recurrence/progression variable',
              'type': 'Variable',
              'permitted': ['factor']},
             {'name': 'recurrenceLevel',
              'title': 'Recurrence/progression event level',
              'type': 'Level',
              'variable': '(recurrence)',
              'optional': True}],
 'results': [{'name': 'summary', 'title': 'Coding Scope', 'type': 'Text'},
             {'name': 'cohort',
              'title': 'Row Accounting',
              'type': 'Table',
              'columns': [{'name': 'input', 'title': 'Input Rows', 'type': 'integer'},
                          {'name': 'valid', 'title': 'Coded Rows', 'type': 'integer'},
                          {'name': 'missing', 'title': 'Unknown Final Status', 'type': 'integer'}]},
             {'name': 'mapping',
              'title': 'Explicit Outcome Mapping',
              'type': 'Table',
              'columns': [{'name': 'level', 'title': 'Original Level', 'type': 'text'},
                          {'name': 'category', 'title': 'Meaning', 'type': 'text'},
                          {'name': 'code', 'title': 'Status Code', 'type': 'integer'},
                          {'name': 'n', 'title': 'Input Count', 'type': 'integer'}]},
             {'name': 'components',
              'title': 'Composite Component Mapping',
              'type': 'Table',
              'visible': '(analysistype:rfs || analysistype:pfs || analysistype:dfs || '
                         'analysistype:ttp)',
              'columns': [{'name': 'component', 'title': 'Component', 'type': 'text'},
                          {'name': 'variable', 'title': 'Variable', 'type': 'text'},
                          {'name': 'level', 'title': 'Original Level', 'type': 'text'},
                          {'name': 'category', 'title': 'Meaning', 'type': 'text'},
                          {'name': 'code', 'title': 'Component Code', 'type': 'integer'},
                          {'name': 'n', 'title': 'Input Count', 'type': 'integer'}]},
             {'name': 'compositeAudit',
              'title': 'Composite Missingness Audit',
              'type': 'Table',
              'visible': '(analysistype:rfs || analysistype:pfs || analysistype:dfs || '
                         'analysistype:ttp)',
              'columns': [{'name': 'outcomeMissing',
                           'title': 'Unknown Outcome Component',
                           'type': 'integer'},
                          {'name': 'recurrenceMissing',
                           'title': 'Unknown Recurrence Component',
                           'type': 'integer'},
                          {'name': 'overrides',
                           'title': 'Known Event Despite Unknown Component',
                           'type': 'integer'}]},
             {'name': 'frequencies',
              'title': 'Recoded Outcome Distribution',
              'type': 'Table',
              'columns': [{'name': 'code', 'title': 'Status Code', 'type': 'integer'},
                          {'name': 'label', 'title': 'Meaning', 'type': 'text'},
                          {'name': 'n', 'title': 'Count', 'type': 'integer'},
                          {'name': 'percent',
                           'title': 'Coded Rows (%)',
                           'type': 'number',
                           'format': 'pc'}]},
             {'name': 'preview',
              'title': 'Source-Row Preview (First 100 Rows)',
              'type': 'Table',
              'visible': '(diagnostics)',
              'columns': [{'name': 'source', 'title': 'Source Row ID', 'type': 'text'},
                          {'name': 'code', 'title': 'Status Code', 'type': 'integer'},
                          {'name': 'outcomeComponent',
                           'title': 'Outcome Component',
                           'type': 'integer',
                           'visible': '(analysistype:rfs || analysistype:pfs || analysistype:dfs '
                                      '|| analysistype:ttp)'},
                          {'name': 'recurrenceComponent',
                           'title': 'Recurrence Component',
                           'type': 'integer',
                           'visible': '(analysistype:rfs || analysistype:pfs || analysistype:dfs '
                                      '|| analysistype:ttp)'},
                          {'name': 'reason',
                           'title': 'Status Rule',
                           'type': 'text',
                           'visible': '(analysistype:rfs || analysistype:pfs || analysistype:dfs '
                                      '|| analysistype:ttp)'}]},
             {'name': 'report',
              'title': 'Descriptive Report',
              'type': 'Text',
              'visible': '(showNaturalSummary)'},
             {'name': 'distribution',
              'title': 'Recoded Outcome Counts',
              'type': 'Image',
              'plot': 'bar',
              'width': 800,
              'height': 500,
              'visible': '(visualization)'},
             {'name': 'addOutcome',
              'title': 'Recoded Outcome',
              'type': 'Output',
              'varTitle': 'Recoded survival outcome',
              'varDescription': 'Explicit row-wise outcome coding; inspect the native mapping '
                                'before downstream use',
              'measureType': 'nominal'}],
 'ui': {'children': [{'type': 'VariableSupplier',
                      'persistentItems': False,
                      'stretchFactor': 1,
                      'children': [{'type': 'TargetLayoutBox',
                                    'label': 'Outcome variable',
                                    'children': [{'type': 'VariablesListBox',
                                                  'name': 'outcome',
                                                  'maxItemCount': 1,
                                                  'isTarget': True}]},
                                   {'type': 'LevelSelector',
                                    'name': 'outcomeLevel',
                                    'enable': '(!multievent && !(analysistype:ttp))'},
                                   {'type': 'TargetLayoutBox',
                                    'label': 'Recurrence/progression variable',
                                    'children': [{'type': 'VariablesListBox',
                                                  'name': 'recurrence',
                                                  'maxItemCount': 1,
                                                  'isTarget': True,
                                                  'enable': '(analysistype:rfs || analysistype:pfs '
                                                            '|| analysistype:dfs || '
                                                            'analysistype:ttp)'}]},
                                   {'type': 'LevelSelector',
                                    'name': 'recurrenceLevel',
                                    'enable': '(analysistype:rfs || analysistype:pfs || '
                                              'analysistype:dfs || analysistype:ttp)'},
                                   {'type': 'LevelSelector',
                                    'name': 'dod',
                                    'enable': '(multievent)'},
                                   {'type': 'LevelSelector',
                                    'name': 'dooc',
                                    'enable': '(multievent)'},
                                   {'type': 'LevelSelector',
                                    'name': 'awd',
                                    'enable': '(multievent)'},
                                   {'type': 'LevelSelector',
                                    'name': 'awod',
                                    'enable': '(multievent)'}]},
                     {'type': 'CollapseBox',
                      'label': 'Outcome Definition',
                      'collapsed': False,
                      'children': [{'type': 'ComboBox', 'name': 'analysistype'},
                                   {'type': 'CheckBox', 'name': 'multievent'}]},
                     {'type': 'CollapseBox',
                      'label': 'Results and Interpretation',
                      'collapsed': False,
                      'children': [{'type': 'CheckBox', 'name': 'diagnostics'},
                                   {'type': 'CheckBox', 'name': 'showNaturalSummary'}]},
                     {'type': 'CollapseBox',
                      'label': 'Plots',
                      'collapsed': True,
                      'children': [{'type': 'CheckBox', 'name': 'visualization'}]},
                     {'type': 'CollapseBox',
                      'label': 'Save and Export',
                      'collapsed': False,
                      'children': [{'type': 'Output', 'name': 'addOutcome'}]},
                     {'type': 'CollapseBox',
                      'label': 'Advanced Settings',
                      'collapsed': True,
                      'children': [{'type': 'CheckBox', 'name': 'showConsole'}]}]}}


def run(data, options, out):
    r = calculate(data,options)
    if r['pending']:
        out.info(r['pending']);out.markdown('summary',md_escape(r['pending']));return
    out.row('cohort',input=r['total'],valid=r['valid'],missing=r['missing'])
    for row in r['mapping']: out.row('mapping',**row)
    for row in r['counts']: out.row('frequencies',**row)
    if 'components' in r:
        for row in r['components']:out.row('components',**row)
        out.row('compositeAudit',outcomeMissing=r['component_missing_outcome'],recurrenceMissing=r['component_missing_recurrence'],overrides=r['known_event_overrides'])
    if options.get('diagnostics',False):
        ids = out.row_ids if out.row_ids is not None else [str(i+1) for i in range(r['total'])]
        for i,(source,code) in enumerate(list(zip(ids,r['status']))[:100]):
            extra=dict(outcomeComponent=r['outcome_status'][i],recurrenceComponent=r['recurrence_status'][i],reason=r['reasons'][i]) if 'components' in r else {}
            out.row('preview',source=source,code=code,**extra)
        if r['total']>100:out.info('The preview shows the first 100 source rows; summaries and saved output use every supplied row.')
    if options.get('visualization',False):
        out.plot('distribution',[dict(label=row['label'],value=row['n'],group='Coded rows') for row in r['counts']],xlab='Outcome code',ylab='Supplied rows')
    if out.row_ids is not None:
        out.column('addOutcome',r['status'],levels=r['levels'],measure_type='nominal',
                   title='Recoded survival outcome',description=('Endpoint status only; '+r['mode']+'; no first-event time computed. ' if 'components' in r else '')+'Status coding: '+', '.join(f"{v['code']}={v['label']}" for v in r['counts']))
    for warning in r['warnings']:out.warn(warning)
    if 'components' in r:
        scope=(f"Input rows: {r['total']}; known final status: {r['valid']}; unknown final status: {r['missing']}. Endpoint status rule: {r['mode']}. "
               'RFS/PFS/DFS use selected outcome event OR recurrence/progression: a known event determines 1 even when the other component is unknown; 0 requires both components known and coded 0. Otherwise final status is missing. '
               'TTP uses the explicitly selected progression indicator alone and ignores the outcome variable and its event level. The outcome variable remains selected only for supplied-row alignment. '
               'Component mapping counts refer to source levels; final frequencies use known final status as denominator. Missing component values are not automatically censoring. '
               'Rows are supplied records, not deduplicated patients. These are STATUS codes, not event times or survival estimates. The user must define the clinical endpoint and supply time to FIRST component event (or appropriate progression/censoring assessment for TTP). '
               'No recurrence/progression time is available here; do not assume death or last-contact time equals first event time. Patient hierarchy, interval/administrative censoring and survival estimation remain pending.')
        out.markdown('summary',md_escape(scope))
    else:
        out.markdown('summary',md_escape(
            f"Input rows: {r['total']}; coded: {r['valid']}; missing outcome: {r['missing']}. Coding route: {r['mode']}. "
            'Missing outcomes remain missing; no row is dropped or converted to censoring. Percentages use coded rows. '
            'The original row identities and order are retained in saved output. Rows are supplied records, not deduplicated patients. '
            'This core recodes status only; it does not validate event times, follow-up origins, transition histories or independent censoring. '
            'Composite/progression choices prepare status only. Patient hierarchies, interval/administrative censoring and survival estimation are not implemented. '
            'A multistate status snapshot is not a multistate event-history dataset. Review the mapping and pair it with appropriate times before downstream analysis.'))
    if options.get('showNaturalSummary',False):
        description='; '.join(f"code {row['code']} ({row['label']}): {row['n']}" for row in r['counts'])
        out.markdown('report',md_escape(f"Outcome status was prepared for {r['valid']} coded records out of {r['total']} supplied rows, with {r['missing']} unknown final statuses. {description}. These descriptive counts are not survival or cumulative-incidence estimates."))
