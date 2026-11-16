"""Validate and draw saved grouped survival geometry without model refitting."""
import math
from cpj_kaplan_meier_plot import validate as validate_curve


def validate(p):
    if (not isinstance(p,dict) or p.get('confidence_method')!='log'
            or not isinstance(p.get('series'),list) or not 1<=len(p['series'])<=20
            or not isinstance(p.get('n'),int) or isinstance(p['n'],bool) or not 1<=p['n']<=100000
            or not isinstance(p.get('maximum'),(int,float)) or isinstance(p['maximum'],bool)
            or not math.isfinite(p['maximum']) or p['maximum']<0):
        raise ValueError('Invalid bounded grouped survival drawing payload')
    codes=set();total=0;steps=0;maximum=0
    for g in p['series']:
        if (not isinstance(g,dict) or not isinstance(g.get('code'),int) or isinstance(g['code'],bool)
                or not 0<=g['code']<1000 or g['code'] in codes
                or not isinstance(g.get('label'),str) or len(g['label'])>120
                or not isinstance(g.get('points'),list)):
            raise ValueError('Invalid grouped curve identity')
        codes.add(g['code'])
        # Reuse the strict risk/product validator without changing the existing
        # single-cohort log-log boundary contract. Grouped log limits at S=1 are [1,1].
        points=[]
        for r in g['points']:
            if not isinstance(r,dict):raise ValueError('Invalid grouped curve step')
            row=dict(r)
            if row.get('survival')==1:
                if row.get('lower')!=1 or row.get('upper')!=1:raise ValueError('Grouped unit-survival limits must be [1,1]')
                row.update(lower=None,upper=None)
            points.append(row)
        validate_curve({**{k:p.get(k) for k in ('schema_version','unit','event_label','label_shortened','confidence','show_ci','show_censors')},
            'n':g.get('n'),'maximum':g.get('maximum'),'points':points})
        total+=g['n'];steps+=len(points);maximum=max(maximum,g['maximum'])
    if total!=p['n'] or maximum!=p['maximum'] or steps>5000:
        raise ValueError('Grouped plot totals or follow-up limits disagree')
    return p


def draw(fig,ax,p,palette,foreground):
    from matplotlib.collections import PolyCollection
    from matplotlib.ticker import FuncFormatter
    import textwrap
    scale=p['maximum'] or 1
    for i,g in enumerate(p['series']):
        points=g['points'];xs=[0]+[r['time']/scale for r in points];ys=[1]+[r['survival'] for r in points]
        if points[-1]['time']<g['maximum']:xs.append(g['maximum']/scale);ys.append(ys[-1])
        color=palette[i%len(palette)]
        cycle=i//len(palette)
        style='-' if cycle==0 else (0,(2+cycle,1+cycle/2,1,1+cycle/2))
        # The code makes shortened/colliding display labels unambiguous; full labels stay native.
        ax.step(xs,ys,where='post',color=color,linestyle=style,linewidth=1.5,
            label=f'{g["code"]+1}: '+textwrap.fill(g['label'],35)+f' (n={g["n"]})')
        if p['show_ci']:
            rectangles=[]
            for j,r in enumerate(points):
                end=points[j+1]['time'] if j+1<len(points) else g['maximum']
                if r['lower'] is not None and end>r['time']:
                    a,b=r['time']/scale,end/scale
                    rectangles.append([(a,r['lower']),(b,r['lower']),(b,r['upper']),(a,r['upper'])])
            if rectangles:ax.add_collection(PolyCollection(rectangles,facecolor=color,edgecolor='none',alpha=.12))
        if p['show_censors']:
            marks=[r for r in points if r['censored']>0]
            if marks:ax.scatter([r['time']/scale for r in marks],[r['survival'] for r in marks],marker='|',s=35,color=color,clip_on=False)
    ax.set_xlim(0,1);ax.set_ylim(0,1.02)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda value,pos:f'{value*scale:.4g}'))
    ax.set_xlabel('Elapsed time ('+p['unit']+')',color=foreground)
    ax.set_ylabel('Event-free probability',color=foreground)
    ax.set_title(textwrap.fill('Event: '+p['event_label'],65)+f'\nN={p["n"]}',color=foreground,fontsize=10)
    fig.legend(*ax.get_legend_handles_labels(),loc='outside lower center',ncol=min(3,len(p['series'])),
        frameon=False,labelcolor=foreground,fontsize=7)
    notes=[]
    if p['show_ci']:notes.append(f'{100*p["confidence"]:g}% pointwise log limits.')
    if p['show_censors']:notes.append('One censor mark per distinct group time.')
    if p['maximum']==0:notes.append('All follow-up times are zero.')
    if p['label_shortened']:notes.append('Labels shortened; full mapping in native tables.')
    if notes:ax.text(0,1.13,textwrap.fill(' '.join(notes),90),transform=ax.transAxes,color=foreground,fontsize=7)
    return fig
