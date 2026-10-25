"""Sequential Testing (Python). Validated core; see docs/python-core-analyses.md for limits."""


SPEC = {'name': 'pysequentialtests',
 'title': 'Sequential Testing (Python)',
 'menuGroup': 'ClinicoPathPj',
 'menuSubgroup': 'Diagnostic tests',
 'version': '0.2.0',
 'options': [{'name': 'sens1',
              'title': 'First test sensitivity (0-1)',
              'type': 'Number',
              'default': 0.95,
              'min': 0,
              'max': 1},
             {'name': 'spec1',
              'title': 'First test specificity (0-1)',
              'type': 'Number',
              'default': 0.7,
              'min': 0,
              'max': 1},
             {'name': 'sens2',
              'title': 'Second test sensitivity (0-1)',
              'type': 'Number',
              'default': 0.8,
              'min': 0,
              'max': 1},
             {'name': 'spec2',
              'title': 'Second test specificity (0-1)',
              'type': 'Number',
              'default': 0.98,
              'min': 0,
              'max': 1},
             {'name': 'prevalence',
              'title': 'Disease prevalence (0-1)',
              'type': 'Number',
              'default': 0.1,
              'min': 0,
              'max': 1},
             {'name': 'populationSize',
              'title': 'Illustrative population size',
              'type': 'Integer',
              'default': 1000,
              'min': 1,
              'max': 1000000000},
             {'name': 'showCosts',
              'title': 'Show illustrative test costs',
              'type': 'Bool',
              'default': False},
             {'name': 'cost1',
              'title': 'First test unit cost',
              'type': 'Number',
              'default': 0,
              'min': 0,
              'max': 1000000000000},
             {'name': 'cost2',
              'title': 'Second test unit cost',
              'type': 'Number',
              'default': 0,
              'min': 0,
              'max': 1000000000000},
             {'name': 'showPlot',
              'title': 'Show combined accuracy plot',
              'type': 'Bool',
              'default': True}],
 'results': [{'name': 'summary', 'title': 'Interpretation', 'type': 'Text'},
             {'name': 'strategies',
              'title': 'Combined Accuracy',
              'type': 'Table',
              'columns': [{'name': 'strategy', 'title': 'Strategy', 'type': 'text'},
                          {'name': 'sensitivity',
                           'title': 'Sensitivity',
                           'type': 'number',
                           'format': 'pc'},
                          {'name': 'specificity',
                           'title': 'Specificity',
                           'type': 'number',
                           'format': 'pc'},
                          {'name': 'ppv', 'title': 'PPV', 'type': 'number', 'format': 'pc'},
                          {'name': 'npv', 'title': 'NPV', 'type': 'number', 'format': 'pc'},
                          {'name': 'lrp', 'title': 'LR+', 'type': 'text'},
                          {'name': 'lrn', 'title': 'LR-', 'type': 'text'}]},
             {'name': 'workload',
              'title': 'Expected Counts and Workload',
              'type': 'Table',
              'columns': [{'name': 'strategy', 'title': 'Strategy', 'type': 'text'},
                          {'name': 'tp', 'title': 'TP', 'type': 'number'},
                          {'name': 'fp', 'title': 'FP', 'type': 'number'},
                          {'name': 'fn', 'title': 'FN', 'type': 'number'},
                          {'name': 'tn', 'title': 'TN', 'type': 'number'},
                          {'name': 'firstTests', 'title': 'First Tests', 'type': 'number'},
                          {'name': 'secondTests', 'title': 'Second Tests', 'type': 'number'}]},
             {'name': 'costs',
              'title': 'Illustrative Test Costs',
              'type': 'Table',
              'columns': [{'name': 'strategy', 'title': 'Strategy', 'type': 'text'},
                          {'name': 'total', 'title': 'Total Test Cost', 'type': 'number'},
                          {'name': 'perPerson', 'title': 'Cost per Person', 'type': 'number'}],
              'visible': '(showCosts)'},
             {'name': 'accuracyPlot',
              'title': 'Combined Sensitivity and Specificity',
              'type': 'Image',
              'plot': 'interval',
              'width': 600,
              'height': 400,
              'visible': '(showPlot)'}]}


def run(data, options, out):
    from cpj_accuracy import probability, finite_number, divide, display
    s1,s2,c1,c2,p = [probability(options.get(k,v), k) for k,v in
                    (('sens1',.95),('sens2',.8),('spec1',.7),('spec2',.98),('prevalence',.1))]
    n = finite_number(options.get('populationSize',1000), 'Population size', integer=True, minimum=1)
    cost1 = finite_number(options.get('cost1',0), 'First test cost', minimum=0)
    cost2 = finite_number(options.get('cost2',0), 'Second test cost', minimum=0)
    first_positive = p*s1+(1-p)*(1-c1)
    combinations = [('Serial positive',s1*s2,1-(1-c1)*(1-c2),first_positive),
                    ('Serial negative',1-(1-s1)*(1-s2),c1*c2,1-first_positive),
                    ('Parallel',1-(1-s1)*(1-s2),c1*c2,1.)]
    plot=[]
    for label,se,sp,retested in combinations:
        tp,fp,fn,tn = n*p*se,n*(1-p)*(1-sp),n*p*(1-se),n*(1-p)*sp
        out.row('strategies',strategy=label,sensitivity=se,specificity=sp,
                ppv=divide(tp,tp+fp),npv=divide(tn,tn+fn),
                lrp=display(divide(se,1-sp)),lrn=display(divide(1-se,sp)))
        out.row('workload',strategy=label,tp=tp,fp=fp,fn=fn,tn=tn,firstTests=n,secondTests=n*retested)
        if options.get('showCosts',False):
            total=n*cost1+n*retested*cost2
            out.row('costs',strategy=label,total=total,perPerson=total/n)
        plot += [dict(label=label+' sensitivity',estimate=se),dict(label=label+' specificity',estimate=sp)]
    out.plot('accuracyPlot',plot,xlab='Probability (0-1)',ylab='')
    out.note('workload','Expected counts are fractional projections, not observed participants. '
             'Serial negative and parallel have identical accuracy under the model, but different second-test workload.')
    out.markdown('summary','Both tests are assumed conditionally independent within each reference group. '
                 'Serial positive requires both tests positive. Serial negative retests first-test negatives '
                 'and uses either-positive classification; parallel applies both tests to everyone. '
                 'Entered test properties are treated as known; no uncertainty intervals are propagated. '
                 'Costs include testing only, in the entered cost units.')
    out.info('Conditional independence is an assumption, not estimated from data. Use pycotest when modelling conditional dependence.')
