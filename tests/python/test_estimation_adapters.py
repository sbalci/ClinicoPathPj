"""Native estimation adapters against independent R fixtures and bounded UI contracts."""
import ast
import json
import sys
import unittest

from cpjtest import ROOT, number, factor, text, run_analysis
sys.path.insert(0, str(ROOT/'inst/python'))
from cpj_runtime import execute

FIXTURES = json.loads((ROOT/'tests/fixtures/estimation-core.json').read_text())['fixtures']


def request(f, run=None, **overrides):
    run = run or next(r for r in f['expected']['runs'] if r['confidence'] == .95)
    paired = f['design'] == 'paired'
    if paired:
        columns = dict(First=number(f['a']), Second=number(f['b']))
        options = dict(dep1='First', dep2='Second')
    else:
        columns = dict(Outcome=number(f['values']), Group=dict(kind='factor', levels=f['levels'],
            codes=[None if c < 0 else c for c in f['codes']]))
        options = dict(dep=['Outcome'], group='Group', firstLevel=f['first'], secondLevel=f['second'],
                       varequal=run['method'] == 'student')
    options.update(conflevel=run['confidence'],showCases=True,showPlot=True)
    options.update(overrides)
    return dict(analysis='pyjjwithinstats' if paired else 'pyjjbetweenstats', columns=columns,
        options=options, row_ids=[str(10+3*i) for i in range(f['expected']['n_source'])])


class EstimationAdapters(unittest.TestCase):
    def test_all_255_independent_reference_configurations(self):
        for f in FIXTURES:
            for ref in f['expected']['runs']:
                result = execute(request(f,ref))
                self.assertEqual(result['status'],'ok',(f['id'],result.get('error')))
                table = result['tables']
                cohort=table['cohort']['rows'][0]
                self.assertEqual(cohort['retained'], f['expected']['n_complete'])
                self.assertEqual(cohort['excluded'], f['expected']['excluded_missing'])
                for row,key in zip(table['descriptives']['rows'], ('first','second')):
                    for column in ('n','mean','sd'):
                        target=f['expected']['summaries'][key][column]
                        self.assertLessEqual(abs(row[column]-target),max(1e-300,abs(target)*1e-11))
                row=table['contrast']['rows'][0]
                for key in ('difference','stderr','df','statistic','p','lower','upper'):
                    target=ref[key]
                    if target is None:self.assertIsNone(row[key])
                    else:self.assertLessEqual(abs(row[key]-target),1e-12 if key=='p' else max(1e-300,abs(target)*1e-11))
                self.assertEqual(row['status'],ref['status'])
                self.assertEqual([r['sourceID'] for r in table['cases']['rows']],
                    [str(10+3*i) for i in f['expected']['retained_indices']])
                plot=result['plots']['differencePlot']
                self.assertEqual(plot['columns']['estimate'],[row['difference']])
                self.assertEqual(plot['columns']['lower'],[row['lower']])
                self.assertEqual(plot['columns']['upper'],[row['upper']])
                self.assertEqual(plot['reference'],0)
                json.dumps(result,allow_nan=False)

    def test_subprocess_bridge_and_disabled_outputs(self):
        for design in ('independent','paired'):
            f=next(f for f in FIXTURES if f['design']==design)
            req=request(f,showCases=False,showPlot=False)
            result=run_analysis(req['analysis'],req['columns'],req['options'],row_ids=req['row_ids'])
            self.assertEqual(result['status'],'ok',result.get('error'))
            self.assertNotIn('cases',result['tables'])
            self.assertFalse(result['plots'])
            self.assertIn('first',result['texts']['summary'].lower())

    def test_ID_labels_and_retained_only_uniqueness(self):
        f=next(f for f in FIXTURES if f['id']=='paired_missing_alignment')
        req=request(f,subject='ID')
        req['columns']['ID']=factor(['x','001','01','x','1',None,'a','b'])
        got=execute(req)
        self.assertEqual(got['status'],'ok',got.get('error'))
        self.assertEqual([r['subjectID'] for r in got['tables']['cases']['rows']],['001','01','1','a','b'])
        req['columns']['ID']=text(['x','same','same','x','1',None,'a','b'])
        self.assertEqual(execute(req)['status'],'input_error')
        req['columns']['ID']=number(range(8))
        self.assertEqual(execute(req)['status'],'input_error')

    def test_invalid_roles_and_date_metadata(self):
        for f in (FIXTURES[0],next(f for f in FIXTURES if f['design']=='paired')):
            req=request(f)
            if f['design']=='paired':req['options']['dep2']='First'
            else:req['options']['dep']=['Outcome','Group']
            self.assertEqual(execute(req)['status'],'input_error')
            req=request(f)
            key='First' if f['design']=='paired' else 'Outcome'
            req['columns'][key]['storage']={'classes':['Date']}
            self.assertEqual(execute(req)['status'],'input_error')
            for option,value in [('typestatistics','bayes'),('typestatistics','robust'),
                                 ('typestatistics','nonparametric'),('effsizetype','biased'),
                                 ('dep3','Third'),('grvar','Split'),('pairwisecomparisons',True)]:
                req=request(f,**{option:value})
                self.assertEqual(execute(req)['status'],'input_error')

    def test_row_identity_errors_and_bounded_case_table(self):
        f=FIXTURES[0]
        req=request(f);req['row_ids']=['same']*len(req['row_ids'])
        invalid=execute(req)
        self.assertEqual(invalid['status'],'exception')
        self.assertIn('Row IDs',invalid['error']['message'])
        self.assertFalse(invalid['tables'])
        values=list(range(1100))
        req=dict(analysis='pyjjwithinstats',columns=dict(A=number(values),B=number([v+(i%3) for i,v in enumerate(values)])),
                 options=dict(dep1='A',dep2='B',showCases=True))
        got=execute(req)
        self.assertEqual(got['status'],'ok',got.get('error'))
        self.assertEqual(got['tables']['cohort']['rows'][0]['retained'],1100)
        self.assertEqual(len(got['tables']['cases']['rows']),1000)
        self.assertIn('all 1100',got['tables']['cases']['notes'][0])

    def test_specs_preserve_supported_defaults_and_omit_unvalidated_branches(self):
        frozen=json.loads((ROOT/'docs/baselines/released-2026-10-25.json').read_text())
        for name in ('jjbetweenstats','jjwithinstats'):
            tree=ast.parse((ROOT/f'inst/python/analyses/jjstatsplot/py{name}.py').read_text())
            spec=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign)
                and any(isinstance(t,ast.Name) and t.id=='SPEC' for t in n.targets)))
            options={o['name']:o for o in spec['options']}
            baseline={o['name']:o for o in frozen[name]['definitions']['a']['options']}
            self.assertEqual(options['conflevel']['default'],baseline['conflevel']['default'])
            if name=='jjbetweenstats':self.assertEqual(options['varequal']['default'],baseline['varequal']['default'])
            for unsupported in ('typestatistics','effsizetype','clinicalpreset','dep3','dep4','grvar','pairwisecomparisons'):
                self.assertNotIn(unsupported,options)
            self.assertTrue(spec['clearOnInputError'])


if __name__=='__main__':unittest.main()
