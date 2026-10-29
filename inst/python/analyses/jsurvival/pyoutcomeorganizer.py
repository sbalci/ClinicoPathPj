"""Explicit outcome coding with native audit tables and row-aligned saved status."""
from cpj_runtime import md_escape
from cpj_outcomes import calculate

SPEC = {
 'name':'pyoutcomeorganizer','title':'Outcome Organizer (Python Core)',
 'clearOnInputError':True,
 'menuGroup':'Survival Py','menuSubgroup':'Data preparation','version':'0.3.44',
 'options':[
  {'name':'outcome','title':'Outcome variable','type':'Variable','permitted':['factor','numeric'],'required':True},
  {'name':'outcomeLevel','title':'Event level (single-event coding)','type':'Level','variable':'(outcome)','optional':True},
  {'name':'analysistype','title':'Outcome preparation type','type':'List','options':[
   {'name':'os','title':'Single event / overall survival'},
   {'name':'cause','title':'Cause-specific survival'},
   {'name':'compete','title':'Competing risks'},
   {'name':'multistate','title':'Multistate status'}],'default':'os'},
  {'name':'multievent','title':'Multiple event levels','type':'Bool','default':False},
  {'name':'dod','title':'Dead of disease','type':'Level','variable':'(outcome)','optional':True},
  {'name':'dooc','title':'Dead of other causes','type':'Level','variable':'(outcome)','optional':True},
  {'name':'awd','title':'Alive with disease','type':'Level','variable':'(outcome)','optional':True},
  {'name':'awod','title':'Alive without disease','type':'Level','variable':'(outcome)','optional':True},
  {'name':'diagnostics','title':'Source-row preview','type':'Bool','default':False},
  {'name':'visualization','title':'Outcome distribution','type':'Bool','default':False},
  {'name':'showNaturalSummary','title':'Descriptive report','type':'Bool','default':False},
  {'name':'addOutcome','title':'Recoded outcome','type':'Output'}],
 'results':[
  {'name':'summary','title':'Coding Scope','type':'Text'},
  {'name':'cohort','title':'Row Accounting','type':'Table','columns':[
   {'name':'input','title':'Input Rows','type':'integer'},
   {'name':'valid','title':'Coded Rows','type':'integer'},
   {'name':'missing','title':'Missing Outcome','type':'integer'}]},
  {'name':'mapping','title':'Explicit Outcome Mapping','type':'Table','columns':[
   {'name':'level','title':'Original Level','type':'text'},
   {'name':'category','title':'Meaning','type':'text'},
   {'name':'code','title':'Status Code','type':'integer'},
   {'name':'n','title':'Input Count','type':'integer'}]},
  {'name':'frequencies','title':'Recoded Outcome Distribution','type':'Table','columns':[
   {'name':'code','title':'Status Code','type':'integer'},
   {'name':'label','title':'Meaning','type':'text'},
   {'name':'n','title':'Count','type':'integer'},
   {'name':'percent','title':'Coded Rows (%)','type':'number','format':'pc'}]},
  {'name':'preview','title':'Source-Row Preview (First 100 Rows)','type':'Table','visible':'(diagnostics)','columns':[
   {'name':'source','title':'Source Row ID','type':'text'},
   {'name':'code','title':'Status Code','type':'integer'}]},
  {'name':'report','title':'Descriptive Report','type':'Text','visible':'(showNaturalSummary)'},
  {'name':'distribution','title':'Recoded Outcome Counts','type':'Image','plot':'bar','width':800,'height':500,'visible':'(visualization)'},
  {'name':'addOutcome','title':'Recoded Outcome','type':'Output','varTitle':'Recoded survival outcome',
   'varDescription':'Explicit row-wise outcome coding; inspect the native mapping before downstream use','measureType':'nominal'}],
 'ui':{'children':[
  {'type':'VariableSupplier','persistentItems':False,'stretchFactor':1,'children':[
   {'type':'TargetLayoutBox','label':'Outcome variable','children':[{'type':'VariablesListBox','name':'outcome','maxItemCount':1,'isTarget':True}]},
   {'type':'LevelSelector','name':'outcomeLevel','enable':'(!multievent)'},
   {'type':'LevelSelector','name':'dod','enable':'(multievent)'},
   {'type':'LevelSelector','name':'dooc','enable':'(multievent)'},
   {'type':'LevelSelector','name':'awd','enable':'(multievent)'},
   {'type':'LevelSelector','name':'awod','enable':'(multievent)'}]},
  {'type':'CollapseBox','label':'Outcome Definition','collapsed':False,'children':[
   {'type':'ComboBox','name':'analysistype'},{'type':'CheckBox','name':'multievent'}]},
  {'type':'CollapseBox','label':'Results and Interpretation','collapsed':False,'children':[
   {'type':'CheckBox','name':'diagnostics'},{'type':'CheckBox','name':'showNaturalSummary'}]},
  {'type':'CollapseBox','label':'Plots','collapsed':True,'children':[{'type':'CheckBox','name':'visualization'}]},
  {'type':'CollapseBox','label':'Save and Export','collapsed':False,'children':[{'type':'Output','name':'addOutcome'}]},
  {'type':'CollapseBox','label':'Advanced Settings','collapsed':True,'children':[{'type':'CheckBox','name':'showConsole'}]}]}}


def run(data, options, out):
    r = calculate(data,options)
    if r['pending']:
        out.info(r['pending']);out.markdown('summary',md_escape(r['pending']));return
    out.row('cohort',input=r['total'],valid=r['valid'],missing=r['missing'])
    for row in r['mapping']: out.row('mapping',**row)
    for row in r['counts']: out.row('frequencies',**row)
    if options.get('diagnostics',False):
        ids = out.row_ids if out.row_ids is not None else [str(i+1) for i in range(r['total'])]
        for source,code in list(zip(ids,r['status']))[:100]:out.row('preview',source=source,code=code)
        if r['total']>100:out.info('The preview shows the first 100 source rows; summaries and saved output use every supplied row.')
    if options.get('visualization',False):
        out.plot('distribution',[dict(label=row['label'],value=row['n'],group='Coded rows') for row in r['counts']],xlab='Outcome code',ylab='Supplied rows')
    if out.row_ids is not None:
        out.column('addOutcome',r['status'],levels=r['levels'],measure_type='nominal',
                   title='Recoded survival outcome',description='Status coding: '+', '.join(f"{v['code']}={v['label']}" for v in r['counts']))
    for warning in r['warnings']:out.warn(warning)
    out.markdown('summary',md_escape(
        f"Input rows: {r['total']}; coded: {r['valid']}; missing outcome: {r['missing']}. Coding route: {r['mode']}. "
        'Missing outcomes remain missing; no row is dropped or converted to censoring. Percentages use coded rows. '
        'The original row identities and order are retained in saved output. Rows are supplied records, not deduplicated patients. '
        'This core recodes status only; it does not validate event times, follow-up origins, transition histories or independent censoring. '
        'Recurrence composites, patient hierarchies, interval/administrative censoring and survival estimation are not implemented. '
        'A multistate status snapshot is not a multistate event-history dataset. Review the mapping and pair it with appropriate times before downstream analysis.'))
    if options.get('showNaturalSummary',False):
        description='; '.join(f"code {row['code']} ({row['label']}): {row['n']}" for row in r['counts'])
        out.markdown('report',md_escape(f"Outcome status was prepared for {r['valid']} coded records out of {r['total']} supplied rows, with {r['missing']} missing outcomes. {description}. These descriptive counts are not survival or cumulative-incidence estimates."))
