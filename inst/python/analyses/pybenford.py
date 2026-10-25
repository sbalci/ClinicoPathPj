"""Benford Analysis (Python). Validated core; see docs/python-core-analyses.md for limits."""
from cpj_runtime import InputError, md_escape

SPEC = {'name': 'pybenford',
 'title': 'Benford Analysis (Python)',
 'menuGroup': 'ClinicoPathPj',
 'menuSubgroup': 'Data quality',
 'version': '0.2.0',
 'options': [{'name': 'measurement',
              'title': 'Positive numeric measurement',
              'type': 'Variable',
              'permitted': ['numeric'],
              'suggested': ['continuous'],
              'required': True},
             {'name': 'digits',
              'title': 'Number of leading digits',
              'type': 'Integer',
              'default': 2,
              'min': 1,
              'max': 3},
             {'name': 'showPlot',
              'title': 'Show digit frequency plot',
              'type': 'Bool',
              'default': True}],
 'results': [{'name': 'summary', 'title': 'Interpretation', 'type': 'Text'},
             {'name': 'test',
              'title': 'Leading-Digit Goodness of Fit',
              'type': 'Table',
              'columns': [{'name': 'n', 'title': 'N', 'type': 'integer'},
                          {'name': 'digits', 'title': 'Digits', 'type': 'integer'},
                          {'name': 'statistic', 'title': 'Pearson Chi-Square', 'type': 'number'},
                          {'name': 'df', 'title': 'df', 'type': 'integer'},
                          {'name': 'p',
                           'title': 'Approximate p',
                           'type': 'number',
                           'format': 'zto,pvalue'},
                          {'name': 'mad', 'title': 'Mean Absolute Deviation', 'type': 'number'},
                          {'name': 'orders', 'title': 'Orders of Magnitude', 'type': 'number'}]},
             {'name': 'frequencies',
              'title': 'Leading-Digit Frequencies',
              'type': 'Table',
              'columns': [{'name': 'digit', 'title': 'Leading Digits', 'type': 'integer'},
                          {'name': 'observed', 'title': 'Observed', 'type': 'integer'},
                          {'name': 'expected', 'title': 'Expected Count', 'type': 'number'},
                          {'name': 'observedProp',
                           'title': 'Observed Proportion',
                           'type': 'number',
                           'format': 'pc'},
                          {'name': 'expectedProp',
                           'title': 'Expected Proportion',
                           'type': 'number',
                           'format': 'pc'}]},
             {'name': 'digitPlot',
              'title': 'Observed and Expected Digit Frequencies',
              'type': 'Image',
              'plot': 'bar',
              'width': 600,
              'height': 400,
              'visible': '(showPlot)'}]}


def leading_digits(values, digits):
    import numpy as np
    from decimal import Decimal
    # Shortest round-trip decimal text preserves ordinary values such as 0.3,
    # while avoiding log/floor errors at powers of ten and subnormal magnitudes.
    return np.array([int((''.join(map(str,Decimal(str(float(x))).as_tuple().digits))+'00')[:digits])
                     for x in values],dtype=int)


def run(data, options, out):
    import numpy as np
    from scipy.stats import chisquare
    from cpj_accuracy import finite_number
    x=np.asarray(data[options['measurement']],dtype=float)
    digits=finite_number(options.get('digits',2),'Number of digits',integer=True,minimum=1)
    if digits>3:
        raise InputError('Choose one, two or three leading digits.')
    if np.isinf(x).any():
        raise InputError('Infinite measurements are invalid; recode them as missing.')
    finite=np.isfinite(x)
    positive=x[finite & (x>0)]
    if not len(positive):
        raise InputError('No positive finite measurements remain.')
    categories=np.arange(10**(digits-1),10**digits)
    leading=leading_digits(positive,digits)
    observed=np.bincount(leading,minlength=10**digits)[categories]
    probabilities=np.log10(1+1/categories)
    expected=len(positive)*probabilities
    test=chisquare(observed,expected)
    mad=np.mean(np.abs(observed/len(positive)-probabilities))
    orders=np.log10(positive.max())-np.log10(positive.min())
    out.row('test',n=len(positive),digits=digits,statistic=test.statistic,df=len(categories)-1,
            p=test.pvalue,mad=mad,orders=orders)
    plot=[]
    for d,o,e,p in zip(categories,observed,expected,probabilities):
        out.row('frequencies',digit=d,observed=o,expected=e,observedProp=o/len(positive),expectedProp=p)
        plot.extend([dict(label=str(d),value=float(o),group='Observed'),
                     dict(label=str(d),value=float(e),group='Benford expected')])
    out.plot('digitPlot',plot,xlab='Leading digits',ylab='Frequency')
    if np.any(expected<5):
        out.warn('Expected frequencies below 5 make the chi-square approximation potentially unreliable. '
                 'Consider fewer leading digits or a larger suitable sample.')
    if orders<2:
        out.warn('The positive measurements span fewer than two orders of magnitude. '
                 'Benford screening may be unsuitable for these data.')
    out.note('test','MAD is descriptive; no fixed conformity label is applied. The p-value is asymptotic. '
             'Departure from Benford frequencies does not establish fraud or identify its cause.')
    out.markdown('summary',md_escape(f'Positive finite measurements: {len(positive)}. '
        f'Excluded missing: {int((~finite).sum())}; zero: {int(np.sum(x==0))}; negative: {int(np.sum(x<0))}. '
        'Use only naturally occurring measurements for which a leading-digit model is defensible; '
        'identifiers, imposed ranges and detection limits can invalidate this comparison. '
        'Mantissa arc tests and suspect-record classifications are outside this core.'))
