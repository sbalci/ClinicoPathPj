"""A failed dependency preparation must preserve the existing bundle."""
import hashlib,importlib.util,json,tempfile,unittest,zipfile
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('vendor',ROOT/'tools/vendor-python.py')
vendor=importlib.util.module_from_spec(spec);spec.loader.exec_module(vendor)

class VendorStaging(unittest.TestCase):
    def fixture(self,root):
        (root/'vendor').mkdir();target=root/'inst/python/_vendor';target.mkdir(parents=True)
        (target/'old').write_text('existing')
        wheel=root/'vendor/example.whl'
        with zipfile.ZipFile(wheel,'w') as z:z.writestr('example/__init__.py','value=1')
        lock=dict(platform='test',packages=[dict(wheel='vendor/example.whl',sha256=hashlib.sha256(wheel.read_bytes()).hexdigest())])
        (root/'vendor/python-lock.json').write_text(json.dumps(lock));return target

    def test_failed_extraction_retains_previous_bundle(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);target=self.fixture(root)
            with mock.patch.object(vendor,'ROOT',root),mock.patch.object(zipfile.ZipFile,'extractall',side_effect=OSError('interrupted')):
                with self.assertRaisesRegex(OSError,'interrupted'):vendor.main()
            self.assertEqual((target/'old').read_text(),'existing')
            self.assertFalse((target/'python-lock.json').exists())

    def test_success_replaces_whole_bundle(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);target=self.fixture(root)
            with mock.patch.object(vendor,'ROOT',root):vendor.main()
            self.assertFalse((target/'old').exists())
            self.assertEqual((target/'example/__init__.py').read_text(),'value=1')
            self.assertTrue((target/'python-lock.json').is_file())

    def test_bad_checksum_retains_previous_bundle(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);target=self.fixture(root);(root/'vendor/example.whl').write_bytes(b'broken')
            with mock.patch.object(vendor,'ROOT',root):
                with self.assertRaisesRegex(ValueError,'checksum'):vendor.main()
            self.assertEqual((target/'old').read_text(),'existing')
