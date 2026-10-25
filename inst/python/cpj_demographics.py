"""Deterministic demographic banding; no display or jamovi dependencies."""
import math
import re
import numpy as np
from cpj_runtime import Factor, InputError

PRESETS = {
    'who': list(range(0, 86, 5)),
    'who_infant': [0, 1] + list(range(5, 86, 5)),
    'pediatric': [0, 1, 2, 5, 10, 15, 18],
    'reproductive': [0, 15, 20, 25, 30, 35, 40, 45, 50],
    'geriatric': [0, 65, 70, 75, 80, 85, 90, 95],
    'lifecourse': [0, 5, 15, 25, 45, 65, 75, 85],
}


def gender_side(label):
    key = re.sub('[^a-z]', '', label.strip().lower())
    if key in ('f','fem','female','females','w','woman','women','k','kadin','kadn'):
        return 'female'
    if key in ('m','male','males','man','men','e','erkek'):
        return 'male'
    return None


def resolve_levels(levels, female=None, male=None):
    for value in (female, male):
        if value is not None and value not in levels:
            raise InputError('A selected gender level is absent from the declared factor levels.')
    mode = 'explicit'
    if female is None and male is None:
        fs = [v for v in levels if gender_side(v) == 'female']
        ms = [v for v in levels if gender_side(v) == 'male']
        if len(fs) == 1 and len(ms) == 1:
            female, male, mode = fs[0], ms[0], 'labels'
        elif len(levels) >= 2:
            female, male, mode = levels[0], levels[1], 'order'
        elif levels:
            if gender_side(levels[0]) == 'male': male = levels[0]
            else: female = levels[0]
            mode = 'single'
    elif female is None or male is None:
        side = 'female' if female is None else 'male'
        remaining = [v for v in levels if v not in (female, male)]
        named = [v for v in remaining if gender_side(v) == side]
        picked = named[0] if len(named) == 1 else (remaining[0] if remaining else None)
        if side == 'female': female = picked
        else: male = picked
        mode = 'partial'
    if female is not None and female == male:
        raise InputError('Female and male levels must be different.')
    return female, male, mode


def age_breaks(maximum, preset='custom', width=5, custom=''):
    notices = []
    if preset in PRESETS:
        return np.array(PRESETS[preset] + [math.inf], dtype=float), None, notices
    if preset != 'custom': raise InputError('Unknown age group preset.')
    if custom.strip():
        values = []; bad = []
        for token in custom.split(','):
            if not token.strip(): continue
            try: value = float(token)
            except ValueError: bad.append(token.strip()); continue
            if not math.isfinite(value): bad.append(token.strip()); continue
            values.append(value)
        if bad: notices.append('Unreadable or nonfinite custom breaks were omitted: '+', '.join(bad)+'.')
        if values:
            values = sorted(set(values))
            if len(values) > 200: raise InputError('At most 200 age bands are supported.')
            return np.array(values + [math.inf]), None, notices
        notices.append('No usable custom breaks remained; age bands use the bin width.')
    if isinstance(width, bool) or not isinstance(width, (int,float)) or not math.isfinite(width) or width <= 0:
        raise InputError('Bin width must be a positive finite number.')
    ratio = max(maximum, width)/width
    if not math.isfinite(ratio) or math.floor(ratio)+1 > 200:
        raise InputError('Too many age bands. Increase the bin width or choose a preset (maximum 200 bands).')
    # seq() in R tolerates roundoff near an exact final multiple.
    last = math.floor(ratio + 1e-10)
    if last+1 > 200: raise InputError('At most 200 age bands are supported.')
    return np.r_[np.arange(last+1)*width, math.inf], width, notices


def age_labels(breaks, right=False, whole_ages=True, last_width=None):
    def whole(v): return math.isfinite(v) and abs(v-round(v)) < math.sqrt(np.finfo(float).eps)
    def fmt(v): return format(v, '.15g')
    result = []
    for i, (lo, hi) in enumerate(zip(breaks[:-1], breaks[1:])):
        a, b = fmt(lo), fmt(hi)
        if right:
            if math.isinf(hi):
                label = a+'+' if i == 0 else (fmt(lo+1)+'+' if whole(lo) and whole_ages else '>'+a)
            elif i == 0: label = a+'-'+b
            elif whole(lo) and whole(hi) and whole_ages:
                label = b if lo+1 == hi else fmt(lo+1)+'-'+b
            else: label = '>'+a+'-'+b
        else:
            if math.isinf(hi):
                label = a+'-'+fmt(lo+last_width-1) if last_width is not None and whole(lo) and whole(last_width) and whole_ages else a+'+'
            elif whole(lo) and whole(hi) and hi-lo == 1: label = '<1' if lo == 0 else a
            elif whole(lo) and whole(hi) and hi-lo >= 1: label = a+'-'+fmt(hi-1)
            else: label = a+'-<'+b
        result.append(label)
    if len(set(result)) != len(result):
        raise InputError('Age-band labels are indistinguishable at display precision; use wider bands.')
    return result


def population(ages, gender, *, female=None, male=None, preset='custom', width=5,
               custom='', interval='left', percentage='within_gender'):
    if isinstance(ages,Factor):
        age_missing = ages.codes < 0
        raw = np.full(len(ages.codes), np.nan)
        for i, label in enumerate(ages.levels):
            try: value = float(label)
            except ValueError: value = np.nan
            raw[ages.codes == i] = value
        ages = raw
    elif isinstance(ages,np.ndarray) and ages.ndim == 1 and np.issubdtype(ages.dtype,np.number):
        age_missing = np.isnan(ages)
    else:
        raise InputError('Age must contain numeric values in years or numeric factor labels.')
    if not isinstance(gender,Factor): raise InputError('Gender must be a categorical variable.')
    if len(ages) != len(gender.codes) or not len(ages): raise InputError('The dataset has no aligned age/gender rows.')
    if interval not in ('left','right') or percentage not in ('within_gender','total'):
        raise InputError('Unknown band closure or percentage denominator.')
    female, male, mode = resolve_levels(gender.levels, female, male)
    missing = age_missing | (gender.codes < 0)
    invalid = ~missing & (~np.isfinite(ages) | (ages < 0))
    side = np.full(len(ages), -1, dtype=int)
    for i, level in enumerate((female, male)):
        if level is not None: side[gender.codes == gender.levels.index(level)] = i
    other = ~missing & ~invalid & (side < 0)
    eligible = ~missing & ~invalid & ~other
    if not eligible.any(): raise InputError('No usable age/gender pairs remain after missing, invalid-age and unselected-level exclusions.')
    x = ages[eligible]
    breaks, last_width, notices = age_breaks(float(x.max()),preset,width,custom)
    right = interval == 'right' and preset == 'custom'
    if interval == 'right' and preset != 'custom': notices.append('Named presets use left-closed bands; the right-closed setting is ignored.')
    labels = age_labels(breaks,right,bool(np.all(np.abs(x-np.round(x)) < 1e-8)),last_width)
    bins = np.searchsorted(breaks,x,side='left' if right else 'right')-1
    bins[x == breaks[0]] = 0
    keep = (bins >= 0) & (bins < len(labels))
    if not keep.any(): raise InputError('No observations fall within the specified age break range.')
    counts = np.zeros((len(labels),2),dtype=int)
    np.add.at(counts,(bins[keep],side[eligible][keep]),1)
    n = int(counts.sum()); totals = counts.sum(axis=0)
    den = np.array([n,n]) if percentage == 'total' else totals
    pct = np.divide(counts,den,out=np.full(counts.shape,np.nan),where=den > 0)
    reasons = dict(total=len(ages),missing=int(missing.sum()),invalid=int(invalid.sum()),
                   other=int(other.sum()),outside=int((~keep).sum()),retained=n)
    return dict(breaks=breaks,labels=labels,counts=counts,percentages=pct,totals=totals,
                reasons=reasons,female=female,male=male,mode=mode,notices=notices,
                right=right,over120=int((x[keep] > 120).sum()))
