"""Native grouped survival against frozen R tables; saved geometry never refits."""
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_runtime import execute
from cpj_plots import figure,render
from cpjtest import number,factor,text
FIXTURES=json.loads((ROOT/'tests/fixtures/grouped-survival-core.json').read_text())['fixtures']


def request(f,**options):
    a=f['inputs']
    return dict(analysis='pysurvival',columns=dict(Time=number(a['time']),
        Status=factor([None if v is None else ['Censored','Event'][v] for v in a['event']],['Censored','Event']),
        Group=dict(kind='factor',levels=a['levels'],codes=[None if v<0 else v for v in a['codes']])),
        row_ids=[str(7*i+3) for i in range(len(a['time']))],options=dict(elapsedtime='Time',outcome='Status',explanatory='Group',
            outcomeLevel='Event',censorLevel='Censored',cutp=','.join(str(v) for v in f['queries']),
            ciWidth=f['confidence']*100,timefix=f['timefix'],**options))


class GroupedAdapter(unittest.TestCase):
    def close(self,a,b):
        if b is None:self.assertIsNone(a)
        else:self.assertAlmostEqual(a,b,delta=2e-10*max(1,abs(b)))

    def test_all_R_configurations_native_tables_and_alignment(self):
        for f in FIXTURES:
            req=request(f,showSteps=True,showCases=True);g=execute(req);e=f['expected']
            self.assertEqual(g['status'],'ok',(f['id'],g.get('error')))
            c=g['tables']['cohort']['rows'][0]
            for a,b in [('source','n_source'),('complete','n_complete'),('excluded','excluded_missing'),('events','events'),('censored','censored'),('normalized','timefix_changed_rows')]:self.assertEqual(c[a],e[b])
            self.assertEqual([r['group'] for r in g['tables']['groups']['rows']],[r['label'] for r in e['groups']])
            for row,ref in zip(g['tables']['medians']['rows'],e['groups']):
                for key in ('estimate','lower','upper'):self.close(row[key],ref['median'][key])
            for name,key in [('steps','curve'),('selectedTimes','selected')]:
                refs=[p for group in e['groups'] for p in group[key]];rows=g['tables'][name]['rows']
                self.assertEqual(len(rows),len(refs))
                for row,ref in zip(rows,refs):
                    for k in ('time','events','censored','survival','lower','upper'):self.close(row[k],ref[k])
                    self.assertEqual(row['risk'],ref['n_risk'])
            test=g['tables']['logrank']['rows'][0];ref=e['logrank']
            self.assertEqual(test['status'],ref['status'])
            for k in ('statistic','df','p'):self.close(test[k],ref[k])
            for row,i in zip(g['tables']['logrankGroups']['rows'],range(len(e['groups']))):
                for k in ('observed','expected','score'):self.close(row[k],ref[k][i])
            for row,val in zip(g['tables']['covariance']['rows'],[v for r in ref['variance'] for v in r]):self.close(row['value'],val)
            self.assertEqual([r['sourceID'] for r in g['tables']['cases']['rows']],[req['row_ids'][i] for i in e['retained_indices']])
            self.assertEqual([r['effectiveTime'] for r in g['tables']['cases']['rows']],e['effective_times'])
            riskrows=g['tables'].get('riskSets',{}).get('rows',[])
            refs=[(p,i) for p in ref['trace'] for i in range(len(e['groups']))][:1000]
            self.assertEqual(len(riskrows),len(refs))
            for row,(p,i) in zip(riskrows,refs):
                self.close(row['time'],p['time']);self.assertEqual(row['risk'],p['group_risk'][i])
                self.assertEqual(row['events'],p['group_events'][i]);self.close(row['expected'],p['group_expected'][i])
            self.assertFalse(g['plots'])

    def test_all_R_saved_plot_coordinates_bands_censors_and_no_refit(self):
        for f in FIXTURES:
            got=execute(request(f,sc=True,ci95=True,censored=True));self.assertEqual(got['status'],'ok',got.get('error'))
            state=got['plots']['survivalPlot']
            with patch('cpj_grouped_survival.grouped_survival_core',side_effect=RuntimeError('no refit')):
                fig=figure(state,palette=['#4477AA'],background='#222222',foreground='white')
            from matplotlib.collections import PolyCollection,PathCollection
            ax=fig.axes[0];e=f['expected'];scale=max(g['maximum'] for g in e['groups']) or 1
            expected_rects=[];expected_marks=[]
            for line,g in zip(ax.lines,e['groups']):
                p=g['curve'];xs=[0]+[r['time']/scale for r in p];ys=[1]+[r['survival'] for r in p]
                if p[-1]['time']<g['maximum']:xs.append(g['maximum']/scale);ys.append(ys[-1])
                np.testing.assert_allclose(line.get_xdata(),xs,rtol=2e-12);np.testing.assert_allclose(line.get_ydata(),ys,rtol=2e-12)
                self.assertEqual(line.get_drawstyle(),'steps-post')
                for j,r in enumerate(p):
                    end=p[j+1]['time'] if j+1<len(p) else g['maximum']
                    if r['lower'] is not None and end>r['time']:
                        a,b=r['time']/scale,end/scale
                        expected_rects.append([(a,r['lower']),(b,r['lower']),(b,r['upper']),(a,r['upper'])])
                marks=[[r['time']/scale,r['survival']] for r in p if r['censored']>0]
                if marks:expected_marks.append(marks)
            rects=[path for c in ax.collections if isinstance(c,PolyCollection) for path in c.get_paths()]
            self.assertEqual(len(rects),len(expected_rects))
            for path,vertices in zip(rects,expected_rects):np.testing.assert_allclose(path.vertices[:4],vertices,rtol=2e-12,atol=1e-15)
            marks=[c for c in ax.collections if isinstance(c,PathCollection)]
            self.assertEqual(len(marks),len(expected_marks))
            for c,v in zip(marks,expected_marks):np.testing.assert_allclose(c.get_offsets(),v,rtol=2e-12)
            self.assertEqual(len(ax.lines),len(e['groups']))
        self.assertEqual(render(state)['mime'],'image/png')

    def test_explicit_roles_missingness_subjects_and_invalid_options(self):
        req=request(FIXTURES[0],subject='ID',showCases=True)
        req['columns']['ID']=text(['001','01','a','b','c','d'])
        got=execute(req);self.assertEqual(got['status'],'ok',got.get('error'))
        self.assertEqual([r['subjectID'] for r in got['tables']['cases']['rows']],['001','01','a','b','c','d'])
        for changes in ({'explanatory':'Status'},{'outcomeLevel':None},{'censorLevel':'Event'},
                        {'cutp':'1,,2'},{'cutp':'nan'},{'cutp':'__import__("os")'},
                        {'ciWidth':True},{'sc':1},{'timefix':1}):
            r=copy.deepcopy(req);r['options'].update(changes);self.assertEqual(execute(r)['status'],'input_error',changes)
        req['columns']['Status']['levels'].append('Competing')
        req['columns']['Status']['codes'][0]=2;req['columns']['Time']['values'][0]=None
        self.assertEqual(execute(req)['status'],'input_error')

    def test_payload_corruptions_and_default_output_bounds(self):
        req=request(FIXTURES[0]);g=execute(req)
        for k in ('steps','cases','covariance','riskSets'):self.assertFalse(g['tables'].get(k,{}).get('rows',[]))
        req['options'].update(sc=True,ci95=True,censored=True);state=execute(req)['plots']['survivalPlot']
        payload=json.loads(state['columns']['payload'][0])
        def changed(path,value):
            q=copy.deepcopy(payload);at=q
            for k in path[:-1]:at=at[k]
            at[path[-1]]=value;return q
        corruptions=[changed(['n'],99),changed(['maximum'],0),changed(['confidence_method'],'log-log'),
            changed(['series',0,'points',0,'n_risk'],99),changed(['series',1,'code'],payload['series'][0]['code']),
            changed(['series',0,'points',0,'survival'],.123),changed(['series',0,'points',0,'lower'],-1)]
        for q in corruptions:
            s=copy.deepcopy(state);s['columns']['payload']=[json.dumps(q)]
            with self.assertRaises(ValueError):figure(s)
        n=5001;req['columns']=dict(Time=number(range(n)),Status=factor(['Event']*n,['Censored','Event']),Group=factor(['A']*n))
        req['row_ids']=None;req['options'].update(showSteps=True,showCases=True)
        g=execute(req);self.assertEqual(g['status'],'ok',g.get('error'));self.assertFalse(g['plots'])
        self.assertEqual(len(g['tables']['steps']['rows']),1000);self.assertEqual(len(g['tables']['cases']['rows']),1000)
        self.assertEqual(g['tables']['cohort']['rows'][0]['complete'],n)


if __name__=='__main__':unittest.main()
