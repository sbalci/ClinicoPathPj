"""Matched-input empirical-vs-Lin CCC coverage, including paired Monte Carlo error."""
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_concordance_empirical import empirical_concordance_interval
from cpj_concordance_uncertainty import concordance_interval

DRAWS=2000
spec=importlib.util.spec_from_file_location('lin_coverage',ROOT/'tools/check-concordance-interval-coverage.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


def scenarios():
    rng=np.random.default_rng(20261111)
    for n in (10,30,100):
        for name,rho in [('normal_positive',.3),('normal_high',.9),('normal_negative',-.5),
                         ('normal_shifted',.8),('lognormal_sensitivity',.6)]:
            tape=rng.standard_normal((DRAWS,n,2))
            x=tape[:,:,0];y=rho*x+math.sqrt(1-rho*rho)*tape[:,:,1];truth=rho
            if name=='normal_shifted':
                y=1.5+1.3*y;truth=2*1.3*rho/(1+1.3**2+1.5**2)
            elif name=='lognormal_sensitivity':
                x,y=np.exp(x),np.exp(y);truth=math.expm1(rho)/math.expm1(1)
            yield name,n,x,y,truth,True
    # Separate deterministic stream: extensions must not alter any original tape.
    rng=np.random.default_rng(20261112)
    for n in (30,100):
        tape=rng.standard_normal((DRAWS,n,2));scale=np.where(rng.random((DRAWS,n))<.05,5.,1.)
        x=scale*tape[:,:,0];y=scale*(.8*tape[:,:,0]+.6*tape[:,:,1])
        yield 'normal_scale_mixture',n,x,y,.8,False
    for n in (500,1000):
        tape=rng.standard_normal((DRAWS,n,2));rho=.6
        x=np.exp(tape[:,:,0]);y=np.exp(rho*tape[:,:,0]+math.sqrt(1-rho*rho)*tape[:,:,1])
        yield 'lognormal_extended',n,x,y,math.expm1(rho)/math.expm1(1),False


def check():
    baseline_path=ROOT/'docs/validation-exports/python-concordance-interval-coverage-20261111.json'
    baseline=json.loads(baseline_path.read_text())
    assert baseline['NumPy_version']==np.__version__
    old={(v['scenario'],v['n']):v for v in baseline['rows'] if v['method']=='z-transform'}
    lin_path=ROOT/'inst/python/cpj_concordance_uncertainty.py'
    assert hashlib.sha256(lin_path.read_bytes()).hexdigest()==baseline['engine_sha256']
    rows=[];paired=[]
    for name,n,x,y,truth,original in scenarios():
        digest=hashlib.sha256(np.stack((x,y),axis=2).astype('<f8').tobytes()).hexdigest()
        if original:
            assert digest==old[(name,n)]['input_pairs_sha256'],(name,n,'input mismatch')
        indicators={}
        for method in ('lin-z','empirical-z','empirical-normal'):
            flags=[];available=0;reasons={}
            for i in range(DRAWS):
                r=(concordance_interval(x[i],y[i],.95,'z-transform') if method=='lin-z' else
                   empirical_concordance_interval(x[i],y[i],.95,method))
                ok=r['status']=='ok'
                available+=ok
                flags.append(bool(ok and r['lower']<=truth<=r['upper']))
                if not ok:
                    reasons[r['reason']]=reasons.get(r['reason'],0)+1
            flags=np.array(flags,dtype=np.int8);indicators[method]=flags
            covered=int(flags.sum());probability=covered/DRAWS
            if original and method=='lin-z':
                assert covered==old[(name,n)]['covered'] and available==old[(name,n)]['available']
            rows.append(dict(scenario=name,n=n,method=method,true_CCC=truth,draws=DRAWS,
                             available=available,unavailable=reasons,covered=covered,
                             coverage_all=probability,coverage_conditional=covered/available if available else None,
                             Monte_Carlo_SE=math.sqrt(probability*(1-probability)/DRAWS),
                             Monte_Carlo_Wilson_95=module.wilson(covered,DRAWS),
                             input_pairs_sha256=digest,original_Lin_tape_verified=original))
        for method in ('empirical-z','empirical-normal'):
            delta=indicators[method]-indicators['lin-z']
            paired.append(dict(scenario=name,n=n,method=method,reference='lin-z',
                               coverage_difference=float(np.mean(delta)),
                               paired_Monte_Carlo_SE=float(np.std(delta,ddof=1)/math.sqrt(DRAWS)),
                               gained=int(np.count_nonzero(delta==1)),lost=int(np.count_nonzero(delta==-1))))
        print(name,n,'completed',flush=True)
    report=dict(scope='source-only matched-input empirical-vs-Lin CCC coverage; not public-method qualification',
                seed_original=20261111,seed_extensions=20261112,draws_per_scenario=DRAWS,
                datasets=DRAWS*19,interval_evaluations=DRAWS*19*3,
                NumPy_version=np.__version__,confidence=.95,original_tapes_verified=15,
                baseline_report_sha256=hashlib.sha256(baseline_path.read_bytes()).hexdigest(),
                engine_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in (lin_path,ROOT/'inst/python/cpj_concordance_empirical.py')},
                stochastic_contract='Exactly shared observed arrays across methods; original 15 tape hashes and Lin coverage counts verified; no cross-RNG seed equivalence claimed.',
                assumptions='iid pairs with finite fourth moments. Empirical moments remove the normal-theory variance assumption, not finite-sample/tail-estimation limitations or outlier sensitivity.',
                rows=rows,paired_differences=paired,clinical_acceptance=False)
    path=ROOT/'docs/validation-exports/python-concordance-empirical-coverage-20261111.json'
    path.write_text(json.dumps(report,indent=2)+'\n')
    print('coverage report',hashlib.sha256(path.read_bytes()).hexdigest(),flush=True)


if __name__=='__main__':check()
