"""Prespecified matched-observation percentile bootstrap CCC coverage screen."""
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_concordance_bootstrap import bootstrap_concordance_interval
spec=importlib.util.spec_from_file_location('empirical_coverage',ROOT/'tools/check-concordance-empirical-coverage.py')
previous=importlib.util.module_from_spec(spec);spec.loader.exec_module(previous)
DRAWS=2000
RESAMPLES=999


def main():
    prior_path=ROOT/'docs/validation-exports/python-concordance-empirical-coverage-20261111.json'
    prior=json.loads(prior_path.read_text())
    assert np.__version__==prior['NumPy_version']
    lookup={(r['scenario'],r['n'],r['method']):r for r in prior['rows']}
    rows=[];tail=[]
    for scenario,(name,n,x,y,truth,_) in enumerate(previous.scenarios()):
        if n>100:continue
        tape_hash=hashlib.sha256(np.stack((x,y),axis=2).astype('<f8').tobytes()).hexdigest()
        assert tape_hash==lookup[name,n,'lin-z']['input_pairs_sha256']
        covered=available=0;reasons={};flags=[];widths=[];indices_digest=hashlib.sha256()
        for i in range(DRAWS):
            seed=20261113+scenario*DRAWS+i
            r=bootstrap_concordance_interval(x[i],y[i],resamples=RESAMPLES,seed=seed)
            ok=r['status']=='ok';available+=ok
            hit=bool(ok and r['lower']<=truth<=r['upper']);covered+=hit;flags.append(hit)
            indices_digest.update((r['index_sha256'] or 'not evaluated').encode('ascii'))
            if ok:widths.append(r['upper']-r['lower'])
            else:reasons[r['reason']]=reasons.get(r['reason'],0)+1
            # Prespecified first twenty replicates of every scenario, not selected by results.
            if i<20:
                more=bootstrap_concordance_interval(x[i],y[i],resamples=1999,seed=seed)
                tail.append(dict(scenario=name,n=n,replicate=i,seed=seed,
                                 status_999=r['status'],status_1999=more['status'],
                                 lower_999=r['lower'],upper_999=r['upper'],
                                 lower_1999=more['lower'],upper_1999=more['upper'],
                                 coverage_999=hit,coverage_1999=bool(more['status']=='ok' and more['lower']<=truth<=more['upper'])))
        p=covered/DRAWS;ci=previous.module.wilson(covered,DRAWS)
        baseline={m:lookup[name,n,m]['coverage_all'] for m in ('lin-z','empirical-z','empirical-normal')}
        rows.append(dict(scenario=name,n=n,true_CCC=truth,draws=DRAWS,resamples=RESAMPLES,
                         available=available,unavailable=reasons,covered=covered,coverage_all=p,
                         coverage_conditional=covered/available if available else None,
                         Monte_Carlo_SE=math.sqrt(p*(1-p)/DRAWS),Monte_Carlo_Wilson_95=ci,
                         input_pairs_sha256=tape_hash,index_hashes_sha256=indices_digest.hexdigest(),
                         mean_available_width=float(np.mean(widths)) if widths else None,
                         prior_same_observation_coverage=baseline,
                         screen_pass=bool(ci[0]>=.93 and ci[1]<=.97 and available/DRAWS>=.99)))
        print(name,n,'coverage',p,'available',available,'screen',rows[-1]['screen_pass'],flush=True)
    result=dict(date='2026-11-11',scope='source-only paired percentile CCC coverage; no public qualification',
                confidence=.95,draws_per_scenario=DRAWS,resamples=RESAMPLES,
                scenarios=len(rows),datasets=len(rows)*DRAWS,observed_tapes_verified=len(rows),
                NumPy_version=np.__version__,resampling_seed='20261113 + scenario_index*2000 + replicate_index; local PCG64',
                prior_report_sha256=hashlib.sha256(prior_path.read_bytes()).hexdigest(),
                engine_sha256=hashlib.sha256((ROOT/'inst/python/cpj_concordance_bootstrap.py').read_bytes()).hexdigest(),
                contract_sha256=hashlib.sha256((ROOT/'docs/validation-exports/python-concordance-bootstrap-contract-20261111.json').read_bytes()).hexdigest(),
                acceptance_rule='Every scenario: unconditional Wilson95 interval entirely within [.93,.97], availability>=.99; research screen only.',
                generic_screen_pass=all(r['screen_pass'] for r in rows),rows=rows,
                resample_count_sensitivity=dict(selection='first twenty observed datasets per scenario, fixed before outcomes',
                                                 comparisons=len(tail),rows=tail),
                clinical_review=False,native_integration=False)
    path=ROOT/'docs/validation-exports/python-concordance-bootstrap-coverage-20261111.json'
    path.write_text(json.dumps(result,indent=2)+'\n')
    print('coverage report',hashlib.sha256(path.read_bytes()).hexdigest(),flush=True)


if __name__=='__main__':main()
