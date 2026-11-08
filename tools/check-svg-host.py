"""Read-only source preflight for jamovi issue #1907; never certifies GUI saving.

Exit 2: known path mismatch present; 1: cannot inspect; 0: signature not found.
An exit of zero still requires native save/reopen and export qualification.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import plistlib


def inspect_sources(analysis, dataset):
    tree = ast.parse(analysis)
    analysis_class = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Analysis')
    method = next(n for n in analysis_class.body if isinstance(n, ast.FunctionDef) and n.name == 'set_svg')
    dataset_class = next(n for n in ast.parse(dataset).body
                         if isinstance(n, ast.ClassDef) and n.name == 'DataSetModel')
    bad = [n for n in ast.walk(method) if isinstance(n, ast.Attribute)
           and ast.dump(n, include_attributes=False) == ast.dump(
               ast.parse('self.dataset.instance_path', mode='eval').body, include_attributes=False)]
    dataset_path = any(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                       and n.name in ('instance_path', '__getattr__', '__getattribute__')
                       for n in dataset_class.body)
    dataset_path |= any(isinstance(n, ast.Attribute) and n.attr == 'instance_path'
                        and isinstance(n.ctx, ast.Store) for n in ast.walk(dataset_class))
    dataset_path |= any(isinstance(n, ast.Name) and n.id == 'instance_path'
                        and isinstance(n.ctx, ast.Store) for n in ast.walk(dataset_class))
    inherited = bool(dataset_class.bases)
    mismatch = bool(bad) and not dataset_path and not inherited
    return dict(status='known_path_mismatch' if mismatch else 'requires_runtime_qualification',
                known_bad_path_lines=[n.lineno for n in bad],
                dataset_path_or_dynamic_accessor_declared=bool(dataset_path),
                dataset_has_base_classes=inherited,
                gui_save_verified=False, export_verified=False,
                source_sha256=hashlib.sha256(analysis.encode()).hexdigest())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--app', type=Path, default=Path('/Applications/jamovi.app'))
    args = parser.parse_args()
    contents = args.app / 'Contents'
    server = contents / 'Resources/jamovi/server/jamovi/server'
    try:
        with (contents / 'Info.plist').open('rb') as stream:
            version = plistlib.load(stream).get('CFBundleShortVersionString')
        result = inspect_sources((server / 'analyses/analysis.py').read_text(),
                                 (server / 'datasetmodel.py').read_text())
        result.update(app=str(args.app), version=version, issue='https://github.com/jamovi/jamovi/issues/1907')
        print(json.dumps(result, indent=2))
        return 2 if result['status'] == 'known_path_mismatch' else 0
    except (OSError, SyntaxError, StopIteration, ValueError) as error:
        print(json.dumps(dict(status='uninspectable', error=str(error), gui_save_verified=False)))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
