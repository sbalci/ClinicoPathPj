"""Known binormal truth, paired ROC confidence coverage and null rejection."""
import hashlib
import json
import math
from pathlib import Path
import sys
import numpy as np
from scipy.stats import norm
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_roc import roc_analysis
from cpj_runtime import Factor
DRAWS=2000


def wilson(k,n):
    z=norm.ppf(.975);p=k/n;den=1+z*z/n
    middle=(p+z*z/(2*n))/den;half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [float(middle-half),float(middle+half)]


def check():
    rng=np.random.default_rng(20261114);rows=[]
    for n in (10,30,100):
        reference=Factor(np.r_[np.zeros(n,dtype=int),np.ones(n,dtype=int)],['Control','Case'])
        for scenario,shift2 in [('paired_null',.8),('paired_difference',.4)]:
            tape=rng.standard_normal((DRAWS,2*n,2))
            first=tape[:,:,0].copy();second=.7*tape[:,:,0]+math.sqrt(1-.7**2)*tape[:,:,1]
            first[:,n:]+=.8;second[:,n:]+=shift2
            truth=[float(norm.cdf(.8/math.sqrt(2))),float(norm.cdf(shift2/math.sqrt(2)))]
            hits=[0,0,0];available=[0,0,0];reject=0
            for i in range(DRAWS):
                r=roc_analysis(reference,{'A':first[i],'B':second[i]},positive='Case')
                for j,m in enumerate(r['models']):
                    ok=m['inference_status']=='ok';available[j]+=ok
                    hits[j]+=bool(ok and m['lower']<=truth[j]<=m['upper'])
                c=r['comparisons'][0];ok=c['status']=='ok';available[2]+=ok
                hits[2]+=bool(ok and c['lower']<=truth[0]-truth[1]<=c['upper'])
                reject+=bool(ok and c['p']<.05)
            rows.append(dict(scenario=scenario,per_class=n,draws=DRAWS,true_AUC=truth,
                             true_difference=truth[0]-truth[1],available=available,
                             covered=hits,coverage=[x/DRAWS for x in hits],
                             coverage_MC_SE=[math.sqrt((x/DRAWS)*(1-x/DRAWS)/DRAWS) for x in hits],
                             coverage_Wilson95=[wilson(x,DRAWS) for x in hits],
                             rejected=reject,rejection_rate=reject/DRAWS,
                             rejection_MC_SE=math.sqrt((reject/DRAWS)*(1-reject/DRAWS)/DRAWS),
                             rejection_Wilson95=wilson(reject,DRAWS),
                             rejection_interpretation='type I error' if scenario=='paired_null' else 'power for specified alternative',
                             input_pairs_sha256=hashlib.sha256(np.stack((first,second),axis=2).astype('<f8').tobytes()).hexdigest()))
            print(scenario,n,'coverage',rows[-1]['coverage'],'rejection',reject/DRAWS,flush=True)
    result=dict(date='2026-11-11',scope='source-only binormal ROC/paired DeLong simulation, not native or clinical qualification',
                seed=20261114,NumPy_version=np.__version__,draws_per_scenario=DRAWS,datasets=DRAWS*len(rows),
                truth='unit-variance normal case/control scores; AUC=Phi(mean shift/sqrt(2)), within-case/control marker correlation=.7',
                assumptions='independent cases; paired markers; equal class sizes, fixed orientation; no fitted model or missingness',
                engine_sha256=hashlib.sha256((ROOT/'inst/python/cpj_roc.py').read_bytes()).hexdigest(),rows=rows)
    p=ROOT/'docs/validation-exports/python-roc-coverage-20261111.json';p.write_text(json.dumps(result,indent=2)+'\n')
    print('report',hashlib.sha256(p.read_bytes()).hexdigest(),flush=True)


if __name__=='__main__':check()
