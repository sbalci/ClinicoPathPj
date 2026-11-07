"""Explicit source-row inclusion, bound to the complete diagnostic input snapshot."""
import hashlib
import json
import re
from cpj_runtime import InputError


def prepare(data, options, result, row_ids):
    roles = ['study','true_positives','false_positives','false_negatives','true_negatives']
    ids = [str(i+1) for i in range(result['input'])] if row_ids is None else list(row_ids)
    if (any(not isinstance(v,str) or not v or len(v)>128 or any(ord(c)<32 for c in v) for v in ids)
            or len(set(ids)) != len(ids)):
        raise InputError('Study inclusion requires distinct, bounded source-row strings.')
    counts = [[None if value != value else float(value) for value in data[options[role]]]
              for role in roles[1:]]
    source = dict(roles=[options[r] for r in roles], ids=ids,
                  labels=result['identity']['values'], counts=counts)
    snapshot = hashlib.sha256(json.dumps(source,ensure_ascii=True,allow_nan=False,
                                        separators=(',',':')).encode()).hexdigest()
    eligible = [r['sourceID'] for r in result['studies']]
    definition = options.get('inclusionDefinition','')
    if not isinstance(definition,str) or len(definition)>30000:
        raise InputError('Saved study inclusion must be text of at most 30,000 characters.')
    valid = True
    requested = eligible
    if definition.strip():
        try:
            value = json.loads(definition)
        except (ValueError,TypeError):
            raise InputError('Saved study inclusion is not valid JSON; clear it in Advanced Settings.') from None
        if (not isinstance(value,dict) or set(value)!={'version','rows','snapshot'}
                or type(value['version']) is not int or value['version']!=1
                or not isinstance(value['rows'],list) or len(value['rows'])>200
                or any(not isinstance(v,str) or not v or len(v)>128 or any(ord(c)<32 for c in v)
                       for v in value['rows'])
                or len(set(value['rows']))!=len(value['rows'])
                or not isinstance(value['snapshot'],str)
                or not re.fullmatch('[0-9a-f]{64}',value['snapshot'])):
            raise InputError('Use version-1 study inclusion with a snapshot and distinct source rows; clear invalid text in Advanced Settings.')
        requested = value['rows']
        valid = value['snapshot']==snapshot and set(requested)<=set(eligible)
    chosen = set(requested) if valid else set()
    selected = [r for r in result['studies'] if r['sourceID'] in chosen]
    return dict(snapshot=snapshot,valid=valid,requested=requested,
                included=[r['sourceID'] for r in selected],selected=selected,
                eligible=len(eligible),omitted=len(eligible)-len(selected))
