"""Exploratory annotated marker heatmap; no patient-level inference or clinical rules."""
import json
import uuid
from pathlib import Path
from cpj_runtime import md_escape
from cpj_ihc import prepare, marker_pair

SPEC = {'name': 'pyihcheatmap',
 'title': 'Annotated IHC Heatmap',
 'menuGroup': 'Descriptives Py',
 'menuSubgroup': 'Biomarker panels',
 'version': '0.3.13',
 'options': [{'name': 'markers',
              'title': 'Numeric IHC markers',
              'type': 'Variables',
              'permitted': ['numeric'],
              'required': True},
             {'name': 'subject',
              'title': 'Patient or specimen ID (annotation)',
              'type': 'Variable'},
             {'name': 'group', 'title': 'Diagnosis or group annotation', 'type': 'Variable'},
             {'name': 'region', 'title': 'Region annotation', 'type': 'Variable'},
             {'name': 'scatterX', 'title': 'Scatter X marker (blank = first marker)',
              'type': 'Variable', 'permitted': ['numeric']},
             {'name': 'scatterY', 'title': 'Scatter Y marker (blank = second marker)',
              'type': 'Variable', 'permitted': ['numeric']},
             {'name': 'scaling',
              'title': 'Color scale',
              'type': 'List',
              'options': [{'name': 'raw', 'title': 'Raw marker units'},
                          {'name': 'zscore', 'title': 'Within-marker z scores (sample SD)'}],
              'default': 'raw'},
             {'name': 'missing',
              'title': 'Missing marker values',
              'type': 'List',
              'options': [{'name': 'available', 'title': 'Keep partial rows; show missing cells'},
                          {'name': 'complete', 'title': 'Retain complete marker rows only'}],
              'default': 'available'},
             {'name': 'clusterRows',
              'title': 'Cluster rows (average linkage, Euclidean)',
              'type': 'Bool',
              'default': False},
             {'name': 'clusterColumns',
              'title': 'Cluster markers (average linkage, Euclidean)',
              'type': 'Bool',
              'default': False},
             {'name': 'showScatter', 'title': 'Linked marker scatterplot',
              'type': 'Bool', 'default': False},
             {'name': 'interactive',
              'title': 'Local cell and row inspection',
              'type': 'Bool',
              'default': True}],
 'results': [{'name': 'summary', 'title': 'Heatmap Cohort and Methods', 'type': 'Text'},
             {'name': 'markerSummary',
              'title': 'Marker Summary in Retained Rows',
              'type': 'Table',
              'columns': [{'name': 'marker', 'title': 'Marker', 'type': 'text'},
                          {'name': 'observed', 'title': 'Observed', 'type': 'integer'},
                          {'name': 'missing', 'title': 'Missing', 'type': 'integer'},
                          {'name': 'mean', 'title': 'Raw Mean', 'type': 'number'},
                          {'name': 'sd', 'title': 'Raw Sample SD', 'type': 'number'}]},
             {'name': 'rowOrder',
              'title': 'Displayed Rows and Annotations',
              'type': 'Table',
              'columns': [{'name': 'position', 'title': 'Display Order', 'type': 'integer'},
                          {'name': 'sourceRow', 'title': 'Source Row', 'type': 'text'},
                          {'name': 'subject', 'title': 'Patient / Specimen', 'type': 'text'},
                          {'name': 'group', 'title': 'Group', 'type': 'text'},
                          {'name': 'region', 'title': 'Region', 'type': 'text'},
                          {'name': 'observed', 'title': 'Observed Markers', 'type': 'integer'}]},
             {'name': 'scatterCohort', 'title': 'Scatterplot Complete Pairs', 'type': 'Table',
              'visible': '(showScatter)', 'columns': [
                  {'name': 'xMarker', 'title': 'X Marker', 'type': 'text'},
                  {'name': 'yMarker', 'title': 'Y Marker', 'type': 'text'},
                  {'name': 'retained', 'title': 'Heatmap Rows', 'type': 'integer'},
                  {'name': 'plotted', 'title': 'Complete Pairs', 'type': 'integer'},
                  {'name': 'omitted', 'title': 'Missing Pair', 'type': 'integer'}]},
             {'name': 'scatterRows', 'title': 'Scatterplot Source Rows', 'type': 'Table',
              'visible': '(showScatter)', 'columns': [
                  {'name': 'sourceRow', 'title': 'Source Row', 'type': 'text'},
                  {'name': 'x', 'title': 'Displayed X', 'type': 'number'},
                  {'name': 'y', 'title': 'Displayed Y', 'type': 'number'}]},
             {'name': 'scatter', 'title': 'Marker Scatterplot', 'type': 'Image',
              'plot': 'points', 'width': 650, 'height': 450, 'visible': '(showScatter)'},
             {'name': 'heatmap',
              'title': 'Annotated IHC Heatmap',
              'type': 'Image',
              'plot': 'ihcheatmap',
              'width': 900,
              'height': 650},
             {'name': 'explorer',
              'title': 'IHC Cell Inspector',
              'type': 'Html',
              'visible': '(interactive)'}],
 'ui': {'children': [{'type': 'VariableSupplier',
                      'persistentItems': True,
                      'stretchFactor': 1,
                      'children': [{'type': 'TargetLayoutBox',
                                    'label': 'Numeric IHC markers',
                                    'children': [{'type': 'VariablesListBox',
                                                  'name': 'markers',
                                                  'isTarget': True}]},
                                   {'type': 'TargetLayoutBox',
                                    'label': 'Patient or specimen ID (annotation)',
                                    'children': [{'type': 'VariablesListBox',
                                                  'name': 'subject',
                                                  'isTarget': True,
                                                  'maxItemCount': 1}]},
                                   {'type': 'TargetLayoutBox',
                                    'label': 'Diagnosis or group annotation',
                                    'children': [{'type': 'VariablesListBox',
                                                  'name': 'group',
                                                  'isTarget': True,
                                                  'maxItemCount': 1}]},
                                   {'type': 'TargetLayoutBox',
                                    'label': 'Region annotation',
                                    'children': [{'type': 'VariablesListBox',
                                                  'name': 'region',
                                                  'isTarget': True,
                                                  'maxItemCount': 1}]},
                                   {'type': 'TargetLayoutBox', 'label': 'Scatter X marker',
                                    'children': [{'type': 'VariablesListBox', 'name': 'scatterX', 'isTarget': True, 'maxItemCount': 1, 'enable': '(showScatter)'}]},
                                   {'type': 'TargetLayoutBox', 'label': 'Scatter Y marker',
                                    'children': [{'type': 'VariablesListBox', 'name': 'scatterY', 'isTarget': True, 'maxItemCount': 1, 'enable': '(showScatter)'}]}]},
                     {'type': 'CollapseBox',
                      'label': 'Analysis and Display',
                      'collapsed': False,
                      'children': [{'type': 'ComboBox', 'name': 'scaling'},
                                   {'type': 'ComboBox', 'name': 'missing'},
                                   {'type': 'CheckBox', 'name': 'clusterRows'},
                                   {'type': 'CheckBox', 'name': 'clusterColumns'}]},
                     {'type': 'CollapseBox',
                      'label': 'Plots and Interaction',
                      'collapsed': True,
                      'children': [{'type': 'CheckBox', 'name': 'showScatter'},
                                   {'type': 'CheckBox', 'name': 'interactive'}]},
                     {'type': 'CollapseBox',
                      'label': 'Advanced Settings',
                      'collapsed': True,
                      'children': [{'type': 'CheckBox', 'name': 'showConsole'}]}]}}


def run(data, options, out):
    p = prepare(data, options, out.row_ids)
    if options.get('showScatter', False):
        pair = marker_pair(p, options['markers'], options.get('scatterX'), options.get('scatterY'))
        p['scatter'] = pair
        out.row('scatterCohort', xMarker=pair['xMarker'], yMarker=pair['yMarker'],
                retained=len(p['rows']), plotted=len(pair['points']), omitted=pair['omitted'])
        for point in pair['points']:
            out.row('scatterRows', sourceRow=point['sourceRow'], x=point['x'], y=point['y'])
        out.plot('scatter', [dict(x=v['x'], y=v['y'], group='Retained complete pairs')
                            for v in pair['points']],
                 xlab=pair['xMarker']+' — '+p['scaleLabel'],
                 ylab=pair['yMarker']+' — '+p['scaleLabel'])
        if not pair['points']:
            out.warn('No complete pairs for the scatter markers. The heatmap retains its cohort; the scatterplot is empty.')
    for row in p['summaries']:
        out.row('markerSummary', **row)
    for i, row in enumerate(p['rows']):
        out.row('rowOrder', position=i+1, sourceRow=row['row'], subject=row['subject'],
                group=row['group'], region=row['region'], observed=row['observed'])
    cells=[]
    for row, values in zip(p['rows'], p['values']):
        label=' | '.join([row['row']] + [row[k] for k in ('subject','group','region') if row[k] is not None])
        # Bound repeated plot labels before transport; native annotations stay complete.
        if len(label)>80:
            label=label[:77]+'...'
        for marker, value in zip(p['markers'], values):
            cells.append(dict(row=row['row'], label=label, variable=marker, value=value))
    out.plot('heatmap', cells, xlab=p['scaleLabel'], ylab='Source row | ID | group | region')
    out.markdown('summary', md_escape(
        f"Input rows: {p['inputRows']}; retained: {len(p['rows'])}; excluded: {p['excluded']}; "
        f"markers: {len(p['markers'])}. Color scale: {p['scaleLabel']}. "
        f"Missing cells in retained rows: {p['missingCells']}. "
        f"Row clustering: {bool(options.get('clusterRows'))}; marker clustering: {bool(options.get('clusterColumns'))}. "
        "Clustering uses average linkage and Euclidean distances on displayed values and requires complete marker data. "
        "Each row is one supplied specimen/region; repeated patient IDs are annotations, not independent replicates. "
        "Raw-unit colors share one numeric scale; markers with different units may need within-marker standardization. "
        "Display clustering and highlighting provide no diagnostic classification, significance test or validated molecular subtype. "
        "The optional scatterplot uses displayed marker values and complete pairs only; its native tables report missing pairs. "
        "Linked row highlighting is local and transient; it does not subset or refit results."))
    if p['constant']:
        out.warn('Zero or unavailable sample SD: ' + ', '.join(p['constant']) +
                 '. Under z scaling, observed cells in these columns are displayed as zero; missing cells remain missing.')
    if options.get('interactive', True):
        encoded=json.dumps(p,ensure_ascii=True,allow_nan=False)
        for char,safe in (('<','\\u003c'),('>','\\u003e'),('&','\\u0026')):
            encoded=encoded.replace(char,safe)
        template=(Path(__file__).resolve().parents[2]/'templates/ihcheatmap.html').read_text()
        out.html('explorer',template.replace('__ROOT__','cpjihc'+uuid.uuid4().hex).replace('__PAYLOAD__',encoded))
