import itertools, sys, unittest
import numpy as np
from cpjtest import ROOT, number, factor, run_analysis
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_runtime import _decode, InputError
from cpj_firstevent import calculate

OPTIONS=dict(timeA='ta',timeB='tb',statusA='sa',statusB='sb',eventA='Y',freeA='N',eventB='Y',freeB='N')

def calc(ta,tb,sa,sb,**opts):
    d=_decode(dict(ta=number(ta),tb=number(tb),sa=factor(sa,levels=['N','Y']),sb=factor(sb,levels=['N','Y'])))
    return calculate(d,dict(OPTIONS,**opts))

class FirstEvent(unittest.TestCase):
    def test_literal_first_event_censor_tie_missing_and_negative(self):
        r=calc([2,8,2,8,5,5,5,0,None,3,-1,3], [8,2,8,2,5,5,5,0,4,4,4,4],
               ['Y','Y','N','N','Y','N','Y','Y','Y',None,'Y','N'],
               ['N','N','Y','Y','N','Y','Y','N','N','Y','N','N'])
        self.assertEqual(r['time'],[2,2,2,2,5,5,5,0,None,None,None,3])
        self.assertEqual(r['status'],[1,0,0,1,1,1,1,1,None,None,None,0])
        self.assertEqual(r['source'],[1,0,0,2,1,2,3,1,None,None,None,0])
        self.assertEqual((r['retained'],r['missing'],r['invalid'],r['ties'],r['late']),(9,2,1,3,2))
        self.assertEqual([x['n'] for x in r['counts']],[3,6])

    def test_independent_chronological_enumeration(self):
        for ta,tb,sa,sb in itertools.product([0,1,5],[0,1,5],['N','Y'],['N','Y']):
            # Process the earliest timeline group: event wins ties; otherwise observation ends.
            records=sorted([(ta,sa,'A'),(tb,sb,'B')])
            first_time=records[0][0]
            earliest=[r for r in records if r[0]==first_time]
            events=[r[2] for r in earliest if r[1]=='Y']
            want_source=3 if len(events)==2 else 1 if events==['A'] else 2 if events==['B'] else 0
            r=calc([ta],[tb],[sa],[sb])
            self.assertEqual((r['time'][0],r['status'][0],r['source'][0]),(first_time,int(bool(events)),want_source))

    def test_component_swap_and_scale_equivariance(self):
        a=[1,7,4,4];b=[7,1,4,4];sa=['Y','Y','N','Y'];sb=['N','N','Y','Y']
        r=calc(a,b,sa,sb);swap=calc(b,a,sb,sa);scaled=calc([x*2 for x in a],[x*2 for x in b],sa,sb)
        self.assertEqual(r['time'],swap['time']);self.assertEqual(r['status'],swap['status'])
        self.assertEqual(swap['source'],[{0:0,1:2,2:1,3:3}[x] for x in r['source']])
        self.assertEqual(scaled['time'],[2*x for x in r['time']])

    def test_known_event_does_not_override_unknown_first_component(self):
        r=calc([1,1],[None,2],['Y','Y'],['N',None])
        self.assertEqual(r['time'],[None,None]);self.assertEqual(r['status'],[None,None])
        self.assertTrue(all(x['percent'] is None for x in r['counts']))

    def test_pending_and_unmapped_levels_are_explicit(self):
        self.assertIn('Choose distinct',calc([1],[2],['Y'],['N'],freeA=None)['pending'])
        with self.assertRaises(InputError):calc([1],[2],['Y'],['N'],freeA='Y')
        with self.assertRaises(InputError):calc([1],[2],['Y'],['N'],eventA='absent')
        d=_decode(dict(ta=number([1]),tb=number([2]),sa=factor(['third'],levels=['N','Y','third']),sb=factor(['N'],levels=['N','Y'])))
        with self.assertRaisesRegex(InputError,'outside'):calculate(d,OPTIONS)
        d['sa']=np.array([1])
        with self.assertRaisesRegex(InputError,'nominal'):calculate(d,OPTIONS)

    def test_storage_lengths_nonfinite_and_limits(self):
        for a,b in [([],[]),([1],[1,2]),([np.inf],[2]),([1]*10001,[2]*10001)]:
            with self.assertRaises(InputError):calc(a,b,['Y']*len(a),['N']*len(b))
        for limit in [True,9,101,1.5]:
            with self.assertRaises(InputError):calc([1],[2],['Y'],['N'],preview_rows=limit)
        d=_decode(dict(ta=number([1]),tb=number([2]),sa=factor(['Y'],levels=['N','Y']),sb=factor(['N'],levels=['N','Y'])))
        d.metadata['ta']={'classes':['Date']}
        with self.assertRaisesRegex(InputError,'convert dates'):calculate(d,OPTIONS)

    def test_runtime_alignment_and_optional_results(self):
        d=dict(ta=number([1,5,None]),tb=number([5,1,3]),sa=factor(['Y','Y','Y'],levels=['N','Y']),sb=factor(['N','N','N'],levels=['N','Y']))
        r=run_analysis('pyfirstevent',d,dict(OPTIONS,showReport=True,showPlot=True),row_ids=['2','8','91'])
        self.assertEqual(r['status'],'ok',r.get('error'))
        self.assertEqual(r['outputs']['timeOut']['values'],[1,1,None])
        self.assertEqual(r['outputs']['statusOut']['values'],[1,0,None])
        self.assertEqual(r['outputs']['sourceOut']['values'],[1,0,None])
        self.assertEqual(r['outputs']['timeOut']['row_ids'],['2','8','91'])
        self.assertEqual(r['outputs']['timeOut']['title'],'Composite time')
        self.assertEqual(r['plots']['distribution']['columns']['value'],[1,1])
        self.assertIn('event wins',r['texts']['summary'])
        r=run_analysis('pyfirstevent',d,OPTIONS)
        self.assertFalse(r['plots']);self.assertNotIn('report',r['texts'])

    def test_bounded_preview_and_same_roles(self):
        r=run_analysis('pyfirstevent',dict(t=number(range(30)),s=factor(['Y']*30,levels=['N','Y'])),
                       dict(OPTIONS,timeA='t',timeB='t',statusA='s',statusB='s',preview_rows=10))
        self.assertEqual(r['status'],'ok');self.assertEqual(len(r['tables']['preview']['rows']),10)
        self.assertEqual(r['tables']['cohort']['rows'][0]['retained'],30)
        self.assertEqual([x['source'] for x in r['tables']['preview']['rows']],['Both components']*10)


class AdministrativeCensoring(unittest.TestCase):
    def test_literal_cutoff_and_inclusive_event_boundary(self):
        r=calc([2,8,2,8,5,5,5,0,None,3,-1,3], [8,2,8,2,5,5,5,0,4,4,4,4],
               ['Y','Y','N','N','Y','N','Y','Y','Y',None,'Y','N'],
               ['N','N','Y','Y','N','Y','Y','N','N','Y','N','N'],use_admin=True,admin_cutoff='2')
        self.assertEqual(r['time'],[2,2,2,2,2,2,2,0,None,None,None,2])
        self.assertEqual(r['status'],[1,0,0,1,0,0,0,1,None,None,None,0])
        self.assertEqual(r['source'],[1,0,0,2,4,4,4,1,None,None,None,4])
        self.assertEqual(r['admin'],dict(enabled=True,cutoff=2.,shortened=4,eventsRemoved=3,censoredShortened=1,tiedEvents=2))
        self.assertEqual((r['rows'][4]['baseTime'],r['rows'][4]['baseStatus'],r['rows'][4]['adminApplied']),(5,1,1))
        self.assertEqual((r['rows'][0]['baseTime'],r['rows'][0]['baseStatus'],r['rows'][0]['adminApplied']),(2,1,0))
        self.assertIsNone(r['rows'][8]['adminApplied'])

    def test_independent_three_timepoint_timeline(self):
        for ta,tb,sa,sb,cutoff in itertools.product([0,1,5],[0,1,5],['N','Y'],['N','Y'],[0,1,3,5,10]):
            timeline=[(ta,sa=='Y'),(tb,sb=='Y'),(cutoff,False)]
            first=min(x[0] for x in timeline)
            event=int(any(t==first and e for t,e in timeline))
            r=calc([ta],[tb],[sa],[sb],use_admin=True,admin_cutoff=str(cutoff))
            self.assertEqual((r['time'][0],r['status'][0]),(first,event))

    def test_disabled_path_preserves_values_sources_and_ignores_inactive_cutoff(self):
        a=calc([1,4],[4,1],['Y','Y'],['N','N'])
        b=calc([1,4],[4,1],['Y','Y'],['N','N'],use_admin=False,admin_cutoff='invalid')
        self.assertEqual(a,b)
        r=calc([0,5],[0,8],['Y','Y'],['N','N'],use_admin=True,admin_cutoff='0')
        self.assertEqual(r['status'],[1,0]);self.assertEqual(r['source'],[1,4])

    def test_explicit_cutoff_validation_and_pending(self):
        for value in ['',None,'   ']:self.assertIn('Enter',calc([1],[2],['Y'],['N'],use_admin=True,admin_cutoff=value)['pending'])
        for value in ['NaN','Inf','-Inf','-1','nonsense','9'*65,True,2]:
            with self.assertRaises(InputError):calc([1],[2],['Y'],['N'],use_admin=True,admin_cutoff=value)
        with self.assertRaises(InputError):calc([1],[2],['Y'],['N'],use_admin='true',admin_cutoff='2')
        self.assertEqual(calc([1],[2],['Y'],['N'],use_admin=True,admin_cutoff=' 1e0 ')['status'],[1])

    def test_runtime_audit_output_contract_and_missing_recovery(self):
        data=dict(ta=number([1,5,None]),tb=number([5,8,3]),sa=factor(['Y','Y','Y'],levels=['N','Y']),sb=factor(['N','N','N'],levels=['N','Y']))
        r=run_analysis('pyfirstevent',data,dict(OPTIONS,use_admin=True,admin_cutoff='2',showReport=True),row_ids=['2','9','41'])
        self.assertEqual(r['status'],'ok',r.get('error'))
        self.assertEqual(r['outputs']['timeOut']['values'],[1,2,None])
        self.assertEqual(r['outputs']['statusOut']['values'],[1,0,None])
        self.assertEqual(r['outputs']['sourceOut']['values'],[1,4,None])
        self.assertEqual(r['outputs']['sourceOut']['levels'][-1],'Administrative cutoff')
        self.assertEqual(r['outputs']['timeOut']['row_ids'],['2','9','41'])
        self.assertEqual(r['tables']['adminAudit']['rows'][0]['eventsRemoved'],1)
        self.assertEqual(r['tables']['preview']['rows'][1]['baseTime'],5)
        self.assertIn('cutoff 2',r['outputs']['timeOut']['description'])
        pending=run_analysis('pyfirstevent',data,dict(OPTIONS,use_admin=True,admin_cutoff=''))
        self.assertEqual(pending['status'],'ok');self.assertFalse(pending['outputs']);self.assertFalse(pending['tables'])
        original=run_analysis('pyfirstevent',data,OPTIONS,row_ids=['2','9','41'])
        self.assertEqual(original['outputs']['statusOut']['values'],[1,1,None])
        self.assertEqual(len(original['outputs']['sourceOut']['levels']),4)
        self.assertNotIn('adminAudit',original['tables'])

if __name__=='__main__':unittest.main()
