"""Matched teaching examples: independent fixtures, edge cases and route wiring."""
import copy
import math
import sys
import unittest
from cpjtest import ROOT, number, rows, run_analysis

sys.path.insert(0, str(ROOT / 'inst/python'))
sys.path.insert(0, str(ROOT / 'tools'))
import generate
from cpj_service_examples import summarize_values


class ServiceExamples(unittest.TestCase):
    def test_literal_summary(self):
        result = summarize_values([1, 2, 3, 4, None, 10])
        self.assertEqual({k: v for k, v in result.items() if k != 'sd'},
                         dict(input=6, n=5, missing=1, mean=4, median=3,
                              minimum=1, maximum=10))
        self.assertAlmostEqual(result['sd'], math.sqrt(12.5))

    def test_empty_singleton_and_invalid(self):
        for values in ([], [None, None]):
            result = summarize_values(values)
            self.assertEqual(result['n'], 0)
            self.assertIsNone(result['mean'])
            self.assertIsNone(result['sd'])
        self.assertIsNone(summarize_values([7])['sd'])
        for values in ([True], ['1'], [float('inf')], [float('nan')], [0] * 100001):
            with self.assertRaises(ValueError):
                summarize_values(values)

    def test_runtime_contract_and_fixed_routes(self):
        results = []
        for name, backend in [('pyservicedirect', 'processx'), ('pyservicepj', 'pj')]:
            spec = generate.read_spec(ROOT / f'inst/python/analyses/utilities/{name}.py')
            generate.validate(spec, name)
            self.assertIn(f'backend = "{backend}"', generate.b_r(spec, 'test'))
            result = run_analysis(name, {'x': number([1, 2, 3, 4, None, 10])},
                                  {'measurement': 'x'})
            self.assertEqual(result['status'], 'ok')
            results.append(rows(result, 'summary'))
        self.assertEqual(results[0], results[1])

    def test_fixed_route_validation(self):
        spec = generate.read_spec(ROOT / 'inst/python/analyses/meddecide/pybridgecompare.py')
        spec['executionBackend'] = 'pj'
        with self.assertRaises(generate.SpecError):
            generate.validate(spec, spec['name'])
        del spec['executionOption']
        generate.validate(spec, spec['name'])
        for value in ('unknown', 'pj;quit()', None, []):
            bad = copy.deepcopy(spec)
            bad['executionBackend'] = value
            with self.assertRaises(generate.SpecError):
                generate.validate(bad, bad['name'])
