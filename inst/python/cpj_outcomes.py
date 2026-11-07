"""Explicit row-wise survival status preparation; no event times or inference."""
import numpy as np
from cpj_runtime import Factor, InputError
from cpj_crosstable import categorical

STATE_TITLES = {'awod':'Alive without disease','awd':'Alive with disease',
                'dod':'Dead of disease','dooc':'Dead of other causes'}
COMPOSITES = {'rfs','pfs','dfs','ttp'}
RULES = {'os':{'awod':0,'awd':0,'dod':1,'dooc':1},
         'cause':{'awod':0,'awd':0,'dod':1,'dooc':0},
         'compete':{'awod':0,'awd':0,'dod':1,'dooc':2},
         'multistate':{'awod':0,'awd':1,'dod':2,'dooc':3}}


def calculate(data, options):
    name = options.get('outcome')
    if name not in data: raise InputError('Select an outcome variable.')
    kind = options.get('analysistype','os')
    if kind in COMPOSITES:
        return composite_status(data,options)
    if kind not in RULES: raise InputError('Unknown outcome preparation type.')
    multi = options.get('multievent',False)
    if not isinstance(multi,bool): raise InputError('Multiple event levels must be true or false.')
    if not multi and kind != 'os':
        raise InputError('Enable Multiple event levels for cause-specific, competing-risk or multistate coding in this core.')
    column = data[name]
    metadata = getattr(data,'metadata',{}).get(name,{})
    if metadata.get('dimensions') or set(metadata.get('classes') or []) - {'numeric','integer','factor','ordered'}:
        raise InputError('Select a scalar numeric or nominal/ordinal outcome; dates and structured columns are not supported.')
    if isinstance(column,Factor):
        codes, levels = categorical(column,name)
        values = [None if code < 0 else levels[code] for code in codes]
        declared = [v for v in levels if v is not None]
    elif isinstance(column,np.ndarray) and column.ndim == 1 and column.dtype.kind in 'fiu':
        if not np.isfinite(column[~np.isnan(column)]).all():
            raise InputError('Recode infinite outcome values before analysis.')
        values = [None if np.isnan(v) else float(v) for v in column]
        declared = sorted(set(v for v in values if v is not None))
    else:
        raise InputError('Select a numeric or nominal/ordinal outcome.')
    n = len(values)
    if not 1 <= n <= 10000: raise InputError('The outcome core accepts one to 10,000 rows without sampling.')
    if len(declared)>20: raise InputError('At most twenty declared outcome levels are supported.')
    observed = {v for v in values if v is not None}
    if not observed: raise InputError('The outcome contains only missing values.')
    selected = options.get('outcomeLevel')
    mapping = []; warnings = []; pending = ''
    handoff = isinstance(column,Factor) and set(declared)=={'Censored','Event','Competing'}
    if multi:
        if not isinstance(column,Factor):
            raise InputError('Four-category mapping requires a nominal or ordinal outcome.')
        assignments = {key:options.get(key) for key in STATE_TITLES if options.get(key) not in (None,'')}
        if not assignments:
            return dict(pending='Assign the observed outcome levels to their vital-status categories.')
        if len(set(assignments.values())) != len(assignments):
            raise InputError('Each outcome level may be assigned to only one category.')
        if any(v not in declared for v in assignments.values()):
            raise InputError('A selected state level is no longer declared by the outcome variable.')
        unmapped = observed-set(assignments.values())
        if unmapped:
            raise InputError('Assign every observed outcome level; unassigned: '+', '.join(sorted(unmapped))+'.')
        recode = {level:RULES[kind][slot] for slot,level in assignments.items()}
        for level in declared:
            slot = next((slot for slot,v in assignments.items() if v==level),None)
            mapping.append(dict(level=level,category=STATE_TITLES[slot] if slot else 'Unused; not assigned',
                                code=recode.get(level),n=values.count(level)))
        mode = kind
    elif handoff:
        if selected == 'Censored': raise InputError('Censored cannot be the event in a Censored/Event/Competing outcome.')
        if selected not in (None,'','Event','Competing'): raise InputError('Choose Event or Competing as the event level.')
        focus = 'Competing' if selected=='Competing' else 'Event'
        other = 'Event' if focus=='Competing' else 'Competing'
        recode = {'Censored':0,focus:1,other:2};mode='compete'
        warnings.append('The complete declared Censored/Event/Competing factor is preserved as a competing-risk interchange, including an unused competing level.')
        mapping = [dict(level=v,category='Competing-risk interchange',code=recode[v],n=values.count(v)) for v in declared]
    else:
        if isinstance(column,Factor):
            if selected in (None,''): return dict(pending='Choose the event level explicitly; every other observed level will be coded 0.')
            if selected not in declared: raise InputError('The selected event level is no longer declared by the outcome variable.')
        else:
            if selected in (None,''):
                if not observed <= {0.,1.}: raise InputError('Numeric outcomes without an event selection must contain only 0 and 1; set other codes to Nominal and choose an event level.')
                selected = 1.
            else:
                try: selected = float(selected)
                except (ValueError,TypeError): raise InputError('Select a valid numeric event value.') from None
                if not np.isfinite(selected) or selected not in observed: raise InputError('The numeric event value does not occur in the data.')
        recode = {v:int(v==selected) for v in declared};mode='selected'
        mapping = [dict(level=str(v),category='Selected event' if v==selected else 'Coded 0',code=recode[v],n=values.count(v)) for v in declared]
    statuses = [None if v is None else recode[v] for v in values]
    labels = (['Censored','Event','Competing'] if mode=='compete' else
              ['0','1','2','3'] if mode=='multistate' else ['0','1'])
    titles = (['Censored','Target event','Competing event'] if mode=='compete' else
              ['Baseline: alive without disease','Alive with disease','Death from disease','Death from other causes'] if mode=='multistate' else
              ['Coded 0 (censored)','Coded 1 (event)'])
    valid = sum(v is not None for v in statuses)
    counts = [dict(code=i,label=title,n=statuses.count(i),percent=statuses.count(i)/valid) for i,title in enumerate(titles)]
    if mode!='multistate' and statuses.count(1)==0:
        warnings.append('No target events were coded. Check the selected event and mapping; zero events do not establish perfect population survival.')
    if mode=='cause':
        warnings.append('Other-cause deaths are coded 0 for a cause-specific endpoint. This coding does not estimate absolute disease risk.')
    if mode=='selected':
        warnings.append('Every other observed level is coded 0, including any competing terminal events. Labels alone do not establish overall survival.')
    return dict(pending=pending,status=statuses,mapping=mapping,counts=counts,mode=mode,
                levels=labels,total=n,valid=valid,missing=n-valid,warnings=warnings)


def binary_component(data,name,event,role,factor_only=False):
    """Explicit binary component; missingness remains unknown even in an all-missing column."""
    if name not in data:
        return dict(pending=f'Select the {role.lower()} variable.')
    column=data[name];metadata=getattr(data,'metadata',{}).get(name,{})
    if metadata.get('dimensions') or set(metadata.get('classes') or [])-{'numeric','integer','factor','ordered'}:
        raise InputError(f'{role}: select a scalar nominal/ordinal or numeric indicator.')
    if isinstance(column,Factor):
        codes,levels=categorical(column,name)
        declared=[v for v in levels if v is not None]
        values=[None if code<0 else levels[code] for code in codes]
        if set(declared)=={'Censored','Event','Competing'}:
            raise InputError(f'{role}: competing-risk interchange is not a binary composite component. Prepare an explicit binary indicator first.')
        if event in (None,''):
            return dict(pending=f'Choose the {role.lower()} event level explicitly.')
        if event not in declared:
            raise InputError(f'{role}: selected event level is no longer declared.')
    elif not factor_only and isinstance(column,np.ndarray) and column.ndim==1 and column.dtype.kind in 'fiu':
        if not np.isfinite(column[~np.isnan(column)]).all():
            raise InputError(f'{role}: recode infinite values before preparation.')
        values=[None if np.isnan(v) else float(v) for v in column]
        declared=sorted({v for v in values if v is not None})
        if event in (None,''):
            if not set(declared)<={0.,1.}:
                raise InputError(f'{role}: numeric values must be 0/1 without an explicit event value.')
            event=1.
        else:
            try:event=float(event)
            except (ValueError,TypeError):raise InputError(f'{role}: select a valid numeric event value.') from None
            if not np.isfinite(event) or (declared and event not in declared):
                raise InputError(f'{role}: selected numeric event does not occur in the data.')
    else:
        raise InputError(f'{role}: select a nominal or ordinal variable.' if factor_only else f'{role}: select a numeric or nominal/ordinal variable.')
    if len(declared)>20:raise InputError(f'{role}: at most twenty declared levels are supported.')
    status=[None if v is None else int(v==event) for v in values]
    mapping=[dict(level=str(v),category='Selected event' if v==event else 'Coded 0',code=int(v==event),n=values.count(v)) for v in declared]
    return dict(pending='',status=status,mapping=mapping)


def composite_status(data,options):
    kind=options['analysistype']
    if options.get('multievent',False) is not False:
        raise InputError('Composite/progression status requires single-event coding; disable Multiple event levels.')
    recurrence=options.get('recurrence')
    rec=binary_component(data,recurrence,options.get('recurrenceLevel'),'Recurrence/progression',factor_only=True)
    if rec['pending']:return rec
    n=len(rec['status'])
    if not 1<=n<=10000:raise InputError('The outcome core accepts one to 10,000 rows without sampling.')
    name=options.get('outcome');column=data.get(name)
    if column is None:raise InputError('Select an outcome variable for row alignment.')
    length=len(column.codes) if isinstance(column,Factor) else len(column) if isinstance(column,(list,np.ndarray)) else -1
    if length!=n:raise InputError('Outcome and recurrence/progression columns must have equal supplied rows.')
    if kind=='ttp':
        base=dict(status=[None]*n,mapping=[])
        status=list(rec['status'])
        reasons=['Progression observed' if v==1 else 'No progression observed' if v==0 else 'Unknown progression status' for v in status]
        labels=['No progression observed (coded 0)','Progression event']
    else:
        base=binary_component(data,name,options.get('outcomeLevel'),'Outcome')
        if base['pending']:return base
        status=[1 if a==1 or b==1 else 0 if a==0 and b==0 else None for a,b in zip(base['status'],rec['status'])]
        reasons=['Known component event' if v==1 else 'Both components coded 0' if v==0 else 'Unknown component without a known event' for v in status]
        labels=['Both components coded 0','Selected event or recurrence/progression']
    valid=sum(v is not None for v in status)
    counts=[dict(code=i,label=label,n=status.count(i),percent=status.count(i)/valid if valid else None) for i,label in enumerate(labels)]
    component_rows=[]
    for role,var,component in [('Outcome',name,base),('Recurrence/progression',recurrence,rec)]:
        for row in component['mapping']:component_rows.append(dict(component=role,variable=var,**row))
    overrides=sum(v==1 and (a is None or b is None) for a,b,v in zip(base['status'],rec['status'],status)) if kind!='ttp' else 0
    warnings=[('Progression-only status ignores the outcome event level and outcome values. Pair it with time to progression or an appropriate last assessment for coded-0 records; death/last-contact time is not automatically progression time.' if kind=='ttp' else
              'Composite status only: choose the appropriate death/event component explicitly and pair this status with time to FIRST component event. No recurrence/progression time is supplied here; death or last-contact time alone can overstate event-free follow-up.')]
    if not valid:warnings.append('No final status can be determined: unknown components were not converted to censoring.')
    elif status.count(1)==0:warnings.append('No target events were coded; this does not establish event-free survival.')
    return dict(pending='',status=status,mapping=base['mapping'] if kind!='ttp' else rec['mapping'],counts=counts,mode=kind,
                levels=['0','1'],total=n,valid=valid,missing=n-valid,warnings=warnings,
                components=component_rows,outcome_status=base['status'],recurrence_status=rec['status'],reasons=reasons,
                component_missing_outcome=sum(v is None for v in base['status']) if kind!='ttp' else None,
                component_missing_recurrence=sum(v is None for v in rec['status']),known_event_overrides=overrides)
