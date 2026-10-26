"""Preview interval categories and explicitly save an ordered/nominal categorical column."""
import json
import numpy as np
from cpj_runtime import InputError, md_escape
from cpj_descriptive import numeric
from cpj_binning import make_breaks, labels_for, interval_labels, assign

SPEC = {
 'name':'pycategorize','title':'Categorize Continuous Variables','menuGroup':'Descriptives Py',
 'menuSubgroup':'Transformations','version':'0.3.11',
 'options':[
  {'name':'var','title':'Variable to categorize','type':'Variable','permitted':['numeric'],'suggested':['continuous'],'required':True},
  {'name':'method','title':'Binning method','type':'List','default':'quantile','options':[
   {'name':'equal','title':'Equal intervals'},{'name':'quantile','title':'Quantiles'},
   {'name':'manual','title':'Manual break points'},{'name':'meansd','title':'Mean +/- SD'},
   {'name':'median','title':'Median split'},{'name':'jenks','title':'Natural breaks (Fisher-Jenks)'}]},
  {'name':'nbins','title':'Number of categories','type':'Integer','min':2,'max':20,'default':4},
  {'name':'breaks','title':'Manual break points (comma separated)','type':'String','default':''},
  {'name':'sdmult','title':'SD multiplier','type':'Number','min':.5,'max':3,'default':1},
  {'name':'seed','title':'Subsampling seed','type':'Integer','min':-2147483647,'max':2147483647,'default':20240101},
  {'name':'labels','title':'Category labels','type':'List','default':'auto','options':[
   {'name':'auto','title':'Numeric ranges'},{'name':'semantic','title':'Low / medium / high'},
   {'name':'numbered','title':'Numbers'},{'name':'lettered','title':'Letters'},{'name':'custom','title':'Custom labels'}]},
  {'name':'customlabels','title':'Custom labels (comma separated)','type':'String','default':''},
  {'name':'newvarname','title':'New variable name (blank = source_cat)','type':'String','default':''},
  {'name':'addtodata','title':'Categorized variable','type':'Output'},
  {'name':'excludeoutofrange','title':'Keep manual bounds and exclude outside values','type':'Bool','default':False},
  {'name':'includelowest','title':'Include the open outer endpoint','type':'Bool','default':True},
  {'name':'rightclosed','title':'Right-closed intervals','type':'Bool','default':True},
  {'name':'ordered','title':'Ordered factor','type':'Bool','default':True},
  {'name':'excl','title':'Percentages exclude missing and uncategorized rows','type':'Bool','default':True},
  {'name':'showcode','title':'R code using displayed break points','type':'Bool','default':True},
  {'name':'showplot','title':'Category distribution','type':'Bool','default':True},
  {'name':'showhistogram','title':'Continuous histogram with break points','type':'Bool','default':False}],
 'results':[
  {'name':'summary','title':'Variable Summary','type':'Table','columns':[
   {'name':'variable','title':'Variable','type':'text'},{'name':'total','title':'Total Rows','type':'integer'},
   {'name':'observed','title':'Observed','type':'integer'},{'name':'missing','title':'Missing','type':'integer'},
   {'name':'categorized','title':'Categorized','type':'integer'},{'name':'uncategorized','title':'Uncategorized','type':'integer'},
   {'name':'mean','title':'Mean','type':'number'},{'name':'sd','title':'SD','type':'number'},
   {'name':'minimum','title':'Minimum','type':'number'},{'name':'maximum','title':'Maximum','type':'number'}]},
  {'name':'freqTable','title':'Category Frequencies','type':'Table','columns':[
   {'name':'category','title':'Category','type':'text'},{'name':'range','title':'Range','type':'text'},
   {'name':'n','title':'Count','type':'integer'},{'name':'percent','title':'Percent','type':'number','format':'pc'},
   {'name':'cumPercent','title':'Cumulative Percent','type':'number','format':'pc'}]},
  {'name':'breakpointsTable','title':'Break Points','type':'Table','columns':[
   {'name':'index','title':'Index','type':'integer'},{'name':'value','title':'Break Value','type':'number'}]},
  {'name':'preview','title':'Row Classification Preview','type':'Table','columns':[
   {'name':'row','title':'Original Row','type':'text'},{'name':'value','title':'Value','type':'number'},
   {'name':'category','title':'Category','type':'text'}]},
  {'name':'interpretation','title':'Categorization Notes','type':'Text'},
  {'name':'rcode','title':'R Code Using Displayed Break Points','type':'Preformatted','visible':'(showcode)'},
  {'name':'plot','title':'Category Distribution','type':'Image','plot':'bar','width':650,'height':400,'visible':'(showplot)'},
  {'name':'histogram','title':'Continuous Distribution and Break Points','type':'Image','plot':'histogram','width':650,'height':400,'visible':'(showhistogram)'},
  {'name':'addtodata','title':'Categorized Variable','type':'Output','varTitle':'Categorized variable',
   'varDescription':'Categories in displayed interval order','measureType':'nominal'}],
 'ui':{'children':[
  {'type':'VariableSupplier','persistentItems':False,'stretchFactor':1,'children':[
   {'type':'TargetLayoutBox','label':'Variable to categorize','children':[{'type':'VariablesListBox','name':'var','isTarget':True,'maxItemCount':1}]}]},
  {'type':'CollapseBox','label':'Binning Method and Boundaries','collapsed':False,'children':[
   {'type':'ComboBox','name':'method'},
   {'type':'TextBox','name':'nbins','format':'number','enable':'(method:equal || method:quantile || method:jenks)'},
   {'type':'TextBox','name':'breaks','format':'string','enable':'(method:manual)'},
   {'type':'TextBox','name':'sdmult','format':'number','enable':'(method:meansd)'},
   {'type':'CheckBox','name':'excludeoutofrange','enable':'(method:manual)'},
   {'type':'CheckBox','name':'includelowest'},{'type':'CheckBox','name':'rightclosed'}]},
  {'type':'CollapseBox','label':'Labels and Reporting','collapsed':True,'children':[
   {'type':'ComboBox','name':'labels'},
   {'type':'TextBox','name':'customlabels','format':'string','enable':'(labels:custom)'},
   {'type':'CheckBox','name':'excl'},{'type':'CheckBox','name':'showcode'},{'type':'CheckBox','name':'showplot'},
   {'type':'CheckBox','name':'showhistogram'}]},
  {'type':'CollapseBox','label':'Save to Data','collapsed':True,'children':[
   {'type':'TextBox','name':'newvarname','format':'string'},
   {'type':'CheckBox','name':'ordered'},{'type':'Output','name':'addtodata'}]},
  {'type':'CollapseBox','label':'Advanced Settings','collapsed':True,'children':[
   {'type':'TextBox','name':'seed','format':'number','enable':'(method:jenks)'},
   {'type':'CheckBox','name':'showConsole'}]}]}}


def r_code(variable,target,breaks,labels,include,right,ordered):
    # Hexadecimal float literals retain the exact displayed IEEE boundaries in R.
    quote=lambda s:json.dumps(s,ensure_ascii=True)
    return ('# Apply these frozen, displayed break points. Rerun the analysis to derive new boundaries.\n'
      f'x <- data[[{quote(variable)}]]\n'
      f'data[[{quote(target)}]] <- cut(x, breaks = c('+', '.join(float(v).hex() for v in breaks)+'),\n'
      '    labels = c('+', '.join(quote(v) for v in labels)+'),\n'
      f'    include.lowest = {str(include).upper()}, right = {str(right).upper()}, ordered_result = {str(ordered).upper()})')


def run(data,options,out):
    variable=options.get('var')
    if not variable:raise InputError('Choose a continuous variable to categorize.')
    raw=data[variable];x=numeric(raw,variable)
    method=options.get('method','quantile');include=bool(options.get('includelowest',True));right=bool(options.get('rightclosed',True))
    b,notes=make_breaks(x,method,options.get('nbins',4),options.get('breaks',''),options.get('sdmult',1),bool(options.get('excludeoutofrange',False)))
    if len(b)>2001:raise InputError('At most 2,000 categories can be displayed and saved in this implementation.')
    labels,warning=labels_for(b,options.get('labels','auto'),options.get('customlabels',''),include,right)
    ranges=interval_labels(b,include,right);codes=assign(raw,b,include,right)
    observed=~np.isnan(raw);valid=codes>=0;missing=int(sum(~observed));uncategorized=int(sum(observed&~valid))
    nvalid=int(sum(valid));denom=nvalid if options.get('excl',True) else len(raw)
    counts=np.bincount(codes[valid],minlength=len(labels));cumulative=np.cumsum(counts)
    out.row('summary',variable=variable,total=len(raw),observed=len(x),missing=missing,categorized=nvalid,uncategorized=uncategorized,
            mean=np.mean(x),sd=np.std(x,ddof=1),minimum=min(x),maximum=max(x))
    for i,(label,interval,count) in enumerate(zip(labels,ranges,counts)):
        out.row('freqTable',category=label,range=interval,n=count,percent=float(count)/denom if denom else None,cumPercent=float(cumulative[i])/denom if denom else None)
    if missing:out.row('freqTable',category='Missing',range='NA',n=missing,percent=None if options.get('excl',True) or not denom else missing/denom)
    if uncategorized:
        boundary=int(sum(observed&~valid&(raw>=b[0])&(raw<=b[-1])))
        label='Out of range' if not boundary else 'Not categorized'
        reason='outside the break points' if not boundary else 'on the open outer break point' if boundary==uncategorized else 'outside or on the open outer break point'
        out.row('freqTable',category=label,range=reason,n=uncategorized,percent=None if options.get('excl',True) or not denom else uncategorized/denom)
        out.warn(f'{uncategorized} observed rows were not categorized: {reason}. They remain missing in the saved column.')
    for i,value in enumerate(b):out.row('breakpointsTable',index=i+1,value=value)
    # The preview is bounded; the saved output always retains every original input row.
    for i in range(min(len(raw),200)):
        out.row('preview',row=str(out.row_ids[i] if out.row_ids is not None else i+1),value=raw[i],category=labels[codes[i]] if codes[i]>=0 else None)
    if len(raw)>200:out.info('The row preview shows the first 200 input rows. Saved values cover every input row.')
    newname=options.get('newvarname','').strip() or variable+'_cat'
    if len(newname)>256 or any(ord(c)<32 for c in newname):raise InputError('Choose a new variable name of at most 256 characters without control characters.')
    if newname==variable:out.warn('The requested name matches the source variable. Executing the exported R code would overwrite that source column.')
    if warning:out.warn(warning)
    for note in notes:out.info(note)
    out.markdown('interpretation',md_escape(f'{method}: {len(labels)} categories; {nvalid} categorized of {len(raw)} input rows. Percentages use '+('categorized rows only.' if options.get('excl',True) else 'all input rows.')+' Categorizing a continuous variable loses information; choose clinical cutoffs independently of outcome effects. The native Save to Data control enables delivery of the new column; once enabled, later option changes update that analysis-owned column.'))
    if options.get('showcode',True):out.text('rcode',r_code(variable,newname,b,labels,include,right,bool(options.get('ordered',True))))
    if options.get('showplot',True):out.plot('plot',[dict(label=label,value=int(count),group=variable) for label,count in zip(labels,counts)],xlab='Category',ylab='Count')
    if options.get('showhistogram',False):
        hist_counts,edges=np.histogram(x,bins=30)
        bins=[dict(group=variable,lower=float(a),upper=float(b),count=int(c))
              for a,b,c in zip(edges[:-1],edges[1:],hist_counts)]
        out.plot('histogram',bins,xlab=variable,ylab='Count',boundaries=b)
        out.info('The continuous histogram uses 30 equal-width bins spanning all observed values, including uncategorized rows. Dashed lines are the displayed categorization break points; histogram bins are for display only. Interval closure is reported in the category table.')
    if out.row_ids is not None:
        out.column('addtodata',[int(code) if code>=0 else None for code in codes],levels=labels,title=newname,
                   description=f'Categorized {variable}; {method}; {len(labels)} categories',measure_type='ordinal' if options.get('ordered',True) else 'nominal')
