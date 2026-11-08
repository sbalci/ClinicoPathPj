"""Jamovi role validation/presentation over the separately tested balanced ICC engine."""
import numpy as np
from cpj_icc import calculate_icc
from cpj_identity import audit
from cpj_runtime import InputError

LABELS = dict(icc11='ICC(1,1): one-way random, single measurement',
              icc21='ICC(2,1): two-way random, absolute agreement, single rater',
              icc31='ICC(3,1): two-way mixed, consistency, single rater',
              icc1k='ICC(1,k): one-way random, mean of k measurements',
              icc2k='ICC(2,k): two-way random, absolute agreement, mean of k raters',
              icc3k='ICC(3,k): two-way mixed, consistency, mean of k raters')


def run_icc(data, options, out):
    variables = options.get('vars') or []
    if not isinstance(variables, list) or any(not isinstance(v, str) for v in variables):
        raise InputError('Choose numeric measurement columns using the variable roles.')
    if len(variables) < 2 or any(v not in data for v in variables):
        message = 'Choose 2–20 numeric rating columns: one row per independent case, one column per rater or measurement slot.'
        out.info(message);out.markdown('summary', message)
        return
    if len(variables) > 20 or len(set(variables)) != len(variables):
        raise InputError('Choose 2–20 distinct measurement columns for balanced ICC.')
    columns = []
    for name in variables:
        value = data[name]
        meta = getattr(data, 'metadata', {}).get(name, {})
        if (not isinstance(value, np.ndarray) or value.ndim != 1 or value.dtype.kind not in 'fiu'
                or meta.get('dimensions') or set(meta.get('classes') or [])-{'numeric','integer'}):
            raise InputError('ICC ratings must be scalar numeric measurements, not dates or categorical codes.')
        columns.append(value)
    if len({len(v) for v in columns}) != 1:
        raise InputError('ICC measurement columns must have aligned source rows.')
    n = len(columns[0])
    ids = list(out.row_ids) if out.row_ids is not None else [str(i+1) for i in range(n)]
    if len(ids) != n or any(not isinstance(v, str) or not v for v in ids) or len(set(ids)) != n:
        raise InputError('Original source-row identities must be distinct strings aligned with the input.')
    try:
        result = calculate_icc(np.column_stack(columns), options.get('iccType','icc21'),
                               options.get('confLevel',.95))
    except ValueError as error:
        raise InputError(str(error)) from error
    labels = ids
    subject = options.get('subject')
    if subject:
        if subject not in data:
            message = 'Choose an available case identifier or clear the optional role.'
            out.info(message);out.markdown('summary', message)
            return
        labels = audit(data, subject, n)['values']
        retained = [labels[i] for i in result['retained_indices']]
        if any(v is None for v in retained) or len(set(retained)) != result['n']:
            raise InputError('Complete ICC cases require known, unique case IDs; repeated-case models are not implemented.')
    out.row('iccAudit', input=result['input'], retained=result['n'], excluded=result['excluded'],
            raters=result['raters'])
    interval = result['interval']
    out.row('iccStatistics', model=LABELS[result['model']], estimate=result['estimate'],
            lower=interval[0] if interval else None, upper=interval[1] if interval else None,
            confidence=result['confidence'])
    out.note('iccStatistics', 'Confidence level applies to the reported limits. One-way and consistency ICCs use ANOVA F limits; single-rater absolute agreement uses approximate F/Satterthwaite limits. Negative estimates are retained. Confidence limits for the mean-rater absolute-agreement ICC(2,k) are unavailable in this core.')
    for index, name in enumerate(variables):
        out.row('iccRaters', position=index+1, rater=name)
    if options.get('showICCCases',False):
        for index in result['retained_indices']:
            out.row('iccCases', sourceID=ids[index], case=labels[index])
    if result['excluded']:
        out.info(str(result['excluded'])+' source row(s) excluded because at least one selected rating is missing; all ICC calculations use the same complete-case cohort.')
    for message in result['notices']:
        if 'interval policy unresolved' not in message:
            out.warn(message)
    if result['model']=='icc2k':
        out.warn('Confidence limits for ICC(2,k) are unavailable in this core. Its estimate describes the mean of k raters. Do not choose a different model solely to obtain confidence limits.')
    out.markdown('summary', 'Balanced ICC assumes independent cases and the selected rater design. For two-way models every complete case is rated by the same selected raters; one-way columns represent balanced measurement slots. Single-rater reliability and reliability of the mean of k ratings are different inferential units. Normal, homoscedastic ANOVA errors underpin intervals. Case-ID checks identify known repeated IDs but cannot prove independence or the sampling design. No clinical interpretation bands, automatic outlier removal or imputation. CCC, categorical agreement, unbalanced/repeated/hierarchical models and bootstrap inference are not implemented. Bland-Altman output is available by changing the analysis method; an ICC does not replace a differences-based agreement assessment.')
