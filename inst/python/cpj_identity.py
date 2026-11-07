"""Exact text-label identity audit; no patient aggregation or history inference."""
from collections import Counter
from cpj_runtime import Factor, InputError
from cpj_crosstable import categorical


def audit(data, name, n, require_unique=False):
    if not isinstance(require_unique,bool):
        raise InputError('The unique-subject requirement must be enabled or disabled explicitly.')
    if name in (None,''):
        if require_unique:return {'pending':'Select a subject ID before requiring one record per subject.'}
        return None
    if name not in data:raise InputError('The selected subject ID column is unavailable.')
    column=data[name];metadata=getattr(data,'metadata',{}).get(name,{})
    if metadata.get('dimensions') or set(metadata.get('classes') or [])-{'character','factor','ordered'}:
        raise InputError('Subject IDs must use scalar text or nominal/ordinal labels. Convert numeric identifiers explicitly to text or a labelled factor first.')
    if isinstance(column,Factor):
        codes,levels=categorical(column,name)
        values=[None if code<0 else levels[code] for code in codes]
    elif isinstance(column,list) and all(v is None or isinstance(v,str) for v in column):values=column
    else:raise InputError('Subject IDs must use text or factor labels; numeric values are not converted automatically.')
    if len(values)!=n:raise InputError('Subject IDs must align with every supplied component record.')
    if any(v is not None and (len(v)>256 or any(ord(c)<32 or ord(c)==127 for c in v)) for v in values):
        raise InputError('Subject IDs must contain at most 256 characters without control characters.')
    # Detect wholly blank labels; preserve exact spelling and spaces in nonblank IDs.
    values=[None if v is None or not v.strip() else v for v in values]
    counts=Counter(v for v in values if v is not None)
    repeated=[dict(subject=v,records=count) for v,count in counts.items() if count>1]
    missing=values.count(None)
    if require_unique and (missing or repeated):
        raise InputError(f'One record per subject is required: {missing} row(s) have missing/blank IDs and {len(repeated)} ID(s) occur in multiple rows. Correct or explicitly resolve the source records; no aggregation was performed.')
    return dict(pending='',input=n,known=n-missing,missing=missing,subjects=len(counts),
                repeatedSubjects=len(repeated),repeatedRows=sum(v['records'] for v in repeated),
                values=values,rowCounts=[None if v is None else counts[v] for v in values],
                flags=[0 if v is None else 1 if counts[v]==1 else 2 for v in values],
                repeated=repeated,strict=require_unique)
