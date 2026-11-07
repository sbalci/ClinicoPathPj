"""Two-component composite at the earliest component observation horizon; no model fit."""
import numpy as np
from cpj_runtime import Factor, InputError
from cpj_crosstable import categorical
from cpj_identity import audit as audit_identity

SOURCES = ['Censored', 'Component A', 'Component B', 'Both components']


def component(data, options, prefix):
    name = options.get('status'+prefix)
    if name not in data:
        return {'pending': 'Select the component '+prefix+' status variable.'}
    column = data[name]
    metadata = getattr(data, 'metadata', {}).get(name, {})
    if not isinstance(column, Factor) or metadata.get('dimensions') or set(metadata.get('classes') or []) - {'factor','ordered'}:
        raise InputError('Component '+prefix+' status must be a scalar nominal or ordinal column.')
    codes, levels = categorical(column, name)
    event, free = options.get('event'+prefix), options.get('free'+prefix)
    if event in (None, '') or free in (None, ''):
        return {'pending': 'Choose distinct event and event-free levels for component '+prefix+'.'}
    if event == free or event not in levels or free not in levels:
        raise InputError('Component '+prefix+': choose two distinct declared event and event-free levels.')
    values = [None if code < 0 else levels[code] for code in codes]
    if any(v is not None and v not in (event, free) for v in values):
        raise InputError('Component '+prefix+' contains observed statuses outside the two selected levels. Recode explicitly before use.')
    return {'pending':'', 'status':[None if v is None else int(v == event) for v in values],
            'mapping':[dict(component=prefix,variable=name,level=str(v),code=i,n=values.count(v)) for v,i in [(free,0),(event,1)]]}


def time_column(data, name):
    if name not in data:
        raise InputError('Select both numeric component event/follow-up times.')
    x = data[name]; metadata = getattr(data, 'metadata', {}).get(name, {})
    if metadata.get('dimensions') or set(metadata.get('classes') or []) - {'numeric','integer'} or not isinstance(x,np.ndarray) or x.ndim != 1 or x.dtype.kind not in 'fiu':
        raise InputError('Times must be scalar numeric durations with a common origin and units; convert dates explicitly.')
    if np.isinf(x).any():
        raise InputError('Infinite times are not supported. Supply finite durations or missing values.')
    return x.astype(float)


def calculate(data, options):
    a = component(data, options, 'A'); b = component(data, options, 'B')
    for x in (a,b):
        if x['pending']: return x
    ta = time_column(data,options.get('timeA')); tb = time_column(data,options.get('timeB'))
    n = len(ta)
    if not 1 <= n <= 10000 or any(len(x) != n for x in [tb,a['status'],b['status']]):
        raise InputError('Supply one to 10,000 aligned component records without sampling.')
    limit = options.get('preview_rows',20)
    if isinstance(limit,bool) or not isinstance(limit,int) or not 10 <= limit <= 100:
        raise InputError('Preview rows must be an integer from 10 to 100.')
    audit_subject = options.get('audit_subject',False)
    strict = options.get('require_unique_id',False)
    if not isinstance(audit_subject,bool) or not isinstance(strict,bool):
        raise InputError('Subject identity switches must be enabled or disabled explicitly.')
    if strict and not audit_subject:return {'pending':'Enable the subject identity audit before requiring one record per subject.'}
    if audit_subject and options.get('subject') in (None,''):return {'pending':'Select a subject ID for the identity audit.'}
    identity = audit_identity(data,options.get('subject'),n,strict) if audit_subject else None
    if identity and identity['pending']:return identity
    use_admin = options.get('use_admin',False)
    if not isinstance(use_admin,bool):
        raise InputError('Administrative censoring must be enabled or disabled explicitly.')
    cutoff = None
    if use_admin:
        raw = options.get('admin_cutoff','')
        if raw is None or (isinstance(raw,str) and not raw.strip()):
            return {'pending':'Enter the administrative cutoff in the same duration units and from the same origin as both component times.'}
        if not isinstance(raw,str) or len(raw)>64:
            raise InputError('Administrative cutoff must be an explicit finite nonnegative number.')
        try: cutoff = float(raw)
        except ValueError: raise InputError('Administrative cutoff must be a finite nonnegative number.') from None
        if not np.isfinite(cutoff) or cutoff < 0:
            raise InputError('Administrative cutoff must be a finite nonnegative number.')
    times=[]; statuses=[]; sources=[]; rows=[]; invalid=missing=ties=late=0
    for t,u,s,v in zip(ta,tb,a['status'],b['status']):
        time=status=source=None
        if (np.isfinite(t) and t < 0) or (np.isfinite(u) and u < 0):
            invalid += 1; reason='Invalid: negative duration'
        elif np.isnan(t) or np.isnan(u) or s is None or v is None:
            missing += 1; reason='Unknown: incomplete component record'
        else:
            time=float(min(t,u))
            event_a = s == 1 and t == time; event_b = v == 1 and u == time
            status=int(event_a or event_b)
            source=3 if event_a and event_b else 1 if event_a else 2 if event_b else 0
            reason=SOURCES[source]+' at common observation horizon'
            if t == u and s != v: ties += 1
            if not status and (s == 1 or v == 1): late += 1
        times.append(time);statuses.append(status);sources.append(source)
        rows.append(dict(timeA=None if np.isnan(t) else float(t),timeB=None if np.isnan(u) else float(u),
                         statusA=s,statusB=v,time=time,status=status,source=None if source is None else SOURCES[source],reason=reason))
    admin = dict(enabled=use_admin,cutoff=cutoff,shortened=0,eventsRemoved=0,censoredShortened=0,tiedEvents=0)
    for i,row in enumerate(rows):
        row.update(baseTime=times[i],baseStatus=statuses[i],adminApplied=None if times[i] is None else 0)
        if use_admin and times[i] is not None:
            if times[i] == cutoff and statuses[i] == 1: admin['tiedEvents'] += 1
            if times[i] > cutoff:
                admin['shortened'] += 1
                admin['eventsRemoved' if statuses[i] == 1 else 'censoredShortened'] += 1
                times[i]=cutoff;statuses[i]=0;sources[i]=4
                row.update(time=cutoff,status=0,source='Administrative cutoff',reason='Administrative cutoff before common observation horizon',adminApplied=1)
    if identity:
        for i,row in enumerate(rows):row.update(subject=identity['values'][i],subjectRecords=identity['rowCounts'][i])
    retained=sum(x is not None for x in statuses)
    counts=[dict(code=i,label=label,n=statuses.count(i),percent=statuses.count(i)/retained if retained else None) for i,label in enumerate(['Censored','Event'])]
    return dict(pending='',n=n,retained=retained,invalid=invalid,missing=missing,ties=ties,late=late,
                time=times,status=statuses,source=sources,rows=rows,counts=counts,mapping=a['mapping']+b['mapping'],limit=limit,admin=admin,identity=identity)
