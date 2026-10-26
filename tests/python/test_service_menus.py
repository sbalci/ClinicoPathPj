"""Registry-owned family menus and identical optional-service analysis contract."""
import copy
import json
import unittest
from cpjtest import ROOT, factor, number, run_analysis
import sys
sys.path.insert(0,str(ROOT/'tools'))
import generate
from cpj_registry import read_registry

class ServiceMenus(unittest.TestCase):
    def test_family_menus_are_compact_and_preserve_namespace(self):
        registry=read_registry()
        groups=set();entries=registry['analyses']
        for e in entries:
            if not e.get('source'):continue
            files=generate.render(ROOT/'inst/python'/e['source'])
            options=json.loads(files[ROOT/'jamovi'/f"{e['id']}.a.yaml"].split('\n',1)[1])
            self.assertEqual(options['menuGroup'],e['menu_group'])
            self.assertEqual(options['menuSubgroup'],e['menu'])
            self.assertEqual(options['menuTitle'],e['menu_title'])
            groups.add(options['menuGroup'])
        self.assertEqual(groups,{'Descriptives Py','Stats Plots Py','MedDecide Py','Python Lab'})
        self.assertEqual(registry['module'],'ClinicoPathPj')
        self.assertTrue(all(len(g)<=15 for g in groups))
        self.assertEqual(next(e for e in entries if e['id']=='pykappaci')['id'],'pykappaci')

    def test_routes_do_not_change_python_statistics(self):
        d={'x':number([1,2,2,4,5,6,None,8]),'g':factor(['N','N','P','N','P','P','P',None])}
        opts=dict(marker='x',reference='g',positive='P',cutoff='2')
        base=run_analysis('pyd3cutoff',d,opts)
        for route in ['processx','pj','pjSystem']:
            got=run_analysis('pybridgecompare',d,dict(opts,execution=route))
            self.assertEqual(got['status'],'ok',got.get('error'))
            for field in ['tables','plots','notices']:self.assertEqual(got[field],base[field])
            self.assertIn('"hostApply": true',got['htmls']['explorer'])
            self.assertIn('"hostManual": true',got['htmls']['explorer'])

    def test_native_summary_reports_the_actual_applied_rule(self):
        d={'x':number([1,2,2,4,5,6,None,8]),'g':factor(['N','N','P','N','P','P','P',None])}
        got=run_analysis('pybridgecompare',d,dict(marker='x',reference='g',positive='P',cutoff='3'))
        self.assertEqual(got['status'],'ok',got.get('error'))
        summary=got['texts']['summary'].replace(chr(92), '')
        self.assertIn('Native applied rule: x >= 3',summary)
        self.assertIn('Complete rows: 6; excluded: 2',summary)
        self.assertIn('close the options panel and reselect the analysis heading',summary)
        self.assertNotIn('Apply to HTML tables',summary)
        precise=run_analysis('pybridgecompare',d,dict(marker='x',reference='g',positive='P',cutoff='3.123456789123'))
        self.assertIn('3.123456789123',precise['texts']['summary'].replace(chr(92), ''))

    def test_generator_checks_execution_and_timing_bindings(self):
        spec=generate.read_spec(ROOT/'inst/python/analyses/meddecide/pybridgecompare.py')
        for key,bad in [('executionOption','missing'),('timingResult','counts')]:
            s=copy.deepcopy(spec);s[key]=bad
            with self.assertRaises(generate.SpecError):generate.validate(s,'pybridgecompare')
        result=generate.b_r(spec,'test')
        self.assertIn('backend = self$options$execution',result)
        self.assertIn('timing = "backendTiming"',result)
