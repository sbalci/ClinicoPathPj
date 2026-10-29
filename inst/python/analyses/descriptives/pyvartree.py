"""Partial categorical count-tree port; advanced vtree features are not imitated."""
import html
import json
from cpj_tree import calculate, node_summaries, reference_summaries
from cpj_runtime import md_escape, InputError

SPEC = {'name': 'pyvartree',
 'title': 'Categorical Variable Tree (Python Core)',
 'menuGroup': 'Descriptives Py',
 'menuSubgroup': 'Descriptive plots',
 'version': '0.3.35',
 'options': [{'name': 'vars',
              'title': 'Categorical variables in branching order',
              'type': 'Variables',
              'permitted': ['factor'],
              'suggested': ['nominal', 'ordinal'],
              'required': True},
             {'name': 'showTree',
              'title': 'Expandable categorical tree',
              'type': 'Bool',
              'default': True},
             {'name': 'showPlot',
              'title': 'Largest leaf counts (up to 30)',
              'type': 'Bool',
              'default': False},
             {'name': 'showPaths', 'title': 'Full branch paths in table', 'type': 'Bool', 'default': False},
             {'name': 'showNodeSummary', 'title': 'Continuous node summaries', 'type': 'Bool', 'default': False},
             {'name': 'summaryvar', 'title': 'Continuous summary variable', 'type': 'Variable', 'permitted': ['numeric'], 'suggested': ['continuous']},
             {'name': 'summarylocation', 'title': 'Summary location', 'type': 'List',
              'options': [{'name': 'leafonly', 'title': 'Leaf nodes only'}, {'name': 'allnodes', 'title': 'All nodes'}], 'default': 'leafonly'},
             {'name': 'pct', 'title': 'Reference-level percentages', 'type': 'Bool', 'default': False},
             {'name': 'percvar', 'title': 'Reference variable', 'type': 'Variable', 'permitted': ['factor'], 'suggested': ['nominal','ordinal']},
             {'name': 'percvarLevel', 'title': 'Reference level', 'type': 'Level', 'variable': '(percvar)', 'optional': True}],
 'results': [{'name': 'summary', 'title': 'Cohort and Tree Rules', 'type': 'Text'},
             {'name': 'nodes',
              'title': 'Observed Branch Counts',
              'type': 'Table',
              'columns': [{'name': 'node', 'title': 'Node ID', 'type': 'integer'},
                          {'name': 'parent', 'title': 'Parent ID', 'type': 'integer'},
                          {'name': 'depth', 'title': 'Depth', 'type': 'integer'},
                          {'name': 'variable', 'title': 'Variable', 'type': 'text'},
                          {'name': 'level', 'title': 'Category', 'type': 'text'},
                          {'name': 'path', 'title': 'Branch Path', 'type': 'text', 'visible': '(showPaths)'},
                          {'name': 'n', 'title': 'Count', 'type': 'integer'},
                          {'name': 'cohortPercent',
                           'title': 'Cohort (%)',
                           'type': 'number',
                           'format': 'pc'},
                          {'name': 'parentPercent',
                           'title': 'Parent (%)',
                           'type': 'number',
                           'format': 'pc'},
                          {'name': 'leaf', 'title': 'Leaf', 'type': 'text'}]},
             {'name': 'summaryScope', 'title': 'Continuous Summary Rules', 'type': 'Text', 'visible': '(showNodeSummary)'},
             {'name': 'nodeSummary', 'title': 'Continuous Node Summaries', 'type': 'Table', 'visible': '(showNodeSummary)',
              'columns': [{'name': 'node', 'title': 'Node ID', 'type': 'integer'},
                          {'name': 'variable', 'title': 'Summary Variable', 'type': 'text'},
                          {'name': 'nodeN', 'title': 'Node Rows', 'type': 'integer'},
                          {'name': 'valid', 'title': 'Valid', 'type': 'integer'},
                          {'name': 'missing', 'title': 'Missing', 'type': 'integer'},
                          {'name': 'mean', 'title': 'Mean', 'type': 'number'},
                          {'name': 'sd', 'title': 'SD', 'type': 'number'}]},
             {'name': 'referenceScope', 'title': 'Reference Percentage Rules', 'type': 'Text', 'visible': '(pct)'},
             {'name': 'referenceSummary', 'title': 'Reference-Level Node Percentages', 'type': 'Table', 'visible': '(pct)',
              'columns': [{'name': 'node', 'title': 'Node ID', 'type': 'integer'},
                          {'name': 'variable', 'title': 'Reference Variable', 'type': 'text'},
                          {'name': 'level', 'title': 'Reference Level', 'type': 'text'},
                          {'name': 'nodeN', 'title': 'Node Rows', 'type': 'integer'},
                          {'name': 'valid', 'title': 'Valid Reference', 'type': 'integer'},
                          {'name': 'missing', 'title': 'Missing Reference', 'type': 'integer'},
                          {'name': 'matches', 'title': 'Matches', 'type': 'integer'},
                          {'name': 'percent', 'title': 'Reference (%)', 'type': 'number', 'format': 'pc'}]},
             {'name': 'explorer',
              'title': 'Expandable Categorical Tree',
              'type': 'Html',
              'visible': '(showTree)'},
             {'name': 'leafPlot',
              'title': 'Largest Leaf Counts by Node ID',
              'type': 'Image',
              'plot': 'bar',
              'width': 1000,
              'height': 650,
              'visible': '(showPlot)'}],
 'ui': {'children': [{'type': 'VariableSupplier',
                      'persistentItems': True,
                      'stretchFactor': 1,
                      'children': [{'type': 'TargetLayoutBox',
                                    'label': 'Categorical variables in branching order',
                                    'children': [{'type': 'VariablesListBox',
                                                  'name': 'vars',
                                                  'isTarget': True}]},
                                   {'type': 'TargetLayoutBox', 'label': 'Continuous summary variable (optional)',
                                    'children': [{'type': 'VariablesListBox', 'name': 'summaryvar', 'maxItemCount': 1, 'isTarget': True, 'enable': '(showNodeSummary)'}]},
                                   {'type': 'TargetLayoutBox', 'label': 'Reference variable (optional)',
                                    'children': [{'type': 'VariablesListBox', 'name': 'percvar', 'maxItemCount': 1, 'isTarget': True, 'enable': '(pct)'}]},
                                   {'type': 'LevelSelector', 'name': 'percvarLevel', 'enable': '(pct)'}]},
                     {'type': 'CollapseBox', 'label': 'Results and Interpretation', 'collapsed': False,
                      'children': [{'type': 'CheckBox', 'name': 'showPaths'},
                                   {'type': 'CheckBox', 'name': 'showNodeSummary'},
                                   {'type': 'CheckBox', 'name': 'pct'},
                                   {'type': 'ComboBox', 'name': 'summarylocation', 'enable': '(showNodeSummary)'}]},
                     {'type': 'CollapseBox',
                      'label': 'Plots and Interaction',
                      'collapsed': False,
                      'children': [{'type': 'CheckBox', 'name': 'showTree'},
                                   {'type': 'CheckBox', 'name': 'showPlot'}]},
                     {'type': 'CollapseBox',
                      'label': 'Advanced Settings',
                      'collapsed': True,
                      'children': [{'type': 'CheckBox', 'name': 'showConsole'}]}]}}


def tree_html(result):
    children={}
    for node in result['nodes']:
        children.setdefault(node['parent'],[]).append(node)
    def branch(node):
        name='Complete cohort' if node['depth']==0 else node['variable']+' = '+node['level']
        label=f"#{node['node']} {name}: {node['n']} rows; {100*node['parentPercent']:.2f}% of parent; {100*node['cohortPercent']:.2f}% of cohort"
        stats=next((v for v in result.get('summaries',[]) if v['node']==node['node']),None)
        if stats is not None:
            mean='undefined' if stats['mean'] is None else format(stats['mean'],'.6g')
            sd='undefined' if stats['sd'] is None else format(stats['sd'],'.6g')
            label+=f"; {stats['variable']}: valid n={stats['valid']}, missing={stats['missing']}, mean={mean}, SD={sd}"
        reference=next((v for v in result.get('references',[]) if v['node']==node['node']),None)
        if reference is not None:
            percent='undefined' if reference['percent'] is None else format(100*reference['percent'],'.6g')+'%'
            label+=f"; {reference['variable']}={reference['level']}: {reference['matches']}/{reference['valid']} valid ({percent}), missing={reference['missing']}"
        label=html.escape(label,quote=True)
        descendants=children.get(node['node'],[])
        if not descendants:return '<li><span>'+label+'</span></li>'
        return '<li><details'+(' open' if node['depth']==0 else '')+'><summary>'+label+'</summary><ul>'+''.join(branch(c) for c in descendants)+'</ul></details></li>'
    return '<div class="cpj-category-tree"><style>.cpj-category-tree{color:inherit;background:transparent;font:14px system-ui;padding:8px}.cpj-category-tree ul{list-style:none;padding-left:20px}.cpj-category-tree summary{cursor:pointer;padding:5px}.cpj-category-tree summary:focus-visible{outline:3px solid currentColor}.cpj-category-tree li>span{display:block;padding:5px}</style><p>Expand or collapse branches locally. With focus on a branch heading, use Enter or Space. Expansion is transient and does not change the cohort or counts. Native tables and the static plot provide exportable counts.</p><ul>'+branch(result['nodes'][0])+'</ul></div>'


def run(data,options,out):
    r=calculate(data,options)
    for node in r['nodes']:
        row=dict(node);row['path']=json.dumps(row['path'],ensure_ascii=False);row['leaf']='Yes' if row['leaf'] else 'No'
        out.row('nodes',**row)
    if options.get('showNodeSummary',False):
        variable=options.get('summaryvar')
        if not variable:
            out.info('Choose a continuous summary variable, or disable continuous node summaries. The categorical tree remains available.')
            out.markdown('summaryScope','Select a numeric summary variable to populate continuous summaries. Categorical counts are unchanged.')
        else:
            r['summaries']=node_summaries(data,r,variable,options.get('summarylocation','leafonly'))
            for row in r['summaries']:out.row('nodeSummary',**row)
            out.markdown('summaryScope',md_escape(f"Summary variable: {variable}. Location: {options.get('summarylocation','leafonly')}. Node IDs match the count table. Missing summary values affect only valid summary n, not node membership or percentage denominators. Mean uses valid values; SD uses n−1 and is undefined below two valid values. All-missing node means are undefined. Repeated subjects are not modeled; summaries are descriptive, without confidence intervals or tests. Local tree labels round to six significant digits; native numeric tables retain unformatted estimates."))
            if any(v['valid']<2 for v in r['summaries']):out.warn('Some displayed node summaries have fewer than two valid values; their SD is undefined. Inspect the valid and missing counts.')
    if options.get('pct',False):
        variable=options.get('percvar');level=options.get('percvarLevel')
        if not variable or level is None:
            out.info('Choose the reference variable and level explicitly; categorical and continuous results remain available.')
            out.markdown('referenceScope','Select a reference variable and level. Reference percentages use valid reference values within each unchanged categorical node.')
        else:
            if variable==options.get('summaryvar'):raise InputError('Use a different reference variable, or remove its assignment from the numeric summary role.')
            r['references']=reference_summaries(data,r,variable,level)
            for row in r['references']:out.row('referenceSummary',**row)
            out.markdown('referenceScope',md_escape(f"Reference: {variable} = {level}. Percentage = matches / valid reference values within each node. Missing reference values do not remove tree rows; they reduce only the reference denominator. Zero valid reference values give an undefined percentage. This differs from parent/cohort percentages in the count table. Labels are matched literally, without parsing conditions. These descriptive proportions have no intervals or hypothesis tests."))
            if any(v['valid']==0 for v in r['references']):out.warn('Some nodes have no valid reference values; their reference percentages are undefined.')
    if options.get('showTree',True):out.html('explorer',tree_html(r))
    leaves=[v for v in r['nodes'] if v['leaf']]
    if options.get('showPlot',False):
        shown=sorted(leaves,key=lambda v:(-v['n'],v['node']))[:30]
        out.plot('leafPlot',[dict(label='#'+str(v['node']),value=v['n'],group='Leaf count') for v in shown],xlab='Node ID (branch path in native table)',ylab='Complete rows')
        if len(leaves)>30:out.info(f'Static plot shows the 30 largest of {len(leaves)} observed leaves, with traversal-order ties. Tables and expandable tree retain every observed node.')
    out.markdown('summary',md_escape(f"Input rows: {r['total']}; complete cohort: {r['n']}; excluded for missing selected categories: {r['excluded']}. Branching order: "+' → '.join(r['names'])+f". Observed non-root nodes: {len(r['nodes'])-1}; observed leaves: {len(leaves)}. Every depth uses the same complete cohort; children partition their parent. Parent and cohort percentages use different denominators. Only observed branches appear; {r['unused']} declared levels are unused in the input. Literal text such as NA remains a category, while genuinely missing codes/levels exclude rows. Counts describe supplied rows, without patient aggregation, inference or clinical classification. This partial core omits pruning/follow rules, baseline styling, missing-category branches and full vtree parity."))
    if r['excluded']:out.warn(f"{r['excluded']} rows excluded across all tree depths because a selected category is missing.")
