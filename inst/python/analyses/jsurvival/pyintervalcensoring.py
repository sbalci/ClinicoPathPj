"""Numeric interval2 preparation with native audit and aligned endpoints."""
from cpj_runtime import md_escape
from cpj_censoring import calculate,KINDS

SPEC = {'name': 'pyintervalcensoring',
 'title': 'Interval-Censoring Inputs (Python)',
 'menuGroup': 'Survival Py',
 'menuSubgroup': 'Data preparation',
 'version': '0.3.50',
 'clearOnInputError': True,
 'allowInfinite': ['left','right'],
 'options': [{'name': 'left',
              'title': 'Left endpoint',
              'type': 'Variable',
              'permitted': ['numeric'],
              'required': True},
             {'name': 'right',
              'title': 'Right endpoint',
              'type': 'Variable',
              'permitted': ['numeric'],
              'required': True},
             {'name': 'preview_rows',
              'title': 'Preview rows',
              'type': 'Integer',
              'default': 20,
              'min': 10,
              'max': 100},
             {'name': 'showPreview',
              'title': 'Source-row endpoint preview',
              'type': 'Bool',
              'default': True},
             {'name': 'showPlot',
              'title': 'Censoring-type counts',
              'type': 'Bool',
              'default': False},
             {'name': 'showReport',
              'title': 'Descriptive report',
              'type': 'Bool',
              'default': False},
             {'name': 'leftOut', 'title': 'Prepared left endpoint', 'type': 'Output'},
             {'name': 'rightOut', 'title': 'Prepared right endpoint', 'type': 'Output'},
             {'name': 'kindOut', 'title': 'Censoring type', 'type': 'Output'}],
 'results': [{'name': 'summary', 'title': 'Endpoint Scope', 'type': 'Text'},
             {'name': 'cohort',
              'title': 'Endpoint Accounting',
              'type': 'Table',
              'columns': [{'name': 'input', 'title': 'Supplied Rows', 'type': 'integer'},
                          {'name': 'retained', 'title': 'Informative Rows', 'type': 'integer'},
                          {'name': 'invalid', 'title': 'Reversed Bounds', 'type': 'integer'},
                          {'name': 'unknown', 'title': 'Both Open or Missing', 'type': 'integer'},
                          {'name': 'infinite', 'title': 'Rows With Infinity', 'type': 'integer'},
                          {'name': 'negative',
                           'title': 'Rows With Negative Finite Bounds',
                           'type': 'integer'}]},
             {'name': 'counts',
              'title': 'Informative Censoring Types',
              'type': 'Table',
              'columns': [{'name': 'code', 'title': 'Audit Code', 'type': 'integer'},
                          {'name': 'kind', 'title': 'Censoring Type', 'type': 'text'},
                          {'name': 'n', 'title': 'Count', 'type': 'integer'},
                          {'name': 'percent',
                           'title': 'Informative Rows (%)',
                           'type': 'number',
                           'format': 'pc'}]},
             {'name': 'preview',
              'title': 'Source-Row Endpoint Preview',
              'type': 'Table',
              'visible': '(showPreview)',
              'columns': [{'name': 'source', 'title': 'Source Row ID', 'type': 'text'},
                          {'name': 'rawLeft', 'title': 'Original Left', 'type': 'text'},
                          {'name': 'rawRight', 'title': 'Original Right', 'type': 'text'},
                          {'name': 'left', 'title': 'Prepared Left', 'type': 'number'},
                          {'name': 'right', 'title': 'Prepared Right', 'type': 'number'},
                          {'name': 'code', 'title': 'Audit Code', 'type': 'integer'},
                          {'name': 'kind', 'title': 'Classification', 'type': 'text'}]},
             {'name': 'report',
              'title': 'Descriptive Report',
              'type': 'Text',
              'visible': '(showReport)'},
             {'name': 'distribution',
              'title': 'Informative Censoring-Type Counts',
              'type': 'Image',
              'plot': 'bar',
              'width': 900,
              'height': 500,
              'visible': '(showPlot)'},
             {'name': 'leftOut',
              'title': 'Prepared interval left',
              'type': 'Output',
              'varTitle': 'Prepared interval left',
              'varDescription': 'Numeric interval2 left endpoint; NA can denote an open bound. '
                                'Invalid/uninformative rows are NA in both bounds.',
              'measureType': 'continuous'},
             {'name': 'rightOut',
              'title': 'Prepared interval right',
              'type': 'Output',
              'varTitle': 'Prepared interval right',
              'varDescription': 'Numeric interval2 right endpoint; NA can denote an open bound. '
                                'Invalid/uninformative rows are NA in both bounds.',
              'measureType': 'continuous'},
             {'name': 'kindOut',
              'title': 'Prepared censoring type',
              'type': 'Output',
              'varTitle': 'Prepared censoring type',
              'varDescription': 'Audit classification only. Surv(type=interval2) takes the '
                                'prepared endpoint pair without a third event argument.',
              'measureType': 'nominal'}],
 'ui': {'children': [{'type': 'VariableSupplier',
                      'persistentItems': True,
                      'stretchFactor': 1,
                      'children': [{'type': 'TargetLayoutBox',
                                    'label': 'Left endpoint',
                                    'children': [{'type': 'VariablesListBox',
                                                  'name': 'left',
                                                  'maxItemCount': 1,
                                                  'isTarget': True}]},
                                   {'type': 'TargetLayoutBox',
                                    'label': 'Right endpoint',
                                    'children': [{'type': 'VariablesListBox',
                                                  'name': 'right',
                                                  'maxItemCount': 1,
                                                  'isTarget': True}]}]},
                     {'type': 'CollapseBox',
                      'label': 'Results and Interpretation',
                      'collapsed': False,
                      'children': [{'type': 'CheckBox', 'name': 'showPreview'},
                                   {'type': 'TextBox', 'name': 'preview_rows', 'format': 'number'},
                                   {'type': 'CheckBox', 'name': 'showReport'}]},
                     {'type': 'CollapseBox',
                      'label': 'Plots',
                      'collapsed': True,
                      'children': [{'type': 'CheckBox', 'name': 'showPlot'}]},
                     {'type': 'CollapseBox',
                      'label': 'Save and Export',
                      'collapsed': False,
                      'children': [{'type': 'Output', 'name': 'leftOut'},
                                   {'type': 'Output', 'name': 'rightOut'},
                                   {'type': 'Output', 'name': 'kindOut'}]},
                     {'type': 'CollapseBox',
                      'label': 'Advanced Settings',
                      'collapsed': True,
                      'children': [{'type': 'CheckBox', 'name': 'showConsole'}]}]}}


def run(data,options,out):
    r=calculate(data,options)
    out.row('cohort',input=r['n'],retained=r['retained'],invalid=r['invalid'],unknown=r['unknown'],infinite=r['infinite'],negative=r['negative'])
    for row in r['counts']:out.row('counts',**row)
    if options.get('showPreview',True):
        ids=out.row_ids if out.row_ids is not None else [str(i+1) for i in range(r['n'])]
        for source,row in list(zip(ids,r['rows']))[:r['limit']]:out.row('preview',source=source,**row)
        if r['n']>r['limit']:out.info('The preview is bounded; all supplied rows remain aligned in accounting and saved outputs.')
    if options.get('showPlot',False):out.plot('distribution',[dict(label=row['kind'],value=row['n'],group='Informative rows') for row in r['counts']],xlab='Censoring type',ylab='Supplied rows')
    if out.row_ids is not None:
        out.column('leftOut',r['left'],measure_type='continuous',title='Prepared interval left',description='Numeric interval2 left endpoint; NA is an open bound only when the other prepared bound is informative. Invalid/uninformative rows have both bounds NA.')
        out.column('rightOut',r['right'],measure_type='continuous',title='Prepared interval right',description='Numeric interval2 right endpoint; NA is an open bound only when the other prepared bound is informative. Invalid/uninformative rows have both bounds NA.')
        out.column('kindOut',r['codes'],levels=KINDS,measure_type='nominal',title='Prepared censoring type',description='Audit classification of the prepared endpoint pair; not an event argument for interval2.')
    if r['invalid']:out.warn(f"{r['invalid']} reversed-bound row(s) cannot be used; both saved bounds and classification remain missing. Correct the original endpoints.")
    if r['unknown']:out.warn(f"{r['unknown']} row(s) have both bounds open/missing and supply no interval information; both saved bounds and classification remain missing.")
    if r['infinite']:out.info('Nonfinite endpoints are treated as open bounds after checking original endpoint order, matching the interval2 reference. Inspect infinity conventions in the source.')
    if r['negative']:out.info('Signed finite time values were retained. Verify the common origin and units; this analysis cannot establish that negative values are appropriate for the intended time scale.')
    out.markdown('summary',md_escape(f"Supplied rows: {r['n']}; informative: {r['retained']}; reversed: {r['invalid']}; both open/missing: {r['unknown']}. "
       'Use numeric endpoints in the same units and from the same origin. Finite equality is exact; finite left < right is interval-censored; an open left with finite right is left-censored; finite left with open right is right-censored. '
       'Original endpoint order is checked before infinities become open bounds. Invalid or uninformative rows remain missing in all saved outputs. A missing prepared left or right can be a valid open bound: do not apply ordinary complete-case deletion to the endpoint pair. '
       'Save both prepared endpoints for downstream use. In R, Surv(left, right, type="interval2") uses two endpoint arguments and NO third event argument; the audit codes are not event indicators. '
       'This utility checks representation, not event-time provenance, independence, censoring assumptions or model fit. Dates/factors/text require explicit numeric conversion; no survival model is estimated and no outcome status is recoded. Rows are supplied records, not deduplicated patients.'))
    if options.get('showReport',False):out.markdown('report',md_escape(f"Prepared {r['retained']} informative interval records out of {r['n']}; {r['invalid']} reversed and {r['unknown']} uninformative records were left missing in saved outputs. Censoring types: "+'; '.join(f"{x['kind']}: {x['n']}" for x in r['counts'])+'. These are input classifications, not survival estimates.'))
