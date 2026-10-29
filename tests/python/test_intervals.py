import sys
import unittest
from datetime import date,timedelta
import numpy as np
from cpjtest import ROOT,text,run_analysis
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_intervals import calculate,DAYS_PER_UNIT
from cpj_runtime import _decode,InputError


def dates(days):
    return {'start':text(['2024-01-01']*len(days)),
            'end':text([None if d is None else str(date(2024,1,1)+timedelta(days=d)) for d in days])}


def calc(days,**kwargs):
    return calculate(_decode(dates(days)),dict(dx_date='start',fu_date='end',output_unit='days',**kwargs))


class Intervals(unittest.TestCase):
    def test_elapsed_units_and_arithmetic_summary(self):
        x=[0,1,2,6,10,30,31,60,365,366]
        for unit,divisor in DAYS_PER_UNIT.items():
            r=calculate(_decode(dates(x)),dict(dx_date='start',fu_date='end',output_unit=unit))
            np.testing.assert_allclose(r['values'],np.array(x)/divisor)
            self.assertAlmostEqual(r['statistics']['total'],871/divisor)
            self.assertAlmostEqual(r['statistics']['sd'],np.std(x,ddof=1)/divisor)
            self.assertAlmostEqual(r['statistics']['median'],20/divisor)
        r=calculate(_decode({'a':text(['2024-01-31 12:00:00']),
                             'b':text(['2024-02-29 18:00:00'])}),
                    dict(dx_date='a',fu_date='b',time_format='ymdhms',output_unit='days'))
        self.assertEqual(r['values'],[29.25])

    def test_landmark_boundary_and_zero_equivalence(self):
        x=[0,1,2,6,10,30,31,60,365,366]
        r=calc(x,use_landmark=True,landmark_time=6)
        self.assertEqual(r['values'],[None]*3+[0,4,24,25,54,359,360])
        self.assertEqual((r['n'],r['landmarkRemoved'],r['statistics']['total']),(7,3,826))
        self.assertEqual(calc(x)['values'],calc(x,use_landmark=True,landmark_time=0)['values'])

    def test_negative_policy_and_source_identifiers(self):
        with self.assertRaisesRegex(InputError,'Negative intervals'):calc([1,-1,6])
        with self.assertRaisesRegex(InputError,'source row IDs: 8'):
            calculate(_decode(dates([1,-1,6])),dict(dx_date='start',fu_date='end'),['2','8','40'])
        r=calc([1,-1,6],remove_negative=True)
        self.assertEqual(r['values'],[1,None,6]);self.assertEqual(r['negativeRemoved'],1)
        self.assertEqual(r['rows'][1]['status'],'Excluded negative interval')

    def test_raw_type7_extremes_and_filter_order(self):
        r=calc([1]*100+[10000],remove_extreme=True)
        self.assertEqual((r['q99'],r['threshold'],r['extremeRemoved'],r['n']),(1,2,1,100))
        r=calc([1]*50+[10000],remove_extreme=True)
        self.assertEqual(r['extremeRemoved'],0)
        self.assertTrue(any('cannot flag' in s for s in r['warnings']))
        r=calc([0]*200+[10],remove_extreme=True)
        self.assertIsNone(r['threshold']);self.assertEqual(r['extremeRemoved'],0)
        r=calc([-1]+[1]*99+[10000],remove_negative=True,remove_extreme=True,
               use_landmark=True,landmark_time=1)
        self.assertEqual((r['negativeRemoved'],r['extremeRemoved'],r['n']),(1,1,99))
        self.assertEqual(r['values'],[None]+[0]*99+[None])

    def test_ci_singleton_empty_and_constant(self):
        r=calc([0,4]);ci=r['uncertainty']
        # Independent analytic t(1) .975 quantile = tan(pi*(.975-.5)).
        margin=2*np.tan(np.pi*.475)
        self.assertAlmostEqual(ci['rawLower'],2-margin,places=8)
        self.assertEqual((ci['lower'],ci['clipped']),(0,'Yes'))
        self.assertAlmostEqual(ci['upper'],2+margin,places=8)
        r=calc([2]);self.assertIsNone(r['statistics']['sd']);self.assertIsNone(r['uncertainty']['upper'])
        r=calc([2,2]);self.assertEqual(r['uncertainty']['lower'],2)
        self.assertTrue(any('collapses' in s for s in r['warnings']))
        r=calc([1,2],use_landmark=True,landmark_time=10)
        self.assertEqual(r['n'],0);self.assertIsNone(r['statistics']['total'])
        self.assertEqual(r['values'],[None,None])

    def test_parse_guard_and_pair_accounting(self):
        d=dates([1,2,3,4,5]);d['end']=text(['2024-01-02']*4+['bad'])
        r=calculate(_decode(d),dict(dx_date='start',fu_date='end'))
        self.assertEqual((r['complete'],r['invalid'],r['missing']),(4,1,0))
        d['end']=text(['2024-01-02']*3+['bad',None])
        with self.assertRaisesRegex(InputError,'80%'):calculate(_decode(d),dict(dx_date='start',fu_date='end'))
        d={'start':text(['2024-01-01',None]),'end':text([None,'2024-01-02'])}
        with self.assertRaisesRegex(InputError,'No complete'):calculate(_decode(d),dict(dx_date='start',fu_date='end'))
        with self.assertRaisesRegex(InputError,'80%'):calc([None,None])

    def test_same_role_and_unsupported_or_invalid_choices(self):
        r=calculate(_decode(dates([1,2])),dict(dx_date='start',fu_date='start',output_unit='days'))
        self.assertEqual(r['values'],[0,0])
        for options in [dict(time_basis='calendar'),dict(time_format='auto'),dict(timezone='system'),
                        dict(confidence_level=89),dict(extreme_multiplier=1),dict(remove_negative=1),
                        dict(preview_rows=10.5),dict(use_landmark=True,landmark_time=-1)]:
            with self.assertRaises(InputError):calc([1,2],**options)

    def test_runtime_native_tables_and_saved_alignment(self):
        d=dates([0,1,6,10,None])
        ids=['2','8','20','30','45']
        r=run_analysis('pytimeinterval',d,dict(dx_date='start',fu_date='end',output_unit='days',
                     use_landmark=True,landmark_time=6,include_quality_metrics=True,show_summary=True),row_ids=ids)
        self.assertEqual(r['status'],'ok',r.get('error'))
        o=r['outputs']['calculated_time']
        self.assertEqual(o['values'],[None,None,0,4,None]);self.assertEqual(o['row_ids'],ids)
        self.assertEqual(o['title'],'Calculated interval');self.assertIn('days',o['description'])
        self.assertEqual(r['tables']['cohort']['rows'][0]['used'],2)
        self.assertEqual([x['source'] for x in r['tables']['preview']['rows']],ids)
        self.assertEqual(len(r['tables']['quality']['rows']),2)
        self.assertIn('2 of 5',r['texts']['report'])
        bad=run_analysis('pytimeinterval',dates([-1,1]),dict(dx_date='start',fu_date='end'))
        self.assertEqual(bad['status'],'input_error');self.assertFalse(bad.get('outputs'))
        r=run_analysis('pytimeinterval',dates([1]*30),dict(dx_date='start',fu_date='end',preview_rows=10))
        self.assertEqual(len(r['tables']['preview']['rows']),10)
        self.assertNotIn('quality',r['tables'])

if __name__=='__main__':unittest.main()
