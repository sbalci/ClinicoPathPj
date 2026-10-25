"""Age pyramid: counts, denominators and exclusions share one Python engine."""
import numpy as np
from cpj_runtime import md_escape
from cpj_demographics import population

SPEC = {
 'name':'pyagepyramid','title':'Age Pyramid','menuGroup':'ClinicoPathPj',
 'menuSubgroup':'Descriptives','version':'0.3.2',
 'options':[
  {'name':'age','title':'Age (years)','type':'Variable','permitted':['numeric','factor'],'coerceNumeric':True,'suggested':['continuous'],'required':True},
  {'name':'gender','title':'Gender','type':'Variable','permitted':['factor'],'suggested':['nominal','ordinal'],'required':True},
  {'name':'female','title':'Female level','type':'Level','variable':'(gender)','allowNone':True},
  {'name':'male','title':'Male level','type':'Level','variable':'(gender)','allowNone':True},
  {'name':'age_groups','title':'Age group preset','type':'List','options':[
   {'name':'custom','title':'Custom (use bin width)'},{'name':'who','title':'WHO/UN standard (0–4, 5–9, … 85+)'},
   {'name':'who_infant','title':'WHO abridged (<1, 1–4, 5–9, … 85+)'},
   {'name':'pediatric','title':'Pediatric (<18)'},{'name':'reproductive','title':'Reproductive (15–50)'},
   {'name':'geriatric','title':'Geriatric (65+)'},{'name':'lifecourse','title':'Life course'}],'default':'custom'},
  {'name':'age_interval','title':'Age band boundaries','type':'List','options':[
   {'name':'left','title':'Left-closed [lower, upper)'},{'name':'right','title':'Right-closed (lower, upper]'}],'default':'left'},
  {'name':'bin_width','title':'Bin width (years)','type':'Number','min':0.01,'default':5},
  {'name':'custom_breaks','title':'Custom age breaks (comma separated)','type':'String','default':''},
  {'name':'pct_base','title':'Percentage base','type':'List','options':[
   {'name':'within_gender','title':'Within each gender'},{'name':'total','title':'All retained observations'}],'default':'within_gender'},
  {'name':'plot_values','title':'Bar values','type':'List','options':[
   {'name':'count','title':'Counts'},{'name':'percent','title':'Percentages'}],'default':'count'},
  {'name':'plot_title','title':'Plot title','type':'String','default':'Age Pyramid'},
  {'name':'showplot','title':'Age pyramid plot','type':'Bool','default':True},
  {'name':'showInterpretation','title':'Interpretation and assumptions','type':'Bool','default':False}],
 'results':[
  {'name':'dataSummary','title':'Data Summary','type':'Table','columns':[
   {'name':'status','title':'Row Classification','type':'text'},{'name':'n','title':'Rows','type':'integer'}]},
  {'name':'population','title':'Population Data','type':'Table','columns':[
   {'name':'band','title':'Age Band','type':'text'},{'name':'female','title':'Female (n)','type':'integer'},
   {'name':'male','title':'Male (n)','type':'integer'},{'name':'total','title':'Total (n)','type':'integer'},
   {'name':'femalePercent','title':'Female (%)','type':'number','format':'pc'},
   {'name':'malePercent','title':'Male (%)','type':'number','format':'pc'}]},
  {'name':'assignment','title':'Levels and Denominators','type':'Text'},
  {'name':'interpretation','title':'Interpretation and Assumptions','type':'Text','visible':'(showInterpretation)'},
  {'name':'pyramid','title':'Age Pyramid','type':'Image','plot':'pyramid','width':650,'height':550,'visible':'(showplot)'}],
 'ui':{'children':[
  {'type':'VariableSupplier','persistentItems':False,'stretchFactor':1,'children':[
   {'type':'TargetLayoutBox','label':'Age (years)','children':[{'type':'VariablesListBox','name':'age','isTarget':True,'maxItemCount':1}]},
   {'type':'TargetLayoutBox','label':'Gender','children':[{'type':'VariablesListBox','name':'gender','isTarget':True,'maxItemCount':1},
    {'type':'LevelSelector','name':'female'},{'type':'LevelSelector','name':'male'}]}]},
  {'type':'CollapseBox','label':'Age Bands and Denominators','collapsed':False,'children':[
   {'type':'ComboBox','name':'age_groups'},
   {'type':'ComboBox','name':'age_interval','enable':'(age_groups:custom)'},
   {'type':'TextBox','name':'bin_width','format':'number','enable':'(age_groups:custom)'},
   {'type':'TextBox','name':'custom_breaks','format':'string','enable':'(age_groups:custom)'},
   {'type':'ComboBox','name':'pct_base'}]},
  {'type':'CollapseBox','label':'Results and Interpretation','collapsed':True,'children':[{'type':'CheckBox','name':'showInterpretation'}]},
  {'type':'CollapseBox','label':'Plots','collapsed':True,'children':[
   {'type':'CheckBox','name':'showplot'},{'type':'ComboBox','name':'plot_values','enable':'(showplot)'},
   {'type':'TextBox','name':'plot_title','format':'string','enable':'(showplot)'}]},
  {'type':'CollapseBox','label':'Advanced Settings','collapsed':True,'children':[{'type':'CheckBox','name':'showConsole'}]}]}}


def run(data, options, out):
 r = population(data[options['age']],data[options['gender']],female=options.get('female'),male=options.get('male'),
  preset=options.get('age_groups','custom'),width=options.get('bin_width',5),custom=options.get('custom_breaks',''),
  interval=options.get('age_interval','left'),percentage=options.get('pct_base','within_gender'))
 n=r['reasons']['retained'];total=r['totals']
 labels={'total':'Input rows','missing':'Missing age or gender','invalid':'Unusable ages (negative or nonfinite)',
         'other':'Unselected gender levels','outside':'Outside age-break range','retained':'Retained observations'}
 for key,title in labels.items():out.row('dataSummary',status=title,n=r['reasons'][key])
 for message in r['notices']:out.warn(message)
 if r['mode'] in ('order','partial','single'):
  out.warn('Gender levels were assigned automatically ('+r['mode']+'). Check the female/male mapping shown below; set both level selectors explicitly to state the coding.')
 elif r['mode']=='labels':out.info('Gender sides were matched from level names. Check the mapping shown below.')
 excluded=r['reasons']['total']-n
 if excluded:out.warn(f'{excluded} of {r["reasons"]["total"]} input rows were excluded. All tables and bars use only the {n} retained observations; see Data Summary for disjoint exclusion reasons.')
 if r['over120']:out.warn(f'{r["over120"]} retained ages exceed 120 years. Check units and missing-value codes; these observations were retained.')
 occupied=np.flatnonzero(r['counts'].sum(axis=1)>0)
 if len(occupied)>25:out.warn('More than 25 occupied bands can make the pyramid hard to read. Consider a wider bin width.')
 widths=np.diff(r['breaks'][:-1])
 if len(widths)>1 and np.ptp(widths)>1e-8:out.warn('Bands span different numbers of years. Counts and percentages are per band, not per year; wider bands collect more observations.')
 if n<30:out.warn('Fewer than 30 retained observations: the pyramid is a descriptive sample profile, not a stable population estimate.')
 def cell(v):return None if not np.isfinite(v) else float(v)
 plot=[]
 for i in occupied:
  f,m=map(int,r['counts'][i]);fp,mp=map(cell,r['percentages'][i])
  out.row('population',band=r['labels'][i],female=f,male=m,total=f+m,femalePercent=fp,malePercent=mp)
  percent=options.get('plot_values','count')=='percent'
  # An absent group's percentage is undefined in the table; a zero-length side is geometric only.
  plot.append(dict(label=r['labels'][i],left=(fp or 0)*100 if percent else f,right=(mp or 0)*100 if percent else m,
                   leftLabel='Female: '+str(r['female'] or '(unassigned)'),rightLabel='Male: '+str(r['male'] or '(unassigned)'),
                   title=options.get('plot_title','Age Pyramid')))
 denominator = n if options.get('pct_base','within_gender')=='total' else None
 out.row('population',band='Total',female=int(total[0]),male=int(total[1]),total=n,
         femalePercent=float(total[0]/denominator) if denominator else (1. if total[0] else None),
         malePercent=float(total[1]/denominator) if denominator else (1. if total[1] else None))
 base='all retained observations (both sides together sum to 100%)' if denominator else 'each gender separately (each nonempty side sums to 100%)'
 out.markdown('assignment',md_escape(f'Female level: {r["female"] or "unassigned"}; male level: {r["male"] or "unassigned"}. Percentages use {base}. Ages are measured in years. Bands are '+('right-closed, with the first lower endpoint included.' if r['right'] else 'left-closed; an exact boundary age starts the next band.')))
 out.note('population','Only occupied bands are displayed, in increasing age order. An absent group has undefined within-group percentages. Empty bands are omitted from the plot; vertical spacing does not represent elapsed years.')
 if options.get('showInterpretation'):
  out.markdown('interpretation','This is a descriptive age profile, without hypothesis tests or population standardization. One row should represent the intended independent observation unit. Missing or unselected records can change the apparent distribution. These counts do not establish clinical reference ranges or population representativeness. Review gender-level definitions and age units before interpreting the two sides.')
 if options.get('showplot',True):out.plot('pyramid',plot,xlab='Percent (%)' if options.get('plot_values')=='percent' else 'Count',ylab='Age band')
