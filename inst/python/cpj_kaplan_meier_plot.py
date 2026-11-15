"""Validate bounded saved KM drawing data without source access or model fitting."""
import math


def validate(p):
    def integer(v,lo,hi):return isinstance(v,int) and not isinstance(v,bool) and lo<=v<=hi
    def number(v):return isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v)
    if (not isinstance(p,dict) or not integer(p.get('schema_version'),1,1)
            or p.get('unit') not in ('days','weeks','months','years')
            or not isinstance(p.get('event_label'),str) or len(p['event_label'])>120
            or any(not isinstance(p.get(k),bool) for k in ('show_ci','show_censors','label_shortened'))
            or not integer(p.get('n'),1,100000) or not number(p.get('confidence'))
            or not .5<=p['confidence']<=.999 or not number(p.get('maximum')) or p['maximum']<0
            or not isinstance(p.get('points'),list) or not 1<=len(p['points'])<=5000):
        raise ValueError('Invalid bounded Kaplan–Meier drawing payload')
    risk=p['n'];previous_time=-1.;survival=1.
    for r in p['points']:
        if (not isinstance(r,dict) or not number(r.get('time')) or not 0<=r['time']<=p['maximum']
                or r['time']<=previous_time or not integer(r.get('n_risk'),1,risk)
                or r['n_risk']!=risk or not integer(r.get('events'),0,risk)
                or not integer(r.get('censored'),0,risk-r['events'])
                or not number(r.get('survival'))):
            raise ValueError('Invalid KM time ordering or risk-set counts')
        survival*=(risk-r['events'])/risk
        if not 0<=r['survival']<=1 or abs(r['survival']-survival)>2e-12:
            raise ValueError('KM drawing probabilities disagree with risk-set counts')
        if r['survival'] in (0.,1.):
            if r.get('lower') is not None or r.get('upper') is not None:
                raise ValueError('Boundary KM limits must remain unavailable')
        elif (not number(r.get('lower')) or not number(r.get('upper'))
                or not 0<=r['lower']<=r['survival']<=r['upper']<=1):
            raise ValueError('Invalid pointwise KM limits')
        risk-=r['events']+r['censored'];previous_time=r['time']
    if risk!=0:raise ValueError('KM drawing omits retained observations')
    return p
