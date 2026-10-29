"""Default-style grouped summaries with explicit denominators and test limitations."""
from cpj_runtime import md_escape
from cpj_crosstable import calculate

SPEC = {
 'name': 'pycrosstable', 'title': 'Cross Tables (Python Core)',
 'menuGroup': 'Descriptives Py', 'menuSubgroup': 'Contingency tables', 'version': '0.3.42',
 'options': [
  {'name':'vars','title':'Summary variables','type':'Variables','permitted':['numeric','factor'],'required':True},
  {'name':'group','title':'Grouping variable','type':'Variable','permitted':['factor'],'suggested':['nominal','ordinal'],'required':True},
  {'name':'excl','title':'Complete-case exclusion across selected variables','type':'Bool','default':False},
  {'name':'cont','title':'Continuous summary','type':'List','options':[
   {'name':'mean','title':'Mean and sample SD'},{'name':'median','title':'Median and quartiles'}],'default':'mean'},
  {'name':'pcat','title':'Categorical comparison','type':'List','options':[
   {'name':'chisq','title':'Pearson; switch to exact for sparse cells'},
   {'name':'fisher','title':'Exact Fisher (2×2 supported)'}],'default':'chisq'},
  {'name':'p_adjust','title':'Multiplicity across available variable tests','type':'List','options':[
   {'name':'none','title':'None'},{'name':'bonferroni','title':'Bonferroni'},
   {'name':'holm','title':'Holm'},{'name':'BH','title':'Benjamini–Hochberg'},
   {'name':'BY','title':'Benjamini–Yekutieli'}],'default':'none'},
  {'name':'numericMode','title':'Numeric variable typing','type':'List','options':[
   {'name':'auto','title':'Baseline: ≤6 distinct numeric values are categorical'},
   {'name':'continuous','title':'Keep all numeric variables continuous'}],'default':'auto'},
  {'name':'showTyping','title':'Variable typing and completeness','type':'Bool','default':False},
  {'name':'showTestDetails','title':'Test sample sizes and statistics','type':'Bool','default':False}],
 'results': [
  {'name':'summary','title':'Cohort, Denominators and Methods','type':'Text'},
  {'name':'cohort','title':'Retained Cohort','type':'Table','columns':[
   {'name':'scope','title':'Scope','type':'text'},{'name':'group','title':'Group','type':'text'},
   {'name':'n','title':'Rows','type':'integer'},{'name':'percent','title':'Retained (%)','type':'number','format':'pc'}]},
  {'name':'continuous','title':'Continuous Summaries','type':'Table','columns':[
   {'name':'variable','title':'Variable','type':'text'},{'name':'scope','title':'Scope','type':'text'},
   {'name':'group','title':'Group','type':'text'},{'name':'n','title':'Valid','type':'integer'},
   {'name':'missing','title':'Missing','type':'integer'},
   {'name':'mean','title':'Mean','type':'number','visible':'(cont:mean)'},
   {'name':'sd','title':'SD','type':'number','visible':'(cont:mean)'},
   {'name':'median','title':'Median','type':'number','visible':'(cont:median)'},
   {'name':'q1','title':'Q1','type':'number','visible':'(cont:median)'},
   {'name':'q3','title':'Q3','type':'number','visible':'(cont:median)'}]},
  {'name':'categories','title':'Categorical Counts and Valid Percentages','type':'Table','columns':[
   {'name':'variable','title':'Variable','type':'text'},{'name':'scope','title':'Scope','type':'text'},
   {'name':'group','title':'Group','type':'text'},{'name':'level','title':'Category','type':'text'},
   {'name':'n','title':'Count','type':'integer'},{'name':'valid','title':'Valid N','type':'integer'},
   {'name':'percent','title':'Valid (%)','type':'number','format':'pc'}]},
  {'name':'tests','title':'Independent Group Comparisons','type':'Table','columns':[
   {'name':'variable','title':'Variable','type':'text'},
   {'name':'n','title':'Test N','type':'integer','visible':'(showTestDetails)'},
   {'name':'groups','title':'Groups','type':'integer','visible':'(showTestDetails)'},
   {'name':'method','title':'Method','type':'text'},
   {'name':'statistic','title':'Statistic','type':'number','visible':'(showTestDetails)'},
   {'name':'df','title':'df','type':'number','visible':'(showTestDetails)'},
   {'name':'p','title':'p','type':'number','format':'zto,pvalue'},
   {'name':'adjusted','title':'Adjusted p','type':'number','format':'zto,pvalue'},
   {'name':'reason','title':'Unavailable Reason','type':'text'}]},
  {'name':'typing','title':'Variable Typing and Completeness','type':'Table','visible':'(showTyping)','columns':[
   {'name':'variable','title':'Variable','type':'text'},{'name':'kind','title':'Type','type':'text'},
   {'name':'rule','title':'Rule','type':'text'},{'name':'valid','title':'Valid','type':'integer'},
   {'name':'missing','title':'Missing','type':'integer'}]}],
 'ui': {'children': [
  {'type':'VariableSupplier','persistentItems':False,'stretchFactor':1,'children':[
   {'type':'TargetLayoutBox','label':'Summary variables','children':[{'type':'VariablesListBox','name':'vars','isTarget':True}]},
   {'type':'TargetLayoutBox','label':'Grouping variable','children':[{'type':'VariablesListBox','name':'group','maxItemCount':1,'isTarget':True}]}]},
  {'type':'CollapseBox','label':'Analysis and Cohort','collapsed':False,'children':[
   {'type':'ComboBox','name':'cont'},{'type':'ComboBox','name':'pcat'},{'type':'CheckBox','name':'excl'}]},
  {'type':'CollapseBox','label':'Uncertainty and Validation','collapsed':False,'children':[{'type':'ComboBox','name':'p_adjust'}]},
  {'type':'CollapseBox','label':'Results and Interpretation','collapsed':True,'children':[
   {'type':'CheckBox','name':'showTyping'},{'type':'CheckBox','name':'showTestDetails'}]},
  {'type':'CollapseBox','label':'Advanced Settings','collapsed':True,'children':[
   {'type':'ComboBox','name':'numericMode'},{'type':'CheckBox','name':'showConsole'}]}]}}


def run(data, options, out):
    r = calculate(data, options)
    for table in ('cohort','continuous','categories','tests','typing'):
        for row in r[table]: out.row(table, **row)
    if not r['continuous']:
        out.note('continuous','No continuous variables under the selected typing rule; inspect variable typing or retain numeric variables as continuous.')
    if not r['categories']:
        out.note('categories','No categorical summary variables under the selected typing rule.')
    unavailable = [row['variable'] for row in r['tests'] if row['p'] is None]
    if unavailable:
        out.warn('No p-value for '+', '.join(unavailable)+'. Read the reason in the comparison table; no substitute method was used.')
    if any(row['rule'].startswith('Numeric ≤6') for row in r['typing']):
        out.info('The baseline typing rule treats numeric variables with at most six distinct values as categorical. Inspect variable typing; Advanced Settings can keep numeric variables continuous.')
    if r['excluded']:
        out.info(f"Excluded {r['excluded']} of {r['total']} input rows; {r['missingGroup']} have missing grouping values.")
    out.markdown('summary', md_escape(
        f"Input rows: {r['total']}; retained: {r['retained']}; excluded: {r['excluded']}; missing group: {r['missingGroup']}. "
        +('One common complete-case cohort is used across all selected variables. ' if options.get('excl',False)
          else 'Missing grouping values are excluded; other missing values are handled separately within each variable. ')
        +'Overall summaries use the same retained cohort as the groups. Categorical percentages divide recorded category counts by valid variable values within each stratum; missing counts are listed without percentages. '
        'Factor categories retain declared order, including zero-count levels; unused grouping levels are omitted. Scope distinguishes Overall from any identically named group. '
        'Means use sample SD; quartiles use R type 7. The continuous display choice does not change tests: Wilcoxon rank-sum for two groups, Kruskal–Wallis for three or more. '
        'Wilcoxon follows R 4.6: exact two-sided inference with both sample sizes below 50, including the conditional rank distribution with ties; otherwise a tie- and continuity-corrected normal approximation. Its statistic is U for the first displayed group. '
        'Categorical comparisons use uncorrected Pearson chi-square only when every expected cell is at least 5; otherwise exact Fisher is requested. Only exact 2×2 tables are implemented; larger exact tables remain unavailable. '
        f"Adjustment: {options.get('p_adjust','none')}; family size: {r['testFamily']} available variable-level tests, excluding unavailable p-values as in base R p.adjust. "
        'Tests assume independent observations; repeated patients, paired data and weights are not modeled. This core supports the default-style subset, not other table engines/styles, SMDs or full gtsummary parity.'))
