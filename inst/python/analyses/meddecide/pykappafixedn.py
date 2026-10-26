"""Lowest expected kappa for a fixed number of subjects (kappaSize FixedNBinary, FixedN3-5Cats)."""

SPEC = {'name': 'pykappafixedn',
 'title': 'Kappa Lower Limit for a Fixed Sample Size',
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
             {'name': 'n',
              'type': 'Integer',
              'title': 'Subjects available',
              'default': 100,
              'min': 11,
              'max': 1000000},
             {'name': 'alpha',
              'type': 'Number',
              'title': 'Alpha (0.05 for a one-sided 95 percent limit)',
              'default': 0.05,
              'min': 0.001,
              'max': 0.2}],
 'results': [{'name': 'summary', 'type': 'Text', 'title': 'Interpretation'},
             {'name': 'bound',
              'type': 'Table',
              'title': 'Lowest Expected Kappa',
              'columns': [{'name': 'kappaL', 'title': 'Expected lower limit', 'type': 'number'},
                          {'name': 'n', 'title': 'Subjects', 'type': 'integer'},
                          {'name': 'categories', 'title': 'Categories', 'type': 'integer'},
                          {'name': 'raters', 'title': 'Raters', 'type': 'integer'},
                          {'name': 'props', 'title': 'Proportions', 'type': 'text'},
                          {'name': 'kappa0', 'title': 'Anticipated kappa', 'type': 'number'},
                          {'name': 'interval', 'title': 'Interval', 'type': 'text'}]}],
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
                                                 {'name': 'n',
                                                  'type': 'TextBox',
                                                  'format': 'number'}]}]},
                     {'type': 'CollapseBox',
                      'label': 'Uncertainty and Validation',
                      'collapsed': True,
                      'children': [{'type': 'LayoutBox',
                                    'margin': 'large',
                                    'children': [{'name': 'alpha',
                                                  'type': 'TextBox',
                                                  'format': 'number'}]}]},
                     {'type': 'CollapseBox',
                      'label': 'Advanced Settings',
                      'collapsed': True,
                      'children': [{'type': 'CheckBox', 'name': 'showConsole'}]}]}}


def run(data, options, out):
    import cpj_kappasize as ks

    categories, raters = int(options["outcome"]), int(options["raters"])
    kappa0, n, alpha = options["kappa0"], int(options["n"]), options["alpha"]
    props, rescaled = ks.parse_props(options["props"], categories)

    bound, floor = ks.fixed_n_bound(categories, raters, props, kappa0, n, alpha)
    level = f"{100 * (1 - alpha):g}%"
    out.row("bound", kappaL=bound, n=n, categories=categories, raters=raters, props=ks.props_text(props),
            kappa0=kappa0, interval=f"{level} one-sided")
    out.note("bound", f"kappaSize fixed-sample approach: kappa is stepped "
                      f"down from {kappa0:g} by 0.001 until the expected goodness-of-fit chi-square exceeds the "
                      f"one-sided critical value. The result is the expected lower confidence limit if the study "
                      f"observes kappa = {kappa0:g}; on this 0.001 grid it lies up to about 0.001 below the exact "
                      f"limit.")
    ks.common_notes(out, "bound", categories, raters, rescaled)
    head = (f"With {n:,} subjects, each rated by {ks.raters_text(raters)}, the expected lower limit of the "
            f"one-sided {level} confidence interval for kappa")
    if bound is None:
        out.note("bound", f"Not available: the limit lies within about 0.001 of {floor:.4g}, the lowest kappa this "
                          f"model allows for these proportions and raters, which the 0.001 steps cannot resolve.")
        out.markdown("summary", f"{head} lies within about 0.001 of {floor:.4g}, the lowest kappa this model allows "
                                f"for these proportions and raters, even if the study observes kappa = {kappa0:g}: "
                                f"it could rule out practically no value of kappa that the model allows.")
        return
    ks.sparse_note(out, "bound", ks.min_expected_count(categories, raters, props, [bound], n), False)
    text = (f"{head} is **{bound:.3f}** if the study observes the anticipated kappa of {kappa0:g}: such a study "
            f"would rule out kappa values below {bound:.3f}.")
    if bound <= 0:
        out.note("bound", "The expected lower limit is not above 0: even if the study observes kappa0, it could "
                          "not rule out agreement no better than chance.")
        text += " It could not rule out agreement no better than chance."
    out.markdown("summary", text)
