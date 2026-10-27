"""IHC display transformations with explicit cohort, missingness and row identities."""
import hashlib
import json
import re
import numpy as np
from cpj_runtime import Factor, InputError


def labels(column, n):
    if column is None:
        return [None]*n
    values=[None if c<0 else column.levels[c] for c in column.codes] if isinstance(column,Factor) else column
    if len(values)!=n:
        raise InputError('Annotation lengths must match marker rows.')
    result=[]
    for v in values:
        text=None if v is None or isinstance(v,(float,np.floating)) and np.isnan(v) else str(v)
        if text is not None and len(text)>120:
            raise InputError('Annotation labels must be at most 120 characters.')
        result.append(text)
    return result


def marker_pair(prepared, selected_markers, x_marker=None, y_marker=None):
    """Extract displayed complete pairs without changing the heatmap cohort or order."""
    x_marker = x_marker or selected_markers[0]
    y_marker = y_marker or selected_markers[1]
    if x_marker == y_marker or any(m not in prepared['markers'] for m in (x_marker, y_marker)):
        raise InputError('Choose two distinct scatter markers from the selected heatmap markers.')
    xi, yi = (prepared['markers'].index(m) for m in (x_marker, y_marker))
    points = [dict(index=i, sourceRow=row['row'], x=values[xi], y=values[yi])
              for i, (row, values) in enumerate(zip(prepared['rows'], prepared['values']))
              if values[xi] is not None and values[yi] is not None]
    return dict(xMarker=x_marker, yMarker=y_marker, points=points,
                omitted=len(prepared['rows'])-len(points))


def applied_selection(definition, prepared, input_ids):
    """Materialize an explicit, snapshot-bound selection in original input-row order."""
    if not isinstance(definition, str) or len(definition)>12000:
        raise InputError('The saved selection definition must be text of at most 12,000 characters.')
    requested=[]
    valid=True
    if definition.strip():
        try:
            value=json.loads(definition)
        except (ValueError, TypeError):
            raise InputError('The saved selection definition is not valid JSON.') from None
        if (not isinstance(value,dict) or set(value)!={'version','rows','snapshot'}
                or type(value['version']) is not int or value['version']!=1
                or not isinstance(value['rows'],list) or len(value['rows'])>200
                or any(not isinstance(v,str) or not v or len(v)>128
                       or any(ord(c)<32 for c in v) for v in value['rows'])
                or len(set(value['rows']))!=len(value['rows'])
                or not isinstance(value['snapshot'],str)
                or not re.fullmatch('[0-9a-f]{64}',value['snapshot'])):
            raise InputError('Use a version-1 selection with a snapshot and at most 200 distinct source-row strings.')
        requested=value['rows']
        valid=not requested or value['snapshot']==prepared['snapshot']
    retained={r['row'] for r in prepared['rows']}
    chosen=set(requested)&retained if valid else set()
    selected=[r for r in prepared['rows'] if r['row'] in chosen]
    return dict(valid=valid,requested=requested,selectedRows=[r['row'] for r in selected],
                selected=selected,unavailable=[v for v in requested if v not in retained],
                values=[int(row in chosen) if valid and row in retained else None for row in input_ids])


def describe_tree(merges, leaf_labels, order, leaf_kind):
    """Describe an already computed linkage; retain leaf identity and display geometry."""
    n = len(leaf_labels)
    positions = {int(leaf): float(i) for i, leaf in enumerate(order)}
    heights = {i: 0. for i in range(n)}
    members = {i: [str(label)] for i, label in enumerate(leaf_labels)}
    references = {i: leaf_kind + ' ' + str(label) for i, label in enumerate(leaf_labels)}
    branches = []
    for i, (left, right, height, count) in enumerate(merges):
        left, right, node = int(left), int(right), n+i
        branch = dict(merge=i+1, left=references[left], right=references[right],
                      height=float(height), count=int(count),
                      members=members[left]+members[right],
                      xLeft=positions[left], xRight=positions[right],
                      leftHeight=heights[left], rightHeight=heights[right],
                      leftLabel=str(leaf_labels[left]) if left<n else None,
                      rightLabel=str(leaf_labels[right]) if right<n else None)
        branches.append(branch)
        positions[node] = (positions[left]+positions[right])/2
        heights[node] = float(height)
        members[node] = branch['members']
        references[node] = 'Merge '+str(i+1)
    return dict(leaves=[str(leaf_labels[j]) for j in order], branches=branches)


def prepare(data, options, row_ids=None):
    markers=options.get('markers') or []
    if not 2<=len(markers)<=20 or len(set(markers))!=len(markers):
        raise InputError('Choose two to twenty distinct numeric IHC markers.')
    columns=[]
    for name in markers:
        c=data[name]
        if isinstance(c,Factor) or np.asarray(c).dtype.kind not in 'fiu':
            raise InputError('IHC markers must be numeric, not categorical scores.')
        columns.append(np.asarray(c,dtype=float))
    if len({len(c) for c in columns})!=1:
        raise InputError('Marker columns must have equal lengths.')
    x=np.column_stack(columns);n=len(x)
    if np.isinf(x).any():
        raise InputError('Infinite marker values are not supported.')
    if options.get('scaling','raw') not in ('raw','zscore') or options.get('missing','available') not in ('available','complete'):
        raise InputError('Unknown scaling or missingness method.')
    keep=np.isfinite(x).all(axis=1) if options.get('missing')=='complete' else np.isfinite(x).any(axis=1)
    if not keep.any():
        raise InputError('No rows with usable marker measurements remain.')
    x=x[keep]
    if len(x)>200:
        raise InputError('This explorer accepts at most 200 retained rows and 20 markers; no display sampling is applied.')
    if not np.isfinite(x).any(axis=0).all():
        raise InputError('Every selected marker needs at least one observed value in retained rows.')
    annotations={k:labels(data.get(options.get(k)),n) for k in ('subject','group','region')}
    ids=[str(i+1) for i in range(n)] if row_ids is None else [str(v) for v in row_ids]
    if len(ids)!=n or len(set(ids))!=n:
        raise InputError('Source row identities must be unique and row aligned.')
    # Bind saved source positions to all supplied view inputs, before display transformations.
    snapshot=None
    if options.get('enableSelection'):
        digest=hashlib.sha256()
        digest.update(json.dumps([markers,[options.get(k) for k in ('subject','group','region')]],
                                 ensure_ascii=True,separators=(',',':')).encode())
        for i in range(n):
            values=[None if np.isnan(c[i]) else float(c[i]) for c in columns]
            digest.update(json.dumps([ids[i],values,[annotations[k][i] for k in ('subject','group','region')]],
                                     ensure_ascii=True,allow_nan=False,separators=(',',':')).encode()+b'\n')
        snapshot=digest.hexdigest()
    rows=[dict(row=ids[i],**{k:v[i] for k,v in annotations.items()},observed=int(np.isfinite(x[j]).sum())) for j,i in enumerate(np.flatnonzero(keep))]
    summaries=[];constant=[];z=x.copy()
    for j,name in enumerate(markers):
        v=x[np.isfinite(x[:,j]),j];sd=float(np.std(v,ddof=1)) if len(v)>1 else None
        mean=float(np.mean(v))
        if not np.isfinite(mean) or sd is not None and not np.isfinite(sd):
            raise InputError('Marker magnitudes exceed stable numeric display calculations.')
        summaries.append(dict(marker=name,observed=len(v),missing=int(len(x)-len(v)),mean=mean,sd=sd))
        if sd is None or sd==0:
            constant.append(name)
            if options.get('scaling')=='zscore':z[np.isfinite(z[:,j]),j]=0
        elif options.get('scaling')=='zscore':z[:,j]=(z[:,j]-mean)/sd
    row_order=np.arange(len(x));col_order=np.arange(len(markers))
    row_tree=marker_tree=None
    if options.get('clusterRows') or options.get('clusterColumns'):
        if not np.isfinite(z).all():
            raise InputError('Clustering requires complete marker rows. Choose complete rows or disable clustering; no imputation is performed.')
        from scipy.cluster.hierarchy import linkage,leaves_list
        if options.get('clusterRows'):
            merges=linkage(z,method='average',metric='euclidean') if len(z)>1 else []
            row_order=leaves_list(merges) if len(z)>1 else row_order
            if options.get('showDendrograms'):
                row_tree=describe_tree(merges,[r['row'] for r in rows],row_order,'Source row')
        if options.get('clusterColumns'):
            merges=linkage(z.T,method='average',metric='euclidean')
            col_order=leaves_list(merges)
            if options.get('showDendrograms'):
                marker_tree=describe_tree(merges,markers,col_order,'Marker')
    def serial(a):return [[float(v) if np.isfinite(v) else None for v in row] for row in a]
    return dict(markers=[markers[j] for j in col_order],rows=[rows[i] for i in row_order],values=serial(z[np.ix_(row_order,col_order)]),raw=serial(x[np.ix_(row_order,col_order)]),summaries=summaries,constant=constant,inputRows=n,excluded=int(n-len(x)),missingCells=int(np.isnan(x).sum()),rowTree=row_tree,markerTree=marker_tree,snapshot=snapshot,scaleLabel='Within-marker z score (sample SD)' if options.get('scaling')=='zscore' else 'Raw marker units')
