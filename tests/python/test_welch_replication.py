"""Independent replication, source provenance and coverage-failure detection."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('welch_replication', ROOT/'tools/check-welch-replication.py')
oracle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oracle)


class WelchReplication(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(oracle.MANIFEST.read_text())
        cls.draws = oracle.load_draws()

    def test_independent_replay_and_original_observation_audits(self):
        result = oracle.verify(self.manifest, self.draws)
        self.assertEqual(result['draws'], 84000)
        self.assertEqual(result['fixture_hashes'][oracle.MANIFEST.name],
                         'f5dd0b3ec68bb5bd7825b7442b6e9c4488fe31856bd84f3d8056811b55ce59bd')
        self.assertEqual(result['fixture_hashes'][oracle.DRAWS.name],
                         '9bb8bbc1294428ed0857b2e84dc4b40745034f02a1e3cc2436c1919cf4895fcc')
        self.assertEqual(len(result['profiles']), 17)
        self.assertGreaterEqual(result['selected_original_dataset_audits'], 34)
        self.assertEqual(result['passed']+result['failed']+result['inconclusive'], 17)
        self.assertLessEqual(result['maximum_R_SciPy_CDF_difference'], 2e-9)

    def test_simultaneous_bounds_all_datasets_and_extreme_counts(self):
        for k, n, expected in ((0, 4000, 'fail'), (4000, 4000, 'pass'),
                               (3800, 4000, 'pass'), (3500, 4000, 'fail')):
            low, high, status = oracle.coverage_bounds(k, n)
            self.assertEqual(status, expected)
            self.assertTrue(0 <= low <= high <= 1)
        self.assertEqual(oracle.coverage_bounds(0, 4000)[0], 0)
        self.assertEqual(oracle.coverage_bounds(4000, 4000)[1], 1)
        low, high, status = oracle.coverage_bounds(1883, 2000, 12)
        self.assertEqual(status, 'inconclusive')
        self.assertAlmostEqual(low, .9248927653162874)
        # Discarding unsupported intervals can turn zero availability into a
        # misleading denominator; the decision always retains all requested draws.
        self.assertEqual(oracle.coverage_bounds(0, 4000)[2], 'fail')
        for args in ((-1, 3), (4, 3), (1., 3), (0, 0), (True, 3)):
            with self.assertRaises(ValueError): oracle.coverage_bounds(*args)

    def test_rejects_changed_engine_or_prior_reference_hash(self):
        for path in ('inst/python/cpj_welch_standardized.py',
                     'tests/fixtures/welch-standardized-coverage.json'):
            manifest = copy.deepcopy(self.manifest)
            manifest['source_hashes'][path] = '0'*64
            with self.subTest(path=path), self.assertRaises(AssertionError):
                oracle.verify(manifest, self.draws)

    def test_rejects_corrupted_probability_and_missing_or_duplicated_replicates(self):
        for change in ('probability', 'missing', 'duplicate'):
            draws = self.draws.copy()
            if change == 'probability': draws['R_probability'][0] += .01
            elif change == 'missing': draws = draws[:-1]
            else: draws['replicate'][1] = draws['replicate'][0]
            with self.subTest(change=change), self.assertRaises(AssertionError):
                oracle.verify(self.manifest, draws)

    def test_rejects_fabricated_coverage_and_original_observation_corruption(self):
        for change in ('coverage', 'observation'):
            manifest = copy.deepcopy(self.manifest)
            if change == 'coverage': manifest['profiles'][0]['successes'] += 1
            else: manifest['selected'][0]['a'][0] += .5
            with self.subTest(change=change), self.assertRaises(AssertionError):
                oracle.verify(manifest, self.draws)

    def test_rejects_changed_real_engine_interval(self):
        original = oracle.between_welch_standardized
        def changed(*args, **kwargs):
            result = original(*args, **kwargs)
            if result['standardized']['status'] == 'ok':
                result['standardized']['delta_lower'] += .1
            return result
        with patch.object(oracle, 'between_welch_standardized', changed):
            with self.assertRaises(AssertionError): oracle.verify(self.manifest, self.draws)


if __name__ == '__main__': unittest.main()
