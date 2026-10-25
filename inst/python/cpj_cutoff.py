"""Empirical cutoff states, tie-aware AUC and binomial intervals computed in Python."""
import math
import numpy as np
from cpj_runtime import InputError

METRICS=['Sensitivity','Specificity','PPV','NPV','Accuracy']


def states(values,truth,direction,method='exact',confidence=.95,fp_cost=1,fn_cost=4):
    from scipy.stats import beta,norm
    unique,groups=np.unique(values,return_inverse=True)
    pos=np.bincount(groups,weights=truth,minlength=len(unique)).astype(int)
    neg=np.bincount(groups,weights=~truth,minlength=len(unique)).astype(int)
    p,n=int(pos.sum()),int(neg.sum())
    if not p or not n:raise InputError('Both reference groups require complete observations.')
    if direction=='ge':
        cuts=np.r_[unique,np.nextafter(unique[-1],np.inf)]
        tp=np.r_[p-np.r_[0,np.cumsum(pos)[:-1]],0];fp=np.r_[n-np.r_[0,np.cumsum(neg)[:-1]],0]
    elif direction=='le':
        cuts=np.r_[np.nextafter(unique[0],-np.inf),unique]
        tp=np.r_[0,np.cumsum(pos)];fp=np.r_[0,np.cumsum(neg)]
    else:raise InputError('Unknown classification direction.')
    if not np.isfinite(cuts).all():raise InputError('Measurements are too extreme to represent the endpoint cutoff safely.')
    fn=p-tp;tn=n-fp;fpr=fp/n;tpr=tp/p
    a=np.stack([tp,tn,tp,tn,tp+tn],axis=1).astype(float)
    den=np.stack([np.full(len(tp),p),np.full(len(tp),n),tp+fp,tn+fn,np.full(len(tp),p+n)],axis=1).astype(float)
    estimate=np.divide(a,den,out=np.full(a.shape,np.nan),where=den>0)
    alpha=1-confidence
    if method=='exact':
        lo=beta.ppf(alpha/2,a,den-a+1);hi=beta.ppf(1-alpha/2,a+1,den-a)
        lo[a==0]=0;hi[a==den]=1
    elif method=='wilson':
        z=norm.ppf(1-alpha/2);valid=np.where(den>0,den,np.nan);d=1+z*z/valid
        mid=(estimate+z*z/(2*valid))/d
        half=z*np.sqrt(estimate*(1-estimate)/valid+z*z/(4*valid*valid))/d
        lo=np.maximum(0,mid-half);hi=np.minimum(1,mid+half)
    else:raise InputError('Unknown interval method.')
    lo[den==0]=np.nan;hi[den==0]=np.nan
    def scalar(x):return None if not np.isfinite(x) else float(x)
    points=[]
    for i,cut in enumerate(cuts):
        points.append(dict(cutoff=float(cut),tp=int(tp[i]),fp=int(fp[i]),fn=int(fn[i]),tn=int(tn[i]),
            tpr=float(tpr[i]),fpr=float(fpr[i]),youden=float(tpr[i]-fpr[i]),cost=float(fp[i]*fp_cost+fn[i]*fn_cost),
            metrics=[[scalar(v) for v in row] for row in np.stack([estimate[i],lo[i],hi[i]],axis=1)]))
    optima={}
    for criterion,objective in [('errors',fp+fn),('youden',-(tpr-fpr)),('cost',fp*fp_cost+fn*fn_cost)]:
        best=float(np.min(objective));ties=np.flatnonzero(np.isclose(objective,best,rtol=0,atol=1e-12*max(1,abs(best))))
        optima[criterion]=dict(point=int(ties[0]),ties=len(ties)) # cuts increase numerically
    order=np.lexsort((tpr,fpr));auc=float(np.sum(np.diff(fpr[order])*(tpr[order][1:]+tpr[order][:-1])/2))
    return dict(points=points,auc=auc,optima=optima)


def select(points,cutoff,direction):
    cuts=np.array([p['cutoff'] for p in points])
    i=np.searchsorted(cuts,cutoff,side='left') if direction=='ge' else np.searchsorted(cuts,cutoff,side='right')-1
    return points[int(np.clip(i,0,len(points)-1))]
