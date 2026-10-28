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
        self.assertEqual(sum(r['plots']['intersectionPlot']['columns']['value']),2)

    def test_saved_rows_and_bounded_preview(self):
        spec=importlib.util.spec_from_file_location('sets_analysis',ROOT/'inst/python/analyses/descriptives/pyvenn.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        data=dict(a=column(['N','Y','N','Y',None]),b=column(['N','N','Y','Y','Y']))
        out=Output(module.SPEC,['2','5','9','12','15']);module.run(data,dict(var1='a',var2='b',var1true='Y',var2true='Y',showMembershipTable=True),out)
        self.assertEqual(out.outputs['membershipGroups']['values'],[0,1,2,3,None]);self.assertEqual(out.outputs['membershipGroups']['measure_type'],'nominal')
        self.assertEqual([v['row'] for v in out.tables['membershipTable']['rows']],['2','5','9','12','15'])
        many=dict(a=column(['N']*505),b=column(['N']*505));out=Output(module.SPEC,[str(i+1) for i in range(505)])
        module.run(many,dict(var1='a',var2='b',var1true='Y',var2true='Y',showMembershipTable=True),out)
        self.assertEqual(len(out.tables['membershipTable']['rows']),500);self.assertEqual(len(out.outputs['membershipGroups']['values']),505)
        self.assertIn('"omittedRows": 405',out.htmls['explorer'])
