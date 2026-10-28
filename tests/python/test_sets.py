import importlib.util,itertools,sys,unittest
import numpy as np
from cpjtest import ROOT,factor,number,run_analysis
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_sets import calculate
from cpj_runtime import Factor,InputError,Output


def column(values,levels=('N','Y')):
    return Factor(np.array([-1 if v is None else levels.index(v) for v in values]),list(levels))


class Sets(unittest.TestCase):
    def test_exact_patterns_none_missing_and_marginals(self):
        p=calculate({'a':column(['N','Y','N','Y',None]),'b':column(['N','N','Y','Y','Y'])},dict(var1='a',var2='b',var1true='Y',var2true='Y'))
        self.assertEqual([v['pattern'] for v in p['patterns']],['00','10','01','11'])
        self.assertEqual([v['n'] for v in p['patterns']],[1]*4)
        self.assertEqual((p['inputRows'],p['retained'],p['excluded'],p['union'],p['allSets']),(5,4,1,3,1))
        self.assertEqual(p['masks'],[0,1,2,3,None]);self.assertEqual([v['members'] for v in p['sets']],[2,2])

    def test_cartesian_four_sets(self):
        rows=list(itertools.product(['N','Y'],repeat=4));data={str(i):column([r[i] for r in rows]) for i in range(4)}
        options={f'var{i+1}':str(i) for i in range(4)};options.update({f'var{i+1}true':'Y' for i in range(4)})
        p=calculate(data,options);self.assertEqual([v['n'] for v in p['patterns']],[1]*16)
        self.assertEqual([v['members'] for v in p['sets']],[8]*4);self.assertEqual((p['union'],p['allSets']),(15,1))

    def test_optional_roles_and_unselected_missingness(self):
        d={'a':column(['N','Y','Y']),'b':column(['N','Y','N']),'c':column([None]*3),'d':column(['Y',None,'N'])}
        options=dict(var1='a',var2='b',var1true='Y',var2true='Y')
        self.assertEqual(calculate(d,options)['retained'],3)
        p=calculate(d,dict(options,var4='d',var4true='Y'));self.assertEqual(p['names'],['a','b','d']);self.assertEqual(p['retained'],2)

    def test_true_na_level_is_missing_but_literal_na_is_a_label(self):
        a=Factor(np.array([0,1,2,-1]),[None,'NA','N']);b=column(['Y']*4)
        p=calculate(dict(a=a,b=b),dict(var1='a',var2='b',var1true='NA',var2true='Y'))
        self.assertEqual(p['masks'],[None,3,2,None]);self.assertEqual((p['retained'],p['excluded']),(2,2))

    def test_validation(self):
        d=dict(a=column(['N','Y']),b=column(['N','Y']));base=dict(var1='a',var2='b',var1true='Y',var2true='Y')
        for opts in [dict(base,var2='a'),dict(base,var1true=None),dict(base,var2true='bad')]:
            with self.assertRaises(InputError):calculate(d,opts)
        with self.assertRaises(InputError):calculate(dict(a=np.arange(2),b=d['b']),base)
        with self.assertRaises(InputError):calculate(dict(a=d['a'],b=column(['Y'])),base)
        with self.assertRaises(InputError):calculate(dict(a=column([None]),b=column(['Y'])),base)

    def test_runtime_escaped_labels_and_native_counts(self):
        name='</script><bad>'
        r=run_analysis('pyvenn',{name:factor(['N','Y',None]),'b':factor(['N','Y','Y'])},dict(var1=name,var2='b',var1true='Y',var2true='Y',showMembershipTable=True))
        self.assertEqual(r['status'],'ok',r.get('error'));self.assertNotIn('</script><bad>',r['htmls']['explorer'])
        self.assertEqual(sum(v['n'] for v in r['tables']['intersections']['rows']),2)
        self.assertEqual(len(r['tables']['membershipTable']['rows']),3)
        self.assertEqual([v['status'] for v in r['tables']['membershipTable']['rows']],['Included','Included','Excluded'])
        self.assertEqual(r['tables']['membershipTable']['rows'][1]['members'],name+' + b')
        self.assertEqual(sum(r['plots']['intersectionPlot']['columns']['value']),2)

    def test_saved_rows_and_bounded_preview(self):
        spec=importlib.util.spec_from_file_location('sets_analysis',ROOT/'inst/python/analyses/descriptives/pyvenn.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        preview=next(v for v in module.SPEC['results'] if v['name']=='membershipTable')
        self.assertIs(next(v for v in preview['columns'] if v['name']=='members')['visible'],False)
        data=dict(a=column(['N','Y','N','Y',None]),b=column(['N','N','Y','Y','Y']))
        out=Output(module.SPEC,['2','5','9','12','15']);module.run(data,dict(var1='a',var2='b',var1true='Y',var2true='Y',showMembershipTable=True),out)
        self.assertEqual(out.outputs['membershipGroups']['values'],[0,1,2,3,None]);self.assertEqual(out.outputs['membershipGroups']['measure_type'],'nominal')
        self.assertEqual([v['row'] for v in out.tables['membershipTable']['rows']],['2','5','9','12','15'])
        many=dict(a=column(['N']*505),b=column(['N']*505));out=Output(module.SPEC,[str(i+1) for i in range(505)])
        module.run(many,dict(var1='a',var2='b',var1true='Y',var2true='Y',showMembershipTable=True),out)
        self.assertEqual(len(out.tables['membershipTable']['rows']),500);self.assertEqual(len(out.outputs['membershipGroups']['values']),505)
        self.assertIn('"omittedRows": 405',out.htmls['explorer'])

    def test_optional_intersection_matrix_reuses_exact_counts(self):
        d=dict(a=factor(['N','Y','N','Y',None]),b=factor(['N','N','Y','Y','Y']))
        opts=dict(var1='a',var2='b',var1true='Y',var2true='Y')
        ordinary=run_analysis('pyvenn',d,opts)
        self.assertNotIn('intersectionMatrix',ordinary['plots'])
        shown=run_analysis('pyvenn',d,dict(opts,showSetMatrix=True))
        matrix=shown['plots']['intersectionMatrix']
        self.assertEqual(matrix['columns']['pattern'],['00','10','01','11'])
        self.assertEqual(matrix['columns']['count'],[1]*4)
        self.assertEqual(ordinary['tables'],shown['tables'])

    def test_unequal_frequency_dataset(self):
        import csv,collections
        with (ROOT/'data/python_set_intersection_unequal_examples.csv').open() as handle:
            rows=list(csv.DictReader(handle))
        expected=[12,8,6,10,4,5,3,2,3,1,2,1,1,0,1,1]
        names=['Marker_A','Marker_B','Marker_C','Marker_D']
        complete=[row for row in rows if all(row[n] for n in names)]
        signatures=collections.Counter(''.join(str(int(row[n]=='Positive')) for n in names) for row in complete)
        options={f'var{j+1}':n for j,n in enumerate(names)}
        options.update({f'var{j+1}true':'Positive' for j in range(4)})
        options.update(showSetMatrix=True,showZero=True)
        result=run_analysis('pyvenn',{n:factor([row[n] or None for row in rows]) for n in names},options)
        self.assertEqual(result['status'],'ok',result.get('error'))
        table=result['tables']['intersections']['rows']
        self.assertEqual([r['n'] for r in table],expected)
        self.assertEqual([signatures[r['pattern']] for r in table],expected)
        self.assertEqual(result['plots']['intersectionMatrix']['columns']['count'],expected)
        self.assertEqual((len(rows),len(complete)),(62,60))

    def test_frequency_order_is_display_only_with_stable_ties(self):
        spec=importlib.util.spec_from_file_location('sets_order_analysis',ROOT/'inst/python/analyses/descriptives/pyvenn.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        d=dict(a=column(['N','Y','Y','N','N','Y',None]),b=column(['N','N','N','Y','Y','Y','Y']))
        opts=dict(var1='a',var2='b',var1true='Y',var2true='Y',showSetMatrix=True,showMembershipTable=True,showZero=True)
        first=Output(module.SPEC,[str(i+1) for i in range(7)]);module.run(d,opts,first)
        sorted_out=Output(module.SPEC,first.row_ids);module.run(d,dict(opts,patternOrder='frequency'),sorted_out)
        patterns=['10','01','00','11']  # counts 2,2,1,1; ties use original bit-code order
        self.assertEqual([r['pattern'] for r in sorted_out.tables['intersections']['rows']],patterns)
        self.assertEqual(sorted_out.plots['intersectionPlot']['columns']['label'],patterns)
        self.assertEqual(sorted_out.plots['intersectionMatrix']['columns']['pattern'],patterns)
        self.assertEqual(sorted_out.outputs,first.outputs)
        self.assertEqual(sorted_out.tables['sets'],first.tables['sets'])
        self.assertEqual(sorted_out.tables['membershipTable'],first.tables['membershipTable'])
        self.assertIn('"patterns": [{"code": 1,',sorted_out.htmls['explorer'])
        self.assertIn('ties use membership order',sorted_out.htmls['explorer'])

    def test_frequency_order_retains_none_and_zero_rules(self):
        d=dict(a=factor(['Y','Y']),b=factor(['N','N']))
        opts=dict(var1='a',var2='b',var1true='Y',var2true='N',patternOrder='frequency')
        r=run_analysis('pyvenn',d,opts)
        self.assertEqual([(v['pattern'],v['n']) for v in r['tables']['intersections']['rows']],[('11',2),('00',0)])
        r=run_analysis('pyvenn',d,dict(opts,showZero=True))
        self.assertEqual([v['pattern'] for v in r['tables']['intersections']['rows']],['11','00','10','01'])
