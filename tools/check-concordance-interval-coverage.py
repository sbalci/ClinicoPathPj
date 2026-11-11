"""Deterministic known-population coverage study; no cross-RNG seed equivalence claim."""
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_concordance_uncertainty import concordance_interval

DRAWS=2000
SEED=20261111


def wilson(success,n):
    z=1.959963984540054
    p=success/n;den=1+z*z/n
    center=(p+z*z/(2*n))/den
    half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [center-half,center+half]


def check():
    rng=np.random.default_rng(SEED)
    rows=[]
    for n in (10,30,100):
        for scenario,rho in [('normal_positive',.3),('normal_high',.9),
                             ('normal_negative',-.5),('normal_shifted',.8),
                             ('lognormal_sensitivity',.6)]:
            # One fixed innovation tape per scenario; BOTH methods receive exactly
            # the same observed pairs. Hashes permit regeneration verification.
            tape=rng.standard_normal((DRAWS,n,2))
            x=tape[:,:,0]
            y=rho*x+math.sqrt(1-rho*rho)*tape[:,:,1]
            truth=rho
            if scenario=='normal_shifted':
                y=1.5+1.3*y
                truth=2*1.3*rho/(1+1.3**2+1.5**2)
            elif scenario=='lognormal_sensitivity':
                x,y=np.exp(x),np.exp(y)
                truth=math.expm1(rho)/math.expm1(1)
            digest=hashlib.sha256(np.stack((x,y),axis=2).astype('<f8').tobytes()).hexdigest()
            for method in ('z-transform','asymptotic'):
                covered=available=0;unavailable={}
                for i in range(DRAWS):
                    result=concordance_interval(x[i],y[i],.95,method)
                    if result['status']=='ok':
                        available+=1
                        covered+=result['lower']<=truth<=result['upper']
                    else:
                        reason=result['reason'];unavailable[reason]=unavailable.get(reason,0)+1
                probability=covered/DRAWS
                rows.append(dict(scenario=scenario,n=n,method=method,true_CCC=truth,
                                 draws=DRAWS,available=available,unavailable=unavailable,
                                 covered=int(covered),coverage_all=probability,
                                 coverage_conditional=covered/available if available else None,
                                 Monte_Carlo_SE=math.sqrt(probability*(1-probability)/DRAWS),
                                 Monte_Carlo_Wilson_95=wilson(covered,DRAWS),
                                 input_pairs_sha256=digest))
            print(scenario,n,'completed',flush=True)
    report=dict(scope='known-population coverage study of source-only Lin interval prototype',
                seed=SEED,NumPy_version=np.__version__,generator='NumPy PCG64 default_rng',
                engine_sha256=hashlib.sha256((ROOT/'inst/python/cpj_concordance_uncertainty.py').read_bytes()).hexdigest(),
                stochastic_contract='same fixed per-scenario observed arrays used for both methods; no R/Python seed equivalence asserted',
                rows=rows,clinical_acceptance=False,
                assumptions='Independent paired observations; normal scenarios meet the intended model. Lognormal is an explicit nonnormal sensitivity scenario, not a validated extension.')
    path=ROOT/'docs/validation-exports/python-concordance-interval-coverage-20261111.json'
    path.write_text(json.dumps(report,indent=2)+'\n')
    print('coverage report',hashlib.sha256(path.read_bytes()).hexdigest(),flush=True)


if __name__=='__main__':check()
