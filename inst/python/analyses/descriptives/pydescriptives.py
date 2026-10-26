"""Descriptive statistics of numeric variables, computed with numpy."""

from cpj_runtime import Factor, InputError

SPEC = {'name': 'pydescriptives',
 'title': 'Descriptives (Python)',
 'menuGroup': 'Descriptives Py',
 'menuSubgroup': 'Summaries',
 'version': '0.1.0',
 'options': [{'name': 'vars',
              'type': 'Variables',
              'title': 'Variables',
              'permitted': ['numeric'],
              'suggested': ['continuous'],
              'required': True}],
 'results': [{'name': 'desc',
              'type': 'Table',
              'title': 'Descriptives',
              'columns': [{'name': 'variable', 'title': 'Variable', 'type': 'text'},
                          {'name': 'n', 'title': 'N', 'type': 'integer'},
                          {'name': 'missing', 'title': 'Missing', 'type': 'integer'},
                          {'name': 'mean', 'title': 'Mean', 'type': 'number'},
                          {'name': 'sd', 'title': 'SD', 'type': 'number'},
                          {'name': 'min', 'title': 'Minimum', 'type': 'number'},
                          {'name': 'q1', 'title': '25th percentile', 'type': 'number'},
                          {'name': 'median', 'title': 'Median', 'type': 'number'},
                          {'name': 'q3', 'title': '75th percentile', 'type': 'number'},
                          {'name': 'max', 'title': 'Maximum', 'type': 'number'}]}],
 'ui': {'children': [{'type': 'VariableSupplier',
                      'persistentItems': False,
                      'stretchFactor': 1,
                      'children': [{'type': 'TargetLayoutBox',
                                    'label': 'Variables',
                                    'children': [{'type': 'VariablesListBox',
                                                  'name': 'vars',
                                                  'isTarget': True}]}]},
                     {'type': 'CollapseBox',
                      'label': 'Advanced Settings',
                      'collapsed': True,
                      'children': [{'type': 'CheckBox', 'name': 'showConsole'}]}]}}


def run(data, options, out):
    import numpy as np

    counts = []
    for name in options["vars"]:
        x = data[name]
        if isinstance(x, Factor) or not isinstance(x, np.ndarray):
            raise InputError(f"'{name}' is not a numeric variable.")
        observed = x[~np.isnan(x)]  # each variable uses its own observed values
        n = observed.size
        row = {"variable": name, "n": n, "missing": x.size - n}
        if n > 0:
            # numpy's default 'linear' percentile is R's quantile(type = 7)
            q1, median, q3 = np.percentile(observed, [25, 50, 75])
            row.update(mean=observed.mean(), min=observed.min(), q1=q1, median=median, q3=q3, max=observed.max())
        if n > 1:
            row["sd"] = observed.std(ddof=1)
        out.row("desc", **row)
        counts.append(n)
    if 0 in counts:
        out.note("desc", "A variable without observed values has no statistics.")
    if 1 in counts:
        out.note("desc", "The SD needs at least two observed values.")
