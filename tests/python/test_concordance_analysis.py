"""Public CCC adapter: roles, frozen minimum, payloads and source identities."""
import json
import sys
import unittest

import numpy as np
from cpjtest import ROOT, number, text, factor, run_analysis
sys.path.insert(0, str(ROOT/'inst/python'))
from cpj_runtime import InputError, _decode
from cpj_concordance_analysis import run_concordance


class ConcordanceAnalysis(unittest.TestCase):
    def run_ccc(self, x=None, y=None, **options):
        x = list(range(10)) if x is None else x
        y = [v+1 for v in x] if y is None else y
        return run_analysis('pyagreement', {'a': number(x), 'b': number(y)},
                            dict(vars=['a', 'b'], method='ccc', **options))

    def test_public_population_moments_and_no_inference(self):
        result = self.run_ccc(showCCCPairs=True, cccPlot=True)
        self.assertEqual(result['status'], 'ok', result.get('error'))
        rows = result['tables']['cccStatistics']['rows']
        self.assertAlmostEqual(rows[0]['estimate'], 16.5/17.5)
        self.assertAlmostEqual(rows[1]['estimate'], 1.)
        self.assertAlmostEqual(rows[2]['estimate'], 16.5/17.5)
        self.assertEqual(set(rows[0]), {'measure', 'estimate'})
        self.assertIn('unavailable', str(result['tables']['cccStatistics']['notes']))
        self.assertEqual(len(result['tables']['cccPairs']['rows']), 10)
        for key in ('statistics', 'pairs', 'iccStatistics', 'iccCases'):
            self.assertFalse(result['tables'].get(key, {}).get('rows'))
        self.assertEqual(set(result['plots']), {'cccFigure'})
        self.assertFalse(result['outputs'])

    def test_ten_pair_minimum_and_incomplete_roles(self):
        for n in (0, 1, 3, 9):
            r = self.run_ccc(list(range(n)))
            self.assertEqual(r['status'], 'input_error')
            self.assertFalse(r.get('tables'))
        self.assertEqual(self.run_ccc()['status'], 'ok')
        r = run_analysis('pyagreement', {}, dict(vars=[], method='ccc'))
        self.assertEqual(r['status'], 'ok')
        self.assertIn('10 complete pairs', str(r['texts']))

    def test_frozen_R_fixtures_through_runtime(self):
        fixtures = json.loads((ROOT/'tests/fixtures/concordance-points.json').read_text())
        # Keep the public original PEFR example and seeded fixtures with >=10 pairs.
        selected = [f for f in fixtures['cases'] if f['n_complete'] >= 10]
        self.assertGreater(len(selected), 5)
        for f in selected:
            with self.subTest(f['id']):
                result = self.run_ccc(f['x'], f['y'])
                self.assertEqual(result['status'], 'ok', result.get('error'))
                rows = result['tables']['cccStatistics']['rows']
                for row, key in zip(rows, ('ccc', 'precision', 'bias_correction')):
                    self.assertAlmostEqual(row['estimate'], f['expected'][key], places=12)

    def test_missing_pairs_and_exact_case_labels(self):
        x = list(range(10))+[None, 11, None]
        y = list(range(10))+[10, None, None]
        data = {'a': number(x), 'b': number(y), 'ID': factor(['NA', '01']+[str(i) for i in range(2, 10)]+['01', None, '01'])}
        r = run_analysis('pyagreement', data, dict(vars=['a','b'], subject='ID', method='ccc', showCCCPairs=True),
                         row_ids=[str(100+i*3) for i in range(13)])
        self.assertEqual(r['status'], 'ok', r.get('error'))
        self.assertEqual(list(r['tables']['cccAudit']['rows'][0].values()), [13, 10, 3, 1, 1, 1])
        self.assertEqual(r['tables']['cccPairs']['rows'][0]['case'], 'NA')
        self.assertEqual(r['tables']['cccPairs']['rows'][1]['case'], '01')
        self.assertEqual(r['tables']['cccPairs']['rows'][-1]['sourceID'], '127')
        for ids in [['same']*13, [None]*13]:
            data['ID'] = text(ids)
            bad = run_analysis('pyagreement', data, dict(vars=['a','b'], subject='ID', method='ccc'))
            self.assertEqual(bad['status'], 'input_error')
            self.assertIn('unique case IDs', bad['error']['message'])
            self.assertFalse(bad['tables'])

    def test_constant_outputs_and_options_do_not_invent_intervals(self):
        equal = self.run_ccc([2]*10, [2]*10)
        self.assertEqual(equal['status'], 'ok')
        self.assertEqual([v['estimate'] for v in equal['tables']['cccStatistics']['rows']], [None]*3)
        self.assertIn('0/0', str(equal['notices']))
        unequal = self.run_ccc([2]*10, [3]*10)
        self.assertEqual([v['estimate'] for v in unequal['tables']['cccStatistics']['rows']], [0., None, 0.])
        base = self.run_ccc()
        changed = self.run_ccc(confLevel=.99, baConfidenceLevel=.99, iccType='icc11')
        self.assertEqual(base['tables'], changed['tables'])
        self.assertFalse(base['plots'])
        self.assertNotIn('cccPairs', base['tables'])

    def test_invalid_roles_storage_and_metadata(self):
        for variables in (['a','a'], ['a','b','c']):
            r = run_analysis('pyagreement', {n: number(range(10)) for n in 'abc'}, dict(vars=variables, method='ccc'))
            self.assertEqual(r['status'], 'input_error')
        for values in (factor(['a']*10), number([float('inf')]*10)):
            r = run_analysis('pyagreement', dict(a=values,b=number(range(10))), dict(vars=['a','b'], method='ccc'))
            self.assertEqual(r['status'], 'input_error')
        data = _decode(dict(a=number(range(10)), b=number(range(10))))
        data.metadata['a'] = dict(classes=['Date'])
        with self.assertRaisesRegex(InputError, 'not dates'):
            run_concordance(data, dict(vars=['a','b']), None)

    def test_static_plot_geometry_has_no_jitter_or_refit(self):
        from cpj_plots import figure
        r = self.run_ccc(cccPlot=True)
        state = r['plots']['cccFigure']
        fig = figure(state)
        ax = fig.axes[0]
        np.testing.assert_allclose(ax.collections[0].get_offsets(), np.column_stack([range(10), range(1,11)]))
        self.assertFalse(ax.lines)
        self.assertEqual(ax.get_xlabel(), 'a')
        self.assertEqual(ax.get_ylabel(), 'b')


if __name__ == '__main__':
    unittest.main()
