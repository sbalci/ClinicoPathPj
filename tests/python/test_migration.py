"""Migration invariants, alias equivalence, frozen provenance and organized UI failures."""
import copy
import hashlib
import json
import sys
import tarfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'inst/python'))
sys.path.insert(0,str(ROOT/'tools'))
import cpj_registry
import cpj_runtime
import generate
from cpjtest import factor, number


class Registry(unittest.TestCase):
    def test_exact_target_set_and_frozen_bytes(self):
        entries=cpj_registry.read_registry()['analyses']
        targets=[e for e in entries if e.get('baseline')]
        self.assertEqual(len(targets),61)
        self.assertEqual({f:sum(e['family']==f for e in targets) for f in {e['family'] for e in targets}},
                         dict(descriptives=14,jjstatsplot=19,meddecide=15,jsurvival=9,oncopath=4))
        with tarfile.open(ROOT/'docs/baselines/released-2026-10-25.tar.gz') as archive:
            for entry in targets:
                for path,digest in entry['baseline']['files'].items():
                    data=archive.extractfile(entry['baseline']['module']+'/'+path).read()
                    self.assertEqual(hashlib.sha256(data).hexdigest(),digest)
        self.assertTrue(all(not e['coverage']['full_parity'] for e in targets))
        self.assertEqual(sum(e['status']=='utility' for e in entries),5)

    def test_planned_sources_and_invalid_paths_cannot_execute(self):
        for name in ['../decision','Decision/evil','decision.py','kappaSizeCI;print(1)']:
            with self.assertRaises(ValueError): cpj_registry.resolve(name)
        with self.assertRaisesRegex(FileNotFoundError,'planned'):cpj_registry.resolve('pysurvival')

    def test_existing_python_contracts_are_preserved(self):
        import tarfile, ast
        with tarfile.open(ROOT/'docs/baselines/clinicopathpj-pre-migration-source.tar.gz') as archive:
            preserved=0
            for entry in cpj_registry.read_registry()['analyses']:
                if not entry.get('baseline') or entry['status']!='partial' or entry['source_name']=='reportcat':continue
                member='inst/python/analyses/'+entry['id']+'.py'
                if member not in archive.getnames():continue
                preserved+=1
                original=archive.extractfile(member).read().decode()
                tree=ast.parse(original)
                previous=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SPEC' for t in n.targets)))
                _,path=cpj_registry.resolve(entry['id'])
                current=generate.read_spec(path)
                self.assertEqual(previous['options'],current['options'])
                self.assertEqual(previous['results'],current['results'])
                self.assertTrue(entry['id'].startswith('py'))
            self.assertEqual(preserved,10)

    def test_organized_ui_is_complete_and_rejects_broken_bindings(self):
        _,path=cpj_registry.resolve('pydecision')
        spec=generate.read_spec(path)
        ui=generate.u_yaml(spec)
        self.assertEqual(ui['compilerMode'],'tame')
        broken=copy.deepcopy(spec)
        broken['ui']['children'].append({'type':'CheckBox','name':'doesNotExist'})
        with self.assertRaisesRegex(generate.SpecError,'Unbound'): generate.validate_ui(broken)
        broken=copy.deepcopy(spec)
        broken['ui']['children'].append({'type':'CheckBox','name':'showConsole'})
        with self.assertRaisesRegex(generate.SpecError,'Duplicate'): generate.validate_ui(broken)
        broken=copy.deepcopy(spec)
        broken['ui']['children'][0]['enable']='(doesNotExist)'
        with self.assertRaisesRegex(generate.SpecError,'unknown'): generate.validate_ui(broken)
        broken=copy.deepcopy(spec);broken['ui']['children']=[]
        with self.assertRaisesRegex(generate.SpecError,'omits'): generate.validate_ui(broken)

    def test_saved_columns_keep_original_filtered_rows_and_missing_positions(self):
        spec={'results':[dict(name='saved',type='Output',measureType='continuous')]}
        out=cpj_runtime.Output(spec,['2','5','9'])
        out.column('saved',[1,None,3])
        self.assertEqual(out.outputs['saved'],dict(row_ids=['2','5','9'],values=[1.,None,3.],levels=None))
        with self.assertRaisesRegex(ValueError,'every input row'):out.column('saved',[1,3])
        categorical=cpj_runtime.Output({'results':[dict(name='saved',type='Output',measureType='ordinal')]},['2','5','9'])
        categorical.column('saved',[0,None,1],levels=['NA','High'])
        self.assertEqual(categorical.outputs['saved']['levels'],['NA','High'])
        with self.assertRaisesRegex(ValueError,'outside'):categorical.column('saved',[0,2,1],levels=['A','B'])

    def test_saved_column_metadata_rejects_invalid_measure_types_and_names(self):
        spec={'results':[dict(name='saved',type='Output',measureType='nominal')]}
        out=cpj_runtime.Output(spec,['2','5'])
        out.column('saved',[0,1],levels=['low','high'],title='Grade / band',description='Ordered groups',measure_type='ordinal')
        self.assertEqual(out.outputs['saved']['measure_type'],'ordinal')
        with self.assertRaisesRegex(ValueError,'measure type'):out.column('saved',[0,1],levels=['low','high'],measure_type='continuous')
        with self.assertRaisesRegex(ValueError,'title'):out.column('saved',[0,1],levels=['low','high'],title='bad\nname')
