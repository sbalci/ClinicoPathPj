import sys
import unittest
import numpy as np
from cpjtest import ROOT, factor, number, run_analysis
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_runtime import Factor, InputError, _decode
from cpj_outcomes import calculate


def data(values,levels=None):
    return _decode({'y':factor(values,levels)})


def options(**kw):
    return dict(outcome='y',**kw)


class Outcomes(unittest.TestCase):
    def test_generator_failure_policy_is_explicit_and_boolean(self):
        import copy
        sys.path.insert(0,str(ROOT/'tools'))
        import generate
        spec=generate.read_spec(ROOT/'inst/python/analyses/jsurvival/pyoutcomeorganizer.py')
        generate.validate(spec,'pyoutcomeorganizer')
        self.assertIn('clearOnInputError = TRUE',generate.b_r(spec,'test'))
        legacy=generate.read_spec(ROOT/'inst/python/analyses/meddecide/pyd3cutoff.py')
        self.assertNotIn('clearOnInputError',generate.b_r(legacy,'test'))
        bad=copy.deepcopy(spec);bad['clearOnInputError']='yes'
        with self.assertRaises(generate.SpecError):generate.validate(bad,'pyoutcomeorganizer')

    def test_explicit_level_and_missing_are_never_guessed(self):
        d=data(['Alive','Dead',None,'Dead'],['Dead','Alive','Unused'])
        self.assertIn('Choose the event',calculate(d,options())['pending'])
        for event,expected in [('Dead',[0,1,None,1]),('Alive',[1,0,None,0]),('Unused',[0,0,None,0])]:
            r=calculate(d,options(outcomeLevel=event))
            self.assertEqual(r['status'],expected)
            self.assertEqual((r['valid'],r['missing']),(3,1))
        self.assertIn('No target events',calculate(d,options(outcomeLevel='Unused'))['warnings'][0])
        with self.assertRaisesRegex(InputError,'no longer declared'):calculate(d,options(outcomeLevel='stale'))

    def test_numeric_zero_one_and_explicit_reversal(self):
        d=_decode({'y':number([0,1,None,0])})
        self.assertEqual(calculate(d,options())['status'],[0,1,None,0])
        self.assertEqual(calculate(d,options(outcomeLevel='0'))['status'],[1,0,None,1])
        self.assertEqual(calculate(_decode({'y':number([0,0])}),options())['status'],[0,0])
        for bad in ([1,2],[-1,2],[1,float('inf')]):
            with self.assertRaises(InputError):calculate({'y':np.array(bad,dtype=float)},options())
        with self.assertRaisesRegex(InputError,'does not occur'):calculate(d,options(outcomeLevel='2'))

    def test_four_state_truth_tables(self):
        d=data(['N','D','X','O',None,'N'],['O','X','D','N','unused'])
        for mode,expected in [('os',[0,0,1,1,None,0]),('cause',[0,0,1,0,None,0]),
                              ('compete',[0,0,1,2,None,0]),('multistate',[0,1,2,3,None,0])]:
            r=calculate(d,options(multievent=True,analysistype=mode,awod='N',awd='D',dod='X',dooc='O'))
            self.assertEqual(r['status'],expected)
            self.assertEqual(sum(v['n'] for v in r['counts']),5)
            self.assertAlmostEqual(sum(v['percent'] for v in r['counts']),1)
            self.assertEqual(r['mapping'][4]['code'],None)
            if mode=='compete':self.assertEqual(r['levels'],['Censored','Event','Competing'])

    def test_ambiguous_unassigned_and_incomplete_states(self):
        d=data(['Alive','Dead'])
        self.assertIn('Assign',calculate(d,options(multievent=True))['pending'])
        with self.assertRaisesRegex(InputError,'only one'):calculate(d,options(multievent=True,dod='Dead',dooc='Dead'))
        with self.assertRaisesRegex(InputError,'unassigned'):calculate(d,options(multievent=True,dod='Dead'))
        with self.assertRaisesRegex(InputError,'no longer'):calculate(d,options(multievent=True,dod='X',awod='Alive'))
        r=calculate(d,options(multievent=True,analysistype='compete',dod='Dead',awod='Alive'))
        self.assertEqual([v['n'] for v in r['counts']],[1,1,0])
        with self.assertRaisesRegex(InputError,'Enable Multiple'):calculate(d,options(analysistype='cause',outcomeLevel='Dead'))

    def test_competing_interchange_and_refocus(self):
        d=data(['Event','Censored','Competing',None],['Competing','Censored','Event'])
        for event,expected in [(None,[1,0,2,None]),('Event',[1,0,2,None]),('Competing',[2,0,1,None])]:
            self.assertEqual(calculate(d,options(outcomeLevel=event))['status'],expected)
        with self.assertRaisesRegex(InputError,'cannot be the event'):calculate(d,options(outcomeLevel='Censored'))
        d=data(['Censored','Event'],['Censored','Event','Competing'])
        self.assertEqual(calculate(d,options())['levels'],['Censored','Event','Competing'])
        ordinary=data(['Event','No event'])
        self.assertEqual(calculate(ordinary,options(outcomeLevel='No event'))['status'],[0,1])

    def test_actual_missing_level_and_literal_labels(self):
        d={'y':Factor(np.array([0,1,2,-1]),['NA',None,'Unknown'])}
        r=calculate(d,options(outcomeLevel='NA'))
        self.assertEqual(r['status'],[1,None,0,None]);self.assertEqual(r['missing'],2)
        self.assertEqual(r['mapping'][1]['level'],'Unknown')

    def test_empty_all_missing_limits_and_invalid_storage(self):
        for values in ([],[None,None]):
            with self.assertRaises(InputError):calculate(data(values,levels=['Alive']),options(outcomeLevel='Alive'))
        with self.assertRaisesRegex(InputError,'10,000'):calculate(data(['A']*10001),options(outcomeLevel='A'))
        d=data(['A','B']);d.metadata['y']={'classes':['Date']}
        with self.assertRaisesRegex(InputError,'scalar'):calculate(d,options(outcomeLevel='A'))
        with self.assertRaisesRegex(InputError,'Unknown'):calculate(data(['A']),options(analysistype='unknown'))

    def test_runtime_saved_alignment_preview_and_counts(self):
        r=run_analysis('pyoutcomeorganizer',{'y':factor(['N','X',None,'O','N'])},
                       options(multievent=True,analysistype='compete',awod='N',dod='X',dooc='O',diagnostics=True,visualization=True,showNaturalSummary=True),row_ids=["1","2","3","4","5"])
        self.assertEqual(r['status'],'ok',r.get('error'))
        self.assertEqual(r['outputs']['addOutcome']['values'],[0,1,None,2,0])
        self.assertEqual(r['outputs']['addOutcome']['row_ids'],['1','2','3','4','5'])
        self.assertEqual([v['n'] for v in r['tables']['frequencies']['rows']],[2,1,1])
        self.assertEqual(len(r['tables']['preview']['rows']),5)
        self.assertIn('4 coded records',r['texts']['report'])
        self.assertIn('distribution',r['plots'])

    def test_incomplete_no_output_and_html_label_escape(self):
        r=run_analysis('pyoutcomeorganizer',{'y':factor(['<script>','Alive'])},options())
        self.assertEqual(r['status'],'ok');self.assertEqual(r['outputs'],{})
        r=run_analysis('pyoutcomeorganizer',{'y':factor(['<script>','Alive'])},options(outcomeLevel='<script>'))
        self.assertEqual(r['status'],'ok')
        self.assertEqual(r['tables']['mapping']['rows'][0]['level'],'<script>')
        self.assertNotIn('preview',r['tables'])


if __name__=='__main__':unittest.main()
