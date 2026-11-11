"""Execute the source CCC interval prototype against independent frozen R values."""
import csv
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'inst/python'))
from cpj_concordance_uncertainty import concordance_interval


def decode(values):
    return [float('nan') if v in ('NA', 'NaN', None) else v for v in values]


def check():
    path = ROOT/'tests/fixtures/concordance-intervals.json'
    fixtures = json.loads(path.read_text())
    precise_path = ROOT/'tests/fixtures/concordance-intervals-mpfr.json'
    precise = json.loads(precise_path.read_text())
    high = {(f['id'],run['confidence']):run for f in precise['fixtures'] for run in f['runs']}
    transition_path = ROOT/'tests/fixtures/concordance-intervals-transition.json'
    transitions = json.loads(transition_path.read_text())
    adjudications = []
    rows = []
    available = unavailable = 0
    for fixture in fixtures['fixtures']:
        x, y = decode(fixture['x']), decode(fixture['y'])
        for run in fixture['runs']:
            base = run['base_r']['value']
            for method, label, limits in [('z-transform','desctools_z_transform','back_transformed_limits'),
                                           ('asymptotic','desctools_asymptotic','wald_limits')]:
                got = concordance_interval(x, y, run['confidence'], method)
                expected_status = 'ok' if base['inference_status']=='available' else 'unavailable'
                checks = [('status',got['status'],expected_status,'base-R domain policy')]
                if expected_status == 'ok':
                    available += 1
                    checks += [(key,got[key],expected,'base R') for key,expected in [
                        ('estimate',base['rho']),('variance',base['variance']),('se',base['se']),
                        ('lower',base[limits][0]),('upper',base[limits][1]),('n_complete',base['n'])]]
                    mp = high.get((fixture['id'],run['confidence']))
                    if method=='z-transform':
                        if mp is None:
                            checks += [('transformed_se',got['transformed_se'],base['z_se'],'base R')]
                        else:
                            adjudications.append(dict(case=fixture['id'],confidence=run['confidence'],
                                field='transformed_se',double_reference=base['z_se'],
                                MPFR256_reference=float(mp['z_se']),observed=got['transformed_se'],
                                double_reference_difference=abs(base['z_se']-float(mp['z_se']))))
                    if mp is not None:
                        checks += [(key,got[key],float(expected),'MPFR256 adjudication') for key,expected in [
                            ('estimate',mp['rho']),('variance',mp['variance']),('se',mp['se']),
                            ('lower',mp[limits][0]),('upper',mp[limits][1])]]
                        if method=='z-transform':
                            checks += [('transformed_se',got['transformed_se'],float(mp['z_se']),'MPFR256 adjudication')]
                    reference = run[label]['value']
                    checks += [('estimate',got['estimate'],reference['rho'],'DescTools'),
                               ('lower',got['lower'],reference['limits'][0],'DescTools'),
                               ('upper',got['upper'],reference['limits'][1],'DescTools')]
                else:
                    unavailable += 1
                    checks += [(key,got[key],None,'unavailable policy') for key in
                               ('lower','upper','se','variance','transformed_se')]
                    checks += [('reason_present',bool(got['reason']),True,'unavailable policy')]
                for field, observed, expected, oracle in checks:
                    numeric = (isinstance(expected,(int,float)) and not isinstance(expected,bool))
                    difference = abs(observed-expected) if numeric and observed is not None else None
                    passed = difference <= 1e-12 if difference is not None else observed == expected
                    rows.append(dict(case=fixture['id'],confidence=run['confidence'],method=method,
                                     field=field,oracle=oracle,observed=observed,expected=expected,
                                     absolute_difference=difference,passed=passed))
    for fixture in transitions['fixtures']:
        x = [float.fromhex(v) for v in fixture['input_hex']['x']]
        y = [float.fromhex(v) for v in fixture['input_hex']['y']]
        for mp in fixture['runs']:
            for method, limits in [('z-transform','back_transformed_limits'),('asymptotic','wald_limits')]:
                got = concordance_interval(x,y,mp['confidence'],method)
                available += 1
                checks = [('status',got['status'],'ok'),
                          ('arithmetic',got.get('arithmetic'),'decimal80_boundary')]
                checks += [(key,got[key],float(expected)) for key,expected in [
                    ('estimate',mp['rho']),('variance',mp['variance']),('se',mp['se']),
                    ('lower',mp[limits][0]),('upper',mp[limits][1])]]
                if method == 'z-transform':
                    checks += [('transformed_se',got['transformed_se'],float(mp['z_se']))]
                for field,observed,expected in checks:
                    numeric = isinstance(expected,(int,float))
                    difference = abs(observed-expected) if numeric else None
                    passed = difference <= 1e-12 if numeric else observed == expected
                    rows.append(dict(case=fixture['id'],confidence=mp['confidence'],method=method,
                                     field=field,oracle='MPFR256 transition',observed=observed,
                                     expected=expected,absolute_difference=difference,passed=passed))
    target=ROOT/'docs/validation-exports/python-concordance-interval-matrix-20261111.csv'
    with target.open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    failed=[row for row in rows if not row['passed']]
    differences=[row['absolute_difference'] for row in rows if row['absolute_difference'] is not None]
    report=dict(scope='source-only numerical interval prototype; not native or coverage qualification',
                reference_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                MPFR256_reference_sha256=hashlib.sha256(precise_path.read_bytes()).hexdigest(),
                transition_reference_sha256=hashlib.sha256(transition_path.read_bytes()).hexdigest(),
                adjudicated_double_intermediates=adjudications,
                cases=len(fixtures['fixtures'])+len(transitions['fixtures']),method_confidence_runs=available+unavailable,
                available=available,unavailable=unavailable,comparisons=len(rows),failures=len(failed),
                max_absolute_difference=max(differences),tolerance=1e-12,
                matrix_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                first_failures=failed[:20])
    (target.parent/'python-concordance-interval-numerical-20261111.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    return not failed


if __name__=='__main__':
    raise SystemExit(not check())
