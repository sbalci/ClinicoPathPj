import sys
import unittest
import numpy as np
from cpjtest import ROOT, factor, number, text, run_analysis
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_runtime import Factor, InputError, _decode
from cpj_tableone import calculate


def f(values,levels=None):
    levels=levels or sorted(set(v for v in values if v is not None))
    return Factor(np.array([-1 if v is None else levels.index(v) for v in values],dtype=int),levels)


class TableOne(unittest.TestCase):
    def test_numeric_measurements_and_binary_second_level(self):
        d=dict(x=np.array([1.,2,np.nan,4]),g=f(['A','B',None,'B'],['B','A']))
        r=calculate(d,dict(vars=['x','g']))
        self.assertEqual((r['total'],r['retained'],r['completeBefore']),(4,4,3))
        x=r['continuous'][0];self.assertAlmostEqual(x['mean'],7/3)
        self.assertAlmostEqual(x['sd'],(7/3)**.5)
        self.assertEqual((x['valid'],x['missing'],x['missingPercent']),(3,1,.25))
        self.assertEqual([(v['level'],v['n'],v['valid'],v['percent']) for v in r['categories']],[('A',1,3,1/3)])

    def test_omitted_all_missing_does_not_destroy_complete_cases(self):
        d=dict(x=np.array([1.,2,np.nan,4]),g=f(['A',None,'B','B']),empty=np.full(4,np.nan))
        r=calculate(d,dict(vars=list(d),excl=True,showAllLevels=True))
        self.assertEqual((r['retained'],r['excluded'],r['included'],r['omitted']),(2,2,2,1))
        self.assertEqual(r['continuous'][0]['mean'],2.5)
        self.assertEqual(r['eligibility'][2]['status'],'Omitted: all values missing')

    def test_unsupported_date_omitted_before_exclusion(self):
        d=_decode(dict(x=number([1,None,3]),date=dict(kind='text',values=['2020-01-01',None,None],
                     storage=dict(classes=['Date'],dimensions=None,rows=3))))
        r=calculate(d,dict(vars=['x','date'],excl=True))
        self.assertEqual((r['retained'],r['omitted']),(2,1))
        self.assertIn('Date',r['eligibility'][1]['status'])

    def test_matrix_and_list_metadata_rejected_before_flattened_values(self):
        for classes,dimensions in [(['matrix','array'],[2,2]),(['list'],None)]:
            d=_decode(dict(x=dict(kind='number',values=[1,2,3,4],
                      storage=dict(classes=classes,dimensions=dimensions,rows=2))))
            with self.assertRaisesRegex(InputError,'matrix, array and list'):
                calculate(d,dict(vars=['x']))

    def test_true_missing_literal_labels_and_unused_levels(self):
        d=dict(g=Factor(np.array([0,1,2,-1]),['NA',None,'Unknown','unused']))
        r=calculate(d,dict(vars=['g']))
        self.assertEqual([(v['level'],v['n']) for v in r['categories']],[('NA',1),('Unknown',1),('unused',0)])
        self.assertEqual(r['categories'][0]['missing'],2)

    def test_all_binary_levels_and_text_logical_categories(self):
        d=dict(text=['z','a',None,'z'],logical=[True,False,None,True])
        r=calculate(d,dict(vars=list(d)))
        self.assertEqual([(v['level'],v['n']) for v in r['categories']],[('z',2),('TRUE',2)])
        all_levels=calculate(d,dict(vars=list(d),showAllLevels=True))
        self.assertEqual([(v['level'],v['n']) for v in all_levels['categories']],
                         [('a',1),('z',2),('FALSE',1),('TRUE',2)])

    def test_no_eligible_and_zero_complete_are_explicit(self):
        r=calculate(dict(x=np.array([np.nan,np.nan])),dict(vars=['x'],excl=True))
        self.assertIsNone(r['retained']);self.assertIsNone(r['excluded'])
        self.assertEqual(r['continuous'],[]);self.assertIn('No eligible',r['reason'])
        r=calculate(dict(x=np.array([1.,np.nan]),y=np.array([np.nan,2.])),dict(vars=['x','y'],excl=True))
        self.assertEqual((r['retained'],r['excluded']),(0,2));self.assertEqual(r['continuous'],[])

    def test_singleton_constant_and_type7(self):
        d=dict(x=np.arange(1.,9),constant=np.ones(8),singleton=np.array([5.]+[np.nan]*7))
        r=calculate(d,dict(vars=list(d)))
        self.assertEqual((r['continuous'][0]['q1'],r['continuous'][0]['median'],r['continuous'][0]['q3']),(2.75,4.5,6.25))
        self.assertEqual(r['continuous'][1]['sd'],0)
        self.assertIsNone(r['continuous'][2]['sd'])
        self.assertEqual(len(r['continuous']),3) # low-distinct numeric columns remain measurements

    def test_storage_units_labels_and_legacy_values_are_separate(self):
        info=dict(classes=['numeric'],dimensions=None,rows=3,units=['mm'],label=['Tumour size'])
        d=_decode(dict(x=dict(kind='number',values=[1,2,3],storage=info)))
        self.assertIsInstance(d['x'],np.ndarray)
        r=calculate(d,dict(vars=['x']))
        self.assertEqual(r['eligibility'][0]['units'],'mm')
        self.assertEqual(r['eligibility'][0]['label'],'Tumour size')
        plain=calculate(dict(x=d['x']),dict(vars=['x']))
        self.assertEqual(plain['continuous'],r['continuous'])

    def test_runtime_optional_text_and_no_inferential_outputs(self):
        columns=dict(x=number([1,2,None,4]),g=factor(['<script>','Y',None,'Y']),empty=number([None]*4))
        a=run_analysis('pytableone',columns,dict(vars=list(columns),showAbout=True,showReportSentence=True))
        self.assertEqual(a['status'],'ok',a.get('error'))
        self.assertEqual(a['plots'],{});self.assertEqual(a['htmls'],{});self.assertNotIn('tests',a['tables'])
        self.assertIn('does not establish',a['texts']['report'])
        b=run_analysis('pytableone',columns,dict(vars=list(columns),cont='median'))
        self.assertEqual(a['tables'],b['tables']);self.assertNotIn('report',b['texts'])

    def test_invalid_inputs_and_resource_limits(self):
        good=dict(x=np.array([1.,2]))
        for data,options in [(good,dict(vars=[])),(good,dict(vars=['x','x'])),
                             (dict(x=np.array([1.,np.inf])),dict(vars=['x'])),
                             (dict(x=np.array([1.]),y=np.array([2.,3.])),dict(vars=['x','y'])),
                             (dict(x=np.ones(10001)),dict(vars=['x']))]:
            with self.assertRaises(InputError):calculate(data,options)
        with self.assertRaises(InputError):calculate(dict(g=f([str(i) for i in range(21)])),dict(vars=['g']))
