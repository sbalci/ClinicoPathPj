"""Offline paired Monte Carlo comparison of ICC(2,k) interval candidates.

Gaussian crossed random effects only; not clinical validation or a release gate.
Both candidates see each identical matrix. Withheld intervals count as not covering
in unconditional coverage; conditional coverage and withholding are also reported.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import sys
import numpy as np
import scipy
from scipy.stats import binomtest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'inst/python'))
from cpj_icc import calculate_icc


def summary(covered, returned, total):
    limits = binomtest(covered, total).proportion_ci(.95, method='exact')
    return dict(covered=covered, returned=returned, withheld=total-returned,
                return_rate=returned/total,
                unconditional_coverage=covered/total,
                conditional_coverage=covered/returned if returned else None,
                monte_carlo_95_interval=[limits.low, limits.high])


def study(replicates=2000, seed=20261107):
    if isinstance(replicates, bool) or not isinstance(replicates, int) or not 100 <= replicates <= 20000:
        raise ValueError('Choose 100–20000 Monte Carlo replicates per configuration')
    configurations = list(itertools.product([6,20,60], [2,4], [.1,1.], [0.,.5]))
    seeds = np.random.SeedSequence(seed).spawn(len(configurations))
    results = []
    for index, (n,k,subject_variance,rater_variance) in enumerate(configurations):
        rng = np.random.default_rng(seeds[index])
        truth = subject_variance/(subject_variance+(rater_variance+1)/k)
        counts = {name:dict(covered=0,returned=0) for name in ['frozen_irr','transformed_single']}
        digest = hashlib.sha256()
        differences = []
        joint = dict(both=0, frozen_only=0, transformed_only=0, neither=0)
        example = None
        undefined = 0
        for _ in range(replicates):
            subjects = rng.normal(0, np.sqrt(subject_variance), (n,1))
            raters = rng.normal(0, np.sqrt(rater_variance), (1,k))
            matrix = subjects+raters+rng.normal(0,1,(n,k))
            digest.update(matrix.astype('<f8',copy=False).tobytes())
            result = calculate_icc(matrix,'icc2k')
            if example is None:
                example = dict(ratings=matrix.tolist(),result=result)
            undefined += result['estimate'] is None
            covered = {}
            for name, count in counts.items():
                interval = result['candidate_intervals'].get(name)
                count['returned'] += interval is not None
                covered[name] = interval is not None and interval[0] <= truth <= interval[1]
                count['covered'] += int(covered[name])
            differences.append(int(covered['transformed_single'])-int(covered['frozen_irr']))
            key = ('both' if covered['frozen_irr'] and covered['transformed_single'] else
                   'frozen_only' if covered['frozen_irr'] else
                   'transformed_only' if covered['transformed_single'] else 'neither')
            joint[key] += 1
        differences = np.asarray(differences,float)
        results.append(dict(n=n,k=k,subject_variance=subject_variance,rater_variance=rater_variance,
                            error_variance=1,true_average_icc=truth,replicates=replicates,
                            undefined_estimates=undefined,draw_sha256=digest.hexdigest(),
                            intervals={name:summary(**count,total=replicates) for name,count in counts.items()},
                            paired_outcome_counts=joint,oracle_example=example,
                            paired_coverage_difference=float(differences.mean()),
                            paired_difference_mc_se=float(differences.std(ddof=1)/np.sqrt(replicates))))
    return dict(scope='Gaussian balanced independent cases with crossed random raters',
                seed=seed,confidence=.95,replicates_per_configuration=replicates,
                configurations=len(results),total_matrices=len(results)*replicates,
                draw_contract='SeedSequence child per ordered configuration; common matrix for both candidates',
                numpy_version=np.__version__,scipy_version=scipy.__version__,
                engine_sha256=hashlib.sha256((ROOT/'inst/python/cpj_icc.py').read_bytes()).hexdigest(),
                study_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                limitations=['No nonnormal, heteroscedastic, missingness or repeated-case coverage study',
                             'Random rater effects are sampled anew for every matrix',
                             'Returned-only coverage is conditional and does not replace unconditional coverage',
                             'This study cannot establish clinical readiness or exact nominal coverage'],
                results=results)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--replicates',type=int,default=2000)
    parser.add_argument('--seed',type=int,default=20261107)
    args = parser.parse_args()
    print(json.dumps(study(args.replicates,args.seed),indent=2))
