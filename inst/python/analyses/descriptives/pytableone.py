"""Standard overall-cohort Table One, rendered as native jamovi tables."""
from cpj_runtime import md_escape
from cpj_tableone import calculate

SPEC = {
 'name':'pytableone','title':'Table One (Python Core)',
 'menuGroup':'Descriptives Py','menuSubgroup':'Summaries','version':'0.3.43',
 'options':[
  {'name':'vars','title':'Variables','type':'Variables','permitted':['numeric','factor','id'],'required':True},
  {'name':'cont','title':'Continuous summary','type':'List','options':[
   {'name':'mean','title':'Mean and sample SD'},{'name':'median','title':'Median and quartiles'}],'default':'mean'},
  {'name':'excl','title':'Complete-case exclusion across included variables','type':'Bool','default':False},
  {'name':'showAllLevels','title':'All levels of binary categories','type':'Bool','default':False},
  {'name':'showSummary','title':'Input completeness and variable eligibility','type':'Bool','default':False},
  {'name':'showAbout','title':'Method explanation','type':'Bool','default':False},
  {'name':'showReportSentence','title':'Copy-ready descriptive report','type':'Bool','default':False}],
 'results':[
  {'name':'summary','title':'Table One Scope and Denominators','type':'Text'},
  {'name':'cohort','title':'Cohort Accounting','type':'Table','columns':[
   {'name':'input','title':'Input Rows','type':'integer'},
   {'name':'included','title':'Included Variables','type':'integer'},
   {'name':'omitted','title':'Omitted Variables','type':'integer'},
   {'name':'complete','title':'Complete Before Exclusion','type':'integer'},
   {'name':'retained','title':'Retained Rows','type':'integer'},
   {'name':'excluded','title':'Excluded Rows','type':'integer'}]},
  {'name':'continuous','title':'Overall Continuous Summaries','type':'Table','columns':[
   {'name':'variable','title':'Variable','type':'text'},
   {'name':'valid','title':'Valid','type':'integer'},
   {'name':'missing','title':'Missing','type':'integer'},
   {'name':'missingPercent','title':'Missing (%)','type':'number','format':'pc'},
   {'name':'mean','title':'Mean','type':'number','visible':'(cont:mean)'},
   {'name':'sd','title':'SD','type':'number','visible':'(cont:mean)'},
   {'name':'median','title':'Median','type':'number','visible':'(cont:median)'},
   {'name':'q1','title':'Q1','type':'number','visible':'(cont:median)'},
   {'name':'q3','title':'Q3','type':'number','visible':'(cont:median)'}]},
  {'name':'categories','title':'Overall Categorical Summaries','type':'Table','columns':[
   {'name':'variable','title':'Variable','type':'text'},
   {'name':'level','title':'Counted Level','type':'text'},
   {'name':'n','title':'Count','type':'integer'},
   {'name':'valid','title':'Valid N','type':'integer'},
   {'name':'percent','title':'Valid (%)','type':'number','format':'pc'},
   {'name':'missing','title':'Missing','type':'integer'},
   {'name':'missingPercent','title':'Missing (%)','type':'number','format':'pc'}]},
  {'name':'eligibility','title':'Input Completeness and Variable Eligibility','type':'Table','visible':'(showSummary)','columns':[
   {'name':'variable','title':'Variable','type':'text'},
   {'name':'kind','title':'Type','type':'text'},
   {'name':'status','title':'Status','type':'text'},
   {'name':'inputValid','title':'Input Valid','type':'integer'},
   {'name':'inputMissing','title':'Input Missing','type':'integer'},
   {'name':'units','title':'Units','type':'text'},
   {'name':'label','title':'Variable Label','type':'text'}]},
  {'name':'about','title':'Method Explanation','type':'Text','visible':'(showAbout)'},
  {'name':'report','title':'Copy-Ready Descriptive Report','type':'Text','visible':'(showReportSentence)'}],
 'ui':{'children':[
  {'type':'VariableSupplier','persistentItems':False,'stretchFactor':1,'children':[
   {'type':'TargetLayoutBox','label':'Variables','children':[{'type':'VariablesListBox','name':'vars','isTarget':True}]}]},
  {'type':'CollapseBox','label':'Analysis and Cohort','collapsed':False,'children':[
   {'type':'ComboBox','name':'cont'},{'type':'CheckBox','name':'excl'}]},
  {'type':'CollapseBox','label':'Results and Interpretation','collapsed':False,'children':[
   {'type':'CheckBox','name':'showAllLevels'},{'type':'CheckBox','name':'showSummary'},
   {'type':'CheckBox','name':'showReportSentence'},{'type':'CheckBox','name':'showAbout'}]},
  {'type':'CollapseBox','label':'Advanced Settings','collapsed':True,'children':[{'type':'CheckBox','name':'showConsole'}]}]}}


def run(data, options, out):
    r = calculate(data, options)
    out.row('cohort',input=r['total'],included=r['included'],omitted=r['omitted'],
            complete=r['completeBefore'],retained=r['retained'],excluded=r['excluded'])
    for table in ('continuous','categories','eligibility'):
        for row in r[table]:out.row(table,**row)
    omitted = [v['variable']+': '+v['status'] for v in r['eligibility'] if v['status']!='Included']
    if omitted:out.info('Not included: '+'; '.join(omitted)+'. Omitted variables do not enter complete-case exclusion.')
    if r['reason']:
        out.info(r['reason']);out.markdown('summary',md_escape(r['reason']))
        if options.get('showReportSentence',False):out.markdown('report','No descriptive report was produced because no eligible analysis cohort remains.')
    else:
        out.markdown('summary',md_escape(
            f"Input rows: {r['total']}; retained: {r['retained']}; excluded: {r['excluded']}; included variables: {r['included']}; omitted variables: {r['omitted']}. "
            +('A common complete-case cohort is used across included variables. ' if options.get('excl',False)
              else 'Each variable uses its own recorded values within all supplied rows. ')
            +'All-missing and unsupported scalar classes are omitted before exclusion. Categorical percentages divide counts by valid variable values; missing percentages divide missing n by retained rows. '
            +('All declared categorical levels are displayed. ' if options.get('showAllLevels',False)
              else 'Binary factors display only their second declared level, named explicitly; other categories display every declared level. ')
            +'Unused declared factor levels retain zero counts. Numeric variables remain measurements even with few distinct values. Text/logical categories use deterministic lexical order; use factors for an explicit level order. '
            'This overall-cohort standard-format core computes no p-values, confidence intervals, group comparisons or SMDs. Rows represent supplied records, not deduplicated patients. Other table engines/styles, frequency weights and full baseline parity are not implemented.'))
        if options.get('showReportSentence',False):
            out.markdown('report',md_escape(
                f"Descriptive summaries were prepared for {r['retained']} retained records and {r['included']} included variables; {r['excluded']} records were excluded. "
                +('Continuous variables are reported as mean and sample SD. ' if options.get('cont','mean')=='mean'
                  else 'Continuous variables are reported as median and first/third quartiles. ')
                +'Categorical counts use valid-value denominators, with missingness reported separately. The table is descriptive and does not establish the number of unique patients.'))
    if options.get('showAbout',False):
        out.markdown('about','Standard Table One describes an overall cohort. Mean/SD and median/quartiles are display choices, without inference. Quartiles use R type 7 and SD uses n−1; singleton SD is undefined. A binary row names the level being counted. Input completeness is measured before optional exclusion. Dates, durations and custom scalar classes require explicit conversion. Matrix, array and list columns are rejected. Units and variable-label annotations are retained when supplied by the bridge; no automatic unit conversion, weighting or patient deduplication is performed.')
