import sys,unittest
from cpjtest import ROOT,number,factor,text,run_analysis
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_runtime import _decode,InputError
from cpj_identity import audit
from cpj_firstevent import calculate
from test_firstevent import OPTIONS

class Identity(unittest.TestCase):
    def test_exact_labels_missing_and_repeated_counts(self):
        labels=['001','001','1','01','NA',None,'','  ',' S','S','S ']
        r=audit(_decode({'id':text(labels)}),'id',len(labels))
        self.assertEqual((r['known'],r['missing'],r['subjects'],r['repeatedSubjects'],r['repeatedRows']),(8,3,7,1,2))
        self.assertEqual(r['repeated'],[dict(subject='001',records=2)])
        self.assertEqual(r['rowCounts'],[2,2,1,1,1,None,None,None,1,1,1])
        self.assertEqual(r['values'][-3:],[' S','S','S '])

    def test_factor_labels_actual_na_unused_levels_and_literal_na(self):
        col=dict(kind='factor',levels=['001','NA',None,'unused'],codes=[0,0,1,2,None])
        r=audit(_decode({'id':col}),'id',5)
        self.assertEqual(r['values'],['001','001','NA',None,None])
        self.assertEqual((r['subjects'],r['missing']),(2,2))
        self.assertEqual(r['repeated'],[dict(subject='001',records=2)])

    def test_strict_validation_and_invalid_storage(self):
        # jamovi defaults exclude ID-measure columns unless explicitly permitted.
        import ast
        source=ROOT/'inst/python/analyses/jsurvival/pyfirstevent.py'
        spec=next(ast.literal_eval(n.value) for n in ast.parse(source.read_text()).body
                  if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SPEC' for t in n.targets))
        role=next(o for o in spec['options'] if o['name']=='subject')
        self.assertEqual(role['permitted'],['factor','id'])
        self.assertIn('id',spec['ui']['children'][0]['permitted'])
        for ids in [['a','a'],['a',None],['a',' ']]:
            with self.assertRaisesRegex(InputError,'One record'):audit(_decode({'id':text(ids)}),'id',2,True)
        self.assertEqual(audit(_decode({'id':text(['a','b'])}),'id',2,True)['subjects'],2)
        for col in [number([1,2]),text(['a\nb','c']),text(['a'*257,'b'])]:
            with self.assertRaises(InputError):audit(_decode({'id':col}),'id',2)
        with self.assertRaises(InputError):audit(_decode({'id':text(['a'])}),'id',2)
        d=_decode({'id':text(['a'])});d.metadata['id']={'classes':['Date']}
        with self.assertRaises(InputError):audit(d,'id',1)

    def test_order_permutation_and_counts_match_independent_positions(self):
        ids=['b','a','b',None,'c','a','b']
        r=audit(_decode({'id':text(ids)}),'id',7)
        expected={x:[i for i,v in enumerate(ids) if v==x] for x in set(ids) if x is not None}
        self.assertEqual(r['rowCounts'],[len(expected[x]) if x is not None else None for x in ids])
        self.assertEqual(r['repeated'],[dict(subject='b',records=3),dict(subject='a',records=2)])
        q=audit(_decode({'id':text(ids[::-1])}),'id',7)
        self.assertEqual(q['rowCounts'],r['rowCounts'][::-1])
        self.assertEqual(q['subjects'],r['subjects'])

    def test_runtime_identity_preserves_endpoint_outputs_and_sparse_rows(self):
        data=dict(ta=number([1,5,None]),tb=number([5,8,3]),sa=factor(['Y']*3,levels=['N','Y']),sb=factor(['N']*3,levels=['N','Y']),id=text(['001','001',None]))
        opts=dict(OPTIONS,audit_subject=True,subject='id',use_admin=True,admin_cutoff='2')
        r=run_analysis('pyfirstevent',data,opts,row_ids=['2','9','41'])
        self.assertEqual(r['status'],'ok',r.get('error'))
        self.assertEqual(r['outputs']['timeOut']['values'],[1,2,None])
        self.assertEqual(r['outputs']['timeOut']['row_ids'],['2','9','41'])
        self.assertEqual(r['tables']['identityAudit']['rows'][0]['repeatedRows'],2)
        self.assertEqual(r['tables']['preview']['rows'][2]['subjectRecords'],None)
        self.assertIn('ALL supplied',r['texts']['identityPolicy'])
        original=run_analysis('pyfirstevent',data,dict(opts,audit_subject=False))
        disabled=run_analysis('pyfirstevent',data,dict(opts,audit_subject=False),row_ids=['2','9','41'])
        self.assertEqual(r['outputs'],disabled['outputs'])
        self.assertNotIn('identityAudit',original['tables'])
        pending=run_analysis('pyfirstevent',data,dict(opts,subject=None))
        self.assertFalse(pending['outputs']);self.assertIn('Select',pending['texts']['summary'])
        strict=run_analysis('pyfirstevent',data,dict(opts,require_unique_id=True))
        self.assertEqual(strict['status'],'input_error');self.assertIn('One record',strict['error']['message'])

    def test_bounded_repeats_and_missing_audit_gate(self):
        ids=[str(i) for i in range(25)]*2
        data=dict(ta=number([1]*50),tb=number([2]*50),sa=factor(['Y']*50,levels=['N','Y']),sb=factor(['N']*50,levels=['N','Y']),id=text(ids))
        r=run_analysis('pyfirstevent',data,dict(OPTIONS,audit_subject=True,subject='id'))
        self.assertEqual(len(r['tables']['repeatedSubjects']['rows']),20)
        self.assertEqual(r['tables']['identityAudit']['rows'][0]['repeatedSubjects'],25)
        pending=calculate(_decode(data),dict(OPTIONS,require_unique_id=True))
        self.assertIn('Enable',pending['pending'])
        for value in ['yes',1]:
            with self.assertRaises(InputError):calculate(_decode(data),dict(OPTIONS,audit_subject=value))

if __name__=='__main__':unittest.main()
