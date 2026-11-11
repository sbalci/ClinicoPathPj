"""Remove regenerable module bytecode from a JMO, preserving all other members."""
import copy
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile
import zipfile


def prune(path):
    path=Path(path)
    with zipfile.ZipFile(path) as source:
        if source.testzip() is not None:raise ValueError('Archive CRC check failed')
        names=set(source.namelist());remove=[]
        for name in names:
            match=re.fullmatch(r'(ClinicoPathPj/R/ClinicoPathPj/python/(?!vendor/).*)/__pycache__/([^/]+)\.cpython-\d+(?:\.opt-\d+)?\.pyc',name)
            # The top-level python/__pycache__ directory needs no intermediate slash.
            if match is None:
                match=re.fullmatch(r'(ClinicoPathPj/R/ClinicoPathPj/python)/__pycache__/([^/]+)\.cpython-\d+(?:\.opt-\d+)?\.pyc',name)
            if match and match[1]+'/'+match[2]+'.py' in names:remove.append(name)
        if not remove:return dict(removed=[],preserved=len(names),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        with tempfile.TemporaryDirectory(prefix='cpj-bytecode-',dir=path.parent) as directory:
            target=Path(directory)/path.name
            with zipfile.ZipFile(target,'w') as result:
                result.comment=source.comment
                for item in source.infolist():
                    if item.filename not in remove:result.writestr(copy.copy(item),source.read(item.filename))
            with zipfile.ZipFile(target) as result:
                if result.testzip() is not None:raise ValueError('Filtered archive CRC check failed')
                for name in names-set(remove):
                    if result.read(name)!=source.read(name):raise ValueError('Archive member changed: '+name)
            target.replace(path)
    return dict(removed=sorted(remove),preserved=len(names)-len(remove),sha256=hashlib.sha256(path.read_bytes()).hexdigest())


if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('Usage: prune-package-bytecode.py module.jmo')
    print(json.dumps(prune(sys.argv[1]),indent=2))
