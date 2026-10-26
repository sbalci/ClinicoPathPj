"""Decision Curve Analysis (Python). Validated core; see docs/python-core-analyses.md for limits."""
from cpj_runtime import InputError, md_escape

SPEC = {'name': 'pydecisioncurve',
 'title': 'Decision Curve Analysis',
 'menuGroup': 'MedDecide Py',
 'menuSubgroup': 'Decision analysis',
 'version': '0.2.0',
 'options': [{'name': 'outcome',
              'title': 'Binary reference outcome',
              'type': 'Variable',
              'permitted': ['factor'],
              'suggested': ['nominal'],
              'required': True},
             {'name': 'models',
              'title': 'Predicted probability columns',
              'type': 'Variables',
              'permitted': ['numeric'],
              'suggested': ['continuous'],
              'required': True},
             {'name': 'positive',
              'title': 'Reference positive level',
              'type': 'Level',
              'variable': '(outcome)',
              'role': 'event'},
             {'name': 'thresholdMin',
              'title': 'Minimum threshold probability',
              'type': 'Number',
              'default': 0.05,
              'min': 0.001,
              'max': 0.999},
             {'name': 'thresholdMax',
              'title': 'Maximum threshold probability',
              'type': 'Number',
              'default': 0.5,
              'min': 0.001,
              'max': 0.999},
             {'name': 'thresholdStep',
              'title': 'Threshold step',
              'type': 'Number',
              'default': 0.01,
              'min': 0.001,
              'max': 0.1},
             {'name': 'showPlot',
              'title': 'Show net benefit curves',
              'type': 'Bool',
              'default': True}],
 'results': [{'name': 'summary', 'title': 'Interpretation', 'type': 'Text'},
             {'name': 'cohort',
              'title': 'Common Complete-Case Cohort',
              'type': 'Table',
              'columns': [{'name': 'n', 'title': 'Included', 'type': 'integer'},
                          {'name': 'excluded', 'title': 'Excluded', 'type': 'integer'},
                          {'name': 'events', 'title': 'Reference Positive', 'type': 'integer'},
                          {'name': 'prevalence',
                           'title': 'Sample Prevalence',
                           'type': 'number',
                           'format': 'pc'}]},
             {'name': 'curves',
              'title': 'Threshold Results',
              'type': 'Table',
              'columns': [{'name': 'model', 'title': 'Strategy', 'type': 'text'},
                          {'name': 'threshold', 'title': 'Threshold', 'type': 'number'},
                          {'name': 'tp', 'title': 'TP', 'type': 'integer'},
                          {'name': 'fp', 'title': 'FP', 'type': 'integer'},
                          {'name': 'netBenefit', 'title': 'Net Benefit', 'type': 'number'},
                          {'name': 'avoided',
                           'title': 'Interventions Avoided per 100',
                           'type': 'number'}]},
             {'name': 'netBenefitPlot',
              'title': 'Net Benefit Curves',
              'type': 'Image',
              'plot': 'line',
              'width': 600,
              'height': 400,
              'visible': '(showPlot)'}],
 'ui': {'children': [{'type': 'VariableSupplier',
                      'persistentItems': False,
                      'stretchFactor': 1,
                      'children': [{'type': 'TargetLayoutBox',
                                    'label': 'Binary reference outcome',
                                    'children': [{'type': 'VariablesListBox',
                                                  'name': 'outcome',
                                                  'isTarget': True,
                                                  'maxItemCount': 1},
                                                 {'type': 'LevelSelector',
                                                  'name': 'positive',
                                                  'enable': '(outcome)'}]},
                                   {'type': 'TargetLayoutBox',
                                    'label': 'Predicted probability columns',
                                    'children': [{'type': 'VariablesListBox',
                                                  'name': 'models',
                                                  'isTarget': True}]}]},
                     {'type': 'CollapseBox',
                      'label': 'Analysis and Model',
                      'collapsed': False,
                      'children': [{'type': 'LayoutBox',
                                    'margin': 'large',
                                    'children': [{'name': 'thresholdMin',
                                                  'type': 'TextBox',
                                                  'format': 'number'},
                                                 {'name': 'thresholdMax',
                                                  'type': 'TextBox',
                                                  'format': 'number'},
                                                 {'name': 'thresholdStep',
                                                  'type': 'TextBox',
                                                  'format': 'number'}]}]},
                     {'type': 'CollapseBox',
                      'label': 'Plots and Interaction',
                      'collapsed': True,
                      'children': [{'type': 'LayoutBox',
                                    'margin': 'large',
                                    'children': [{'name': 'showPlot', 'type': 'CheckBox'}]}]},
                     {'type': 'CollapseBox',
                      'label': 'Advanced Settings',
                      'collapsed': True,
                      'children': [{'type': 'CheckBox', 'name': 'showConsole'}]}]}}


def threshold_grid(low, high, step):
    import numpy as np
    from cpj_accuracy import finite_number
    low,high,step=[finite_number(v,n) for v,n in ((low,'Minimum threshold'),(high,'Maximum threshold'),(step,'Threshold step'))]
    if not 0<low<high<1 or step<=0:
        raise InputError('Require 0 < minimum < maximum < 1 and a positive step.')
    count=int(np.floor((high-low)/step+1e-10))+1
    if count<2 or count>1000:
        raise InputError('Choose a grid containing between 2 and 1,000 thresholds.')
    grid=low+np.arange(count)*step
    rounded=np.round(grid,10)
    snap=np.abs(grid-rounded)<=8*np.finfo(float).eps
    grid[snap]=rounded[snap]
    return grid


def run(data, options, out):
    import numpy as np
    from cpj_accuracy import binary
    group=data[options['outcome']]
    truth=binary(group,options.get('positive'),'reference outcome')
    models=options.get('models') or []
    if not isinstance(models,list) or not models or len(set(models))!=len(models):
        raise InputError('Select distinct predicted-probability columns.')
    grid=threshold_grid(options.get('thresholdMin',.05),options.get('thresholdMax',.5),options.get('thresholdStep',.01))
    if (len(models)+2)*len(grid)>20000:
        raise InputError('Models and thresholds exceed the 20,000-point plot limit; select fewer models or a wider step.')
    keep=group.codes>=0
    arrays=[]
    for name in models:
        x=np.asarray(data[name],dtype=float)
        if np.isinf(x).any() or np.any(x[np.isfinite(x)]<0) or np.any(x[np.isfinite(x)]>1):
            raise InputError(f'{name}: predictions must be probabilities between 0 and 1, or missing.')
        keep &= np.isfinite(x)
        arrays.append(x)
    y=truth[keep]
    n=len(y)
    if not n or y.all() or not y.any():
        raise InputError('The common complete-case cohort must contain both outcome classes.')
    events=int(y.sum())
    prevalence=events/n
    out.row('cohort',n=n,excluded=int((~keep).sum()),events=events,prevalence=prevalence)
    # Treat-all/none occupy reserved internal strategies, never keys based on user names.
    strategies=[('Model: '+name,x[keep]) for name,x in zip(models,arrays)]
    strategies += [('Reference: treat all',np.ones(n)),('Reference: treat none',np.zeros(n))]
    plot=[]
    for label,pred in strategies:
        order=np.argsort(pred,kind='stable')
        sorted_pred=pred[order]
        cumulative=np.r_[0,np.cumsum(y[order])]
        below=np.searchsorted(sorted_pred,grid,side='left')
        tp=events-cumulative[below]
        fp=n-below-tp
        for t,a,b in zip(grid,tp,fp):
            odds=t/(1-t)
            net=a/n-b/n*odds
            all_net=prevalence-(1-prevalence)*odds
            avoided=(net-all_net)/odds*100
            out.row('curves',model=label,threshold=t,tp=a,fp=b,netBenefit=net,avoided=avoided)
            plot.append(dict(x=float(t),y=float(net),group=label))
    out.plot('netBenefitPlot',plot,xlab='Threshold probability',ylab='Net benefit',reference=0)
    out.note('curves','Positive classification is predicted probability >= threshold. Interventions avoided '
             'per 100 are relative to treat all at the same threshold; negative values indicate more interventions '
             'at equivalent net benefit. All strategies use the same complete-case cohort. No uncertainty intervals are included.')
    out.markdown('summary',md_escape(f'Compared {len(models)} supplied probability columns on {n} common complete cases '
        f'({int((~keep).sum())} rows excluded). Models are not fitted or recalibrated. '
        'Thresholds encode the relative consequences of false positives and missed events; the default range '
        'is a computational convenience, not a clinical recommendation. Net benefit uses the observed cohort '
        'prevalence and assumes independent observations. Bootstrap inference, case-control prevalence correction, '
        'model-comparison tests and economic modelling are outside this core.'))
