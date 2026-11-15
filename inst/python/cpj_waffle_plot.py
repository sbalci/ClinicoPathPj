"""Strict validation of bounded saved drawing state; no source data access."""
import math


def validate(p):
    def integer(v,lo,hi):
        return isinstance(v,int) and not isinstance(v,bool) and lo<=v<=hi
    def text(v):
        return isinstance(v,str) and len(v)<=20000
    if (not isinstance(p,dict) or p.get('schema_version')!=1
            or not integer(p.get('rows'),1,100) or not isinstance(p.get('flip'),bool)
            or not isinstance(p.get('legend'),bool)
            or any(not text(p.get(k)) or len(p[k])>200 for k in ('title','legend_title'))
            or not isinstance(p.get('panels'),list) or not 1<=len(p['panels'])<=8):
        raise ValueError('Invalid bounded waffle drawing payload')
    labels,codes_seen,mapping,total=set(),set(),None,0
    for panel in p['panels']:
        if (not isinstance(panel,dict) or not text(panel.get('label')) or panel['label'] in labels
                or not integer(panel.get('code'),0,999) or panel['code'] in codes_seen
                or not integer(panel.get('n_total'),1,2**53-1)
                or not isinstance(panel.get('cells'),list) or not 1<=len(panel['cells'])<=20
                or not isinstance(panel.get('geometry'),list) or len(panel['geometry'])!=100):
            raise ValueError('Invalid waffle panel, denominator or tile count')
        labels.add(panel['label']);codes_seen.add(panel['code']);total+=panel['n_total']
        names=[];codes=[];expanded=[];counts=0;quotients=[];remainders=[]
        for c in panel['cells']:
            if (not isinstance(c,dict) or not text(c.get('label')) or not integer(c.get('code'),0,999)
                    or not integer(c.get('count'),0,panel['n_total']) or not integer(c.get('tiles'),0,100)):
                raise ValueError('Invalid waffle category or counts')
            names.append(c['label']);codes.append(c['code']);counts+=c['count']
            expanded.extend([c['code']]*c['tiles'])
            quotients.append(100*c['count']//panel['n_total'])
            remainders.append(100*c['count']%panel['n_total'])
            for key,value in [('proportion',c['count']/panel['n_total']),
                    ('represented_proportion',c['tiles']/100),
                    ('allocation_error',c['tiles']/100-c['count']/panel['n_total'])]:
                v=c.get(key)
                if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v!=value:
                    raise ValueError('Waffle proportions disagree with exact counts')
            if c.get('omitted_positive') is not (c['count']>0 and c['tiles']==0):
                raise ValueError('Invalid omitted-category disclosure')
        current=list(zip(codes,names))
        if (counts!=panel['n_total'] or len(expanded)!=100 or len(set(names))!=len(names)
                or codes!=sorted(set(codes)) or (mapping is not None and mapping!=current)):
            raise ValueError('Invalid waffle totals or category mapping')
        mapping=current
        winners=sorted(range(len(codes)),key=lambda i:(-remainders[i],-i))[:100-sum(quotients)]
        if [c['tiles'] for c in panel['cells']]!=[q+int(i in winners) for i,q in enumerate(quotients)]:
            raise ValueError('Waffle allocation violates the integer remainder contract')
        for k,tile in enumerate(panel['geometry']):
            x,y=k//p['rows']+1,k%p['rows']+1
            if p['flip']:x,y=y,x
            expected=dict(code=expanded[k],x=x,y=y,xmin=x-.5,xmax=x+.5,ymin=y-.5,ymax=y+.5)
            if not isinstance(tile,dict) or any(isinstance(tile.get(key),bool) or tile.get(key)!=v for key,v in expected.items()):
                raise ValueError('Waffle tile geometry disagrees with allocation')
    if total>2**53-1:
        raise ValueError('Waffle frequency total exceeds the exact limit')
    return p
