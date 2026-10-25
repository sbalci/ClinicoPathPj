"""Validated, offline analysis registry shared by the generator and packaged runtime."""
import json
import re
from pathlib import Path

IDENTIFIER = re.compile(r'[a-z][A-Za-z0-9]*\Z')


def read_registry(root=None):
    root = Path(root) if root is not None else Path(__file__).resolve().parent
    document = json.loads((root / 'registry.json').read_text(encoding='utf-8'))
    if document.get('schema_version') != 1 or document.get('module') != 'ClinicoPathPj':
        raise ValueError('Unsupported ClinicoPathPj registry schema or module')
    entries = document.get('analyses')
    if not isinstance(entries, list):
        raise ValueError('Registry analyses must be a list')
    identities, sources = set(), set()
    for entry in entries:
        if not isinstance(entry.get('id'), str) or not entry['id'].startswith('py'):
            raise ValueError('All public analysis identifiers must start with py')
        for name in [entry['id']] + entry.get('aliases', []):
            if not isinstance(name, str) or not IDENTIFIER.fullmatch(name) or name in identities:
                raise ValueError(f'Duplicate or invalid registry identifier: {name!r}')
            identities.add(name)
        source = entry.get('source')
        if source is not None:
            path = Path(source)
            if path.is_absolute() or '..' in path.parts or path.suffix != '.py' or \
                    path.parts[:2] != ('analyses', entry['family']):
                raise ValueError(f'Invalid analysis source: {source!r}')
            if source in sources:
                raise ValueError(f'Duplicate analysis source: {source}')
            sources.add(source)
            if not (root / path).resolve().is_relative_to((root / 'analyses').resolve()):
                raise ValueError('Analysis source escapes the installed analysis directory')
    return document


def resolve(name, root=None):
    if not isinstance(name, str) or not IDENTIFIER.fullmatch(name):
        raise ValueError(f'invalid analysis name {name!r}')
    root = Path(root) if root is not None else Path(__file__).resolve().parent
    for entry in read_registry(root)['analyses']:
        if name == entry['id'] or name in entry.get('aliases', []):
            if entry.get('source') is None:
                raise FileNotFoundError(f'analysis {name!r} is planned, not implemented')
            return entry, root / entry['source']
    raise FileNotFoundError(f'analysis {name!r} is not installed')
