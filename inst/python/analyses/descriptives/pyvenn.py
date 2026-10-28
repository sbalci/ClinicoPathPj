"""Exact set-intersection core; full Venn/UpSet feature parity is not implemented."""
import json,uuid
from itertools import islice
from pathlib import Path
from cpj_runtime import md_escape,InputError
from cpj_sets import calculate

SPEC = {'name': 'pyvenn',
 'title': 'Set Intersections (Python Core)',
 'menuGroup': 'Descriptives Py',
 'menuSubgroup': 'Sets and Overlaps',
 'version': '0.3.27',
 'options': [{'name': 'var1',
              'title': 'Variable 1 (required)',
              'type': 'Variable',
              'permitted': ['factor'],
              'suggested': ['nominal', 'ordinal'],
              'required': True},
             {'name': 'var2',
              'title': 'Variable 2 (required)',
              'type': 'Variable',
              'permitted': ['factor'],
              'suggested': ['nominal', 'ordinal'],
              'required': True},
             {'name': 'var3',
              'title': 'Variable 3 (optional)',
              'type': 'Variable',
              'permitted': ['factor'],
              'suggested': ['nominal', 'ordinal']},
             {'name': 'var4',
              'title': 'Variable 4 (optional)',
              'type': 'Variable',
              'permitted': ['factor'],
              'suggested': ['nominal', 'ordinal']},
             {'name': 'var1true',
              'title': 'Set 1 positive level',
              'type': 'Level',
              'variable': '(var1)',
              'role': 'event'},
             {'name': 'var2true',
              'title': 'Set 2 positive level',
              'type': 'Level',
              'variable': '(var2)',
              'role': 'event'},
             {'name': 'var3true',
              'title': 'Set 3 positive level',
              'type': 'Level',
              'variable': '(var3)',
              'role': 'event'},
             {'name': 'var4true',
              'title': 'Set 4 positive level',
              'type': 'Level',
              'variable': '(var4)',
              'role': 'event'},
             {'name': 'patternOrder', 'title': 'Pattern order', 'type': 'List',
              'options': [{'name': 'membership', 'title': 'Membership order'},
                          {'name': 'frequency', 'title': 'Frequency (largest first)'}],
              'default': 'membership'},
             {'name': 'showZero', 'title': 'Zero-count patterns', 'type': 'Bool', 'default': False},
             {'name': 'showMembershipTable',
              'title': 'Membership table (first 500 input rows)',
              'type': 'Bool',
              'default': False},
             {'name': 'interactive',
              'title': 'Local intersection inspection',
              'type': 'Bool',
              'default': True},
             {'name': 'showSetMatrix', 'title': 'Intersection membership matrix', 'type': 'Bool', 'default': False},
             {'name': 'membershipGroups',
              'title': 'Save exact membership pattern',
              'type': 'Output'}],
 'results': [{'name': 'summary', 'title': 'Set Cohort and Definitions', 'type': 'Text'},
             {'name': 'sets',
              'title': 'Set Definitions and Sizes',
              'type': 'Table',
              'columns': [{'name': 'position', 'title': 'Digit', 'type': 'integer'},
                          {'name': 'variable', 'title': 'Variable', 'type': 'text'},
                          {'name': 'positive', 'title': 'Positive Level', 'type': 'text'},
                          {'name': 'n', 'title': 'Complete Cohort', 'type': 'integer'},
                          {'name': 'members', 'title': 'Members', 'type': 'integer'},
                          {'name': 'missing', 'title': 'Missing in Input', 'type': 'integer'}]},
             {'name': 'intersections',
              'title': 'Exact Membership Patterns',
              'type': 'Table',
              'columns': [{'name': 'pattern', 'title': 'Pattern', 'type': 'text'},
                          {'name': 'members', 'title': 'Included Sets (Only)', 'type': 'text'},
                          {'name': 'n', 'title': 'Rows', 'type': 'integer'},
                          {'name': 'percent',
                           'title': 'Complete Cohort (%)',
                           'type': 'number',
                           'format': 'pc'}]},
             {'name': 'membershipTable',
              'title': 'Row Membership Preview',
              'type': 'Table',
              'visible': '(showMembershipTable)',
              'columns': [{'name': 'row', 'title': 'Source Row', 'type': 'text'},
                          {'name': 'pattern', 'title': 'Pattern', 'type': 'text'},
                          {'name': 'members', 'title': 'Included Sets', 'type': 'text', 'visible': False},
                          {'name': 'status', 'title': 'Status', 'type': 'text'}]},
             {'name': 'intersectionPlot',
              'title': 'Exact Pattern Sizes',
              'type': 'Image',
              'plot': 'bar',
              'width': 800,
              'height': 500},
             {'name': 'intersectionMatrix', 'title': 'Exact Intersections and Set Membership',
              'type': 'Image', 'plot': 'setmatrix', 'width': 900, 'height': 600,
              'visible': '(showSetMatrix)'},
             {'name': 'explorer',
              'title': 'Local Intersection Inspector',
              'type': 'Html',
              'visible': '(interactive)'},
             {'name': 'membershipGroups',
              'title': 'Saved Membership Pattern',
              'type': 'Output',
              'varTitle': 'Set membership pattern',
              'varDescription': 'Exact positive-membership digits in displayed set order; excluded '
                                'rows remain missing',
              'measureType': 'nominal'}],
 'ui': {'children': [{'type': 'VariableSupplier',
                      'persistentItems': False,
                      'stretchFactor': 1,
                      'children': [{'type': 'TargetLayoutBox',
                                    'label': 'Set 1 (required)',
                                    'children': [{'type': 'VariablesListBox',
                                                  'name': 'var1',
                                                  'isTarget': True,
                                                  'maxItemCount': 1},
                                                 {'type': 'LevelSelector',
                                                  'name': 'var1true',
                                                  'enable': '(var1)'}]},
                                   {'type': 'TargetLayoutBox',
                                    'label': 'Set 2 (required)',
                                    'children': [{'type': 'VariablesListBox',
                                                  'name': 'var2',
                                                  'isTarget': True,
                                                  'maxItemCount': 1},
                                                 {'type': 'LevelSelector',
                                                  'name': 'var2true',
                                                  'enable': '(var2)'}]},
                                   {'type': 'TargetLayoutBox',
                                    'label': 'Set 3 (optional)',
                                    'children': [{'type': 'VariablesListBox',
                                                  'name': 'var3',
                                                  'isTarget': True,
                                                  'maxItemCount': 1},
                                                 {'type': 'LevelSelector',
                                                  'name': 'var3true',
                                                  'enable': '(var3)'}]},
                                   {'type': 'TargetLayoutBox',
                                    'label': 'Set 4 (optional)',
                                    'children': [{'type': 'VariablesListBox',
                                                  'name': 'var4',
                                                  'isTarget': True,
                                                  'maxItemCount': 1},
                                                 {'type': 'LevelSelector',
                                                  'name': 'var4true',
                                                  'enable': '(var4)'}]}]},
                     {'type': 'CollapseBox',
                      'label': 'Results and Interpretation',
                      'collapsed': False,
                      'children': [{'type': 'ComboBox', 'name': 'patternOrder'},
                                   {'type': 'CheckBox', 'name': 'showZero'},
                                   {'type': 'CheckBox', 'name': 'showMembershipTable'}]},
                     {'type': 'CollapseBox',
                      'label': 'Plots and Interaction',
                      'collapsed': True,
                      'children': [{'type': 'CheckBox', 'name': 'showSetMatrix'},
                                   {'type': 'CheckBox', 'name': 'interactive'}]},
                     {'type': 'CollapseBox',
                      'label': 'Save and Export',
                      'collapsed': True,
                      'children': [{'type': 'Output', 'name': 'membershipGroups'}]},
                     {'type': 'CollapseBox',
                      'label': 'Advanced Settings',
                      'collapsed': True,
                      'children': [{'type': 'CheckBox', 'name': 'showConsole'}]}]}}


def run(data,options,out):
    result=calculate(data,options)
    for row in result['sets']:out.row('sets',**row)
    shown=[row for row in result['patterns'] if row['n'] or row['code']==0 or options.get('showZero',False)]
    order=options.get('patternOrder','membership')
    if order not in ('membership','frequency'):raise InputError('Unknown pattern order')
    if order=='frequency':shown.sort(key=lambda row:(-row['n'],row['code']))
    order_title='Frequency (largest first; ties use membership order)' if order=='frequency' else 'Membership order'
    for row in shown:out.row('intersections',**{k:v for k,v in row.items() if k!='code'})
    out.plot('intersectionPlot',[dict(label=r['pattern'],value=r['n'],group='Exact membership') for r in shown],xlab='Membership digits in set order (all-zero = none)',ylab='Rows')
    if options.get('showSetMatrix',False):
        labels=json.dumps(result['names'],ensure_ascii=True)
        out.plot('intersectionMatrix',[dict(pattern=r['pattern'],count=r['n'],sets=labels) for r in shown])
    ids=out.row_ids if out.row_ids is not None else [str(i+1) for i in range(result['inputRows'])]
    if options.get('showMembershipTable',False):
        for i,mask in enumerate(result['masks'][:500]):
            row=result['patterns'][mask] if mask is not None else None
            out.row('membershipTable',row=ids[i],pattern=row['pattern'] if row else '',members=row['members'] if row else '',status='Included' if row else 'Excluded')
        if result['inputRows']>500:out.info('The native row preview shows only the first 500 input rows; all complete rows contribute to counts and saved membership.')
    if out.row_ids is not None:
        out.column('membershipGroups',result['masks'],levels=[v['pattern'] for v in result['patterns']],title='Set membership pattern',description='Digits follow Set Definitions order; 1=chosen positive level, 0=other nonmissing level; missing selected values remain missing',measure_type='nominal')
    out.markdown('summary',md_escape(f"Input rows: {result['inputRows']}; complete cohort: {result['retained']}; excluded: {result['excluded']}. Union: {result['union']}; all selected sets: {result['allSets']}. Pattern display order: {order_title}. Each digit follows the Set Definitions order: 1 is the explicitly chosen positive level; 0 is any other nonmissing level. Patterns are exclusive (only the indicated sets). The all-zero pattern is outside the union and remains in the cohort denominator. Missing values in any selected variable exclude that row from every count; unselected variables do not affect the cohort. Each row is one supplied item; repeated patients/specimens are not deduplicated. No hypothesis tests, enrichment analysis, Venn/Euler geometry, full UpSet layout, weighted counts or more than four sets are implemented in this core. Native tables/static plot use saved options; local inspection never changes membership or the cohort."))
    if result['excluded']:out.warn(f"{result['excluded']} input row(s) excluded for missing selected set values; missing values were not counted as negatives.")
    if options.get('interactive',True):
        for row in shown:
            matches=list(islice((ids[i] for i,mask in enumerate(result['masks']) if mask==row['code']),100))
            row['rows']=matches;row['omittedRows']=max(0,row['n']-len(matches))
        payload=dict(names=result['names'],sets=result['sets'],patterns=shown,retained=result['retained'],orderTitle=order_title)
        encoded=json.dumps(payload,allow_nan=False,ensure_ascii=True)
        for char,safe in (('<','\\u003c'),('>','\\u003e'),('&','\\u0026')):encoded=encoded.replace(char,safe)
        template=(Path(__file__).resolve().parents[2]/'templates/sets.html').read_text()
        out.html('explorer',template.replace('__ROOT__','cpjsets'+uuid.uuid4().hex).replace('__PAYLOAD__',encoded))
