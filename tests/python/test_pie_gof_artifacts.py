"""Synthetic HTML probes qualify the checker, not jamovi desktop saving."""
import base64
import copy
from html import escape
import importlib.util
import re
import unittest
from unittest.mock import patch
from urllib.parse import unquote
import zipfile
from cpjtest import ROOT

spec = importlib.util.spec_from_file_location('pie_gof_artifacts', ROOT/'tools/check-pie-gof-artifacts.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def table(rows):
    return '<table>'+''.join('<tr>'+''.join('<td>'+escape(str(c))+'</td>' for c in r)+'</tr>' for r in rows)+'</table>'


class PieGOFArtifacts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Reuse an actual qualified descriptive display; inference HTML below is
        # synthetic, explicitly not a saved GUI artifact or numerical engine oracle.
        with zipfile.ZipFile(ROOT/'docs/validation-exports/python-pie-0.3.72-reopened.omv') as z:
            html = z.read('index.html').decode()
            cls.descriptive = checker.base.module.Tables(html).tables
            path = re.findall(r'<img[^>]*src="([^"]+\.png)"', html)[0]
            cls.png = z.read(unquote(path))
        cls.image = '<img src="data:image/png;base64,'+base64.b64encode(cls.png).decode()+'">'

    def rows(self, mode='custom'):
        rows = copy.deepcopy(self.descriptive)
        if mode in ('legacy', 'off'):
            return rows
        ref = checker.REF['equal' if mode == 'equal' else 'custom']
        gof = [['Fixed-Null Goodness-of-Fit'], ['Method','Null','X2','df','p','Minimum','Small','Status'],
            ['Pearson chi-square goodness of fit',
             'Equal probabilities' if mode == 'equal' else 'Custom labelled ratios',
             f'{ref["statistic"]:.2f}', str(ref['df']), f'{ref["p"]:.3f}',
             str(ref['minimum']), str(ref['small']),
             'Asymptotic approximation' if mode == 'equal' else 'Sparse approximation'],
            ['A large p-value does not establish equivalence']]
        expected = [['Expected Category Mapping and Pearson Audit'],
            ['Code','Category','Observed','Probability','Expected','Residual','Contribution']]
        for i, category in enumerate(ref['categories']):
            expected.append([str(i),category,str(ref['observed'][i]),
                f'{100*ref["probability"][i]:.1f}%',str(ref['expected'][i]),
                f'{ref["residual"][i]:.3f}',f'{ref["contribution"][i]:.3f}'])
        expected.append(['Prespecified probabilities'])
        return rows[:3]+[gof]+([] if mode == 'expectedoff' else [expected])+rows[3:]

    def html(self, rows, image=True):
        return ''.join(table(r) for r in rows)+(self.image if image else '')

    def test_all_valid_display_modes(self):
        for mode in ('legacy','equal','custom','off','expectedoff','recovered','reopened'):
            with self.subTest(mode=mode):
                self.assertEqual(len(checker.inspect(self.html(self.rows(mode)),mode)),1)

    def test_wrong_expected_values_and_labels_are_rejected(self):
        for column, value in ((0,'9'),(1,'WRONG'),(2,'99'),(3,'90%'),(4,'99'),(5,'99'),(6,'99')):
            rows = self.rows()
            rows[4][2][column] = value
            with self.subTest(column=column), self.assertRaises(ValueError):
                checker.inspect(self.html(rows),'custom')

    def test_truncated_or_extended_expected_rows_are_rejected(self):
        for alter in (lambda r:r[:-1],lambda r:r+['unexpected']):
            rows = self.rows()
            rows[4][2] = alter(rows[4][2])
            with self.subTest(alter=alter), self.assertRaises(ValueError):
                checker.inspect(self.html(rows),'custom')

    def test_extra_observed_and_case_cells_are_rejected(self):
        for index in (2,5):
            rows = self.rows()
            rows[index][2].append('unexpected')
            with self.subTest(index=index), self.assertRaises(ValueError):
                checker.inspect(self.html(rows),'custom')

    def test_empty_states_reject_stale_values_notes_and_images(self):
        empty = [[['Title'],['Column'],['']] for _ in range(6)]
        self.assertEqual(checker.inspect(self.html(empty,False),'incomplete'),[])
        self.assertEqual(checker.inspect('duplicate label'+self.html(empty,False),'invalid'),[])
        for stale in (self.html(empty), 'total frequency N=25'+self.html(empty,False),
                      self.html(empty,False).replace('<td></td>','<td>stale note</td>',1)):
            with self.subTest(stale=stale[:80]), self.assertRaises(ValueError):
                checker.inspect(stale,'incomplete')

    def test_missing_or_duplicate_plot_is_rejected(self):
        html = self.html(self.rows())
        for changed in (html.replace(self.image,''),html+self.image):
            with self.assertRaises(ValueError):
                checker.inspect(changed,'custom')

    def test_unknown_mode_is_rejected(self):
        with self.assertRaises(ValueError):
            checker.inspect(self.html(self.rows()),'custmo')

    def test_version_selects_real_files_and_cannot_escape_export_folder(self):
        with patch.object(checker.zipfile,'ZipFile',side_effect=FileNotFoundError('not created')) as read:
            with self.assertRaises(FileNotFoundError):checker.check('0.3.74')
            read.assert_called_once_with(checker.EXPORTS/'python-pie-gof-0.3.74-legacy.omv')
        for version in ('../../escape','0.3',None,74):
            with self.subTest(version=version),self.assertRaisesRegex(ValueError,'Invalid package version'):
                checker.check(version)

    def test_export_preserves_saved_tables_and_pixels(self):
        rows = self.rows()
        html = self.html(rows)
        image = checker.inspect(html,'reopened')[0]
        self.assertEqual(checker.inspect_export(html,rows,image),[image])
        # Both displays round correctly against R, but the export must retain
        # the saved native table's precision and all of its labels/notes.
        rounded = copy.deepcopy(rows)
        rounded[3][2][2] = '3'
        self.assertEqual(len(checker.inspect(self.html(rounded),'reopened')),1)
        with self.assertRaisesRegex(ValueError,'HTML tables differ'):
            checker.inspect_export(self.html(rounded),rows,image)
        with self.assertRaisesRegex(ValueError,'HTML plot changed'):
            checker.inspect_export(html,rows,dict(image,pixel_sha256='wrong'))

    def test_native_percentage_spacing_preserves_digits_and_precision(self):
        rows=self.rows();image=checker.inspect(self.html(rows),'reopened')[0]
        spaced=copy.deepcopy(rows)
        for table_index,column in ((2,4),(4,3)):
            for row in spaced[table_index][2:6]:row[column]=row[column].replace('%',' %')
        self.assertEqual(checker.inspect_export(self.html(spaced),rows,image),[image])
        spaced[4][2][3]='40 %'
        with self.assertRaisesRegex(ValueError,'HTML tables differ'):
            checker.inspect_export(self.html(spaced),rows,image)


if __name__ == '__main__':
    unittest.main()
