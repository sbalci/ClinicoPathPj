"""jamovi roles and native presentation for Lin CCC point estimates."""
import numpy as np

from cpj_concordance import concordance
from cpj_identity import audit
from cpj_runtime import InputError


def run_concordance(data, options, out):
    variables = options.get('vars') or []
    if not isinstance(variables, list) or any(not isinstance(v, str) for v in variables):
        raise InputError('Choose two numeric measurement columns using the variable roles.')
    if len(variables) < 2 or any(v not in data for v in variables):
        message = ('Choose exactly two measurement columns in the same units; '
                   'one row must represent one independent case. CCC requires at least 10 complete pairs.')
        out.info(message)
        out.markdown('summary', message)
        return
    if len(variables) != 2 or len(set(variables)) != 2:
        raise InputError('CCC requires exactly two distinct measurement columns in the same units.')
    columns = []
    for name in variables:
        value = data[name]
        meta = getattr(data, 'metadata', {}).get(name, {})
        if (not isinstance(value, np.ndarray) or value.ndim != 1 or value.dtype.kind not in 'fiu'
                or meta.get('dimensions') or set(meta.get('classes') or []) - {'numeric', 'integer'}):
            raise InputError('CCC measurements must be scalar numeric values in the same units, not dates or categorical codes.')
        columns.append(value)
    n = len(columns[0])
    if not 1 <= n <= 5000 or len(columns[1]) != n:
        raise InputError('Supply one to 5,000 aligned source rows without display sampling.')
    ids = list(out.row_ids) if out.row_ids is not None else [str(i+1) for i in range(n)]
    if len(ids) != n or any(not isinstance(v, str) or not v for v in ids) or len(set(ids)) != n:
        raise InputError('Original source-row identities must be distinct strings aligned with the input.')
    # The numerical helper supports small hand fixtures; the released analysis
    # contract requires ten pairs and is deliberately stricter here.
    complete = ~(np.isnan(columns[0]) | np.isnan(columns[1]))
    if int(complete.sum()) < 10:
        raise InputError('CCC requires at least 10 complete independent measurement pairs.')
    result = concordance(*columns)
    labels = ids
    subject = options.get('subject')
    if subject:
        if subject not in data:
            message = 'Choose an available case identifier or clear the optional role.'
            out.info(message)
            out.markdown('summary', message)
            return
        labels = audit(data, subject, n)['values']
        retained = [labels[i] for i in result['retained_indices']]
        if any(v is None for v in retained) or len(set(retained)) != result['n_complete']:
            raise InputError('Complete CCC pairs require known, unique case IDs; repeated-case inference is not implemented.')
    out.row('cccAudit', input=n, retained=result['n_complete'], excluded=result['missing_either'],
            firstMissing=result['missing_x']-result['missing_both'],
            secondMissing=result['missing_y']-result['missing_both'], bothMissing=result['missing_both'])
    for label, key in [('Lin concordance correlation (CCC)', 'ccc'),
                       ('Pearson correlation (precision)', 'precision'),
                       ('Bias correction factor (Cb)', 'bias_correction')]:
        out.row('cccStatistics', measure=label, estimate=result[key])
    out.note('cccStatistics', 'Point estimates only; confidence intervals and p-values are unavailable in this core. Population moments use divisor n. Undefined coefficients are left blank and explained in the notices. Negative CCC is retained; no clinical interpretation bands are applied.')
    for key in ('undefined_reason', 'precision_undefined_reason'):
        if result[key]:
            out.warn(result[key])
    if result['missing_either']:
        out.info(str(result['missing_either'])+' source row(s) excluded because one or both measurements are missing.')
    if options.get('showCCCPairs', False):
        for i in result['retained_indices']:
            out.row('cccPairs', sourceID=ids[i], case=labels[i], first=float(columns[0][i]),
                    second=float(columns[1][i]))
    if options.get('cccPlot', False):
        out.plot('cccFigure', [dict(x=float(columns[0][i]), y=float(columns[1][i]), group='Complete pairs')
                            for i in result['retained_indices']],
                 xlab=variables[0], ylab=variables[1])
    out.markdown('summary', 'Lin CCC describes concordance between two measurements in the same units on each independent case. Pearson correlation describes precision; bias correction describes departure from the identity relationship. CCC depends on case mix and does not replace a differences-based agreement assessment. Missing measurements are excluded as pairs. Case-ID checks identify known repeated IDs but cannot prove independence or common units. At least 10 complete pairs are required. This partial core provides point estimates only: no confidence intervals, hypothesis tests, clinical acceptance bands, outlier deletion, imputation or repeated-case inference. The measurement plot shows the retained raw pairs without fitting a model.')
