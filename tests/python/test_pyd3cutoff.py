"""Independent count/rank oracles for the separate D3 experiment."""
import importlib.util
import json
import subprocess
import tempfile
import unittest
import sys
import numpy as np
from cpjtest import ROOT, factor, number, rows, run_analysis
sys.path.insert(0, str(ROOT / "inst/python"))
from cpj_cutoff import states, select

spec = importlib.util.spec_from_file_location('d3cutoff', ROOT/'inst/python/analyses/meddecide/pyd3cutoff.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class D3Cutoff(unittest.TestCase):
    def run_case(self, values=(1,2,2,4,5,6), labels=('N','N','P','N','P','P'), **opts):
        options = dict(marker='x',reference='g',positive='P',cutoff='2',direction='ge')
        options.update(opts)
        return run_analysis('pyd3cutoff',{'x':number(values),'g':factor(labels)},options)

    def test_boundary_counts_auc_and_optima(self):
        rng=np.random.default_rng(254)
        for _ in range(20):
            x=rng.integers(-6,8,40).astype(float)
            truth=np.arange(40)<13
            for direction in ('ge','le'):
                curve=states(x,truth,direction,fp_cost=2,fn_cost=7)
                for p in curve['points']:
                    pred=x>=p['cutoff'] if direction=='ge' else x<=p['cutoff']
                    expected=[sum(pred&truth),sum(pred&~truth),sum(~pred&truth),sum(~pred&~truth)]
                    self.assertEqual([p[k] for k in ('tp','fp','fn','tn')],expected)
                a,b=x[truth,None],x[None,~truth]
                auc=np.mean((a>b if direction=='ge' else a<b)+.5*(a==b))
                self.assertAlmostEqual(curve['auc'],auc)
                for criterion in ('errors','youden','cost'):
                    objective=[p['fp']+p['fn'] if criterion=='errors' else -p['youden'] if criterion=='youden' else 2*p['fp']+7*p['fn'] for p in curve['points']]
                    indices=[i for i,v in enumerate(objective) if abs(v-min(objective))<1e-12]
                    self.assertEqual(curve['optima'][criterion],dict(point=indices[0],ties=len(indices)))
                for cutoff in [-100,-2.5,2,2.00001,100]:
                    p=select(curve['points'],cutoff,direction)
                    pred=x>=cutoff if direction=='ge' else x<=cutoff
                    self.assertEqual(p['tp'],sum(pred&truth));self.assertEqual(p['fp'],sum(pred&~truth))

    def test_exact_intervals_against_r(self):
        x=np.array([1,2,2,4,5,6.]);truth=np.array([0,0,1,0,1,1],bool)
        for method in ('exact','wilson'):
            p=select(states(x,truth,'ge',method,.9)['points'],2,'ge')
            # R's uncorrected score interval is the Wilson interval.
            code=';'.join(f'cat({"binom.test" if method=="exact" else "prop.test"}({a},{b},conf.level=.9'+('' if method=='exact' else ',correct=FALSE')+')$conf.int,"\\n")' for a,b in [(3,3),(1,3),(3,5),(1,1),(4,6)])
            result=subprocess.run(['Rscript','--vanilla','-e',code],capture_output=True,text=True,check=True)
            expected=np.array([list(map(float,line.split())) for line in result.stdout.strip().splitlines()])
            np.testing.assert_allclose(np.array(p['metrics'])[:,1:],expected,atol=6e-8)

    def test_existing_dotplot_agreement_and_outputs(self):
        result=self.run_case()
        old=run_analysis('pydotdecision',{'x':number([1,2,2,4,5,6]),'g':factor(['N','N','P','N','P','P'])},dict(marker='x',reference='g',positive='P',cutoff='2',direction='high'))
        self.assertEqual(result['status'],'ok',result.get('error'))
        self.assertEqual(rows(result,'counts'),rows(old,'counts'))
        for a,b in zip(rows(result,'metrics'),rows(old,'metrics')):
            for key in ('estimate','lower','upper'):self.assertAlmostEqual(a[key],b[key],places=10)
        self.assertEqual(set(result['plots']),{'staticDotplot','staticROC'})
        self.assertIn('only the local snapshot',result['texts']['summary'])

    def test_missing_and_undefined(self):
        result=self.run_case([1,2,2,4,5,6,None,8],['N','N','P','N','P','P','P',None],cutoff='100')
        self.assertEqual(result['status'],'ok',result.get('error'))
        self.assertIsNone(rows(result,'metrics')[2]['estimate'])
        self.assertIsNone(rows(result,'metrics')[2]['lower'])
        self.assertIn('"excluded": 2',result['htmls']['explorer'])

    def test_validation(self):
        for opts in [dict(cutoff='nan'),dict(cutoff='inf'),dict(cutoff='bad'),dict(positive=None),dict(ciWidth=100),dict(ciWidth=float('nan')),dict(ciMethod='bad'),dict(fpCost=-1),dict(fnCost=float('inf')),dict(direction='bad'),dict(criterion='bad')]:
            self.assertEqual(self.run_case(**opts)['status'],'input_error',opts)
        self.assertEqual(self.run_case([1,2],['P','P'])['status'],'input_error')
        self.assertEqual(self.run_case(list(range(1001)),['N']*500+['P']*501)['status'],'input_error')

    def test_payload_is_local_and_bounded(self):
        result=self.run_case(range(1000),['N']*500+['P']*500)
        self.assertEqual(result['status'],'ok',result.get('error'))
        html=result['htmls']['explorer'];self.assertLess(len(html.encode()),1500000)
        template=(ROOT/'inst/python/templates/d3cutoff.html').read_text()
        self.assertNotIn('setOption',template)
        self.assertNotIn('function interval',template)
        self.assertNotIn('function loss',template)
        self.assertIn('Apply to HTML tables',template)
        self.assertIn('d3js.org v7.9.0',html)

    def test_html_escaping_and_javascript_syntax(self):
        document=module.html_document(dict(label='</script><img src=x onerror="alert(1)">'))
        self.assertNotIn('<img src=x',document)
        self.assertEqual(document.count('</script>'),2)
        scripts=[s.split('</script>')[0] for s in document.split('<script>')[1:]]
        with tempfile.TemporaryDirectory() as directory:
            for i,script in enumerate(scripts):
                from pathlib import Path
                path=Path(directory)/f'{i}.js';path.write_text(script)
                subprocess.run(['node','--check',str(path)],capture_output=True,check=True)
