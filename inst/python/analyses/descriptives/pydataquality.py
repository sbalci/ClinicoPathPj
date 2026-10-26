"""Multi-variable quality accounting with native exports and local missingness inspection."""
import json
import uuid
from pathlib import Path
import numpy as np
from cpj_runtime import md_escape
from cpj_quality import profile, duplicate_rows, preview

SPEC = {
 'name':'pydataquality','title':'Multi-Variable Visual Quality','menuGroup':'Descriptives Py',
 'menuSubgroup':'Data quality','version':'0.3.3',
 'options':[
  {'name':'vars','title':'Variables','type':'Variables','required':True},
  {'name':'check_duplicates','title':'Duplicate values','type':'Bool','default':False},
  {'name':'check_missing','title':'Missing value analysis','type':'Bool','default':False},
  {'name':'row_level_duplicates','title':'Duplicate rows','type':'Bool','default':False},
  {'name':'plot_data_overview','title':'Data overview plot','type':'Bool','default':False},
  {'name':'plot_missing_patterns','title':'Missing patterns plot','type':'Bool','default':False},
  {'name':'plot_data_types','title':'Declared data types plot','type':'Bool','default':False},
  {'name':'missing_threshold_visual','title':'Missing-data flag threshold (percent)','type':'Number','min':0,'max':100,'default':10},
  {'name':'showSummary','title':'Plain-language summary','type':'Bool','default':True},
  {'name':'showRecommendations','title':'Action recommendations','type':'Bool','default':True},
  {'name':'showExplanations','title':'Educational explanations','type':'Bool','default':False},
  {'name':'showInteractive','title':'Interactive missingness preview and static counterpart','type':'Bool','default':False}],
 'results':[
  {'name':'overview','title':'Variable Quality Profile','type':'Table','columns':[
   {'name':'variable','title':'Variable','type':'text'},{'name':'kind','title':'Declared Type','type':'text'},
   {'name':'n','title':'Rows','type':'integer'},{'name':'valid','title':'Observed','type':'integer'},
   {'name':'missing','title':'Missing','type':'integer'},{'name':'missingRate','title':'Missing (%)','type':'number','format':'pc'},
   {'name':'unique','title':'Distinct Observed','type':'integer'},{'name':'repeats','title':'Excess Repeated Values','type':'integer'},
   {'name':'repeatRate','title':'Repeated (%) of Observed','type':'number','format':'pc'},
   {'name':'constant','title':'Constant','type':'text'},{'name':'highCardinality','title':'High Cardinality','type':'text'},
   {'name':'aboveThreshold','title':'Above Missing Threshold','type':'text'},
   {'name':'outliers','title':'IQR Flags','type':'integer'},{'name':'outlierRate','title':'IQR Flags (%) of Observed','type':'number','format':'pc'}]},
  {'name':'completeness','title':'Cohort Completeness','type':'Table','columns':[
   {'name':'rows','title':'Rows','type':'integer'},{'name':'variables','title':'Variables','type':'integer'},
   {'name':'complete','title':'Complete Rows','type':'integer'},{'name':'completeRate','title':'Complete (%)','type':'number','format':'pc'},
   {'name':'cells','title':'Cells','type':'integer'},{'name':'missing','title':'Missing Cells','type':'integer'},
   {'name':'missingRate','title':'Missing Cells (%)','type':'number','format':'pc'}]},
  {'name':'rowMissing','title':'Missing Variables per Row','type':'Table','visible':'(check_missing)','columns':[
   {'name':'missing','title':'Missing Variables','type':'integer'},{'name':'n','title':'Rows','type':'integer'},
   {'name':'percent','title':'Rows (%)','type':'number','format':'pc'}]},
  {'name':'duplicates','title':'Duplicate Accounting','type':'Table','visible':'(check_duplicates)','columns':[
   {'name':'unit','title':'Counting Unit','type':'text'},{'name':'total','title':'Denominator','type':'integer'},
   {'name':'unique','title':'Distinct','type':'integer'},{'name':'excess','title':'Excess Repeats','type':'integer'},
   {'name':'rate','title':'Excess (%)','type':'number','format':'pc'}]},
  {'name':'duplicatePatterns','title':'Top Five Repeated Row Groups','type':'Table','visible':'(check_duplicates)','columns':[
   {'name':'firstRow','title':'First Original Row','type':'text'},{'name':'n','title':'Occurrences','type':'integer'},
   {'name':'excess','title':'Excess Repeats','type':'integer'}]},
  {'name':'summary','title':'Plain-Language Summary','type':'Text','visible':'(showSummary)'},
  {'name':'recommendations','title':'Recommended Actions','type':'Text','visible':'(showRecommendations)'},
  {'name':'explanations','title':'Understanding Quality Metrics','type':'Text','visible':'(showExplanations)'},
  {'name':'scope','title':'Display Scope and Assumptions','type':'Text'},
  {'name':'overviewMap','title':'Data Overview','type':'Image','plot':'qualitymap','width':800,'height':550,'visible':'(plot_data_overview)'},
  {'name':'missingMap','title':'Missing Patterns','type':'Image','plot':'qualitymap','width':800,'height':550,'visible':'(plot_missing_patterns)'},
  {'name':'typePlot','title':'Declared Variable Types','type':'Image','plot':'bar','width':600,'height':400,'visible':'(plot_data_types)'},
  {'name':'explorer','title':'Interactive Missingness Preview','type':'Html','visible':'(showInteractive)'},
  {'name':'previewMap','title':'Missingness Preview Static Counterpart','type':'Image','plot':'qualitymap','width':800,'height':550,'visible':'(showInteractive)'}],
 'ui':{'children':[
  {'type':'VariableSupplier','persistentItems':False,'stretchFactor':1,'children':[
   {'type':'TargetLayoutBox','label':'Variables','children':[{'type':'VariablesListBox','name':'vars','isTarget':True}]}]},
  {'type':'CollapseBox','label':'Quality Checks','collapsed':False,'children':[
   {'type':'CheckBox','name':'check_missing'},
   {'type':'TextBox','name':'missing_threshold_visual','format':'number'},
   {'type':'CheckBox','name':'check_duplicates'},
   {'type':'CheckBox','name':'row_level_duplicates','enable':'(check_duplicates)'}]},
  {'type':'CollapseBox','label':'Results and Interpretation','collapsed':True,'children':[
   {'type':'CheckBox','name':'showSummary'},{'type':'CheckBox','name':'showRecommendations'},
   {'type':'CheckBox','name':'showExplanations'}]},
  {'type':'CollapseBox','label':'Plots and Interaction','collapsed':True,'children':[
   {'type':'CheckBox','name':'plot_data_overview'},{'type':'CheckBox','name':'plot_missing_patterns'},
   {'type':'CheckBox','name':'plot_data_types'},{'type':'CheckBox','name':'showInteractive'}]},
  {'type':'CollapseBox','label':'Advanced Settings','collapsed':True,'children':[{'type':'CheckBox','name':'showConsole'}]}]}}


def html_document(payload):
 encoded=json.dumps(payload,allow_nan=False,ensure_ascii=True)
 for char,safe in (('<','\\u003c'),('>','\\u003e'),('&','\\u0026')):encoded=encoded.replace(char,safe)
 template=(Path(__file__).resolve().parents[2]/'templates'/'quality.html').read_text()
 return template.replace('__ROOT__','cpjquality'+uuid.uuid4().hex).replace('__PAYLOAD__',encoded)


def run(data,options,out):
 names=options.get('vars') or []
 r=profile({name:data[name] for name in names},options.get('missing_threshold_visual',10))
 n,p=r['n'],r['p'];high=[];constant=[]
 for row in r['summaries']:
  out.row('overview',**{k:('Yes' if v else 'No') if isinstance(v,(bool,np.bool_)) else v for k,v in row.items()})
  if row['aboveThreshold']:high.append(row['variable'])
  if row['constant']:constant.append(row['variable'])
  if row['missingRate']>.5:out.warn(f'{row["variable"]}: more than 50% of values are missing.')
  if row['constant']:out.warn(f'{row["variable"]}: one distinct observed value (constant).')
  if row['highCardinality']:out.warn(f'{row["variable"]}: more than 50 distinct values and more than half of observed values are unique; review whether this is an identifier.')
 out.row('completeness',rows=n,variables=p,complete=r['complete'],completeRate=r['complete']/n,
  cells=n*p,missing=r['missingCells'],missingRate=r['missingCells']/(n*p))
 out.note('overview','Excess repeated values = observed minus distinct observed; missing values are excluded from that count. Constants have one distinct observed value. IQR flags use 1.5 x IQR only above 10 observed numeric values; zero IQR gives zero flags, matching the frozen baseline. Unavailable cells are not zero.')
 if options.get('check_missing'):
  for count in np.unique(r['rowMissing']):
   rows=int(np.sum(r['rowMissing']==count));out.row('rowMissing',missing=int(count),n=rows,percent=rows/n)
  out.note('rowMissing','Counts use all selected variables and all input rows. No formal MCAR test is implemented in this Python core; missingness patterns cannot establish the missingness mechanism.')
 if options.get('check_duplicates'):
  if options.get('row_level_duplicates') and p>1:
   dup=duplicate_rows(r['codes'])
   out.row('duplicates',unit='Rows across selected variables',total=n,unique=dup['unique'],excess=dup['excess'],rate=dup['excess']/n)
   for first,count in dup['patterns']:
    out.row('duplicatePatterns',firstRow=str(out.row_ids[first] if out.row_ids is not None else first+1),n=count,excess=count-1)
   out.note('duplicatePatterns',f'{dup["groups"]} repeated row groups in total; at most five are shown, ordered by frequency then first occurrence. Only original row IDs and counts are shown; examine source records before deciding whether any are erroneous.')
  else:
   if options.get('row_level_duplicates'):out.info('One variable selected: row-level mode falls back to observed-value duplicates, matching the baseline. Missing values are excluded from this count.')
   for row in r['summaries']:
    out.row('duplicates',unit=row['variable'],total=row['valid'],unique=row['unique'],excess=row['repeats'],rate=row['repeatRate'])
  out.note('duplicates','Excess repeats count occurrences after the first, not all members of repeated groups. Row-level mode includes equal missing-value patterns; observed-value mode excludes missing values. Repeated categories are often valid and do not imply duplicate patients.')
 if n<20:out.warn('Fewer than 20 input rows: quality summaries describe a small dataset.')
 if options.get('showSummary',True):
  out.markdown('summary',md_escape(f'{n} rows and {p} selected variables; {r["complete"]} complete rows ({100*r["complete"]/n:.1f}%). {r["missingCells"]} of {n*p} cells are missing. {len(high)} variables exceed the entered missing-data threshold; {len(constant)} are constant. These are descriptive screening counts, not a validated quality grade.'))
 if options.get('showRecommendations',True):
  advice=[]
  if high:advice.append('Review missing-data sources and potential selection bias for: '+', '.join(high)+'. Do not infer MCAR, MAR or MNAR from these summaries.')
  if constant:advice.append('Confirm coding and intended scope of constant variables: '+', '.join(constant)+'.')
  if options.get('check_duplicates'):advice.append('Review identifiers and repeated measurements before deleting any repeated record; equal selected values do not establish duplicate patients.')
  advice.append('Document the observation unit, missing-data handling and any corrections. No imputation, exclusion or data editing is performed.')
  out.markdown('recommendations','\n\n'.join(md_escape(a) for a in advice))
 if options.get('showExplanations'):
  out.markdown('explanations','Completeness uses all selected variables. A missing-data flag is raised only when the unrounded missing proportion is strictly above the entered threshold. Distinct values exclude missing codes; literal text such as NA remains observed. A constant is exactly one observed value, not a near-zero-variance test. Numeric IQR flags are exploratory and observations are never removed. Declared transport types are shown; parsing-based type guessing and Little\'s MCAR inference are outside this core.')
 display=any(options.get(k) for k in ('plot_data_overview','plot_missing_patterns','showInteractive'))
 scope='Full-data tables use every input row and selected variable. One row should represent the intended observation unit. No independence-based inferential test is performed.'
 if display:
  payload=preview(r,names,out.row_ids);nr=len(payload['row_ids']);nc=len(payload['variables'])
  scope+=f' Maps and interactive preview show the first {nr} of {n} rows and first {nc} of {p} variables in selection order. This is a bounded display, not random sampling; omitted cells do not affect the tables.'
  maps=[];overview=[]
  for i,row_id in enumerate(payload['row_ids']):
   for j,name in enumerate(payload['variables']):
    missing=bool(payload['missing'][i][j]);maps.append(dict(variable=name,row=row_id,state='Missing' if missing else 'Observed'))
    overview.append(dict(variable=name,row=row_id,state='Missing' if missing else r['summaries'][j]['kind']))
  if options.get('plot_missing_patterns'):out.plot('missingMap',maps,xlab='Variable',ylab='Original row')
  if options.get('plot_data_overview'):out.plot('overviewMap',overview,xlab='Variable',ylab='Original row')
  if options.get('showInteractive'):
   out.html('explorer',html_document(payload));out.plot('previewMap',maps,xlab='Variable',ylab='Original row')
 if options.get('plot_data_types'):
  kinds=[row['kind'] for row in r['summaries']]
  out.plot('typePlot',[dict(label=kind,value=kinds.count(kind),group='Variables') for kind in dict.fromkeys(kinds)],xlab='Declared type',ylab='Variables')
 out.markdown('scope',md_escape(scope))
