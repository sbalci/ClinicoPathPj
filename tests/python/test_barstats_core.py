"""Independent categorical references, denominator/geometry invariants and refusals."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_runtime import Factor,InputError,execute
import cpj_barstats as engine
from cpjtest import number,factor,text,run_analysis
s=importlib.util.spec_from_file_location('bar_oracle',ROOT/'tools/check-barstats-core.py')
oracle=importlib.util.module_from_spec(s);s.loader.exec_module(oracle)
FIXTURES=json.loads(oracle.FIXTURE.read_text())['fixtures']


def request(f,**opts):
    a=f['inputs'];columns=dict(Outcome=dict(kind='factor',codes=[None if c<0 else c for c in a['outcome_codes']],levels=a['outcome_levels']),
        Group=dict(kind='factor',codes=[None if c<0 else c for c in a['group_codes']],levels=a['group_levels']))
    options=dict(dep=['Outcome'],group='Group')
    if a['weights'] is not None:columns['Frequency']=number(a['weights']);options['counts']='Frequency'
    options.update(opts)
    return dict(analysis='pyjjbarstats',columns=columns,options=options,
                row_ids=[str(10+3*i) for i in range(len(a['outcome_codes']))])


class BarCore(unittest.TestCase):
    def test_independent_R_archive_and_actual_ggplot_geometry(self):
        r=oracle.verify();self.assertEqual(r['datasets'],28);self.assertEqual(r['configurations'],47)
        self.assertEqual(r['checks'],8837)
        self.assertEqual(r['fixture_sha256'],'7625190c09221ee622ab312f09daa60ab7e4285dda651149fd815192e972f1d2')

    def test_frequency_expansion_permutation_and_scaling(self):
        a,b,w=oracle.inputs(FIXTURES[0]);base=engine.bar_core(a,b,weights=w,inference=True)
        ac=np.repeat(a.codes,w);bc=np.repeat(b.codes,w)
        expanded=engine.bar_core(Factor(ac,a.levels),Factor(bc,b.levels),inference=True)
        self.assertEqual(base['cells'],expanded['cells']);self.assertEqual(base['association'],expanded['association'])
        perm=[3,1,0,2]
        shuffled=engine.bar_core(Factor(a.codes[perm],a.levels),Factor(b.codes[perm],b.levels),weights=np.array(w)[perm],inference=True)
        self.assertEqual(base['cells'],shuffled['cells'])
        scaled=engine.bar_core(a,b,weights=np.array(w)*3,inference=True)
        self.assertAlmostEqual(scaled['association']['pearson_statistic'],3*base['association']['pearson_statistic'])
        self.assertAlmostEqual(scaled['association']['cramers_v_raw'],base['association']['cramers_v_raw'])
        self.assertNotEqual(scaled['association']['cramers_v_corrected'],base['association']['cramers_v_corrected'])
        for key in ('lower','upper','center'):
            self.assertEqual([c[key] for c in scaled['geometry']['percentage']],
                             [c[key] for c in base['geometry']['percentage']])

    def test_unequal_group_heights_and_zero_cells(self):
        f=next(f for f in FIXTURES if f['id']=='unequal_2x3');a,b,w=oracle.inputs(f)
        got=engine.bar_core(a,b,weights=w)
        for group in got['group_codes']:
            for scale in ('percentage','count'):
                cells=[c for c in got['geometry'][scale] if c['group']==group]
                self.assertEqual(cells[0]['upper'],1 if scale=='percentage' else cells[0]['group_total'])
                self.assertEqual(cells[-1]['lower'],0)
                self.assertAlmostEqual(sum(c['upper']-c['lower'] for c in cells),cells[0]['upper'])
        self.assertGreater(len(set(c['group_total'] for c in got['cells'])),1)
        z=next(f for f in FIXTURES if f['id']=='zero_cells_dense_margins');a,b,w=oracle.inputs(z)
        self.assertTrue(any(c['count']==0 for c in engine.bar_core(a,b,weights=w)['cells']))

    def test_ids_missing_codes_order_and_off_switch(self):
        a=Factor(np.array([0,1,0,1,2]),['01','1',None],True)
        b=Factor(np.array([0,0,1,1,0]),['B','A'],True)
        ids=['001','01','1','a',None]
        got=engine.bar_core(a,b,subject_ids=ids)
        self.assertEqual(got['retained_subject_ids'],ids[:-1]);self.assertEqual(got['missing_outcome'],1)
        self.assertEqual(got['group_codes'],[0,1]);self.assertEqual(got['dropped_outcome_codes'],[2])
        with patch.object(engine,'_association',wraps=engine._association) as assoc:
            got=engine.bar_core(a,b,inference=False)
            self.assertFalse(assoc.call_args.args[-1]);self.assertIsNone(got['association']['primary_p'])
        for bad in (['x','x','a','b',None],['x',None,'a','b',None]):
            with self.assertRaises(InputError):engine.bar_core(a,b,subject_ids=bad)
        with self.assertRaises(InputError):engine.bar_core(a,b,weights=[1]*5,subject_ids=ids)

    def test_invalid_roles_frequencies_and_resource_guards(self):
        a,b,w=oracle.inputs(FIXTURES[0])
        for weights in ([1,True,1,1],[1,'2',1,1],np.ma.array(w),[1,None],np.array([[1,2],[3,4]])):
            with self.assertRaises(InputError):engine.bar_core(a,b,weights=weights)
        for inference in (None,1,'yes'):
            with self.assertRaises(InputError):engine.bar_core(a,b,inference=inference)
        with self.assertRaises(InputError):engine.bar_core(a,Factor(np.array([0]),['A','B']))
        with self.assertRaises(InputError):engine.bar_core(Factor(np.ma.array(a.codes),a.levels),b)
        with self.assertRaises(InputError):engine.bar_core(Factor(a.codes,[str(i) for i in range(1001)]),b)
        with self.assertRaises(InputError):engine.bar_core(Factor(np.tile([0,1],50001),['A','B']),Factor(np.tile([0,1],50001),['A','B']))

    def test_oracle_rejects_six_corruptions(self):
        original=oracle.bar_core
        for kind in ('denominator','stack','continuity','fisher','frequency','missingness'):
            def changed(*args,**kwargs):
                got=original(*args,**kwargs)
                if kind=='denominator':got['cells'][0]['group_proportion']=got['cells'][0]['overall_proportion']
                elif kind=='stack':got['geometry']['percentage'][0]['lower']=0
                elif kind=='frequency':got['cells'][0]['count']+=1
                elif kind=='missingness':got['n_complete']+=1
                elif kwargs.get('inference'):
                    if kind=='continuity':got['association']['pearson_statistic']*=.9
                    if kind=='fisher' and got['association']['primary_method']=='fisher_exact':got['association']['primary_p']=got['association']['pearson_p']
                return got
            with self.subTest(kind=kind),patch.object(oracle,'bar_core',changed):
                with self.assertRaises(AssertionError):oracle.verify()


class BarAdapter(unittest.TestCase):
    def test_all_frozen_reference_inputs_and_plot_grid(self):
        for f in FIXTURES:
            if f['expected']['status']=='error':
                if f['id'] not in ('infinite_weight','invalid_code'):
                    self.assertEqual(execute(request(f))['status'],'input_error',f['id'])
                continue
            for enabled in (False,True):
                got=execute(request(f,resultssubtitle=enabled,showCases=True))
                self.assertEqual(got['status'],'ok',(f['id'],got.get('error')))
                self.assertEqual(got['tables']['cohort']['rows'][0]['total'],f['expected']['n_total'])
                cells=got['tables']['cells']['rows']
                self.assertEqual([c['count'] for c in cells],[c['count'] for c in f['expected']['cells']])
                self.assertEqual(got['plots']['barPlot']['columns']['upper'],[c['upper'] for c in f['expected']['geometry']['percentage']])
                if enabled:
                    row=got['tables']['association']['rows'][0];ref=f['expected']['association']
                    self.assertAlmostEqual(row['p'],ref['primary_p'])
                    self.assertNotIn('statistic',row)
                    self.assertNotIn('lower',got['tables']['effects']['rows'][0])
                else:self.assertNotIn('association',got['tables'])

    def test_supported_off_controls_and_unsupported_requests(self):
        f=FIXTURES[0]
        with patch('cpj_barstats._association',side_effect=lambda *args: {}):
            got=execute(request(f,showPlot=False,showCases=False,showCells=False))
            self.assertEqual(got['status'],'ok',got.get('error'))
            for name in ('cells','cases','association','effects','pearson'):self.assertNotIn(name,got['tables'])
            self.assertFalse(got['plots'])
        for opts in [dict(paired=True),dict(typestatistics='bayes'),dict(grvar='Group'),dict(conflevel=.9),
                     dict(resultssubtitle=1),dict(barScale='bogus'),dict(digitsperc=True)]:
            self.assertEqual(execute(request(f,**opts))['status'],'input_error',opts)

    def test_subject_source_identity_and_frequency_exclusion(self):
        f=next(f for f in FIXTURES if f['id']=='unweighted_missing')
        req=request(f,subject='ID',showCases=True);req['columns']['ID']=text([f'ID{i}' for i in range(len(req['row_ids']))])
        got=execute(req);self.assertEqual(got['status'],'ok',got.get('error'))
        self.assertEqual([r['sourceID'] for r in got['tables']['cases']['rows']],
            [req['row_ids'][i] for i in f['expected']['retained_indices']])
        req['columns']['Frequency']=number([1]*len(req['row_ids']));req['options']['counts']='Frequency'
        self.assertEqual(execute(req)['status'],'input_error')

    def test_subprocess_count_scale_and_labels(self):
        req=request(FIXTURES[0],barScale='count',label='both',resultssubtitle=True)
        got=run_analysis(req['analysis'],req['columns'],req['options'],row_ids=req['row_ids'])
        self.assertEqual(got['status'],'ok',got.get('error'))
        self.assertEqual(got['plots']['barPlot']['columns']['upper'],[20,8,20,17])
        self.assertEqual(got['plots']['barPlot']['columns']['annotation'],['12\n(60%)','8\n(40%)','3\n(15%)','17\n(85%)'])

    def test_stacked_renderer_uses_verified_geometry_without_refitting(self):
        from cpj_plots import figure,render
        f=next(f for f in FIXTURES if f['id']=='unequal_2x3')
        for scale in ('percentage','count'):
            got=execute(request(f,barScale=scale));state=got['plots']['barPlot']
            with patch.object(engine,'bar_core',side_effect=RuntimeError('no refit')):
                fig=figure(state,width=650,height=450)
                self.assertEqual(len(fig.axes[0].patches),len(f['expected']['cells']))
                outcomes=list(dict.fromkeys(state['columns']['outcome']))
                expected=[r for o in outcomes for r in f['expected']['geometry'][scale] if f['inputs']['outcome_levels'][r['outcome']]==o]
                for patch_obj,row in zip(fig.axes[0].patches,expected):
                    self.assertAlmostEqual(patch_obj.get_x(),row['xmin'])
                    self.assertAlmostEqual(patch_obj.get_y(),row['lower'])
                    self.assertAlmostEqual(patch_obj.get_height(),row['upper']-row['lower'])
                self.assertEqual(render(state,width=650,height=450)['mime'],'image/png')
            bad=copy.deepcopy(state);bad['columns']['lower'][0]+=2
            with self.assertRaises(ValueError):figure(bad)


if __name__=='__main__':unittest.main()
