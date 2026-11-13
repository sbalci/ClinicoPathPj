"""Native presentation of the bounded histogram and one-sample Student core."""
from cpj_estimation_adapter import _numeric
from cpj_histogram import one_sample_core
from cpj_histogram_geometry import histogram_geometry
from cpj_identity import audit
from cpj_runtime import InputError, md_escape

BOOL_DEFAULTS = dict(changebinwidth=False,centralityline=False,resultssubtitle=False,
    enableOneSampleTest=False,showBins=False,showCases=False,showPlot=True)
ALLOWED = set(BOOL_DEFAULTS) | {'dep','subject','typestatistics','alternative','binwidth',
    'testValue','conflevel','showConsole'}


def run(data, options, out):
    unknown = set(options)-ALLOWED
    if unknown:
        raise InputError('Unsupported options in this partial histogram core: '+', '.join(sorted(unknown))+'.')
    if options.get('typestatistics','parametric')!='parametric':
        raise InputError('This partial histogram core supports the Student model only; rank, robust and Bayesian methods are not available.')
    if options.get('alternative','two.sided')!='two.sided':
        raise InputError('Only the two-sided Student alternative is supported in this partial core.')
    flags = {key:options.get(key,default) for key,default in BOOL_DEFAULTS.items()}
    if any(not isinstance(v,bool) for v in flags.values()):
        raise InputError('Histogram switches must be enabled or disabled explicitly.')
    names = options.get('dep') or []
    if not isinstance(names,(list,tuple)) or len(names)!=1 or not isinstance(names[0],str):
        raise InputError('Choose exactly one numeric measurement in this partial histogram core.')
    name,subject = names[0],options.get('subject')
    if subject and subject==name:
        raise InputError('Choose distinct measurement and subject-ID columns.')
    values = _numeric(data,name)
    identity = audit(data,subject,len(values)) if subject else None
    ids = identity['values'] if identity else None
    result = histogram_geometry(values,width=options.get('binwidth',1.1) if flags['changebinwidth'] else None,
                                subject_ids=ids)
    inference = None
    if flags['resultssubtitle']:
        inference = one_sample_core(values,reference=options.get('testValue',0) if flags['enableOneSampleTest'] else 0,
                                    confidence=options.get('conflevel',.95),subject_ids=ids)
    row_ids = list(out.row_ids) if out.row_ids is not None else [str(i+1) for i in range(len(values))]
    if len(row_ids)!=len(values) or len(set(row_ids))!=len(row_ids):
        raise InputError('Original source-row IDs must be distinct and aligned with the measurement.')
    out.row('cohort',source=result['n_source'],retained=result['n_complete'],excluded=result['excluded_missing'])
    out.row('descriptives',**result['summary'])
    out.row('binning',mode='Automatic: range / sqrt(n)' if result['automatic'] else 'Manual width',
            width=result['width'],bins=len(result['bins']),status=result['geometry_status'])
    out.note('binning','Right-closed counting with ggplot2 edge fuzz; default origin is half a bin width. '
        'Displayed bounds are unfuzzed drawing bounds, not exact membership cutoffs. Empty bins are retained; no observations are sampled or dropped.')
    if flags['showBins']:
        for b in result['bins']:
            out.row('bins',**{key:b[key] for key in ('lower','upper','count','proportion','density')})
        out.note('bins','Proportion = count / retained N; density = count / (actual bin width × retained N). '
                 'Edge fuzz affects near-boundary membership; see the binning audit.')
    if flags['showCases']:
        for i in result['retained_indices'][:1000]:
            out.row('cases',sourceID=row_ids[i],subjectID=ids[i] if ids else None,value=values[i])
        if result['n_complete']>1000:
            out.note('cases',f'Only the first 1,000 retained rows are displayed; all {result["n_complete"]} retained rows contribute to the results.')
    if inference is not None:
        out.row('meanTest',**{key:inference[key] for key in
            ('reference','difference','stderr','df','statistic','p','status')})
        for target,key,estimate in [('Mean','mean',result['summary']['mean']),
                                    ('Mean minus reference','difference',inference['difference'])]:
            out.row('meanLimits',target=target,estimate=estimate,lower=inference[key+'_lower'],
                    upper=inference[key+'_upper'],confidence=inference['confidence'])
        out.note('meanTest','Two-sided one-sample Student t-test in the measurement units. '
            'Independent observations and a normal sampling model are assumed. The custom-null switch controls the reference value, not whether the test runs. '
            'A large p-value does not establish equivalence or clinical unimportance.')
        out.note('meanLimits','Mean and mean-minus-reference confidence limits are separate targets; neither is a standardized-effect interval.')
        if inference['status']!='ok':
            out.warn('Student inference is unavailable: fewer than two retained observations or a zero/essentially constant standard error. '
                     'Descriptive points are retained; no artificial interval or significance is supplied.')
    if result['geometry_status']!='ok':
        out.warn(result['reason'])
    elif flags['showPlot']:
        out.plot('histogramPlot',[dict(group=name,**{key:b[key] for key in ('lower','upper','count')})
            for b in result['bins']],boundaries=[result['summary']['mean']] if flags['centralityline'] else [],
            xlab=name,ylab='Count')
    out.markdown('summary',md_escape(
        f'{result["n_complete"]} retained measurements from {result["n_source"]} source rows. '
        'Each retained row must represent an independent case. '
        + ('Retained subject IDs are known and unique; this does not establish independence. ' if subject else
           'No subject IDs were supplied; independence must be established from the study design. ')
        + ('Optional Student results appear in native tables, without a statistical plot subtitle. ' if inference else
           'Statistical results are off; no one-sample inference was computed. ')
        + 'This partial core omits split/multiple outcomes, nonparametric/robust/Bayesian and one-sided tests, '
        'standardized effects, normality classifiers, clinical presets, KDE/QQ/ECDF panels and interactive inspection.'))
