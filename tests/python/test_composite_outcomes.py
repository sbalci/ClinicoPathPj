import sys,unittest,copy
from itertools import product
from cpjtest import ROOT,factor,number,run_analysis
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_runtime import _decode,InputError
from cpj_outcomes import calculate

PAIRS=list(product([0,1,None],repeat=2))
# Independently enumerated truth table: no implicit censoring for an unknown component.
OR=[0,1,None,1,1,1,None,1,None]

def columns():
    return {'y':number([a for a,b in PAIRS]),'r':factor([None if b is None else 'Yes' if b else 'No' for a,b in PAIRS],levels=['Yes','No','Unused'])}

def opts(kind='rfs',**kw):return dict(outcome='y',recurrence='r',recurrenceLevel='Yes',analysistype=kind,**kw)

class CompositeOutcomes(unittest.TestCase):
    def test_nine_pair_truth_tables_and_denominators(self):
        for mode in ['rfs','pfs','dfs']:
            r=calculate(_decode(columns()),opts(mode))
            self.assertEqual(r['status'],OR)
            self.assertEqual([x['n'] for x in r['counts']],[1,5])
            self.assertEqual([x['percent'] for x in r['counts']],[1/6,5/6])
            self.assertEqual((r['missing'],r['known_event_overrides']),(3,2))
            self.assertEqual((r['component_missing_outcome'],r['component_missing_recurrence']),(3,3))
            self.assertEqual(sum(x['n'] for x in r['components'] if x['component']=='Recurrence/progression'),6)

    def test_progression_only_ignores_outcome_values_and_event_level(self):
        d=columns();d['y']=number([None]*9)
        r=calculate(_decode(d),opts('ttp',outcomeLevel='stale'))
        self.assertEqual(r['status'],[b for a,b in PAIRS])
        self.assertIsNone(r['component_missing_outcome'])
        self.assertTrue(all(x['component']=='Recurrence/progression' for x in r['components']))
        self.assertTrue(any('ignores' in w for w in r['warnings']))

    def test_all_missing_components_are_not_censored(self):
        d={'y':number([None]*3),'r':factor(['Yes','No',None],levels=['No','Yes'])}
        r=calculate(_decode(d),opts());self.assertEqual(r['status'],[1,None,None])
        d['r']=factor([None]*3,levels=['No','Yes'])
        r=calculate(_decode(d),opts());self.assertEqual(r['status'],[None]*3)
        self.assertTrue(all(x['percent'] is None for x in r['counts']))

    def test_explicit_levels_pending_invalid_and_unsupported_states(self):
        d=columns()
        self.assertIn('Choose',calculate(_decode(d),dict(outcome='y',recurrence='r',analysistype='rfs'))['pending'])
        self.assertIn('Select',calculate(_decode(d),dict(outcome='y',analysistype='rfs'))['pending'])
        for options in [dict(opts(),recurrenceLevel='stale'),opts(multievent=True)]:
            with self.assertRaises(InputError):calculate(_decode(d),options)
        bad=columns();bad['r']=number([0]*9)
        with self.assertRaisesRegex(InputError,'nominal'):calculate(_decode(bad),opts())
        bad=columns();bad['y']=factor(['Censored','Event','Competing']*3)
        with self.assertRaisesRegex(InputError,'competing-risk'):calculate(_decode(bad),opts(outcomeLevel='Event'))
        d=columns();d['y']=number([0])
        with self.assertRaisesRegex(InputError,'equal'):calculate(_decode(d),opts())

    def test_runtime_sparse_saved_output_and_audit(self):
        ids=[str(i*3+2) for i in range(9)]
        r=run_analysis('pyoutcomeorganizer',columns(),opts(diagnostics=True,showNaturalSummary=True,visualization=True),row_ids=ids)
        self.assertEqual(r['status'],'ok',r.get('error'))
        self.assertEqual(r['outputs']['addOutcome']['values'],OR)
        self.assertEqual(r['outputs']['addOutcome']['row_ids'],ids)
        self.assertEqual(r['outputs']['addOutcome']['levels'],['0','1'])
        self.assertIn('no first-event time',r['outputs']['addOutcome']['description'])
        self.assertEqual(r['tables']['compositeAudit']['rows'][0]['overrides'],2)
        self.assertEqual([x['code'] for x in r['tables']['preview']['rows']],OR)
        self.assertEqual(r['tables']['preview']['rows'][5]['outcomeComponent'],1)
        self.assertIn('FIRST',r['texts']['summary'])
        r=run_analysis('pyoutcomeorganizer',columns(),dict(opts(),recurrenceLevel=None),row_ids=ids)
        self.assertEqual(r['status'],'ok');self.assertFalse(r['outputs'])

    def test_generator_binds_and_rejects_invalid_list_visibility(self):
        sys.path.insert(0,str(ROOT/'tools'));import generate
        spec=generate.read_spec(ROOT/'inst/python/analyses/jsurvival/pyoutcomeorganizer.py')
        generate.validate(spec,'pyoutcomeorganizer')
        self.assertTrue(generate.list_visibility('(analysistype:rfs || analysistype:ttp)',{'analysistype':{'rfs','ttp'}}))
        for expression in ['(analysistype:missing)','(unknown:rfs)','(analysistype:rfs || bad:ttp)','(analysistype:rfs; run())','(analysistype:rfs || )']:
            changed=copy.deepcopy(spec);changed['results'][3]['visible']=expression
            with self.assertRaises(generate.SpecError):generate.validate(changed,'pyoutcomeorganizer')

if __name__=='__main__':unittest.main()
