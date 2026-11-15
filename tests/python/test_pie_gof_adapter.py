"""Native fixed-null tables and strict labelled-ratio input, without new plot fitting."""
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_runtime import execute
from cpjtest import number,run_analysis

FIXTURES=json.loads((ROOT/'tests/fixtures/pie-gof-core.json').read_text())['fixtures']


def request(f,**opts):
    a=f['inputs'];columns={'Outcome':dict(kind='factor',codes=[None if c<0 else c for c in a['codes']],levels=a['levels'])}
    options=dict(dep='Outcome',**opts)
    if a['weights'] is not None:
        columns['Frequency']=number(a['weights']);options['counts']='Frequency'
    return dict(analysis='pyjjpiestats',columns=columns,options=options,
                row_ids=[str(9*i+4) for i in range(len(a['codes']))])


class PieGOFAdapter(unittest.TestCase):
    def test_all_independent_enabled_reference_runs_through_public_interface(self):
        for f in FIXTURES:
            for run in f['runs']:
                ref=run['expected'];custom=run['ratios'] is not None
                req=request(f,resultssubtitle=True,customRatios=custom,
                    ratio=json.dumps(run['ratios']) if custom else '')
                r=execute(req);self.assertEqual(r['status'],'ok',(f['id'],r.get('error')))
                row=r['tables']['gof']['rows'][0]
                for key in ('statistic','df','p'):
                    if ref[key] is None:self.assertIsNone(row[key])
                    else:self.assertAlmostEqual(row[key],ref[key],delta=max(1e-12,abs(ref[key])*1e-10))
                self.assertAlmostEqual(row['minimum'],ref['minimum_expected'])
                self.assertEqual(row['small'],ref['expected_below5'])
                self.assertEqual(row['null'],'Custom labelled ratios' if custom else 'Equal probabilities')
                expected=r['tables']['expected']['rows']
                self.assertEqual(len(expected),len(ref['rows']))
                for actual,e in zip(expected,ref['rows']):
                    self.assertEqual(actual['category'],e['label']);self.assertEqual(actual['code'],e['code'])
                    for key,source in [('observed','observed'),('probability','probability'),('expected','expected'),('residual','pearson_residual'),('contribution','contribution')]:
                        if e[source] is None:self.assertIsNone(actual[key])
                        else:self.assertAlmostEqual(actual[key],e[source],delta=2e-12*max(1,abs(e[source])))
                notices=r['notices']
                if ref['status']=='unavailable':self.assertTrue(any('only one declared' in n['text'] for n in notices))
                elif ref['sparse_warning']:self.assertTrue(any('below 5' in n['text'] for n in notices))

    def test_defaults_and_inactive_custom_input_leave_descriptives_and_plot_unchanged(self):
        f=FIXTURES[0];baseline=execute(request(f,showCases=True))
        with patch('cpj_pie_adapter._parse_ratios',side_effect=AssertionError('parsed')):
            off=execute(request(f,showCases=True,customRatios=True,ratio='invalid inactive text'))
        self.assertEqual(off['tables'],baseline['tables']);self.assertEqual(off['plots'],baseline['plots'])
        on=execute(request(f,showCases=True,resultssubtitle=True,ratio='ignored',customRatios=False))
        for name,table in baseline['tables'].items():self.assertEqual(on['tables'][name],table)
        self.assertEqual(on['plots'],baseline['plots'])
        self.assertNotIn('gof',off['tables']);self.assertNotIn('expected',off['tables'])

    def test_duplicate_and_executable_or_malformed_custom_text_is_refused(self):
        invalid=['{"A":1,"A":2,"B":1,"C":1}',
            '{"A":1,"\\u0041":2,"B":1,"C":1}',
            '{"A":NaN,"B":1,"C":1}','{"A":Infinity,"B":1,"C":1}',
            '[1,2,3]','1,2,3','true','{"A":1}',
            '{"A":true,"B":1,"C":1}','{"A":0,"B":1,"C":1}',
            '__import__("os").system("echo INVALID")','['*2000+']'*2000,
            '{"A":'+('1'*6000)+',"B":1,"C":1}','x'*20001]
        for value in invalid:
            r=execute(request(FIXTURES[0],resultssubtitle=True,customRatios=True,ratio=value))
            self.assertEqual(r['status'],'input_error',(value[:40],r.get('error')))

    def test_raw_labels_exact_mapping_and_reordering(self):
        f=next(f for f in FIXTURES if f['id']=='ordinal_unicode')
        ratios=f['runs'][1]['ratios']
        a=execute(request(f,resultssubtitle=True,customRatios=True,ratio=json.dumps(ratios)))
        b=execute(request(f,resultssubtitle=True,customRatios=True,ratio=json.dumps(dict(reversed(list(ratios.items()))))))
        self.assertEqual(a['tables']['gof'],b['tables']['gof'])
        self.assertEqual(a['tables']['expected'],b['tables']['expected'])
        bad=dict(ratios);bad['< A & B>']=bad.pop('<A & B>')
        self.assertEqual(execute(request(f,resultssubtitle=True,customRatios=True,ratio=json.dumps(bad)))['status'],'input_error')

    def test_expected_output_gate_does_not_change_the_test(self):
        first=execute(request(FIXTURES[0],resultssubtitle=True))
        hidden=execute(request(FIXTURES[0],resultssubtitle=True,showExpected=False))
        self.assertEqual(first['tables']['gof'],hidden['tables']['gof'])
        self.assertNotIn('expected',hidden['tables'])
        for key in ('resultssubtitle','customRatios','showExpected'):
            self.assertEqual(execute(request(FIXTURES[0],**{key:1}))['status'],'input_error')

    def test_actual_subprocess_with_custom_ratios(self):
        f=next(f for f in FIXTURES if f['id']=='perfect_custom_fit')
        req=request(f,resultssubtitle=True,customRatios=True,ratio=json.dumps(f['runs'][1]['ratios']))
        got=run_analysis(req['analysis'],req['columns'],req['options'],row_ids=req['row_ids'])
        self.assertEqual(got['status'],'ok',got.get('error'))
        self.assertEqual(got['tables']['gof']['rows'][0]['statistic'],0)
        self.assertEqual(got['tables']['gof']['rows'][0]['p'],1)


if __name__=='__main__':unittest.main()
