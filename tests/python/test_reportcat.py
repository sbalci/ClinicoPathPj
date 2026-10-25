import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'inst/python'))
import cpj_runtime
from cpjtest import factor,number


def run(columns):
    return cpj_runtime.execute(dict(analysis='pyreportcat',columns=columns,options={'vars':list(columns)}))

class CategoricalReport(unittest.TestCase):
    def test_ties_unused_levels_literal_na_and_denominators(self):
        r=run({'Grade [x]':factor(['NA','High','NA','High',None],['High','NA','unused'])})
        self.assertEqual(r['status'],'ok',r.get('error'))
        row=r['tables']['overview']['rows'][0]
        self.assertEqual((row['valid'],row['missing'],row['declared'],row['observed']),(4,1,3,2))
        self.assertEqual(row['mode'],'High, NA')
        self.assertEqual([x['n'] for x in r['tables']['frequencies']['rows']],[2,2,0])
        self.assertEqual([x['validPercent'] for x in r['tables']['frequencies']['rows']],[.5,.5,0])
        self.assertEqual([x['totalPercent'] for x in r['tables']['frequencies']['rows']],[.4,.4,0])
        self.assertIn('equally',r['texts']['reportSentences'])

    def test_ordered_levels_keep_their_order(self):
        nominal=factor(['G2','G2','G1'],['G1','G2','G3'])
        ordinal=dict(nominal,ordered=True)
        self.assertEqual([r['level'] for r in run({'g':ordinal})['tables']['frequencies']['rows']],['G1','G2','G3'])
        self.assertEqual([r['level'] for r in run({'g':nominal})['tables']['frequencies']['rows']],['G2','G1','G3'])

    def test_empty_columns_are_excluded_without_hiding_valid_results(self):
        r=run({'good':factor(['a',None]),'empty':factor([None,None],['NA','unused'])})
        self.assertEqual(r['status'],'ok')
        self.assertEqual(len(r['tables']['overview']['rows']),1)
        self.assertTrue(any('excluded' in n['text'] for n in r['notices']))
        self.assertEqual(run({'empty':factor([None],['NA'])})['status'],'input_error')
        self.assertEqual(run({'empty':factor([],['NA'])})['status'],'input_error')
        self.assertEqual(run({'numeric':number([1,2])})['status'],'input_error')

    def test_sparse_warning_ignores_unused_levels_and_high_missingness_is_not_averaged_away(self):
        r=run({'a':factor(['x']*30+['y']*30, ['x','y','unused']),
               'b':factor(['yes']*6+[None]*54,['yes'])})
        self.assertFalse(any('fewer than 5' in n['text'] for n in r['notices']))
        self.assertIn('90\\.0\\%',r['texts']['clinicalSummary'])
        self.assertTrue(any('90.0%' in n['text'] for n in r['notices']))
