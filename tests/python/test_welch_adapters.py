"""Welch native adapter contract: independent R point-only effects, no inference."""
import ast
import json
import sys
import unittest
from unittest.mock import patch

from cpjtest import ROOT, number, run_analysis
sys.path.insert(0, str(ROOT/'inst/python'))
from cpj_runtime import execute
import cpj_welch_standardized as engine

FIXTURES = json.loads((ROOT/'tests/fixtures/welch-standardized-effects.json').read_text())['fixtures']


def request(f, confidence=.95, **changes):
    options = dict(dep=['Outcome'], group='Group', firstLevel=f['first'], secondLevel=f['second'],
                   varequal=False, conflevel=confidence, showStandardized=True, showCases=True)
    options.update(changes)
    return dict(analysis='pyjjbetweenstats', columns=dict(Outcome=number(f['values']),
        Group=dict(kind='factor', levels=f['levels'], codes=[None if c<0 else c for c in f['codes']])),
        options=options, row_ids=[str(10+3*i) for i in range(len(f['values']))])


class WelchAdapters(unittest.TestCase):
    def test_all_110_independent_R_configurations(self):
        for f in FIXTURES:
            for ref in f['runs']:
                with self.subTest(case=f['id'], confidence=ref['confidence']):
                    got = execute(request(f, ref['confidence']))
                    self.assertEqual(got['status'], 'ok', got.get('error'))
                    effect = got['tables']['welchEffect']['rows'][0]
                    model = got['tables']['welchStandardizer']['rows'][0]
                    for observed, key in ((effect['estimate'], 'd_rms'), (model['sd'], 'standardizer_sd'),
                        (model['welch_df'], 'welch_df'), (model['sd_moment_df'], 'sd_moment_df')):
                        expected = ref[key]
                        if expected is None: self.assertIsNone(observed)
                        else: self.assertLessEqual(abs(observed-expected), abs(expected)*1e-10 if expected else 0)
                    self.assertEqual(effect['status'], 'degenerate' if ref['status']=='degenerate' else 'point_only')
                    self.assertEqual(effect['first'], f['first']); self.assertEqual(effect['second'], f['second'])
                    self.assertEqual(set(effect), {'first','second','estimate','status'})
                    self.assertEqual(set(model), {'denominator','sd','welch_df','sd_moment_df'})
                    for name in ('standardizer','standardized','hedges'):
                        self.assertNotIn(name, got['tables'])
                    self.assertNotIn('standardizedPlot', got['plots'])
                    self.assertTrue(any('no standardized confidence interval' in n for n in got['tables']['welchEffect']['notes']))
                    json.dumps(got, allow_nan=False)

    def test_no_plugin_interval_engine_calls_and_off_does_not_call_Welch_engine(self):
        f = FIXTURES[0]
        with patch.object(engine, '_plugin_interval', side_effect=RuntimeError('must not infer')):
            self.assertEqual(execute(request(f))['status'], 'ok')
        with patch.object(engine, 'between_welch_standardized', side_effect=RuntimeError('must not compute')):
            self.assertEqual(execute(request(f, showStandardized=False))['status'], 'ok')
            self.assertEqual(execute(request(f, varequal=True))['status'], 'ok')

    def test_raw_cohort_cases_plot_unchanged_and_point_confidence_invariance(self):
        f = next(f for f in FIXTURES if f['id']=='missing_factor_and_outcome')
        on, off = execute(request(f)), execute(request(f, showStandardized=False))
        for name in ('cohort','missing','descriptives','contrast','cases'):
            self.assertEqual(on['tables'][name], off['tables'][name])
        self.assertEqual(on['plots'], off['plots'])
        self.assertNotIn('welchEffect', off['tables'])
        self.assertNotIn('welchStandardizer', off['tables'])
        changed = execute(request(f, confidence=.8))
        for name in ('welchEffect','welchStandardizer'):
            self.assertEqual(on['tables'][name], changed['tables'][name])
        self.assertNotEqual(on['tables']['contrast']['rows'][0]['lower'], changed['tables']['contrast']['rows'][0]['lower'])

    def test_runtime_subprocess_labels_df1_and_degenerate(self):
        for id in ('unicode_literal_NA','one_constant_df1','both_constant'):
            req = request(next(f for f in FIXTURES if f['id']==id))
            got = run_analysis(req['analysis'], req['columns'], req['options'], row_ids=req['row_ids'])
            self.assertEqual(got['status'], 'ok', got.get('error'))
            self.assertIn('welchEffect', got['tables'])
            self.assertNotIn('hedges', got['tables'])
            self.assertNotIn('standardizedPlot', got['plots'])

    def test_SPEC_default_off_distinct_visibility_and_no_interval_columns(self):
        path = ROOT/'inst/python/analyses/jjstatsplot/pyjjbetweenstats.py'
        tree = ast.parse(path.read_text())
        spec = ast.literal_eval(next(n.value for n in tree.body if isinstance(n, ast.Assign)
            and any(isinstance(t,ast.Name) and t.id=='SPEC' for t in n.targets)))
        options = {o['name']:o for o in spec['options']}
        self.assertFalse(options['varequal']['default']); self.assertFalse(options['showStandardized']['default'])
        results = {r['name']:r for r in spec['results']}
        for key in ('welchStandardizer','welchEffect'):
            self.assertEqual(results[key]['visible'], '(showStandardized && !varequal)')
            self.assertFalse({'lower','upper','correction','confidence'} & {c['name'] for c in results[key]['columns']})
        for key in ('standardizer','standardized','hedges','standardizedPlot'):
            self.assertEqual(results[key]['visible'], '(showStandardized && varequal)')


if __name__ == '__main__': unittest.main()
