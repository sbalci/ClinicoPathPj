"""Native standardized adapters: independent R values, explicit models and clearing."""
import ast
import json
import sys
import unittest
from unittest.mock import patch

from cpjtest import ROOT, number, factor, run_analysis
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_runtime import execute
import cpj_standardized as engine

FIXTURES=json.loads((ROOT/'tests/fixtures/standardized-effects.json').read_text())['fixtures']


def request(case,run=None,**overrides):
    run=run or next(r for r in case['runs'] if r['confidence']==.95)
    paired=case['design']=='paired'
    if paired:
        columns=dict(First=number(case['a']),Second=number(case['b']))
        options=dict(dep1='First',dep2='Second')
    else:
        columns=dict(Outcome=number(case['values']),Group=dict(kind='factor',levels=case['levels'],
            codes=[None if c<0 else c for c in case['codes']]))
        options=dict(dep=['Outcome'],group='Group',firstLevel=case['first'],secondLevel=case['second'],varequal=True)
    options.update(conflevel=run['confidence'],showStandardized=True,showCases=True)
    options.update(overrides)
    n=len(case['a'] if paired else case['values'])
    return dict(analysis='pyjjwithinstats' if paired else 'pyjjbetweenstats',columns=columns,
                options=options,row_ids=[str(10+3*i) for i in range(n)])


class StandardizedAdapters(unittest.TestCase):
    def test_all_160_independent_R_configurations(self):
        for case in FIXTURES:
            for ref in case['runs']:
                with self.subTest(case=case['id'],confidence=ref['confidence']):
                    got=execute(request(case,ref))
                    self.assertEqual(got['status'],'ok',got.get('error'))
                    row=got['tables']['standardized']['rows'][0]
                    for column,key in [('estimate','cohens_d'),('sd','standardizer_sd'),('df','df'),('lower','delta_lower'),('upper','delta_upper')]:
                        target=ref[key]
                        if target is None:self.assertIsNone(got['tables']['standardizer']['rows'][0][column] if column in ('sd','df') else row[column])
                        else:self.assertLessEqual(abs((got['tables']['standardizer']['rows'][0][column] if column in ('sd','df') else row[column])-target),2e-7*max(1,abs(target)))
                    self.assertEqual(row['status'],ref['status'])
                    g=got['tables']['hedges']['rows'][0]
                    for key,target in [('estimate',ref['hedges_g']),('correction',ref['correction'])]:
                        if target is None:self.assertIsNone(g[key])
                        else:self.assertLessEqual(abs(g[key]-target),abs(target)*1e-10)
                    self.assertNotIn('lower',g);self.assertNotIn('upper',g)
                    self.assertEqual(g['metric'],'Hedges g_z (point only)' if case['design']=='paired' else 'Hedges g (point only)')
                    if ref['cohens_d'] is None:
                        self.assertNotIn('standardizedPlot',got['plots'])
                    else:
                        plot=got['plots']['standardizedPlot']
                        self.assertEqual(plot['columns']['estimate'],[row['estimate']])
                        self.assertEqual(plot['columns']['lower'],[row['lower']])
                        self.assertEqual(plot['columns']['upper'],[row['upper']])
                        self.assertEqual(plot['reference'],0)
                    json.dumps(got,allow_nan=False)

    def test_raw_tables_and_plots_unchanged_on_off_and_Welch(self):
        for paired in (False,True):
            case=next(f for f in FIXTURES if (f['design']=='paired')==paired)
            on=execute(request(case));off=execute(request(case,showStandardized=False))
            for name in ('cohort','missing','descriptives','contrast','cases'):
                self.assertEqual(on['tables'][name],off['tables'][name])
            self.assertEqual(on['plots']['differencePlot'],off['plots']['differencePlot'])
            self.assertNotIn('standardized',off['tables']);self.assertNotIn('hedges',off['tables'])
            self.assertNotIn('standardizer',off['tables'])
            self.assertNotIn('standardizedPlot',off['plots'])
            raw_hidden=execute(request(case,showPlot=False))
            self.assertNotIn('differencePlot',raw_hidden['plots'])
            self.assertIn('standardizedPlot',raw_hidden['plots'])
            if not paired:
                unsupported=execute(request(case,varequal=False))
                raw=execute(request(case,varequal=False,showStandardized=False))
                self.assertEqual(unsupported['status'],'ok')
                self.assertEqual({k:v for k,v in unsupported['tables'].items() if k not in ('welchStandardizer','welchEffect')},raw['tables'])
                self.assertIn('welchEffect',unsupported['tables'])
                self.assertEqual(unsupported['plots'],raw['plots'])
                self.assertFalse(any('Raw Welch results are retained' in n['text'] for n in unsupported['notices']))

    def test_subprocess_bridge_both_designs(self):
        for paired in (False,True):
            case=next(f for f in FIXTURES if (f['design']=='paired')==paired)
            req=request(case)
            got=run_analysis(req['analysis'],req['columns'],req['options'],row_ids=req['row_ids'])
            self.assertEqual(got['status'],'ok',got.get('error'))
            self.assertEqual(len(got['tables']['standardized']['rows']),1)
            self.assertEqual(len(got['tables']['hedges']['rows']),1)
            self.assertIn('population\\-delta',got['texts']['summary'])

    def test_unavailable_interval_keeps_points_and_degenerate_has_nulls(self):
        case=next(f for f in FIXTURES if f['design']=='paired')
        with patch.object(engine,'_noncentral_interval',side_effect=ArithmeticError('Forced nonconvergence')):
            got=execute(request(case))
        self.assertEqual(got['status'],'ok')
        row=got['tables']['standardized']['rows'][0]
        self.assertEqual(row['status'],'interval_unavailable')
        self.assertIsNone(row['lower']);self.assertIsNone(row['upper'])
        self.assertIsNotNone(row['estimate'])
        self.assertEqual(got['tables']['hedges']['rows'][0]['status'],'point_available')
        self.assertTrue(any('Forced nonconvergence' in n['text'] for n in got['notices']))
        case=next(f for f in FIXTURES if f['id']=='constant_difference')
        got=execute(request(case))
        self.assertEqual(got['status'],'ok')
        self.assertIsNone(got['tables']['standardized']['rows'][0]['estimate'])
        self.assertEqual(got['tables']['hedges']['rows'][0]['status'],'unavailable')

    def test_validation_and_off_switch_do_not_call_engine(self):
        case=FIXTURES[0]
        with patch.object(engine,'between_standardized',side_effect=RuntimeError('must not call')):
            self.assertEqual(execute(request(case,showStandardized=False))['status'],'ok')
            self.assertEqual(execute(request(case,varequal=False))['status'],'ok')
        for bad in (1,'yes',None):
            self.assertEqual(execute(request(case,showStandardized=bad))['status'],'input_error')
        req=request(case);req['options']['secondLevel']=None
        self.assertEqual(execute(req)['status'],'input_error')
        req=request(case);req['options']['effsizetype']='unbiased'
        self.assertEqual(execute(req)['status'],'input_error')

    def test_specs_default_off_labels_and_option_gating(self):
        for name,paired in [('pyjjbetweenstats',False),('pyjjwithinstats',True)]:
            tree=ast.parse((ROOT/f'inst/python/analyses/jjstatsplot/{name}.py').read_text())
            spec=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SPEC' for t in n.targets)))
            options={o['name']:o for o in spec['options']}
            self.assertFalse(options['showStandardized']['default'])
            if not paired:self.assertFalse(options['varequal']['default'])
            results={r['name']:r for r in spec['results']}
            for key in ('standardizer','standardized','hedges','standardizedPlot'):
                self.assertEqual(results[key]['visible'],'(showStandardized)' if paired else '(showStandardized && varequal)')
            self.assertFalse(any(c['name'] in ('lower','upper') for c in results['hedges']['columns']))
            controls=[c for b in spec['ui']['children'] for c in b.get('children',[]) if c.get('name')=='showStandardized']
            self.assertEqual(len(controls),1)
            if not paired:self.assertNotIn('enable',controls[0])


if __name__=='__main__':unittest.main()
