"""Read-only DOCX/LaTeX checks for the two saved execution comparisons.

Does not render Word pages or compile TeX. Those actions have separate logs and
visual evidence. Only the literal, locally generated export fixtures are checked.
"""
import hashlib
import json
from pathlib import Path
import re
import runpy
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
EXPORTS = ROOT / 'docs/validation-exports'
SUPPORT = runpy.run_path(str(ROOT / 'tools/check-svg-artifacts.py'))
require = SUPPORT['require']
read = SUPPORT['read_member']
open_archive = SUPPORT['open_archive']
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}
SUMMARY = [['Input rows', 'N', 'Missing', 'Mean', 'Sample SD', 'Median', 'Minimum', 'Maximum'],
           ['6', '5', '1', '4.00', '3.54', '3.00', '1.00', '10.0']]
AUDIT = [['Row Classification', 'Rows'], ['Input rows', '22'],
         ['Missing age or gender', '2'], ['Unusable ages (negative or nonfinite)', '1'],
         ['Unselected gender levels', '1'], ['Outside age-break range', '0'],
         ['Retained observations', '18']]
POPULATION = [['Age Band', 'Female (n)', 'Male (n)', 'Total (n)', 'Female (%)', 'Male (%)'],
              ['0-4', '2', '1', '3', '25.0%', '10.0%'],
              ['5-9', '1', '2', '3', '12.5%', '20.0%'],
              ['10-14', '1', '3', '4', '12.5%', '30.0%'],
              ['15-19', '1', '0', '1', '12.5%', '0.0%'],
              ['20-24', '2', '2', '4', '25.0%', '20.0%'],
              ['65-69', '0', '1', '1', '0.0%', '10.0%'],
              ['85+', '1', '1', '2', '12.5%', '10.0%'],
              ['Total', '8', '10', '18', '100.0%', '100.0%']]


def normalize(value):
    return re.sub(r'\s+', ' ', value.replace(r'\u2009', '').replace('\u2009', '')
                  .replace(r'\%', '%').replace('~', '')).strip()


def expected_tables(family):
    return [SUMMARY, SUMMARY] if family == 'summary-service' else [AUDIT, POPULATION] * 2


def docx_tables(raw):
    document = SUPPORT['xml'](raw)
    tables = []
    for table in document.findall('.//w:tbl', NS):
        rows = [[normalize(''.join(cell.itertext())) for cell in row.findall('w:tc', NS)]
                for row in table.findall('w:tr', NS)]
        # Population notes use one merged cell after the numerical rows.
        tables.append([row for row in rows if len(row) > 1])
    return tables, document


def inspect_word(path, family):
    with open_archive(path) as archive:
        require(archive.testzip() is None, 'DOCX CRC failure')
        tables, document = docx_tables(read(archive, 'word/document.xml'))
        require(tables == expected_tables(family), 'DOCX native table values differ')
        drawings = document.findall('.//a:blip', NS)
        count = 0 if family == 'summary-service' else 2
        require(len(drawings) == count, 'Unexpected DOCX drawing count')
        text = ' '.join(document.itertext())
        require('Pj 1.5.0; runner: processx;' in text, 'Missing Word service identity')
    media = SUPPORT['inspect_docx'](path)['embedded_images'] if count else {}
    return dict(native_tables=len(tables), drawing_references=len(drawings),
                embedded_images=media, sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def tex_tables(source):
    tables = []
    for body in re.findall(r'\\begin\{tabular\}\{[^}]*\}(.*?)\\end\{tabular\}', source, re.S):
        body = re.sub(r'\\(?:toprule|midrule|bottomrule)\b', '', body)
        rows = [[normalize(cell) for cell in row.split('&')]
                for row in body.split('\\\\') if row.strip()]
        tables.append(rows)
    return tables


def inspect_tex(path, family):
    expected = 0 if family == 'summary-service' else 2
    figures = SUPPORT['inspect_latex'](path, expected_figures=expected)
    require(len(figures['active_figure_references']) == expected, 'Unexpected LaTeX figures')
    with open_archive(path) as archive:
        require(archive.testzip() is None, 'LaTeX bundle CRC failure')
        source = read(archive, 'article.tex').decode()
        active = re.sub(r'(?<!\\)%[^\n]*', '', source)
        require(tex_tables(active) == expected_tables(family), 'LaTeX native table values differ')
        require('Pj 1.5.0; runner: processx;' in source, 'Missing LaTeX service identity')
        labels = re.findall(r'\\label\{([^{}]+)\}', active)
        duplicates = sorted({label for label in labels if labels.count(label) > 1})
        figures['figure_sha256'] = {
            name: hashlib.sha256(read(archive, name)).hexdigest()
            for name in figures['active_figure_references']}
    return dict(native_tables=len(tex_tables(active)), **figures,
                duplicate_labels=duplicates, sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def check():
    records = {}
    for family in ('summary-service', 'age-pyramid'):
        stem = f'python-{family}-0.3.62-reopened'
        records[family] = dict(word=inspect_word(EXPORTS / (stem + '.docx'), family),
                               latex=inspect_tex(EXPORTS / (stem + '-latex.zip'), family))
    return dict(status='pass', scope='Native tables and media references; rendering/compilation separate',
                exports=records, native_Microsoft_Word_rendering_verified=False,
                latex_full_document_compilation_verified=False)


if __name__ == '__main__':
    print(json.dumps(check(), indent=2))
