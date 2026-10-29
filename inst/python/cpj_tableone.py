"""Overall-cohort standard Table One summaries; no hypothesis testing or grouping."""
import numpy as np
from cpj_runtime import Factor, InputError
from cpj_crosstable import categorical, quantiles
from cpj_tree import _mean_sd


def prepare_column(column, metadata, name):
    classes = metadata.get('classes') or []
    dimensions = metadata.get('dimensions') or []
    if (not isinstance(classes,list) or any(not isinstance(v,str) for v in classes) or
            not isinstance(dimensions,list)):
        raise InputError(f'{name}: invalid storage metadata.')
    if dimensions or set(classes) & {'matrix','array','list','data.frame'}:
        raise InputError(f'{name}: matrix, array and list columns are not supported. Select scalar measurements or categories.')
    if set(classes) - {'numeric','integer','factor','ordered','character','logical'}:
        return None, 'Unsupported storage: '+', '.join(classes)
    if isinstance(column,Factor):
        values,labels = categorical(column,name)
        return dict(kind='categorical',values=values,labels=labels), ''
    if isinstance(column,np.ndarray) and column.ndim == 1 and column.dtype.kind in 'fiu':
        values = np.asarray(column,dtype=float)
        if np.isinf(values).any():raise InputError(f'{name}: recode infinite observations before analysis.')
        return dict(kind='continuous',values=values), ''
    if isinstance(column,list) or (isinstance(column,np.ndarray) and column.ndim == 1 and column.dtype.kind == 'b'):
        raw = list(column)
        if any(v is not None and not isinstance(v,(str,bool,np.bool_)) for v in raw):
            raise InputError(f'{name}: only scalar text or logical values are supported.')
        labels = sorted(set(str(v).upper() if isinstance(v,(bool,np.bool_)) else v for v in raw if v is not None))
        values = np.array([-1 if v is None else labels.index(str(v).upper() if isinstance(v,(bool,np.bool_)) else v) for v in raw],dtype=int)
        return dict(kind='categorical',values=values,labels=labels), ''
    raise InputError(f'{name}: select a scalar numeric, factor, text or logical variable.')


def calculate(data, options):
    names = options.get('vars') or []
    if (not isinstance(names,list) or not 1 <= len(names) <= 20 or
            any(not isinstance(v,str) or not v for v in names) or len(set(names)) != len(names)):
        raise InputError('Select one to twenty distinct variables.')
    if options.get('cont','mean') not in ('mean','median'):
        raise InputError('Unknown continuous summary selection.')
    exclude = options.get('excl',False)
    if not isinstance(exclude,bool):raise InputError('Missing-value exclusion must be true or false.')
    active = {}; eligibility = []; lengths = set()
    metadata = getattr(data,'metadata',{})
    for name in names:
        column = data.get(name)
        info = metadata.get(name,{})
        if not isinstance(info,dict):raise InputError(f'{name}: invalid storage metadata.')
        # Inspect shape/class before looking at flattened transport values.
        prepared,reason = prepare_column(column,info,name)
        length = info.get('rows',len(column.codes) if isinstance(column,Factor) else len(column) if isinstance(column,(np.ndarray,list)) else 0)
        if not isinstance(length,int) or isinstance(length,bool):raise InputError('Column row counts must be integers.')
        lengths.add(length)
        units = info.get('units') or []; labels = info.get('label') or []
        if not isinstance(units,list) or not isinstance(labels,list):raise InputError('Units and variable labels must be text lists.')
        if any(not isinstance(v,str) for v in units+labels):raise InputError('Units and variable labels must be text.')
        row = dict(variable=name,kind=prepared['kind'] if prepared else 'unsupported',
                   status=reason or 'Included',inputValid=None,inputMissing=None,
                   units='; '.join(units),label='; '.join(labels))
        if prepared:
            values = prepared['values']
            if len(values) != length:raise InputError(f'{name}: values do not match the transported row count.')
            valid = np.isfinite(values) if prepared['kind']=='continuous' else values >= 0
            row.update(inputValid=int(valid.sum()),inputMissing=int((~valid).sum()))
            if not np.any(valid):
                row['status'] = 'Omitted: all values missing'
            else:
                if prepared['kind']=='categorical' and len([v for v in prepared['labels'] if v is not None]) > 20:
                    raise InputError(f'{name}: at most twenty declared categories are supported.')
                prepared['valid'] = valid;active[name] = prepared
        eligibility.append(row)
    if len(lengths) != 1:raise InputError('Selected variables must have equal row counts.')
    total = lengths.pop()
    if not 1 <= total <= 10000:raise InputError('The standard Table One core accepts one to 10,000 rows without sampling.')
    result = dict(total=total,retained=None,excluded=None,completeBefore=None,
                  included=len(active),omitted=len(names)-len(active),eligibility=eligibility,
                  continuous=[],categories=[],reason='')
    if not active:
        result['reason'] = 'No eligible variables remain; no exclusion or summaries were performed.'
        return result
    complete = np.logical_and.reduce([v['valid'] for v in active.values()])
    keep = complete if exclude else np.ones(total,dtype=bool)
    n = int(keep.sum())
    result.update(retained=n,excluded=total-n,completeBefore=int(complete.sum()))
    if not n:
        result['reason'] = 'Complete-case exclusion left no rows; disable exclusion or select fewer variables.'
        return result
    for name,column in active.items():
        selected = column['values'][keep]
        valid = np.isfinite(selected) if column['kind']=='continuous' else selected >= 0
        observed = selected[valid]; count = int(valid.sum()); missing = n-count
        base = dict(variable=name,valid=count,missing=missing,missingPercent=missing/n)
        if column['kind']=='continuous':
            mean,sd = _mean_sd(observed)
            q1,median,q3 = quantiles(observed) if count else (None,None,None)
            result['continuous'].append(dict(base,mean=mean,sd=sd,median=median,q1=q1,q3=q3))
        else:
            labels = column['labels']; levels = [j for j,v in enumerate(labels) if v is not None]
            # print.TableOne's standard binary row explicitly counts its second level.
            if len(levels)==2 and not options.get('showAllLevels',False):levels=levels[1:]
            for code in levels:
                freq = int(np.sum(observed == code))
                result['categories'].append(dict(base,level=labels[code],n=freq,
                                                  percent=freq/count if count else None))
    return result
