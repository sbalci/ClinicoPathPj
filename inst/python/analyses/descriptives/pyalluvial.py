"""Categorical count-flow core; local highlighting never changes the analyzed cohort."""
import json
import uuid
from pathlib import Path
from cpj_runtime import md_escape
from cpj_alluvial import calculate, geometry

SPEC = {
    'name': 'pyalluvial', 'title': 'Categorical Alluvial Flows (Python Core)',
    'menuGroup': 'Descriptives Py', 'menuSubgroup': 'Descriptive plots', 'version': '0.3.41',
    'options': [
        {'name': 'vars', 'title': 'Categorical variables in axis order', 'type': 'Variables',
         'permitted': ['factor'], 'suggested': ['nominal', 'ordinal'], 'required': True},
        {'name': 'excl', 'title': 'Exclude rows with missing categories', 'type': 'Bool', 'default': False},
        {'name': 'showFlowTable', 'title': 'Flow count table', 'type': 'Bool', 'default': False},
        {'name': 'showCategories', 'title': 'Axis category counts', 'type': 'Bool', 'default': False},
        {'name': 'showPlot', 'title': 'Static alluvial diagram', 'type': 'Bool', 'default': True},
        {'name': 'interactive', 'title': 'Local flow highlighting', 'type': 'Bool', 'default': True}],
    'results': [
        {'name': 'summary', 'title': 'Flow Cohort and Interpretation', 'type': 'Text'},
        {'name': 'flows', 'title': 'Observed Flow Counts', 'type': 'Table', 'visible': '(showFlowTable)',
         'columns': [
             {'name': 'id', 'title': 'Flow ID', 'type': 'integer'},
             {'name': 'path', 'title': 'Category Path (JSON)', 'type': 'text'},
             {'name': 'n', 'title': 'Rows', 'type': 'integer'},
             {'name': 'percent', 'title': 'Retained (%)', 'type': 'number', 'format': 'pc'}]},
        {'name': 'categories', 'title': 'Observed Axis Category Counts', 'type': 'Table', 'visible': '(showCategories)',
         'columns': [
             {'name': 'axis', 'title': 'Axis', 'type': 'integer'},
             {'name': 'variable', 'title': 'Variable', 'type': 'text'},
             {'name': 'label', 'title': 'Category', 'type': 'text'},
             {'name': 'n', 'title': 'Rows', 'type': 'integer'},
             {'name': 'percent', 'title': 'Retained (%)', 'type': 'number', 'format': 'pc'}]},
        {'name': 'flowPlot', 'title': 'Alluvial Row Counts', 'type': 'Image', 'plot': 'alluvial',
         'width': 1100, 'height': 700, 'visible': '(showPlot)'},
        {'name': 'explorer', 'title': 'Local Flow Explorer', 'type': 'Html', 'visible': '(interactive)'}],
    'ui': {'children': [
        {'type': 'VariableSupplier', 'persistentItems': False, 'stretchFactor': 1,
         'children': [{'type': 'TargetLayoutBox', 'label': 'Categorical variables in axis order',
                       'children': [{'type': 'VariablesListBox', 'name': 'vars', 'isTarget': True}]}]},
        {'type': 'CollapseBox', 'label': 'Analysis and Cohort', 'collapsed': False,
         'children': [{'type': 'CheckBox', 'name': 'excl'}]},
        {'type': 'CollapseBox', 'label': 'Results and Interpretation', 'collapsed': False,
         'children': [{'type': 'CheckBox', 'name': 'showFlowTable'}, {'type': 'CheckBox', 'name': 'showCategories'}]},
        {'type': 'CollapseBox', 'label': 'Plots and Interaction', 'collapsed': False,
         'children': [{'type': 'CheckBox', 'name': 'showPlot'}, {'type': 'CheckBox', 'name': 'interactive'}]},
        {'type': 'CollapseBox', 'label': 'Advanced Settings', 'collapsed': True,
         'children': [{'type': 'CheckBox', 'name': 'showConsole'}]}]}}


def explorer(result, drawing):
    template = Path(__file__).resolve().parents[2] / 'templates' / 'alluvial.html'
    payload = dict(drawing=drawing, flows=[dict(id=f['id'], labels=f['labels'], n=f['n'], percent=f['percent'])
                                          for f in result['flows']])
    # JSON is data, never markup; preserve literal script-closing labels safely.
    encoded = json.dumps(payload, ensure_ascii=True).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    return template.read_text().replace('__ID__', 'cpj-flow-'+uuid.uuid4().hex).replace('__PAYLOAD__', encoded)


def run(data, options, out):
    result = calculate(data, options)
    drawing = geometry(result)
    for flow in sorted(result['flows'], key=lambda f: (-f['n'], f['codes'])):
        out.row('flows', id=flow['id'], path=json.dumps(flow['labels'], ensure_ascii=False),
                n=flow['n'], percent=flow['percent'])
    for category in result['categories']:
        out.row('categories', axis=category['axis']+1, variable=category['variable'], label=category['label'],
                n=category['n'], percent=category['percent'])
    if options.get('showPlot', True):
        out.plot('flowPlot', [dict(payload=json.dumps(drawing, ensure_ascii=True))])
    if options.get('interactive', True):
        out.html('explorer', explorer(result, drawing))
    policy = ('Rows missing any selected category are excluded from every axis.' if options.get('excl', False)
              else f"Missing category cells are retained under the distinct label {result['missingLabel']}.")
    out.markdown('summary', md_escape(
        f"Input rows: {result['total']}; retained: {result['n']}; excluded: {result['excluded']}; "
        f"rows with a missing selected category: {result['missingRows']}. {policy} "
        f"Observed paths: {len(result['flows'])}. Axis order: "+' → '.join(result['names'])+
        '. Ribbon thickness is the number of supplied rows on the complete path, using one common scale across axes; '
        'gaps separate categories. Colors identify the first-axis category. Axes follow declared factor order, '
        'with missing categories appended; unused categories are omitted. Flow table order is decreasing count '
        'with declared-code ties. JSON paths preserve labels containing separators. '
        'Local highlighting is transient and changes no counts, cohort, saved options or native results. '
        'Rows are not aggregated by patient ID; the diagram is descriptive and does not imply temporal order, '
        'causality or independent-observation inference. This core omits weights, condensation, numeric binning, '
        'marginal plots, alternative fill rules, orientations and full baseline styling.'))
    if result['missingRows']:
        out.info(f"{result['missingRows']} rows contain missing selected categories; inspect the reported inclusion policy.")
