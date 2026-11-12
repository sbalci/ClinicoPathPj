"""Check source standardized effects against frozen independent R/package references."""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_runtime import Factor
from cpj_standardized import between_standardized, within_standardized, _noncentral_interval


def verify():
    fixture = ROOT/'tests/fixtures/standardized-effects.json'
    references = json.loads(fixture.read_text())
    checks, configs, maximum = 0, 0, 0.

    def compare(got, expected, key):
        nonlocal checks, maximum
        checks += 1
        if expected is None or isinstance(expected,str):
            assert got == expected,(key,got,expected)
        else:
            assert isinstance(got,(int,float)),(key,got,expected)
            error = abs(got-expected)
            # NCP inverse implementations differ; independent mixture tail grid
            # additionally checks difficult low/high-df and t=40 endpoints.
            if key in ('ncp_lower','ncp_upper','delta_lower','delta_upper'):
                tolerance = 2e-7*max(1,abs(expected))
            else:
                tolerance = abs(expected)*1e-10 if expected != 0 else 0
            assert error <= tolerance,(key,got,expected,error,tolerance)
            maximum = max(maximum,error/max(1,abs(expected)))

    for f in references['fixtures']:
        paired = f['design'] == 'paired'
        if paired:
            inputs = dict(first=f['a'],second=f['b'],standardizer='difference')
        else:
            inputs = dict(values=f['values'],group=Factor(np.array(f['codes'],dtype=int),f['levels']),
                          first_level=f['first'],second_level=f['second'],standardizer='pooled')
        call = within_standardized if paired else between_standardized
        for ref in f['runs']:
            result = call(**inputs,confidence=ref['confidence'])
            for key,value in ref.items():
                if key != 'confidence': compare(result['standardized'][key],value,key)
            json.dumps(result,allow_nan=False)
            configs += 1
    for grid in ('inversion_grid','mixture_grid'):
        for ref in references[grid]:
            lower,upper = _noncentral_interval(ref['t'],ref['df'],ref['confidence'])
            compare(lower,ref['ncp_lower'],'ncp_lower')
            compare(upper,ref['ncp_upper'],'ncp_upper')
    return dict(scope='Source-only pooled/difference standardized effects; no native/GUI qualification',
        datasets=len(references['fixtures']),configurations=configs,
        inversion_grid=len(references['inversion_grid']),mixture_grid=len(references['mixture_grid']),
        checks=checks,maximum_scaled_absolute_difference=maximum,
        point_relative_tolerance=1e-10,interval_scaled_absolute_tolerance=2e-7,
        package_cross_checks=references['package_cross_checks'],
        R_endpoint_mixture_checks=references['pt_endpoint_mixture_checks'],
        maximum_R_mixture_probability_residual=references['maximum_mixture_probability_residual'],
        fixture_sha256=hashlib.sha256(fixture.read_bytes()).hexdigest())


if __name__=='__main__':
    report = verify()
    (ROOT/'docs/validation-exports/python-standardized-effects-20261112.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
