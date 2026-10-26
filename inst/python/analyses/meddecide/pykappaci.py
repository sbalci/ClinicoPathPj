"""Sample size for a kappa study by the confidence-interval approach (kappaSize CIBinary, CI3-5Cats)."""

from cpj_runtime import InputError

SPEC = {'name': 'pykappaci',
 'title': 'Kappa Sample Size by Confidence Interval',
 'menuGroup': 'MedDecide Py',
 'menuSubgroup': 'Agreement sample size',
 'version': '0.1.0',
 'options': [{'name': 'outcome',
              'type': 'List',
              'title': 'Outcome categories',
              'default': '2',
              'options': [{'name': '2', 'title': '2 (binary)'},
                          {'name': '3', 'title': '3'},
                          {'name': '4', 'title': '4'},
                          {'name': '5', 'title': '5'}]},
             {'name': 'props',
              'type': 'String',
              'title': 'Expected proportion of each category',
              'default': '0.20, 0.80'},
             {'name': 'raters',
              'type': 'List',
              'title': 'Raters',
              'default': '2',
              'options': [{'name': '2', 'title': '2'},
                          {'name': '3', 'title': '3'},
                          {'name': '4', 'title': '4'},
                          {'name': '5', 'title': '5'},
                          {'name': '6', 'title': '6'}]},
             {'name': 'kappa0',
              'type': 'Number',
              'title': 'Anticipated kappa (kappa0)',
              'default': 0.6,
              'min': 0.01,
              'max': 0.99},
             {'name': 'citype',
              'type': 'List',
              'title': 'Confidence interval',
              'default': 'two_sided',
              'options': [{'name': 'two_sided', 'title': 'Two-sided'},
                          {'name': 'one_sided', 'title': 'One-sided (lower limit)'}]},
             {'name': 'kappaL',
              'type': 'Number',
              'title': 'Target lower limit (kappaL)',
              'default': 0.4,
              'min': 0.01,
              'max': 0.99},
             {'name': 'kappaU',
              'type': 'Number',
              'title': 'Target upper limit (kappaU)',
              'default': 0.8,
              'min': 0.01,
              'max': 0.99},
             {'name': 'alpha',
              'type': 'Number',
              'title': 'Alpha (0.05 for a 95 percent interval)',
              'default': 0.05,
              'min': 0.001,
              'max': 0.2},
             {'name': 'simulate',
              'type': 'Bool',
              'title': 'Monte Carlo check of the planned study',
              'default': False},
             {'name': 'draws',
              'type': 'Integer',
              'title': 'Simulated studies',
              'default': 2000,
              'min': 100,
              'max': 20000},
             {'name': 'seed',
              'type': 'Integer',
              'title': 'Random seed',
              'default': 20261018,
              'min': 1,
              'max': 2147483647}],
 'results': [{'name': 'summary', 'type': 'Text', 'title': 'Interpretation'},
             {'name': 'size',
              'type': 'Table',
              'title': 'Required Sample Size',
              'columns': [{'name': 'n', 'title': 'Subjects', 'type': 'integer'},
                          {'name': 'categories', 'title': 'Categories', 'type': 'integer'},
                          {'name': 'raters', 'title': 'Raters', 'type': 'integer'},
                          {'name': 'props', 'title': 'Proportions', 'type': 'text'},
                          {'name': 'kappa0', 'title': 'Anticipated kappa', 'type': 'number'},
                          {'name': 'kappaL',
                           'title': 'Lower',
                           'type': 'number',
                           'superTitle': 'Target limits'},
                          {'name': 'kappaU',
                           'title': 'Upper',
                           'type': 'number',
                           'superTitle': 'Target limits'},
                          {'name': 'interval', 'title': 'Interval', 'type': 'text'}]},
             {'name': 'check',
              'type': 'Table',
              'title': 'Monte Carlo Check',
              'visible': '(simulate)',
              'columns': [{'name': 'statistic', 'title': '', 'type': 'text'},
                          {'name': 'planned', 'title': 'Planned', 'type': 'number'},
                          {'name': 'simulated', 'title': 'Simulated', 'type': 'number'},
                          {'name': 'se', 'title': 'Monte Carlo SE', 'type': 'number'}]}],
 'ui': {'children': [{'type': 'CollapseBox',
                      'label': 'Analysis and Model',
                      'collapsed': False,
                      'children': [{'type': 'LayoutBox',
                                    'margin': 'large',
                                    'children': [{'name': 'outcome', 'type': 'ComboBox'},
                                                 {'name': 'props',
                                                  'type': 'TextBox',
                                                  'format': 'string'},
                                                 {'name': 'raters', 'type': 'ComboBox'},
                                                 {'name': 'kappa0',
                                                  'type': 'TextBox',
                                                  'format': 'number'},
                                                 {'name': 'citype', 'type': 'ComboBox'},
                                                 {'name': 'kappaL',
                                                  'type': 'TextBox',
                                                  'format': 'number'},
                                                 {'name': 'kappaU',
                                                  'type': 'TextBox',
                                                  'format': 'number'}]}]},
                     {'type': 'CollapseBox',
                      'label': 'Uncertainty and Validation',
                      'collapsed': True,
                      'children': [{'type': 'LayoutBox',
                                    'margin': 'large',
                                    'children': [{'name': 'alpha',
                                                  'type': 'TextBox',
                                                  'format': 'number'},
                                                 {'name': 'simulate', 'type': 'CheckBox'},
                                                 {'name': 'draws',
                                                  'type': 'TextBox',
                                                  'format': 'number',
                                                  'enable': '(simulate)'},
                                                 {'name': 'seed',
                                                  'type': 'TextBox',
                                                  'format': 'number',
                                                  'enable': '(simulate)'}]}]},
                     {'type': 'CollapseBox',
                      'label': 'Advanced Settings',
                      'collapsed': True,
                      'children': [{'type': 'CheckBox', 'name': 'showConsole'}]}]}}


def run(data, options, out):
    import cpj_kappasize as ks

    categories, raters = int(options["outcome"]), int(options["raters"])
    kappa0, kappa_l, alpha = options["kappa0"], options["kappaL"], options["alpha"]
    two_sided = options["citype"] == "two_sided"
    kappa_u = options["kappaU"] if two_sided else None
    props, rescaled = ks.parse_props(options["props"], categories)
    if not kappa_l < kappa0:
        raise InputError("The target lower limit (kappaL) must be below the anticipated kappa (kappa0).")
    if two_sided and not kappa0 < kappa_u:
        raise InputError("The target upper limit (kappaU) must be above the anticipated kappa (kappa0).")

    n = ks.ci_n(categories, raters, props, kappa0, kappa_l, kappa_u, alpha)
    level = f"{100 * (1 - alpha):g}%"
    out.row("size", n=n, categories=categories, raters=raters, props=ks.props_text(props), kappa0=kappa0,
            kappaL=kappa_l, kappaU=kappa_u, interval=f"{level} {'two-sided' if two_sided else 'one-sided'}")
    out.note("size", f"kappaSize confidence-interval approach (Rotondi and Donner 2012): the smallest number of "
                     f"subjects, at least 11, for which the expected goodness-of-fit confidence limits reach the "
                     f"targets when the study observes kappa = {kappa0:g}.")
    ks.common_notes(out, "size", categories, raters, rescaled)
    ks.sparse_note(out, "size", ks.min_expected_count(categories, raters, props, [kappa_l, kappa_u], n),
                   ks.mc_available(categories, raters))

    if two_sided:
        aim = (f"for the expected {level} confidence limits around an anticipated kappa of {kappa0:g} to reach "
               f"{kappa_l:g} and {kappa_u:g}. These are expected limits, reached")
        reach_label, reach_text, expected = ("Interval within the target limits", "lay within the target limits",
                                             "limits reach the targets")
    else:
        aim = (f"for the expected lower limit of the one-sided {level} confidence interval around an anticipated "
               f"kappa of {kappa0:g} to reach {kappa_l:g}. This is an expected limit, reached")
        reach_label, reach_text, expected = ("Lower limit at or above the target", "had a lower limit at or above "
                                             "the target", "lower limit reach the target")
    text = (f"**{n:,} subjects**, each rated by {ks.raters_text(raters)}, are needed {aim} if the study observes "
            f"kappa = {kappa0:g}; if it observes less, the lower limit will usually fall below {kappa_l:g}.")

    if options["simulate"] and not ks.mc_available(categories, raters):
        out.note("check", ks.MC_UNAVAILABLE)
    elif options["simulate"]:
        draws, seed = int(options["draws"]), int(options["seed"])
        covered, reached = ks.simulate_ci(raters, props, kappa0, kappa_l, kappa_u, alpha, n, draws, seed)
        out.row("check", statistic="Interval contains the true kappa (coverage)", planned=1 - alpha,
                simulated=covered, se=ks.mc_se(covered, draws))
        out.row("check", statistic=reach_label, simulated=reached, se=ks.mc_se(reached, draws))
        out.note("check", f"{draws:,} simulated studies of {n:,} subjects, random seed {seed}, true kappa "
                          f"{kappa0:g}; each analysed with {ks.MC_ANALYSIS.format('interval')}.")
        out.note("check", f"'{reach_label}' has no planned value: the sample size makes the {expected} only "
                          f"if the study observes kappa = {kappa0:g}.")
        text += (f" In {draws:,} simulated studies (seed {seed}) the interval contained the true kappa in "
                 f"{100 * covered:.1f}% (planned {level}) and {reach_text} in {100 * reached:.1f}%.")
    out.markdown("summary", text)
