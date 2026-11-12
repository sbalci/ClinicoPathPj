"""Paired diagnostic source contract, independent R fixture and adversarial inputs."""
import copy
import importlib.util
import json
import sys
import unittest

import numpy as np
from cpjtest import ROOT
sys.path.insert(0, str(ROOT/'inst/python'))
from cpj_paired_decision import MAX_ROWS, mcnemar_discordance, paired_decision
from cpj_runtime import Factor, InputError

loader = importlib.util.spec_from_file_location('paired_reference_check', ROOT/'tools/check-paired-decision.py')
oracle = importlib.util.module_from_spec(loader)
loader.loader.exec_module(oracle)
FIXTURES = json.loads((ROOT/'tests/fixtures/paired-decision.json').read_text())['fixtures']


def example(name='hand_correctness_not_positivity'):
    return oracle.inputs(next(f for f in FIXTURES if f['id'] == name))


class PairedDecision(unittest.TestCase):
    def test_independent_base_R_fixtures(self):
        report = oracle.verify()
        self.assertEqual(report['failures'], 0)
        self.assertGreater(report['checks'], 10000)

    def test_published_example_and_equal_discordance_definition(self):
        self.assertAlmostEqual(mcnemar_discordance(1, 7)['p'], .0390625, places=14)
        self.assertAlmostEqual(mcnemar_discordance(1, 7, 'exact')['p'], .0703125, places=14)
        self.assertAlmostEqual(mcnemar_discordance(6, 16)['p'], .03468966484069824)
        self.assertAlmostEqual(mcnemar_discordance(1, 1)['p'], .75, places=14)
        self.assertEqual(mcnemar_discordance(1, 1, 'asymptotic')['p'], 1.)
        self.assertEqual(mcnemar_discordance(0, 0)['status'], 'no_discordance')

    def test_correctness_is_not_raw_positivity(self):
        args = example(); got = paired_decision(**args)
        truth = args['reference'].codes == 1
        a, b = (args['tests'][name].codes == 1 for name in ['A', 'B'])
        row = got['pairs'][0]['accuracy']
        self.assertEqual(row['counts'][1], int(np.sum((a == truth) & (b != truth))))
        self.assertNotEqual(row['counts'][1], int(np.sum(a & ~b)))

    def test_test_reversal_changes_difference_sign_only(self):
        args = example('different_missingness'); a = paired_decision(**args)
        args['tests'] = dict(reversed(list(args['tests'].items())))
        b = paired_decision(**args)
        for metric in ['accuracy', 'sensitivity', 'specificity']:
            x, y = a['pairs'][0][metric], b['pairs'][0][metric]
            self.assertAlmostEqual(x['difference'], -y['difference'])
            self.assertAlmostEqual(x['p'], y['p'])
            self.assertEqual(x['counts'], [y['counts'][0], y['counts'][2], y['counts'][1], y['counts'][3]])

    def test_explicit_orientation_reversal(self):
        args = example('different_missingness'); a = paired_decision(**args)
        args['reference_levels'] = tuple(reversed(args['reference_levels']))
        args['test_levels'] = {k: tuple(reversed(v)) for k, v in args['test_levels'].items()}
        b = paired_decision(**args)
        for name in args['tests']:
            x, y = a['models'][name], b['models'][name]
            self.assertEqual(x['counts'], list(reversed(y['counts'])))
        self.assertEqual(a['pairs'][0]['accuracy'], b['pairs'][0]['accuracy'])
        self.assertEqual(a['pairs'][0]['sensitivity'], b['pairs'][0]['specificity'])

    def test_cohort_exclusion_partition_and_original_positions(self):
        got = paired_decision(**example('explicit_other_exclusion'))
        self.assertEqual(got['retained_indices'], [0, 1, 2, 3])
        self.assertEqual((got['excluded_missing'], got['excluded_indeterminate']), (1, 3))
        self.assertEqual(got['n_source'], got['n_complete']+got['excluded_missing']+got['excluded_indeterminate'])
        self.assertEqual(got['indeterminate_by_role']['A'], 2)
        self.assertEqual(got['factor_levels']['A'][-1], 'unused')
        args = example('explicit_other_exclusion'); args['exclude_indeterminate'] = False
        with self.assertRaisesRegex(InputError, 'outside'):
            paired_decision(**args)

    def test_common_cohort_changes_when_third_test_added(self):
        args = example('different_missingness'); a = paired_decision(**args)
        new = args['tests']['A'].codes.copy(); new[0] = -1
        args['tests']['C'] = Factor(new, args['tests']['A'].levels)
        args['test_levels']['C'] = args['test_levels']['A']
        b = paired_decision(**args)
        self.assertEqual(b['n_complete'], a['n_complete']-1)
        self.assertTrue(all(p['accuracy']['n'] == b['n_complete'] for p in b['pairs']))

    def test_absent_class_is_undefined_not_no_discordance(self):
        got = paired_decision(**example('one_class_positive'))
        row = got['pairs'][0]['specificity']
        self.assertEqual(row['status'], 'absent_class')
        self.assertIsNone(row['p']); self.assertIsNone(row['difference'])
        self.assertIsNone(got['models']['A']['proportions'][1]['estimate'])
        same = paired_decision(**example('no_discordance'))
        self.assertEqual(same['pairs'][0]['accuracy']['p'], 1.)
        self.assertEqual(same['pairs'][0]['accuracy']['status'], 'no_discordance')

    def test_holm_family_excludes_no_discordance_and_none_preserves_raw(self):
        args = example('holm_excludes_duplicate'); got = paired_decision(**args)
        self.assertEqual(got['holm_family'], 2)
        self.assertTrue(got['holm_applied'])
        self.assertEqual(got['pairs'][0]['accuracy']['p_adjusted'], 1.)
        for p in got['pairs'][1:]:
            self.assertAlmostEqual(p['accuracy']['p_adjusted'], 2*p['accuracy']['p'])
            self.assertNotIn('p_adjusted', p['sensitivity'])
        raw = paired_decision(**args, adjustment='none')
        self.assertFalse(raw['holm_applied'])
        self.assertTrue(all(p['accuracy']['p_adjusted'] == p['accuracy']['p'] for p in raw['pairs']))

    def test_count_validation_and_resource_bounds(self):
        for bad in [True, -1, .5, float('inf'), float('nan'), '1', None, 1000001]:
            for position in [0, 1]:
                counts = [1, 1]; counts[position] = bad
                with self.subTest(value=bad, position=position), self.assertRaises(InputError):
                    mcnemar_discordance(*counts)
        with self.assertRaises(InputError): mcnemar_discordance(600000, 600000)
        for method in ['auto', None, 1, []]:
            with self.assertRaises(InputError): mcnemar_discordance(1, 1, method)
        large = mcnemar_discordance(0, 1000)
        self.assertGreaterEqual(large['p'], 0.); self.assertLess(large['p'], 1e-250)

    def test_options_validation(self):
        for key, values in {'confidence': [True, .79, 1, None, '95', float('nan')],
                            'method': ['auto', [], None], 'adjustment': ['BH', [], None],
                            'exclude_indeterminate': [1, None, 'yes']}.items():
            for value in values:
                args = example(); args[key] = value
                with self.subTest(key=key, value=value), self.assertRaises(InputError):
                    paired_decision(**args)

    def test_factor_and_mapping_validation(self):
        levels = ['Negative', 'Positive']
        bad_roles = [Factor([True, 1]*8, levels), Factor(np.array([0., 1.]*8), levels),
                     Factor(np.array([0, -2]*8), levels), Factor(np.array([0, 2]*8), levels),
                     Factor(np.array([[0, 1]]*8), levels),
                     Factor(np.array([0, 1]*8), ['Positive', 'Positive']),
                     Factor(np.ma.array([0, 1]*8, mask=[False, True]*8), levels),
                     Factor([[0], [1, 0]], levels),
                     [0, 1]*8, Factor(np.array([0, 1]*8), [0, 1])]
        for role in bad_roles:
            args = example(); args['reference'] = role
            with self.subTest(role=str(role)), self.assertRaisesRegex(
                    InputError, 'factor|codes|integer|missing cells|labels|one-dimensional'):
                paired_decision(**args)
        for mapping in [None, ('Positive',), ('Positive', 'Positive'), ('Positive', 'absent')]:
            args = example(); args['reference_levels'] = mapping
            with self.subTest(mapping=mapping), self.assertRaises(InputError): paired_decision(**args)
        for tests in [{}, {'A': Factor(np.array([0, 1]), ['N', 'P'])}, {'reference': None, 'B': None}]:
            args = example(); args['tests'] = tests
            with self.assertRaises(InputError): paired_decision(**args)

    def test_empty_misaligned_all_missing_and_limit(self):
        for codes in [np.array([], dtype=int), np.array([-1]*16), np.zeros(MAX_ROWS+1, dtype=int),
                      np.array([0, 1], dtype=int)]:
            args = example(); args['reference'] = Factor(codes, args['reference'].levels)
            with self.assertRaises(InputError): paired_decision(**args)
        args = example(); args['test_levels'].pop('A')
        with self.assertRaises(InputError): paired_decision(**args)

    def test_inputs_not_mutated_and_output_json_safe(self):
        args = example(); before = copy.deepcopy(args)
        got = paired_decision(**args)
        np.testing.assert_array_equal(args['reference'].codes, before['reference'].codes)
        for name in args['tests']:
            np.testing.assert_array_equal(args['tests'][name].codes, before['tests'][name].codes)
        self.assertEqual(args['test_levels'], before['test_levels'])
        json.dumps(got, allow_nan=False)
        self.assertFalse(any(k in p['accuracy'] for p in got['pairs'] for k in ['lower', 'upper']))


if __name__ == '__main__': unittest.main()
