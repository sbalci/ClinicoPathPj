"""Host preflight must detect the signature without declaring a host GUI-safe."""
import runpy
import unittest
from cpjtest import ROOT

inspect_sources = runpy.run_path(str(ROOT / 'tools/check-svg-host.py'))['inspect_sources']


class SvgHostPreflight(unittest.TestCase):
    def test_known_mismatch(self):
        result = inspect_sources('class Analysis:\n def set_svg(self):\n  return self.dataset.instance_path\n',
                                 'class DataSetModel:\n pass\n')
        self.assertEqual(result['status'], 'known_path_mismatch')
        self.assertEqual(result['known_bad_path_lines'], [3])

    def test_new_path_never_certifies_gui(self):
        result = inspect_sources('class Analysis:\n def set_svg(self):\n  return self.project.instance_path\n',
                                 'class DataSetModel:\n pass\n')
        self.assertEqual(result['status'], 'requires_runtime_qualification')
        self.assertFalse(result['gui_save_verified'])
        self.assertFalse(result['export_verified'])

    def test_compatible_accessor_and_inheritance_are_not_reported_as_confirmed_mismatch(self):
        source = 'class Analysis:\n def set_svg(self):\n  return self.dataset.instance_path\n'
        for dataset in ['class DataSetModel:\n instance_path = "example"\n',
                        'class DataSetModel:\n def __init__(self):\n  self.instance_path = "example"\n',
                        'class DataSetModel(Base):\n pass\n',
                        'class DataSetModel:\n def __getattr__(self, name):\n  pass\n']:
            with self.subTest(dataset=dataset):
                self.assertEqual(inspect_sources(source, dataset)['status'], 'requires_runtime_qualification')

    def test_unrecognized_source_cannot_pass(self):
        with self.assertRaises(StopIteration):
            inspect_sources('class Different:\n pass\n', 'class DataSetModel:\n pass\n')
