"""Adversarial synthetic archives test structural gates, not native jamovi saving."""
import json
from pathlib import Path
import runpy
import struct
import tempfile
import unittest
import zipfile
from cpjtest import ROOT

CHECK = runpy.run_path(str(ROOT / 'tools/check-svg-artifacts.py'))
SVG = b'<svg xmlns="http://www.w3.org/2000/svg" width="20" height="10"><circle cx="2" cy="3" r="1"/></svg>'
PNG = b'\x89PNG\r\n\x1a\n' + struct.pack('>I', 13) + b'IHDR' + struct.pack('>II', 20, 10) + b'\x08\x06\x00\x00\x00' + b'\x00' * 4
SNAPSHOT = '02 pysvgcutoff/resources/chart.svg'


def source():
    return {'metadata.json': json.dumps({'dataSet': {'rowCount': 6, 'columnCount': 2,
            'fields': [{'name': 'Measurement', 'type': 'number'}, {'name': 'Reference', 'type': 'integer'}]}}),
            'data.bin': b'synthetic numeric storage', 'xdata.json': '{}'}


def archive(path, entries):
    with zipfile.ZipFile(path, 'w') as output:
        for name, value in entries.items():
            output.writestr(name, value)
    return path


class SvgArtifacts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.baseline = archive(self.folder / 'baseline.omv', source())

    def saved(self, **changes):
        entries = source()
        entries.update({'02 pysvgcutoff/analysis': b'placeholder protobuf bytes ' + SNAPSHOT.encode(),
                        SNAPSHOT: SVG})
        entries.update(changes)
        return archive(self.folder / 'saved.omv', entries)

    def test_referenced_snapshot_and_unchanged_data(self):
        result = CHECK['inspect_omv'](self.saved(), self.baseline)
        self.assertTrue(result['referenced_snapshot_present'])
        self.assertTrue(result['source_data_unchanged'])
        self.assertEqual(result['rows'], 6)
        self.assertFalse(result['fresh_engine_reopen_verified'])
        self.assertFalse(result['options_and_native_statistics_verified'])

    def test_data_only_file_cannot_qualify(self):
        with self.assertRaisesRegex(ValueError, 'data-only files do not qualify'):
            CHECK['inspect_omv'](self.baseline, self.baseline)

    def test_modified_data_labels_or_types_rejected(self):
        for change in [{'data.bin': b'changed'}, {'xdata.json': '{"Reference": "changed"}'},
                       {'metadata.json': json.dumps({'dataSet': {'rowCount': 6, 'columnCount': 2,
                        'fields': [{'name': 'Measurement', 'type': 'integer'}, {'name': 'Reference', 'type': 'integer'}]}})}]:
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, 'Source data differ'):
                CHECK['inspect_omv'](self.saved(**change), self.baseline)

    def test_missing_unreferenced_empty_or_invalid_snapshot_rejected(self):
        for change in [{SNAPSHOT: b''}, {SNAPSHOT: b'<html/>'},
                       {'02 pysvgcutoff/analysis': b'unreferenced snapshot'},
                       {'02 pysvgcutoff/analysis': b''}]:
            with self.subTest(change=change), self.assertRaises((ValueError, CHECK['ET'].ParseError)):
                CHECK['inspect_omv'](self.saved(**change), self.baseline)
        entries = source()
        entries['02 pysvgcutoff/analysis'] = b'no resource'
        with self.assertRaisesRegex(ValueError, 'no SVG snapshot'):
            CHECK['inspect_omv'](archive(self.folder / 'missing.omv', entries), self.baseline)

    def test_duplicate_analyses_rejected(self):
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            CHECK['inspect_omv'](self.saved(**{'03 pysvgcutoff/analysis': b'another'}), self.baseline)

    def test_svg_empty_dtd_and_oversize_rejected(self):
        for raw in [b'<svg xmlns="http://www.w3.org/2000/svg"/>',
                    b'<!DOCTYPE svg><svg/>', b'x' * (CHECK['LIMIT'] + 1)]:
            with self.subTest(raw=raw[:30]), self.assertRaises(ValueError):
                CHECK['inspect_svg'](raw)

    def test_png_header_does_not_claim_pixel_validation(self):
        result = CHECK['inspect_png'](PNG)
        self.assertEqual((result['width'], result['height']), (20, 10))
        self.assertFalse(result['pixel_decoding_verified'])
        for raw in [b'wrong', PNG[:20], PNG[:16] + b'\0' * 8 + PNG[24:]]:
            with self.assertRaises(ValueError):
                CHECK['inspect_png'](raw)

    def docx(self, target='media/image1.png', mode='', drawing=True, media=True):
        document = ('<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
                    'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
                    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">' +
                    ('<a:blip r:embed="rId1"/>' if drawing else '') + '</w:document>')
        entries = {'word/document.xml': document,
                   'word/_rels/document.xml.rels': '<Relationships><Relationship Id="rId1" '
                   'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
                   f'Target="{target}" TargetMode="{mode}"/></Relationships>'}
        if media:
            entries['word/media/image1.png'] = PNG
        return archive(self.folder / 'export.docx', entries)

    def test_docx_resolves_drawing_to_embedded_media(self):
        result = CHECK['inspect_docx'](self.docx())
        self.assertEqual(list(result['embedded_images']), ['word/media/image1.png'])
        self.assertFalse(result['plot_identity_verified'])
        self.assertFalse(result['visual_rendering_verified'])

    def test_docx_missing_drawing_media_or_external_target_rejected(self):
        for options in [dict(drawing=False), dict(media=False), dict(mode='External'),
                        dict(target='../image1.png'), dict(target='https://example.com/image.png')]:
            with self.subTest(options=options), self.assertRaises((ValueError, KeyError)):
                CHECK['inspect_docx'](self.docx(**options))

    def test_historical_exports_and_false_positive_controls(self):
        result = CHECK['historical']()
        self.assertEqual(len(result['data_only_controls_rejected']), 2)
        self.assertEqual(result['svg']['graphic_marks'] > 0, True)

    def test_recorded_word_native_table_and_inspected_preview_image(self):
        result = CHECK['word_example']()
        self.assertEqual(result['native_counts'], [3, 2, 0, 1])
        self.assertEqual((result['native_cutoff'], result['preview_cutoff'],
                          result['local_snapshot_cutoff']), (2, 3, 2))
        self.assertFalse(result['word_page_rendering_verified'])
        self.assertFalse(result['save_reopen_verified'])

    def latex(self, source, figures=True):
        entries = {'article.tex': source}
        if figures:
            entries.update({f'figure_{i}.png': PNG for i in range(1, 4)})
        return archive(self.folder / 'latex.zip', entries)

    def test_latex_active_references_and_figure_files(self):
        path = self.latex('\n'.join(r'\includegraphics[width=3cm]{figure_' + str(i) + '.png}'
                                   for i in range(1, 4)))
        result = CHECK['inspect_latex'](path)
        self.assertEqual(len(result['active_figure_references']), 3)
        self.assertFalse(result['tex_compilation_verified'])
        self.assertFalse(result['visual_rendering_verified'])

    def test_latex_commented_missing_and_duplicate_figures_do_not_qualify(self):
        for source in ['% \\includegraphics{figure_1.png}',
                       '\\includegraphics{missing.png}',
                       '\n'.join(['\\includegraphics{figure_1.png}'] * 3)]:
            with self.subTest(source=source), self.assertRaises((ValueError, KeyError)):
                CHECK['inspect_latex'](self.latex(source))

    def test_latex_dynamic_paths_and_traversal_rejected(self):
        for target in ['../outside.png', '/tmp/image.png', '${address:2/explorer}', '\\custompath']:
            with self.subTest(target=target), self.assertRaises(ValueError):
                CHECK['inspect_latex'](self.latex('\\includegraphics{' + target + '}'))

    def test_empty_latex_destination_is_failure(self):
        path = self.folder / 'empty.zip'
        path.write_bytes(b'')
        with self.assertRaisesRegex(ValueError, 'zero bytes'):
            CHECK['inspect_latex'](path)

    def test_recorded_native_latex_export_did_not_produce_bundle(self):
        path = ROOT / 'docs/validation-exports/python-svg-28.17-latex.zip'
        # Closing the stalled jamovi session finalized an empty ZIP directory;
        # neither the initial zero-byte state nor that empty archive is a pass.
        if path.stat().st_size:
            with zipfile.ZipFile(path) as archive:
                self.assertEqual(archive.namelist(),[])
        with self.assertRaisesRegex(ValueError, 'zero bytes|no TeX source'):
            CHECK['inspect_latex'](path)
