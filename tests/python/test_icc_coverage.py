"""Audit simulation accounting without treating stochastic evidence as release approval."""
import json
import math
import runpy
import unittest
from unittest import mock
from cpjtest import ROOT

STUDY = runpy.run_path(str(ROOT/'tools/study-icc-coverage.py'))


class ICCCoverage(unittest.TestCase):
    def test_average_parameterization_identity(self):
        for rho in [.01,.2,.7,.99]:
            for k in [2,4,20]:
                for n in [6,20,60]:
                    average = k*rho/(1+(k-1)*rho)
                    single_a = k*rho/(n*(1-rho))
                    average_a = average/(n*(1-average))
                    self.assertAlmostEqual(single_a,average_a,places=10)

    def test_withholding_denominators_and_paired_draw_contract(self):
        seen = []
        def engine(matrix,*args):
            seen.append(matrix.copy())
            return dict(estimate=.5,candidate_intervals=dict(frozen_irr=[0,1],transformed_single=None))
        with mock.patch.dict(STUDY['study'].__globals__,calculate_icc=engine):
            result = STUDY['study'](100,42)
        self.assertEqual(len(seen),2400)
        for row in result['results']:
            self.assertEqual(row['intervals']['frozen_irr']['unconditional_coverage'],1)
            transformed = row['intervals']['transformed_single']
            self.assertEqual(transformed['unconditional_coverage'],0)
            self.assertIsNone(transformed['conditional_coverage'])
            self.assertEqual(transformed['withheld'],100)
            self.assertEqual(row['paired_coverage_difference'],-1)
            self.assertEqual(row['paired_difference_mc_se'],0)

    def test_recorded_joint_counts_and_coverage_accounting(self):
        report = json.loads((ROOT/'docs/validation-exports/python-icc-coverage-2026-11-07.json').read_text())
        self.assertEqual(report['total_matrices'],48000)
        self.assertEqual(len(report['results']),24)
        for row in report['results']:
            n = row['replicates'];joint=row['paired_outcome_counts']
            self.assertEqual(sum(joint.values()),n)
            self.assertEqual(row['intervals']['frozen_irr']['covered'],joint['both']+joint['frozen_only'])
            self.assertEqual(row['intervals']['transformed_single']['covered'],joint['both']+joint['transformed_only'])
            difference = (joint['transformed_only']-joint['frozen_only'])/n
            se = math.sqrt((joint['transformed_only']+joint['frozen_only']-n*difference**2)/(n-1)/n)
            self.assertAlmostEqual(row['paired_coverage_difference'],difference)
            self.assertAlmostEqual(row['paired_difference_mc_se'],se)
            for result in row['intervals'].values():
                self.assertEqual(result['withheld']+result['returned'],n)
                self.assertLessEqual(result['covered'],result['returned'])
                self.assertEqual(result['unconditional_coverage'],result['covered']/n)
                if result['returned']:
                    self.assertEqual(result['conditional_coverage'],result['covered']/result['returned'])

    def test_limits_and_summary(self):
        for value in [True,99,20001,1.5]:
            with self.assertRaises(ValueError):STUDY['study'](value)
        summary = STUDY['summary'](80,90,100)
        self.assertEqual(summary['unconditional_coverage'],.8)
        self.assertAlmostEqual(summary['conditional_coverage'],80/90)
        self.assertEqual(summary['withheld'],10)
        self.assertEqual(summary['return_rate'],.9)
