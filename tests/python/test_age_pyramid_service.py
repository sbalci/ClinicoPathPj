"""Shared calculation with fixed Pj routing, frozen R oracles and unequal bars."""
import copy
import json
import sys
import unittest
from cpjtest import ROOT, factor, number
sys.path.insert(0, str(ROOT / 'inst/python'))
sys.path.insert(0, str(ROOT / 'tools'))
import generate
from cpj_runtime import execute
from cpj_plots import figure


class AgePyramidService(unittest.TestCase):
    def compare(self, columns, options):
        own = execute(dict(analysis='pyagepyramid', columns=columns, options=options))
        pj = execute(dict(analysis='pyagepyramidpj', columns=columns, options=options))
        self.assertEqual(own['status'], pj['status'])
        if own['status'] == 'ok':
            for key in ('tables', 'plots', 'notices'):
                self.assertEqual(own[key], pj[key], key)
            for key, value in own['texts'].items():
                self.assertEqual(pj['texts'][key], value)
            self.assertIn('Pj', pj['texts']['executionRoute'])
        else:
            self.assertEqual(own['error'], pj['error'])
        return pj

    def test_contract_is_identical_except_service_outputs(self):
        a = generate.read_spec(ROOT / 'inst/python/analyses/descriptives/pyagepyramid.py')
        b = generate.read_spec(ROOT / 'inst/python/analyses/utilities/pyagepyramidpj.py')
        generate.validate(b, b['name'])
        self.assertEqual(a['options'], b['options'])
        self.assertEqual(a['ui'], b['ui'])
        self.assertEqual(a['results'], b['results'][:-2])
        self.assertIn('backend = "pj"', generate.b_r(b, 'test'))

    def test_all_frozen_R_fixtures_and_display_modes(self):
        cases = json.loads((ROOT / 'tests/fixtures/demographic-oracles.json').read_text())['cases']
        for index, case in enumerate(cases):
            for display in ('count', 'percent'):
                with self.subTest(case=index, display=display):
                    columns = {'a': number(case['ages']), 'g': factor(case['gender'], ['Female', 'Male'])}
                    options = dict(age='a', gender='g', female='Female', male='Male',
                        age_groups=case['preset'], bin_width=case['width'],
                        custom_breaks=case['custom'], age_interval=case['interval'],
                        pct_base=case['percentage'], plot_values=display, showInterpretation=True)
                    result = self.compare(columns, options)
                    self.assertEqual(result['status'], 'ok', result.get('error'))
                    occupied = [i for i, (f, m) in enumerate(zip(case['female'], case['male'])) if f + m]
                    rows = result['tables']['population']['rows'][:-1]
                    self.assertEqual([r['female'] for r in rows], [case['female'][i] for i in occupied])
                    self.assertEqual([r['male'] for r in rows], [case['male'][i] for i in occupied])
                    for row, i in zip(rows, occupied):
                        for cell, key in [('femalePercent', 'fp'), ('malePercent', 'mp')]:
                            if case[key][i] is None:
                                self.assertIsNone(row[cell])
                            else:
                                self.assertAlmostEqual(row[cell], case[key][i], places=12)

    def test_unequal_bar_geometry_and_exclusions(self):
        columns = {'a': number([0, 1, 4, 5, 5, 9, 10, 10, 10, 14, 15, 20, 20, 20, 20, 65, 85, 90, None, -1, 30, 40]),
            'g': factor(['Female', 'Male', 'Female', 'Male', 'Male', 'Female', 'Female', 'Male', 'Male', 'Male', 'Female', 'Female', 'Female', 'Male', 'Male', 'Male', 'Female', 'Male', 'Female', 'Male', 'Other', None])}
        result = self.compare(columns, dict(age='a', gender='g', female='Female', male='Male', age_groups='who'))
        self.assertEqual([r['n'] for r in result['tables']['dataSummary']['rows']], [22, 2, 1, 1, 0, 18])
        rows = result['tables']['population']['rows']
        self.assertEqual([r['female'] for r in rows], [2, 1, 1, 1, 2, 0, 1, 8])
        self.assertEqual([r['male'] for r in rows], [1, 2, 3, 0, 2, 1, 1, 10])
        plot = figure(result['plots']['pyramid'])
        widths = [p.get_width() for p in plot.axes[0].patches]
        self.assertEqual([w for w in widths if w != 0],
                         [-2, -1, -1, -1, -2, -1, 1, 2, 3, 2, 1, 1])
        plot.clear()

    def test_labels_unused_levels_missing_data_and_recovery(self):
        columns = {'a': factor(['0', '65', 'bad', None], ['bad', '65', '0']),
                   'g': factor(['F_[x]', 'M_*', 'F_[x]', 'M_*'], ['M_*', 'unused', 'F_[x]'])}
        options = dict(age='a', gender='g', female='F_[x]', male='M_*', age_groups='who', showplot=False)
        good = self.compare(columns, options)
        self.assertFalse(good['plots'])
        bad = copy.deepcopy(options)
        bad['male'] = 'F_[x]'
        self.assertEqual(self.compare(columns, bad)['status'], 'input_error')
        self.assertEqual(self.compare({'a': number([None]), 'g': factor(['F_[x]'])}, options)['status'], 'input_error')
        self.assertEqual(self.compare(columns, options)['tables'], good['tables'])
