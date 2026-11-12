"""Shared native presentation for validated raw and standardized mean effects."""
import numpy as np

from cpj_estimation import between_estimation, within_estimation
from cpj_identity import audit
from cpj_runtime import InputError, md_escape

CASE_LIMIT = 1000


def _numeric(data, name):
    if name not in data:
        raise InputError('Choose an available numeric measurement column.')
    value = data[name]
    metadata = getattr(data, 'metadata', {}).get(name, {})
    if (not isinstance(value, np.ndarray) or value.ndim != 1 or value.dtype.kind not in 'fiu'
            or metadata.get('dimensions') or set(metadata.get('classes') or [])-{'numeric','integer'}):
        raise InputError('Measurements must be scalar numeric values, not dates or categorical codes.')
    return value


def run(data, options, out, *, paired):
    if options.get('typestatistics', 'parametric') != 'parametric':
        raise InputError('This partial core supports classical mean estimation only; rank, robust and Bayesian methods are not available.')
    if any(options.get(name) for name in ('dep3', 'dep4', 'grvar', 'pairwisecomparisons')):
        raise InputError('Additional measurements, splitting and pairwise families are not available in this partial core.')
    if options.get('effsizetype') is not None:
        raise InputError('The legacy effect-size selector is unsupported; use the explicit standardized-results option.')
    if paired:
        names = [options.get('dep1'), options.get('dep2')]
    else:
        outcomes = options.get('dep') or []
        if not isinstance(outcomes, (list, tuple)) or len(outcomes) != 1:
            raise InputError('Choose exactly one numeric outcome in this partial core.')
        names = [outcomes[0], options.get('group')]
    subject = options.get('subject')
    roles = names+([subject] if subject else [])
    if any(not isinstance(name, str) or name not in data for name in roles):
        raise InputError('Choose the required measurement and group roles from the current dataset.')
    if len(set(roles)) != len(roles):
        raise InputError('Choose distinct columns for measurement, group and optional subject-ID roles.')
    first = _numeric(data, names[0])
    identity = audit(data, subject, len(first)) if subject else None
    ids = identity['values'] if identity else None
    confidence = options.get('conflevel', .95)
    if paired:
        second = _numeric(data, names[1])
        result = within_estimation(first, second, confidence=confidence, subject_ids=ids)
        labels = names
    else:
        result = between_estimation(first, data[names[1]], options.get('firstLevel'),
            options.get('secondLevel'), equal_variances=options.get('varequal', False),
            confidence=confidence, subject_ids=ids)
        labels = [result['mapping']['first'], result['mapping']['second']]
    requested = options.get('showStandardized', False)
    if not isinstance(requested, bool):
        raise InputError('Choose explicitly whether to show standardized results.')
    effect = None
    if requested:
        if not paired and not options.get('varequal', False):
            out.warn('Standardized results require the Student equal-variance model and have been cleared. '
                     'Raw Welch results are retained; choose an equal-variance model only when justified by the design.')
        else:
            from cpj_standardized import between_standardized, within_standardized
            if paired:
                effect = within_standardized(first, second, standardizer='difference',
                    confidence=confidence, subject_ids=ids)['standardized']
            else:
                effect = between_standardized(first, data[names[1]], options.get('firstLevel'),
                    options.get('secondLevel'), standardizer='pooled', confidence=confidence,
                    subject_ids=ids)['standardized']
    row_ids = list(out.row_ids) if out.row_ids is not None else [str(i+1) for i in range(len(first))]
    if (len(row_ids) != len(first) or any(not isinstance(value, str) or not value for value in row_ids)
            or len(set(row_ids)) != len(row_ids)):
        raise InputError('Original source-row IDs must be distinct strings aligned with the input.')
    method = {'welch': 'Welch independent t-test', 'student': 'Student pooled-variance t-test',
              'paired_t': 'Paired t-test'}[result['method']]
    out.row('cohort', source=result['n_source'], retained=result['n_complete'], excluded=result['excluded_missing'])
    missing_roles = [('First measurement', names[0], 'first'), ('Second measurement', names[1], 'second')] if paired else [
        ('Outcome', names[0], 'outcome'), ('Group', names[1], 'group')]
    for role, name, key in missing_roles:
        out.row('missing', role=role, variable=name, missing=result['missing_by_role'][key])
    out.note('missing', 'Role-specific missing counts may overlap; cohort exclusions count their union.')
    for key, label in zip(('first','second'), labels):
        out.row('descriptives', role=key.capitalize(), label=label, **result['summaries'][key])
    out.row('contrast', first=labels[0], second=labels[1], method=method,
            confidence=confidence, **{k: result[k] for k in
            ('difference','stderr','df','statistic','p','lower','upper','status')})
    out.note('contrast', 'First minus second, in the measurement units. Two-sided t test; raw mean limits are not standardized-effect intervals. '
             'A confidence interval containing zero or a large p-value does not establish equivalence or clinical unimportance.')
    if options.get('showCases', False):
        for index in result['retained_indices'][:CASE_LIMIT]:
            common = dict(sourceID=row_ids[index], subjectID=ids[index] if ids else None)
            if paired:
                out.row('cases', **common, first=first[index], second=second[index], difference=first[index]-second[index])
            else:
                group = data[names[1]]
                out.row('cases', **common, sample=group.levels[int(group.codes[index])], value=first[index])
        if result['n_complete'] > CASE_LIMIT:
            out.note('cases', f'Only the first {CASE_LIMIT} retained source rows are displayed; all {result["n_complete"]} retained rows contribute to inference.')
    if options.get('showPlot', True):
        out.plot('differencePlot', [dict(label=labels[0]+' minus '+labels[1], estimate=result['difference'],
            lower=result['lower'], upper=result['upper'])], reference=0,
            xlab=f'Raw mean difference ({confidence*100:g}% CI)', ylab='First minus second')
    if effect is not None:
        metric = 'Cohen d_z' if paired else 'Cohen d'
        denominator = 'Within-row difference SD' if paired else 'Sample-size-weighted pooled SD'
        target = 'Population delta_z' if paired else 'Population delta'
        out.row('standardizer', denominator=denominator, sd=effect['standardizer_sd'],
            df=effect['df'])
        out.row('standardized', metric=metric, estimate=effect['cohens_d'],
            lower=effect['delta_lower'], upper=effect['delta_upper'],
            confidence=confidence, status=effect['status'])
        out.note('standardized', target+': first minus second, standardized by the stated SD. '
            'Equal-tail noncentral-t limits target the population standardized contrast; they are not raw-mean or J-scaled g intervals. '
            + '; '.join(effect['assumptions']) + '. No clinical interpretation bands or equivalence conclusion are provided.'
            + (' Availability: '+effect['reason'] if effect['reason'] else ''))
        out.row('hedges', metric='Hedges g_z (point only)' if paired else 'Hedges g (point only)',
            estimate=effect['hedges_g'], correction=effect['correction'],
            status='unavailable' if effect['hedges_g'] is None else 'point_available')
        out.note('hedges', 'Exact gamma-ratio J(df) corrects the Cohen point estimate. '
            'No g-specific confidence interval is supplied; population-delta limits are reported separately.')
        if effect['cohens_d'] is not None:
            out.plot('standardizedPlot', [dict(label=metric+': '+labels[0]+' minus '+labels[1],
                estimate=effect['cohens_d'], lower=effect['delta_lower'], upper=effect['delta_upper'])],
                reference=0, xlab=f'{target} ({confidence*100:g}% CI)', ylab=metric+' estimator')
        if effect['status'] == 'interval_unavailable':
            out.warn('Standardized confidence limits are unavailable: '+effect['reason']+
                     ' Finite standardized point estimates are retained without approximate limits.')
    if result['status'] == 'degenerate':
        out.warn('Inference is undefined because the standard error is zero or essentially constant at this numeric scale. '
                 'Only descriptive means and the raw contrast are available; no zero-width interval or infinite significance is reported.')
    if min(s['n'] for s in result['summaries'].values()) < 10:
        out.warn('The retained sample is small. Assess distributional assumptions and uncertainty; no alternative method was selected automatically.')
    design = ('One row represents one independent subject; measurements are paired within the same original row. '
              'Only rows complete for both measurements are retained; measurements must use comparable units.' if paired else
              'Each retained row represents one independent case; the two groups must be independent. '
              'Only rows with a complete outcome and group are retained; no third complete-data group is silently excluded.')
    description = (f'{result["n_complete"]} retained rows from {result["n_source"]}; {method}. '
        f'Contrast: {labels[0]} minus {labels[1]}. '+design+
        (' Supplied retained subject IDs are known and unique; IDs do not establish independence.' if subject else
         ' No subject IDs were supplied; independence must be established from the study design.')+
        ' Optional standardized results use pooled SD under Student or paired-difference SD; Cohen population-delta limits and Hedges point-only estimates are separate. '
        'This partial core omits unequal-variance standardized effects, rank/robust/Bayesian tests, more than two groups or measurements, '
        'split analyses, multiple endpoints, box/violin plots and interactive inspection. The raw plot shows the raw contrast and its interval; the optional standardized plot shows the Cohen estimate and population-delta interval.')
    out.markdown('summary', md_escape(description))
