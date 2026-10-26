"""Continuous summaries with explicit diagnostic and outlier denominators."""
from cpj_runtime import InputError, md_escape
from cpj_descriptive import numeric, summarize, histogram, display_p

SPEC = {
 'name':'pysummarydata','title':'Summary of Continuous Variables','menuGroup':'Descriptives Py',
 'menuSubgroup':'Summaries','version':'0.3.1',
 'options':[
  {'name':'vars','title':'Continuous variables','type':'Variables','permitted':['numeric'],'suggested':['continuous'],'required':True},
  {'name':'distr','title':'Distribution diagnostics','type':'Bool','default':False},
  {'name':'decimal_places','title':'Decimal places in narratives','type':'Integer','min':0,'max':5,'default':2},
  {'name':'outliers','title':'Outlier detection','type':'Bool','default':False},
  {'name':'report_sentences','title':'Draft report sentences','type':'Bool','default':False},
  {'name':'show_guidance','title':'Interpretation guidance and glossary','type':'Bool','default':False},
  {'name':'showplot','title':'Distribution histograms','type':'Bool','default':True}],
 'results':[
  {'name':'descriptives','title':'Continuous Variable Summary','type':'Table','columns':[
   {'name':'variable','title':'Variable','type':'text'},
   {'name':'n','title':'N','type':'integer'},{'name':'missing','title':'Missing','type':'integer'},
   {'name':'mean','title':'Mean','type':'number'},{'name':'sd','title':'SD','type':'number'},
   {'name':'minimum','title':'Minimum','type':'number'},{'name':'q1','title':'Q1','type':'number'},
   {'name':'median','title':'Median','type':'number'},{'name':'q3','title':'Q3','type':'number'},
   {'name':'maximum','title':'Maximum','type':'number'}]},
  {'name':'diagnostics','title':'Distribution Diagnostics','type':'Table','visible':'(distr)','columns':[
   {'name':'variable','title':'Variable','type':'text'},{'name':'n','title':'N','type':'integer'},
   {'name':'w','title':'Shapiro-Wilk W','type':'number'},{'name':'p','title':'p','type':'number','format':'pvalue'},
   {'name':'skewness','title':'Skewness','type':'number'},{'name':'kurtosis','title':'Pearson Kurtosis','type':'number'},
   {'name':'status','title':'Shapiro-Wilk Status','type':'text'}]},
  {'name':'outlierSummary','title':'IQR Outlier Fences','type':'Table','visible':'(outliers)','columns':[
   {'name':'variable','title':'Variable','type':'text'},{'name':'lower','title':'Lower Fence','type':'number'},
   {'name':'upper','title':'Upper Fence','type':'number'},{'name':'flagged','title':'Flagged','type':'integer'},
   {'name':'status','title':'Status','type':'text'}]},
  {'name':'outlierRows','title':'Flagged Observations','type':'Table','visible':'(outliers)','columns':[
   {'name':'variable','title':'Variable','type':'text'},{'name':'row','title':'Original Row','type':'text'},
   {'name':'value','title':'Value','type':'number'}]},
  {'name':'text','title':'Variable Summaries','type':'Text'},
  {'name':'reportSentences','title':'Draft Statistical Summary','type':'Text','visible':'(report_sentences)'},
  {'name':'guidance','title':'Interpretation Guidance and Glossary','type':'Text','visible':'(show_guidance)'},
  {'name':'distribution','title':'Continuous Data Distributions','type':'Image','plot':'histogram','width':650,'height':500,'visible':'(showplot)'}],
 'ui':{'children':[
  {'type':'VariableSupplier','persistentItems':False,'stretchFactor':1,'children':[
   {'type':'TargetLayoutBox','label':'Continuous variables','children':[{'type':'VariablesListBox','name':'vars','isTarget':True}]}]},
  {'type':'CollapseBox','label':'Analysis and Diagnostics','collapsed':False,'children':[
   {'type':'CheckBox','name':'distr'},{'type':'CheckBox','name':'outliers'}]},
  {'type':'CollapseBox','label':'Results and Interpretation','collapsed':True,'children':[
   {'type':'TextBox','name':'decimal_places','format':'number'},
   {'type':'CheckBox','name':'report_sentences'},{'type':'CheckBox','name':'show_guidance'}]},
  {'type':'CollapseBox','label':'Plots','collapsed':True,'children':[{'type':'CheckBox','name':'showplot'}]},
  {'type':'CollapseBox','label':'Advanced Settings','collapsed':True,'children':[{'type':'CheckBox','name':'showConsole'}]}]}}


def run(data,options,out):
 import numpy as np
 names=options.get('vars') or []
 if not names:raise InputError('Choose continuous variables.')
 dp=options.get('decimal_places',2)
 if isinstance(dp,bool) or not isinstance(dp,int) or not 0<=dp<=5:raise InputError('Decimal places must be an integer from 0 to 5.')
 texts=[];drafts=[];plot=[];retained=0
 for name in names:
  raw=data[name];x=numeric(raw,name)
  if not len(raw):raise InputError('The dataset has no rows.')
  if not len(x):out.warn(f'{name} was excluded because every value is missing.');continue
  retained+=1;s=summarize(x,bool(options.get('distr')),bool(options.get('outliers')))
  missing=len(raw)-len(x)
  out.row('descriptives',variable=name,missing=missing,**{k:s[k] for k in ('n','mean','sd','minimum','q1','median','q3','maximum')})
  fmt=lambda value:'undefined' if value is None else f'{value:.{dp}f}'
  sentence=f'For {name}, {len(x)} of {len(raw)} records had non-missing values ({missing} missing); mean {fmt(s["mean"])}'
  sentence+=f' (SD {fmt(s["sd"])}).' if len(x)>1 else ' (SD is undefined for one observation).'
  sentence+=f' Median {fmt(s["median"])}; observed range {fmt(s["minimum"])} to {fmt(s["maximum"])}.'
  draft=sentence
  if missing/len(raw)>.2:out.warn(f'{name}: {missing} of {len(raw)} rows are missing; the available observations may not represent the full dataset.')
  if len(x)<3:out.warn(f'{name}: fewer than three observations; descriptive estimates are unstable and normality cannot be assessed.')
  if options.get('distr'):
   out.row('diagnostics',variable=name,n=len(x),w=s['w'],p=s['p'],skewness=s['skewness'],kurtosis=s['kurtosis'],status=s['diagnostic_status'])
   diagnostic=f' Shapiro-Wilk p {display_p(s["p"])}; skewness {fmt(s["skewness"])}; Pearson kurtosis {fmt(s["kurtosis"])} (normal = 3).'
   if s['p'] is not None:
    verdict='no evidence of departure from normality' if s['p']>.05 else 'evidence of departure from normality'
    diagnostic+=f' There was {verdict}; this test cannot establish normality.'
    draft+=f' The Shapiro-Wilk test gave {verdict} (p {display_p(s["p"])}).'
   else:diagnostic+=' Normality test unavailable: '+s['diagnostic_status']+'.'
   sentence+=diagnostic
  texts.append(md_escape(sentence));drafts.append(md_escape(draft))
  if options.get('outliers'):
   if s['lower'] is None:
    out.row('outlierSummary',variable=name,status='Fewer than four non-missing observations')
   else:
    indices=np.flatnonzero((raw<s['lower'])|(raw>s['upper']))
    out.row('outlierSummary',variable=name,lower=s['lower'],upper=s['upper'],flagged=len(indices),status='1.5 x IQR')
    for i in indices:out.row('outlierRows',variable=name,row=str(out.row_ids[i] if out.row_ids is not None else i+1),value=raw[i])
  if options.get('showplot',True):plot.extend(histogram(x,name))
 if not retained:out.info('No selected variable has observed numeric values.');return
 out.markdown('text','\n\n'.join(texts))
 out.note('descriptives','Each variable uses its own non-missing observations. Quartiles use R type 7. Native numeric tables follow jamovi display preferences; decimal places controls the narratives.')
 if options.get('report_sentences'):out.markdown('reportSentences','\n\n'.join(drafts)+'\n\nAdd measurement units, population, time point and missing-data handling before using these draft sentences.')
 if options.get('show_guidance'):out.markdown('guidance','SD describes dispersion; quartiles and median describe location and spread. Pearson kurtosis is 3 for a normal distribution. Potential outliers lie beyond Q1 - 1.5 IQR or Q3 + 1.5 IQR and require contextual review; they are not removed. Distribution tests are exploratory and do not establish normality or clinical reference intervals. One row should represent the intended observation unit.')
 if options.get('distr'):out.note('diagnostics','Shapiro-Wilk assumes independent observations and is available only for 3-5000 non-missing, nonconstant values. Tests across variables are unadjusted. Skewness and Pearson kurtosis use population central moments.')
 if options.get('distr') and retained>1:out.info('Separate Shapiro-Wilk tests are unadjusted exploratory checks across selected variables.')
 if options.get('showplot',True):
  if retained>12 or len(plot)>2000:out.warn('Distribution plots are omitted above 12 variables or 2,000 aggregate bins; summary tables retain every variable.')
  else:out.plot('distribution',plot,xlab='Value',ylab='Count')
