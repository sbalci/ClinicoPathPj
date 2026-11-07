"""Local display payload from already-computed study results; no statistical fitting."""
import json
from pathlib import Path
import uuid


def render(studies, confidence, inclusion=None):
    if not 1 <= len(studies) <= 200:
        raise ValueError('Study inspector requires one to 200 precomputed retained rows.')
    payload=dict(studies=studies,confidence=confidence)
    if inclusion is not None:
        payload['inclusion']={k:inclusion[k] for k in ['snapshot','valid','included']}
    encoded=json.dumps(payload,ensure_ascii=True,allow_nan=False)
    for character,escape in (('<','\\u003c'),('>','\\u003e'),('&','\\u0026')):
        encoded=encoded.replace(character,escape)
    template=Path(__file__).with_name('templates').joinpath('diagnostic-studies.html').read_text()
    return template.replace('__ROOT__','cpjstudy'+uuid.uuid4().hex).replace('__PAYLOAD__',encoded)
