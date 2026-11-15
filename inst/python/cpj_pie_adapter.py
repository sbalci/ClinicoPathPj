"""Native pie presentation with optional fixed-null goodness-of-fit."""
import json

from cpj_estimation_adapter import _numeric
from cpj_identity import audit
from cpj_pie_gof import pie_gof
from cpj_runtime import InputError, md_escape


def _parse_ratios(text):
    if not isinstance(text,str) or not text.strip() or len(text)>20000:
        raise InputError('Supply a labelled expected-ratio object of at most 20,000 characters.')
    def unique(pairs):
        result={}
        for key,value in pairs:
            if key in result:
                raise InputError('Each expected-ratio category must appear exactly once; duplicate labels are invalid.')
            result[key]=value
        return result
    def invalid_constant(value):
        raise InputError('Expected ratios must contain finite numbers; NaN and Infinity are invalid.')
    try:
        ratios=json.loads(text,object_pairs_hook=unique,parse_constant=invalid_constant)
    except (ValueError,RecursionError):
        raise InputError('Use a labelled object such as {"No": 1, "Yes": 1}; positional lists and executable expressions are unsupported.') from None
    if not isinstance(ratios,dict):
        raise InputError('Expected ratios must be a labelled object, not a list or scalar.')
    return ratios


def run(data, options, out):
    allowed = {'dep','counts','subject','showCases','showPlot','label','digitsperc','showConsole',
               'resultssubtitle','customRatios','ratio','showExpected'}
    if set(options)-allowed:
        raise InputError('Unsupported options in this descriptive pie core: '+
                         ', '.join(sorted(set(options)-allowed))+'.')
    outcome, counts, subject = (options.get(k) for k in ('dep','counts','subject'))
    roles = [outcome]+([counts] if counts else [])+([subject] if subject else [])
    if any(not isinstance(k,str) or k not in data for k in roles) or len(set(roles))!=len(roles):
        raise InputError('Select available distinct outcome, frequency and subject columns.')
    if counts and subject:
        raise InputError('Subject-ID auditing is unavailable for aggregated frequency rows.')
    show_cases, show_plot = options.get('showCases',False), options.get('showPlot',True)
    if not isinstance(show_cases,bool) or not isinstance(show_plot,bool):
        raise InputError('Enable or disable each output explicitly.')
    enabled,custom,show_expected=(options.get('resultssubtitle',False),
        options.get('customRatios',False),options.get('showExpected',True))
    if any(not isinstance(v,bool) for v in (enabled,custom,show_expected)):
        raise InputError('Enable or disable goodness-of-fit and expected-count controls explicitly.')
    label, digits = options.get('label','percentage'), options.get('digitsperc',0)
    if label not in ('percentage','counts','both'):
        raise InputError('Choose percentage, count, or combined slice labels.')
    if isinstance(digits,bool) or not isinstance(digits,int) or not 0<=digits<=2:
        raise InputError('Percentage labels require 0–2 decimal places.')
    n = len(data[outcome].codes) if hasattr(data[outcome],'codes') else 0
    identity = audit(data,subject,n) if subject else None
    ratios=_parse_ratios(options.get('ratio','')) if enabled and custom else None
    calculated=pie_gof(data[outcome],weights=_numeric(data,counts) if counts else None,
        subject_ids=identity['values'] if identity else None,enabled=enabled,ratios=ratios)
    result,gof=calculated['descriptives'],calculated['gof']
    out.row('cohort',source=result['n_source'],complete=result['n_complete'],
            excluded=result['excluded_missing'],zero=result['zero_frequency'],
            contributing=result['n_contributing'],total=result['n_total'])
    out.note('cohort','Complete rows include zero frequencies. Total N sums positive complete frequencies; it is not the number of aggregated source rows.')
    out.row('missing',role='Outcome',variable=outcome,missing=result['missing_outcome'])
    if counts: out.row('missing',role='Frequency',variable=counts,missing=result['missing_frequency'])
    out.note('missing','Role counts overlap; excluded rows count their union. Actual missing levels are excluded; a literal NA category remains.')
    rows = []
    for c in result['cells']:
        out.row('frequencies',code=c['code'],category=c['label'],count=c['count'],
                denominator=result['n_total'],proportion=c['proportion'],
                status='zero_count' if c['count']==0 else 'positive')
        percent = f'{100*c["proportion"]:.{digits}f}%'
        count = f'{c["count"]:,}'
        annotation = (percent if label=='percentage' else count if label=='counts'
                      else count+'\n('+percent+')') if c['count'] else None
        rows.append(dict(category=c['label'],count=c['count'],total=result['n_total'],
                         lower=c['lower'],upper=c['upper'],annotation=annotation))
    out.note('frequencies','Proportion = category count / total complete frequency N. All nonmissing declared categories remain, including unused or zero-count categories. Codes index the transported category order after genuine missing levels are normalized. Match custom ratios by dataset labels. Enabled null probabilities are reported separately.')
    if enabled:
        unavailable=gof['status']=='unavailable'
        out.row('gof',method='Unavailable' if unavailable else 'Pearson chi-square goodness of fit',
            null='Custom labelled ratios' if custom else 'Equal probabilities',
            statistic=gof['statistic'],df=gof['df'],p=gof['p'],
            minimum=gof['minimum_expected'],small=gof['expected_below5'],
            status='Unavailable: one declared category' if unavailable else
                'Sparse approximation' if gof['sparse_warning'] else 'Asymptotic approximation')
        out.note('gof','Independent observations and prespecified fixed probabilities are assumed. No parameters are fitted to the tested observations. For an available test, df = declared nonmissing categories minus one. No continuity correction or automatic exact/Monte Carlo switch. A large p-value does not establish equivalence.')
        if show_expected:
            for c in gof['rows']:
                out.row('expected',code=c['code'],category=c['label'],observed=c['observed'],
                    probability=c['probability'],expected=c['expected'],
                    residual=c['pearson_residual'],contribution=c['contribution'])
            out.note('expected','The null includes every nonmissing declared category, including zero counts. Ratios are normalized to probabilities in the displayed mapping. Where available, Pearson residual = (observed - expected) / sqrt(expected) and contributions sum to the Pearson statistic. These are not per-category hypothesis tests.')
        if unavailable:
            out.info('Goodness-of-fit is unavailable with only one declared nonmissing category. Descriptive results are retained; no statistic, degrees of freedom or p-value was supplied.')
        elif gof['sparse_warning']:
            out.warn('Some expected counts are below 5. The Pearson p-value is an asymptotic approximation and may be unreliable; no exact, Fisher or Monte Carlo replacement was performed.')
    if show_cases:
        source_ids = list(out.row_ids) if out.row_ids is not None else [str(i+1) for i in range(n)]
        for j,i in enumerate(result['retained_indices'][:1000]):
            out.row('cases',sourceID=source_ids[i],subjectID=result['retained_subject_ids'][j] if identity else None,
                    outcome=data[outcome].levels[int(data[outcome].codes[i])],
                    frequency=data[counts][i] if counts else 1)
        if result['n_contributing']>1000:
            out.note('cases','Only the first 1,000 contributing source rows are displayed; all positive complete rows contribute to counts.')
    if show_plot: out.plot('piePlot',rows,xlab=outcome)
    out.markdown('summary',md_escape(f'{result["n_contributing"]} contributing source rows; total frequency N={result["n_total"]}. '
        'Frequencies represent observation counts, not survey weights. Declared zero-count categories remain in the table and legend; they have no visible slice or label. '
        +('Contributing subject IDs are known and unique; this does not establish independent observations. ' if identity else '')
        +('Fixed-null goodness-of-fit results are in native tables; expected probabilities include all declared nonmissing categories. ' if enabled else 'Goodness-of-fit results are off; no expected counts or test were calculated. ')
        +'Confidence intervals, effect-size points, group/split pies, paired/Bayesian models, donut plots and interactive inspection are omitted.'))
