"""Extract only hash-locked official wheels; never install or download at runtime."""
import hashlib
import json
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    lock = json.loads((ROOT / 'vendor/python-lock.json').read_text())
    target = ROOT / 'inst/python/_vendor'
    for row in lock['packages']:
        path = ROOT / row['wheel']
        if hashlib.sha256(path.read_bytes()).hexdigest() != row['sha256']:
            raise ValueError(f'Wheel checksum mismatch: {path.name}')
    if '--check' in sys.argv:
        if not (target / 'python-lock.json').is_file() or json.loads((target/'python-lock.json').read_text()) != lock:
            raise ValueError('Bundled Python dependencies are missing or stale')
        print(f"Verified {len(lock['packages'])} locked wheels")
        return
    if target.exists():
        shutil.rmtree(target)
    target.mkdir()
    for row in lock['packages']:
        with zipfile.ZipFile(ROOT / row['wheel']) as archive:
            for name in archive.namelist():
                dest = (target / name).resolve()
                if not dest.is_relative_to(target.resolve()):
                    raise ValueError('Unsafe wheel member')
            archive.extractall(target)
    shutil.copy2(ROOT/'vendor/python-lock.json', target/'python-lock.json')
    print(f"Bundled {len(lock['packages'])} pinned packages ({lock['platform']})")

if __name__ == '__main__': main()
