"""Single-variable screening core, with explicit unported baseline features."""
import json
import uuid
from pathlib import Path
import numpy as np
from cpj_runtime import md_escape, InputError
from cpj_single_quality import screen

SPEC = {'name': 'pycheckdata',
 'title': 'Single Variable Quality Check',
 'menuGroup': 'ClinicoPathPj',
 'menuSubgroup': 'Descriptives',
 'version': '0.3.6',
 'options': [{'name': 'var', 'title': 'Variable to check', 'type': 'Variable', 'required': True},
             {'name':'screeningFlag','title':'Screening flag','type':'Output'},
             {'name': 'showOutliers', 'title': 'Outlier analysis', 'type': 'Bool', 'default': True},
             {'name': 'outlierTransform',
              'title': 'Outlier-detection transformation',
              'type': 'List',
              'options': [{'name': 'none', 'title': 'Raw values'},
                          {'name': 'log', 'title': 'Logarithm'},
                          {'name': 'sqrt', 'title': 'Square root'}],
              'default': 'none'},
             {'name': 'rareCategoryThreshold',
              'title': 'Rare category threshold (%)',
              'type': 'Number',
              'min': 0.1,
              'max': 20,
              'default': 5},
             {'name': 'cvMinMean',
              'title': 'Minimum absolute mean for CV',
              'type': 'Number',
              'min': 0,
              'max': 10,
              'default': 0.01},
             {'name': 'showDistribution',
              'title': 'Distribution summary',
              'type': 'Bool',
              'default': False},
             {'name': 'showDuplicates',
              'title': 'Repeated values or category frequencies',
              'type': 'Bool',
              'default': False},
             {'name': 'showPatterns',
              'title': 'Missingness sequence summary',
              'type': 'Bool',
              'default': False},
             {'name': 'showSummary',
              'title': 'Plain-language summary',
              'type': 'Bool',
              'default': False},
             {'name': 'showPlot', 'title': 'Row screening plot', 'type': 'Bool', 'default': True},
             {'name': 'showInteractive',
              'title': 'Interactive row inspection',
              'type': 'Bool',
              'default': False}],
 'results': [{'name': 'overview',
              'title': 'Single Variable Overview',
              'type': 'Table',
              'columns': [{'name': 'kind', 'title': 'Declared Type', 'type': 'text'},
                          {'name': 'total', 'title': 'Input Rows', 'type': 'integer'},
                          {'name': 'valid', 'title': 'Observed', 'type': 'integer'},
                          {'name': 'missing', 'title': 'Missing', 'type': 'integer'},
                          {'name': 'missingRate',
                           'title': 'Missing (%)',
                           'type': 'number',
                           'format': 'pc'},
                          {'name': 'distinct', 'title': 'Distinct Observed', 'type': 'integer'},
                          {'name': 'repeats', 'title': 'Excess Repeats', 'type': 'integer'}]},
             {'name': 'distribution',
              'title': 'Numeric Distribution',
              'type': 'Table',
              'columns': [{'name': 'statistic', 'title': 'Statistic', 'type': 'text'},
                          {'name': 'value', 'title': 'Value', 'type': 'number'}],
              'visible': '(showDistribution)'},
             {'name': 'methods',
              'title': 'Outlier Methods',
              'type': 'Table',
              'columns': [{'name': 'method', 'title': 'Method', 'type': 'text'},
                          {'name': 'available', 'title': 'Available', 'type': 'text'},
                          {'name': 'flagged', 'title': 'Flags', 'type': 'integer'},
                          {'name': 'threshold', 'title': 'Rule on Screening Scale', 'type': 'text'}],
              'visible': '(showOutliers)'},
             {'name': 'outliers',
              'title': 'Selected Screening Flags (First 200)',
              'type': 'Table',
              'columns': [{'name': 'row', 'title': 'Original Row', 'type': 'text'},
                          {'name': 'value', 'title': 'Raw Value', 'type': 'number'},
                          {'name': 'z', 'title': 'Z-score', 'type': 'number'},
                          {'name': 'modified', 'title': 'Modified Z-score', 'type': 'number'},
                          {'name': 'zFlag', 'title': 'Z Flag', 'type': 'text'},
                          {'name': 'iqrFlag', 'title': 'IQR Flag', 'type': 'text'},
                          {'name': 'madFlag', 'title': 'MAD Flag', 'type': 'text'},
                          {'name': 'votes', 'title': 'Method Votes', 'type': 'integer'}],
              'visible': '(showOutliers)'},
             {'name': 'frequencies',
              'title': 'Observed Frequencies (First 200)',
              'type': 'Table',
              'columns': [{'name': 'value', 'title': 'Observed Value', 'type': 'text'},
                          {'name': 'n', 'title': 'Count', 'type': 'integer'},
                          {'name': 'proportion',
                           'title': 'Observed (%)',
                           'type': 'number',
                           'format': 'pc'},
                          {'name': 'rare', 'title': 'Below Rare Threshold', 'type': 'text'}],
              'visible': '(showDuplicates)'},
             {'name': 'patterns',
              'title': 'Missingness Sequence',
              'type': 'Table',
              'columns': [{'name': 'measure', 'title': 'Measure', 'type': 'text'},
                          {'name': 'value', 'title': 'Rows or Runs', 'type': 'integer'}],
              'visible': '(showPatterns)'},
             {'name': 'summary',
              'title': 'Screening Summary',
              'type': 'Text',
              'visible': '(showSummary)'},
             {'name': 'scope', 'title': 'Methods, Scope and Omissions', 'type': 'Text'},
             {'name': 'plot',
              'title': 'Row Screening Static View',
              'type': 'Image',
              'plot': 'points',
              'width': 650,
              'height': 400,
              'visible': '(showPlot)'},
             {'name': 'explorer',
              'title': 'Row Inspection',
              'type': 'Html',
              'visible': '(showInteractive)'},
             {'name': 'screeningFlag',
              'title': 'Screening Flag',
              'type': 'Output',
              'varTitle': 'Screening flag',
              'varDescription': 'Exploratory consensus flag; missing when not assessed',
              'measureType': 'nominal'}],
 'ui': {'children': [{'type': 'VariableSupplier',
                      'persistentItems': False,
                      'stretchFactor': 1,
                      'children': [{'type': 'TargetLayoutBox',
                                    'label': 'Variable to check',
                                    'children': [{'type': 'VariablesListBox',
                                                  'name': 'var',
                                                  'isTarget': True,
                                                  'maxItemCount': 1}]}]},
                     {'type': 'CollapseBox',
                      'label': 'Screening Methods',
                      'collapsed': False,
                      'children': [{'type': 'LayoutBox',
                                    'margin': 'large',
                                    'children': [{'name': 'showOutliers', 'type': 'CheckBox'},
                                                 {'name': 'outlierTransform',
                                                  'type': 'ComboBox',
                                                  'enable': '(showOutliers)'},
                                                 {'name': 'rareCategoryThreshold',
                                                  'type': 'TextBox',
                                                  'format': 'number'},
                                                 {'name': 'cvMinMean',
                                                  'type': 'TextBox',
                                                  'format': 'number'}]}]},
                     {'type': 'CollapseBox',
                      'label': 'Results and Interpretation',
                      'collapsed': True,
                      'children': [{'type': 'LayoutBox',
                                    'margin': 'large',
                                    'children': [{'name': 'showDistribution', 'type': 'CheckBox'},
                                                 {'name': 'showDuplicates', 'type': 'CheckBox'},
                                                 {'name': 'showPatterns', 'type': 'CheckBox'},
                                                 {'name': 'showSummary', 'type': 'CheckBox'}]}]},
                     {'type': 'CollapseBox',
                      'label': 'Plots and Interaction',
                      'collapsed': True,
                      'children': [{'type': 'LayoutBox',
                                    'margin': 'large',
                                    'children': [{'name': 'showPlot', 'type': 'CheckBox'},
                                                 {'name': 'showInteractive', 'type': 'CheckBox'}]}]},
                     {'type': 'CollapseBox',
                      'label': 'Save to Data',
                      'collapsed': True,
                      'children': [{'type': 'LayoutBox',
                                    'margin': 'large',
                                    'children': [{'name': 'screeningFlag', 'type': 'Output'}]}]},
                     {'type': 'CollapseBox',
                      'label': 'Advanced Settings',
                      'collapsed': True,
                      'children': [{'type': 'LayoutBox',
                                    'margin': 'large',
                                    'children': [{'name': 'showConsole', 'type': 'CheckBox'}]}]}]}}

def html_document(payload):
    encoded=json.dumps(payload,allow_nan=False,ensure_ascii=True)
    for char,safe in (('<','\\u003c'),('>','\\u003e'),('&','\\u0026')):encoded=encoded.replace(char,safe)
    base=Path(__file__).resolve().parents[2]
    libraries=['d3-7.9.0.min.js','htl-0.3.1.min.js','observable-inputs-0.12.0.min.js','observable-plot-0.6.17.min.js']
    document=''.join('<script>'+(base/'vendor'/name).read_text()+'</script>' for name in libraries)
    template=(base/'templates/single-quality.html').read_text()
    document+=template.replace('__ROOT__','cpjqc'+uuid.uuid4().hex).replace('__PAYLOAD__',encoded)
    if len(document.encode())>1_500_000:
        raise InputError('The interactive preview exceeds 1.5 MB. Disable interactive inspection or shorten unusually long text values.')
    return document


def run(data,options,out):
    name=options.get('var')
    if not name:
        raise InputError('Choose one variable to check.')
    r=screen(data[name],options.get('outlierTransform','none'),options.get('rareCategoryThreshold',5),options.get('cvMinMean',.01),options.get('showOutliers',True))
    missing=r['missing'];numeric=r['kind']=='Numeric';selected=r['selected'];n=r['n'];total=r['total']
    ids=[str(out.row_ids[i] if out.row_ids is not None else i+1) for i in range(total)]
    out.row('overview',kind=r['kind'],total=total,valid=n,missing=total-n,missingRate=(total-n)/total,distinct=r['distinct'],repeats=r['repeats'])
    out.note('overview','Missing codes are excluded from observed counts. Literal NA text remains observed. Excess repeats = observed minus distinct observed; equal values do not establish duplicate patients.')
    if options.get('showDistribution'):
        if numeric:
            for label,value in r['stats'].items():
                out.row('distribution',statistic='CV (%)' if label=='cv' else label,value=100*value if label=='cv' and value is not None else value)
            out.note('distribution','Raw-scale summaries: sample SD, type-7 quartiles, MAD multiplied once by 1.4826 and population-moment skewness. Skewness is zero for fewer than three observed values or a constant, matching the baseline. CV is suppressed at zero or when |mean| is below its threshold; CV assumes a meaningful ratio-scale zero.')
        else:out.info('Numeric distribution and outlier screening do not apply to categorical or text data. Use observed frequencies.')
    if options.get('showOutliers',True) and numeric:
        available=r['assessed']
        for j,(method,rule) in enumerate([('Z-score','|z| > 3'),('IQR','Outside Q1 - 1.5 IQR to Q3 + 1.5 IQR'),('Modified Z-score','|M| > 3.5; scaled MAD')]):
            usable=available and (j!=2 or r['mad_available']) and (j!=0 or np.isfinite(r['z']).any())
            out.row('methods',method=method,available='Yes' if usable else 'No',flagged=int(r['flags'][:,j].sum()) if usable else None,threshold=rule)
        for i in np.flatnonzero(selected)[:200]:
            out.row('outliers',row=ids[i],value=float(r['values'][i]),z=float(r['z'][i]) if np.isfinite(r['z'][i]) else None,modified=float(r['modified'][i]) if np.isfinite(r['modified'][i]) else None,
                    zFlag='Yes' if r['flags'][i,0] else 'No',iqrFlag='Yes' if r['flags'][i,1] else 'No',madFlag=('Yes' if r['flags'][i,2] else 'No') if r['mad_available'] else 'Unavailable',votes=int(r['votes'][i]))
        note=f"Full-data selected flags: {int(selected.sum())}; first 200 listed in input order. Screening scale: {r['transform']}. "
        note+=('Fewer than three observed values: screening unavailable.' if not available else 'Informative only (n < 10): at least one method selects a row.' if r['informative'] else 'At least two methods must select a row.')
        if available and not np.isfinite(r['z']).any():note+=' Z-scores are undefined when the screening-scale SD is zero.'
        if not r['mad_available']:note+=' MAD screening is unavailable when n <= 3 or scaled MAD is zero.'
        out.note('outliers',note)
        if available and r['informative']:out.warn('Fewer than ten observed values: single-method flags are informative only, not robust consensus evidence.')
    for warning in r['warnings']:out.warn(warning)
    if options.get('showDuplicates'):
        frequencies=[f for f in r['frequencies'] if not numeric or f['n']>1]
        for f in frequencies[:200]:out.row('frequencies',**{**f,'rare':('Yes' if f['rare'] else 'No') if not numeric else 'Not applicable'})
        out.note('frequencies','Numeric values are listed only when repeated; categories/text include all observed levels. Unused levels are omitted. Percentages use all observed values. First 200 entries by decreasing frequency (value order breaks ties); full-data distinct/repeat counts remain in Overview. Rare means strictly below the entered percentage of observed rows and does not establish test assumptions.')
    if options.get('showPatterns'):
        for label,value in [('Observed/missing runs',r['runs']),('Longest missing run',r['longest_missing']),('Trailing missing rows',r['trailing_missing'])]:out.row('patterns',measure=label,value=value)
        out.note('patterns','Descriptive sequence counts follow input row order; they are not a runs test or evidence of MCAR, MAR or MNAR. Sorting rows changes these counts.')
    if options.get('showSummary'):
        out.markdown('summary',md_escape(f'{name}: {n} observed of {total} input rows; {total-n} missing; {r["distinct"]} distinct observed values and {r["repeats"]} excess repeats. '+(f'{int(selected.sum())} selected screening flags.' if r['assessed'] else 'Outlier screening was not assessed.')))
    out.markdown('scope',md_escape('All summary calculations use every input row; no values are removed or corrected. Original row IDs accompany flags and saved output. Heuristic grades, name-based clinical plausibility ranges, severity labels, missingness-run inference and category naming diagnostics from the baseline are not implemented in this core. Little\'s MCAR test cannot be computed from a single variable. Screening flags indicate records to review, not errors or diagnoses. '+('The first 500 input rows form the interactive/static row preview; this is an ordered display bound, not random sampling.' if numeric else 'Categorical/text variables receive descriptive frequencies; saved outlier flags remain missing.')))
    rows=[]
    for i in range(min(total,500)):
        value=None if missing[i] else float(r['values'][i]) if numeric else str(r['values'][i])
        status='Missing' if missing[i] else 'Flagged' if selected[i] else 'Not flagged' if r['assessed'] else 'Not assessed'
        rows.append(dict(row=ids[i],position=i+1,value=value,status=status,votes=int(r['votes'][i]) if r['assessed'] and not missing[i] else None))
    if numeric and options.get('showPlot',True):
        out.plot('plot',[dict(x=row['position'],y=row['value'],group=row['status']) for row in rows if row['value'] is not None],xlab='Input row position (first 500)',ylab=name)
    if options.get('showInteractive'):
        out.html('explorer',html_document(dict(variable=name,numeric=numeric,total=total,rows=rows)))
    if out.row_ids is not None:
        flags=[int(selected[i]) if r['assessed'] and not missing[i] else None for i in range(total)]
        out.column('screeningFlag',flags,levels=['Not selected','Selected'],title=name[:240]+'_screening_flag',description='Exploratory screening only; n < 10 uses one-method informative flags; otherwise two-method consensus.',measure_type='nominal')
