"""Package cleanup must remove only regenerable module caches, never source/assets."""
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile
from cpjtest import ROOT
spec=importlib.util.spec_from_file_location('prune_bytecode',ROOT/'tools/prune-package-bytecode.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class PackageBytecode(unittest.TestCase):
    def test_preserves_member_bytes_metadata_and_orphan_or_vendor_bytecode(self):
        prefix='ClinicoPathPj/R/ClinicoPathPj/python/'
        records={prefix+'cpj_runtime.py':b'runtime source',prefix+'__pycache__/cpj_runtime.cpython-311.pyc':b'cache',
                 prefix+'analyses/meddecide/demo.py':b'analysis source',
                 prefix+'analyses/meddecide/__pycache__/demo.cpython-311.opt-1.pyc':b'cache',
                 prefix+'__pycache__/orphan.cpython-311.pyc':b'only implementation',
                 prefix+'vendor/library.py':b'vendor source',prefix+'vendor/__pycache__/library.cpython-311.pyc':b'reviewed vendor asset',
                 'ClinicoPathPj/jamovi.yaml':b'name: ClinicoPathPj\n'}
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'module.jmo'
            with zipfile.ZipFile(path,'w') as z:
                z.comment=b'archive comment'
                for name,data in records.items():
                    info=zipfile.ZipInfo(name,date_time=(2020,1,2,3,4,6));info.compress_type=zipfile.ZIP_DEFLATED
                    z.writestr(info,data)
            result=module.prune(path);self.assertEqual(len(result['removed']),2)
            with zipfile.ZipFile(path) as z:
                self.assertIsNone(z.testzip());self.assertEqual(z.comment,b'archive comment')
                for name in z.namelist():
                    self.assertEqual(z.read(name),records[name]);self.assertEqual(z.getinfo(name).date_time,(2020,1,2,3,4,6))
                self.assertIn(prefix+'vendor/__pycache__/library.cpython-311.pyc',z.namelist())
                self.assertIn(prefix+'__pycache__/orphan.cpython-311.pyc',z.namelist())
            first=path.read_bytes();second=module.prune(path)
            self.assertEqual(second['removed'],[]);self.assertEqual(path.read_bytes(),first)
            self.assertEqual(second['sha256'],hashlib.sha256(first).hexdigest())

    def test_invalid_archive_is_not_replaced(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'bad.jmo';path.write_bytes(b'not a zip')
            with self.assertRaises(zipfile.BadZipFile):module.prune(path)
            self.assertEqual(path.read_bytes(),b'not a zip')
