"""Bounded categorical flow counts and shared static/local drawing geometry."""
from collections import Counter
import math
import numpy as np
from cpj_runtime import Factor, InputError


def calculate(data, options):
    names = options.get('vars') or []
    if (not isinstance(names, list) or not 2 <= len(names) <= 4 or
            any(not isinstance(v, str) or not v for v in names) or len(set(names)) != len(names)):
        raise InputError('Select two to four distinct categorical variables in axis order.')
    columns = []
    labels = []
    valid = []
    for name in names:
        column = data.get(name)
        if not isinstance(column, Factor):
            raise InputError('All flow variables must be nominal or ordinal.')
        codes = np.asarray(column.codes)
        text = [v for v in column.levels if v is not None]
        if (codes.ndim != 1 or codes.dtype.kind not in 'iu' or
                np.any(codes < -1) or np.any(codes >= len(column.levels)) or
                any(not isinstance(v, str) for v in text) or len(set(text)) != len(text)):
            raise InputError('Invalid categorical labels or codes.')
        observed = (codes >= 0) & ~np.isin(codes, [j for j, v in enumerate(column.levels) if v is None])
        columns.append(codes)
        labels.append(list(column.levels))
        valid.append(observed)
    total = len(columns[0])
    if any(len(c) != total for c in columns):
        raise InputError('Flow variables must have equal lengths.')
    if not 1 <= total <= 10000:
        raise InputError('The flow core accepts one to 10,000 input rows without sampling.')
    complete = np.logical_and.reduce(valid)
    missing_rows = int((~complete).sum())
    exclude = options.get('excl', False)
    if not isinstance(exclude, bool):
        raise InputError('Missing-value exclusion must be true or false.')
    keep = complete if exclude else np.ones(total, dtype=bool)
    n = int(keep.sum())
    if not n:
        raise InputError('No rows remain after missing-category exclusion.')
    # One collision-free missing label across all axes, including unused declared levels.
    missing_label = '(Missing)'
    suffix = 1
    while any(missing_label in v for v in labels):
        suffix += 1
        missing_label = f'(Missing {suffix})'
    prepared = []
    for codes, levels, observed in zip(columns, labels, valid):
        copy = codes[keep].copy()
        if not exclude and np.any(~observed[keep]):
            copy[~observed[keep]] = len(levels)
            levels.append(missing_label)
        prepared.append(copy)
    counts = Counter(tuple(int(c[i]) for c in prepared) for i in range(n))
    if len(counts) > 60:
        raise InputError('More than 60 observed paths. Combine categories explicitly; no flows are sampled or hidden.')
    flows = [dict(id=i, codes=list(key), labels=[labels[j][code] for j, code in enumerate(key)],
                  n=counts[key], percent=counts[key]/n) for i, key in enumerate(sorted(counts))]
    categories = []
    for axis, name in enumerate(names):
        marginal = Counter()
        for flow in flows:
            marginal[flow['codes'][axis]] += flow['n']
        if len(marginal) > 20:
            raise InputError('More than 20 observed categories on an axis. Combine categories explicitly.')
        categories.extend(dict(axis=axis, variable=name, code=code, label=labels[axis][code],
                               n=count, percent=count/n) for code, count in sorted(marginal.items()))
    return dict(names=names, total=total, n=n, excluded=total-n, missingRows=missing_rows,
                missingLabel=missing_label, flows=flows, categories=categories)


def geometry(result):
    """Every path keeps its identity and count at each adjacent axis pair."""
    nodes = []
    positions = {}
    gap = result['n'] * .035
    height = result['n'] + gap * (max(sum(v['axis'] == j for v in result['categories'])
                                         for j in range(len(result['names']))) - 1)
    for axis in range(len(result['names'])):
        y = 0
        for category in (v for v in result['categories'] if v['axis'] == axis):
            positions[(axis, category['code'])] = y
            nodes.append(dict(axis=axis, code=category['code'], label=category['label'],
                              y=y, n=category['n']))
            y += category['n'] + gap
    offsets = dict(positions)
    slots = {}
    for flow in result['flows']:
        for axis, code in enumerate(flow['codes']):
            key = axis, code
            slots[flow['id'], axis] = offsets[key]
            offsets[key] += flow['n']
    ribbons = [dict(flow=f['id'], axis=j, source=slots[f['id'], j],
                    target=slots[f['id'], j+1], n=f['n'], group=f['codes'][0])
               for f in result['flows'] for j in range(len(result['names'])-1)]
    return dict(names=result['names'], n=result['n'], height=height, nodes=nodes, ribbons=ribbons)


def validate_geometry(g):
    """Reject malformed saved drawing states without accessing observations or refitting."""
    names = g['names']; n = g['n']; height = g['height']
    if (not 2 <= len(names) <= 4 or len(set(names)) != len(names) or
            any(not isinstance(v, str) or not v for v in names) or
            not isinstance(n, int) or not 1 <= n <= 10000 or
            not math.isfinite(height) or not n <= height <= n*2 or
            not 2 <= len(g['nodes']) <= 80 or not 1 <= len(g['ribbons']) <= 180):
        raise ValueError('Invalid alluvial drawing dimensions')
    for node in g['nodes']:
        if (not isinstance(node['axis'], int) or not 0 <= node['axis'] < len(names) or
                not isinstance(node['code'], int) or node['code'] < 0 or
                not isinstance(node['label'], str) or not isinstance(node['n'], int) or
                not 1 <= node['n'] <= n or not math.isfinite(node['y']) or
                not 0 <= node['y'] <= height-node['n']+1e-8):
            raise ValueError('Invalid alluvial node')
    for ribbon in g['ribbons']:
        if (not isinstance(ribbon['axis'], int) or not 0 <= ribbon['axis'] < len(names)-1 or
                not isinstance(ribbon['flow'], int) or not 0 <= ribbon['flow'] < 60 or
                not isinstance(ribbon['group'], int) or ribbon['group'] < 0 or
                not isinstance(ribbon['n'], int) or not 1 <= ribbon['n'] <= n or
                any(not math.isfinite(ribbon[k]) or not 0 <= ribbon[k] <= height-ribbon['n']+1e-8
                    for k in ('source', 'target'))):
            raise ValueError('Invalid alluvial ribbon')
    return g
