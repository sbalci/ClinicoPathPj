"""Partial categorical count-tree port; advanced vtree features are not imitated."""
import html
import json
from cpj_tree import calculate
from cpj_runtime import md_escape

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
             {'name': 'showPaths', 'title': 'Full branch paths in table', 'type': 'Bool', 'default': False}],
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
                      'persistentItems': False,
                      'stretchFactor': 1,
                      'children': [{'type': 'TargetLayoutBox',
                                    'label': 'Categorical variables in branching order',
                                    'children': [{'type': 'VariablesListBox',
                                                  'name': 'vars',
                                                  'isTarget': True}]}]},
                     {'type': 'CollapseBox', 'label': 'Results and Interpretation', 'collapsed': False,
                      'children': [{'type': 'CheckBox', 'name': 'showPaths'}]},
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
    if options.get('showTree',True):out.html('explorer',tree_html(r))
    leaves=[v for v in r['nodes'] if v['leaf']]
    if options.get('showPlot',False):
        shown=sorted(leaves,key=lambda v:(-v['n'],v['node']))[:30]
        out.plot('leafPlot',[dict(label='#'+str(v['node']),value=v['n'],group='Leaf count') for v in shown],xlab='Node ID (branch path in native table)',ylab='Complete rows')
        if len(leaves)>30:out.info(f'Static plot shows the 30 largest of {len(leaves)} observed leaves, with traversal-order ties. Tables and expandable tree retain every observed node.')
    out.markdown('summary',md_escape(f"Input rows: {r['total']}; complete cohort: {r['n']}; excluded for missing selected categories: {r['excluded']}. Branching order: "+' → '.join(r['names'])+f". Observed non-root nodes: {len(r['nodes'])-1}; observed leaves: {len(leaves)}. Every depth uses the same complete cohort; children partition their parent. Parent and cohort percentages use different denominators. Only observed branches appear; {r['unused']} declared levels are unused in the input. Literal text such as NA remains a category, while genuinely missing codes/levels exclude rows. Counts describe supplied rows, without patient aggregation, inference or clinical classification. This partial core omits pruning/follow rules, continuous summaries, percentage variables, baseline styling, missing-category branches and full vtree parity."))
    if r['excluded']:out.warn(f"{r['excluded']} rows excluded across all tree depths because a selected category is missing.")
