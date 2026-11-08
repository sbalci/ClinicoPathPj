"""Read-only structural SVG qualification checks; never certifies desktop behavior.

No archive extraction, JavaScript, R, office software or LaTeX is executed.
--historical checks recorded image exports and rejects the old data-only controls.
New --omv checks require a data-only --baseline saved from the same synthetic data.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import struct
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
LIMIT = 16 * 1024 * 1024


def require(condition, message):
    if not condition:
        raise ValueError(message)


def xml(raw):
    require(len(raw) <= LIMIT, 'XML exceeds inspection limit')
    require(b'<!DOCTYPE' not in raw.upper() and b'<!ENTITY' not in raw.upper(),
            'DTD/entity declarations are unsupported')
    return ET.fromstring(raw)


def inspect_svg(raw):
    root = xml(raw)
    require(root.tag == '{http://www.w3.org/2000/svg}svg', 'Expected an SVG root')
    marks = sum(n.tag.rsplit('}', 1)[-1] in
                {'path', 'circle', 'ellipse', 'rect', 'line', 'polyline', 'polygon'}
                for n in root.iter())
    require(marks > 0, 'SVG contains no graphic marks')
    return dict(width=root.get('width'), height=root.get('height'),
                viewBox=root.get('viewBox'), graphic_marks=marks,
                sha256=hashlib.sha256(raw).hexdigest())


def inspect_png(raw):
    require(len(raw) >= 33 and raw[:8] == b'\x89PNG\r\n\x1a\n'
            and raw[12:16] == b'IHDR', 'Expected a PNG header')
    width, height = struct.unpack('>II', raw[16:24])
    require(width > 0 and height > 0, 'PNG dimensions must be positive')
    return dict(width=width, height=height, sha256=hashlib.sha256(raw).hexdigest(),
                pixel_decoding_verified=False)


def read_member(archive, name):
    info = archive.getinfo(name)
    require(info.file_size <= LIMIT, 'Archive member exceeds inspection limit: ' + name)
    return archive.read(info)


def open_archive(path):
    archive = zipfile.ZipFile(path)
    names = archive.namelist()
    if len(names) != len(set(names)) or len(names) > 2000:
        archive.close()
        raise ValueError('Duplicate or excessive archive members')
    return archive


def source_data(archive):
    metadata = json.loads(read_member(archive, 'metadata.json'))['dataSet']
    require(metadata['rowCount'] > 0 and metadata['columnCount'] > 0, 'Expected populated source data')
    return dict(rows=metadata['rowCount'], columns=metadata['columnCount'],
                fields=metadata['fields'],
                data=read_member(archive, 'data.bin'),
                labels=json.loads(read_member(archive, 'xdata.json')),
                strings=read_member(archive, 'strings.bin') if 'strings.bin' in archive.namelist() else b'')


def inspect_omv(path, baseline):
    with open_archive(baseline) as archive:
        original = source_data(archive)
    with open_archive(path) as archive:
        actual = source_data(archive)
        require(actual == original, 'Source data differ from the data-only baseline')
        candidates = [n for n in archive.namelist() if re.fullmatch(r'\d+ pysvgcutoff/analysis', n)]
        require(len(candidates) == 1, 'Expected exactly one saved pysvgcutoff analysis; data-only files do not qualify')
        record = read_member(archive, candidates[0])
        require(bool(record), 'Saved analysis record is empty')
        prefix = candidates[0].removesuffix('analysis') + 'resources/'
        snapshots = [n for n in archive.namelist() if n.startswith(prefix) and n.endswith('.svg')]
        require(bool(snapshots), 'Saved analysis has no SVG snapshot resource')
        snapshots = {n: inspect_svg(read_member(archive, n)) for n in snapshots}
        require(any(n.encode() in record for n in snapshots), 'SVG resources are not referenced by the saved analysis')
    return dict(source_data_unchanged=True, rows=actual['rows'], columns=actual['columns'],
                analysis=candidates[0], referenced_snapshot_present=True, snapshots=snapshots,
                options_and_native_statistics_verified=False, fresh_engine_reopen_verified=False)


def inspect_docx(path):
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
          'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
          'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
    with open_archive(path) as archive:
        document = xml(read_member(archive, 'word/document.xml'))
        rels = xml(read_member(archive, 'word/_rels/document.xml.rels'))
        mapping = {r.get('Id'): r for r in rels}
        embedded = document.findall('.//a:blip', ns)
        require(bool(embedded), 'DOCX has no embedded drawing images')
        images = {}
        for blip in embedded:
            relation = mapping.get(blip.get('{' + ns['r'] + '}embed'))
            require(relation is not None, 'Drawing image relationship is missing')
            require(relation.get('TargetMode') != 'External', 'Drawing image must be embedded')
            require(relation.get('Type', '').endswith('/image'), 'Expected an image relationship')
            target = relation.get('Target', '')
            member = PurePosixPath('word') / target
            require(target.startswith('media/') and '..' not in member.parts,
                    'Unsupported image relationship target')
            raw = read_member(archive, str(member))
            if member.suffix.lower() == '.png':
                images[str(member)] = inspect_png(raw)
            elif member.suffix.lower() == '.svg':
                images[str(member)] = inspect_svg(raw)
            else:
                raise ValueError('Unsupported image format: ' + member.suffix)
    return dict(embedded_images=images, plot_identity_verified=False,
                visual_rendering_verified=False, javascript_absence_verified=False)


def historical():
    folder = ROOT / 'docs/validation-exports'
    stem = 'python-svg-cutoff-0.3.7-'
    svg = inspect_svg((folder / (stem + 'preview.svg')).read_bytes())
    png = inspect_png((folder / (stem + 'preview.png')).read_bytes())
    require((svg['width'], svg['height']) == ('980', '720'), 'Historical SVG dimensions changed')
    require((png['width'], png['height']) == (3136, 2342), 'Historical PNG dimensions changed')
    root = xml((folder / (stem + 'preview.svg')).read_bytes())
    labels = ' | '.join(''.join(n.itertext()) for n in root.iter()
                        if n.tag == '{http://www.w3.org/2000/svg}text')
    for expected in ['Native applied rule: Measurement ≥ 2.0',
                     'Preview cutoff 3: TP 2 · FP 1 · FN 1 · TN 2',
                     'Local snapshot cutoff 3: TP 2 · FP 1 · FN 1 · TN 2']:
        require(expected in labels, 'Historical native/preview/snapshot label changed: ' + expected)
    require(root.get('data-payload') is None, 'Runtime lookup payload remains in exported SVG')
    rejected = []
    baseline = folder / (stem + 'data-only-control.omv')
    for name in ['data-only-control.omv', 'validation.omv']:
        try:
            inspect_omv(folder / (stem + name), baseline)
        except ValueError as error:
            require('data-only files do not qualify' in str(error), 'Unexpected control failure: ' + str(error))
            rejected.append(stem + name)
        else:
            raise ValueError('A historical data-only file was accepted as a saved SVG analysis')
    return dict(svg=svg, png=png, native_preview_snapshot_labels='pass',
                data_only_controls_rejected=rejected)


def word_example():
    """Recheck the recorded six-row macOS 28.17 export, not arbitrary DOCX files."""
    folder = ROOT / 'docs/validation-exports'
    path = folder / 'python-svg-28.17-confirmed-preview3.docx'
    structural = inspect_docx(path)
    with open_archive(path) as archive:
        document = xml(read_member(archive, 'word/document.xml'))
        ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        text = ''.join(document.itertext())
        for marker in ['<script', 'document.addEventListener', 'function(', 'data-payload', 'cpj-svg']:
            require(marker not in text, 'JavaScript marker found in exported document text: ' + marker)
        tables = []
        for table in document.findall('.//w:tbl', ns):
            tables.append([[''.join(cell.itertext()) for cell in row.findall('w:tc', ns)]
                           for row in table.findall('w:tr', ns)])
        classification = next(t for t in tables if t and t[0] == ['Classification', 'Count'])
        require(classification[1:] == [['True positive', '3'], ['False positive', '2'],
                                      ['False negative', '0'], ['True negative', '1']],
                'Native cutoff-2 classification table changed')
        require('Native applied rule: Measurement >= 2.0' in text, 'Native rule label changed')
        expected = 'f3c6fd2f2ff60acab28a663fef3b7eaaa762c302178559cf44b17a9207018ad9'
        matching = [name for name, image in structural['embedded_images'].items()
                    if image['sha256'] == expected]
        require(len(matching) == 1, 'Visually inspected SVG preview image changed')
        require(read_member(archive, matching[0]) ==
                (folder / 'python-svg-28.17-preview3-embedded.png').read_bytes(),
                'Extracted preview differs from embedded DOCX bytes')
    return dict(native_counts=[3, 2, 0, 1], native_cutoff=2, preview_cutoff=3,
                local_snapshot_cutoff=2, native_rule_text='pass',
                inspected_preview_media_sha256=expected, embedded_media=matching[0],
                exported_text_marker_scan='pass; limited patterns, not a general JavaScript detector',
                word_page_rendering_verified=False, save_reopen_verified=False)


def inspect_latex(path, expected_figures=3):
    """Inspect ordinary includegraphics references; does not evaluate TeX/macros."""
    require(path.stat().st_size > 0, 'LaTeX destination is zero bytes; no bundle to qualify')
    with open_archive(path) as archive:
        tex_files = [n for n in archive.namelist() if n.endswith('.tex')]
        require(bool(tex_files), 'LaTeX bundle has no TeX source')
        references = []
        for name in tex_files:
            source = read_member(archive, name).decode('utf-8')
            # Bounded literal inspection, not a TeX parser: dynamic paths/macros
            # and extension inference deliberately do not qualify here.
            active = re.sub(r'(?<!\\)%[^\n]*', '', source)
            targets = re.findall(r'\\includegraphics\*?\s*(?:\[[^\]]*\]\s*)?\{([^{}]+)\}', active)
            for target in targets:
                relative = PurePosixPath(target)
                require(not relative.is_absolute() and '..' not in relative.parts
                        and '\\' not in target and '$' not in target,
                        'Unsupported dynamic or external LaTeX image path')
                member = str(PurePosixPath(name).parent / relative)
                raw = read_member(archive, member)
                require(bool(raw), 'LaTeX image is empty: ' + member)
                suffix = relative.suffix.lower()
                if suffix == '.png':
                    inspect_png(raw)
                elif suffix == '.svg':
                    inspect_svg(raw)
                elif suffix == '.pdf':
                    require(raw.startswith(b'%PDF-'), 'Invalid PDF figure header')
                elif suffix == '.eps':
                    require(raw.startswith(b'%!PS'), 'Invalid EPS figure header')
                else:
                    raise ValueError('Unsupported LaTeX figure format: ' + suffix)
                references.append(member)
        require(len(set(references)) >= expected_figures,
                'Expected at least ' + str(expected_figures) + ' distinct actively referenced figures')
    return dict(active_figure_references=references, expected_figures=expected_figures,
                tex_compilation_verified=False, plot_identity_verified=False,
                visual_rendering_verified=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--historical', action='store_true')
    parser.add_argument('--word-example', action='store_true')
    parser.add_argument('--baseline', type=Path)
    parser.add_argument('--omv', type=Path, action='append', default=[])
    parser.add_argument('--docx', type=Path, action='append', default=[])
    parser.add_argument('--latex', type=Path, action='append', default=[])
    args = parser.parse_args()
    if not (args.historical or args.word_example or args.omv or args.docx or args.latex):
        parser.error('Choose --historical, --word-example, --omv, --docx or --latex')
    if args.omv and args.baseline is None:
        parser.error('--omv requires a data-only --baseline')
    try:
        result = dict(scope='structural artifact checks only', gui_qualification=False)
        if args.historical:
            result['historical'] = historical()
        if args.word_example:
            result['word_example'] = word_example()
        result['omv'] = {str(p): inspect_omv(p, args.baseline) for p in args.omv}
        result['docx'] = {str(p): inspect_docx(p) for p in args.docx}
        result['latex'] = {str(p): inspect_latex(p) for p in args.latex}
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError, KeyError, StopIteration, zipfile.BadZipFile, ET.ParseError) as error:
        print(json.dumps(dict(status='failed', error=str(error), gui_qualification=False)))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
