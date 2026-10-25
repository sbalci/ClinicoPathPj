"""Which Python does ClinicoPathPj run in? Lists the interpreter and its numeric libraries."""

SPEC = {'name': 'pyruntime',
 'title': 'Python Runtime Check',
 'menuGroup': 'ClinicoPathPj',
 'menuSubgroup': 'Utilities',
 'version': '0.1.0',
 'options': [],
 'results': [{'name': 'runtime',
              'type': 'Table',
              'title': 'Python Runtime',
              'columns': [{'name': 'item', 'title': '', 'type': 'text'},
                          {'name': 'value', 'title': 'Value', 'type': 'text'}]}],
 'ui': {'children': [{'type': 'CollapseBox',
                      'label': 'Advanced Settings',
                      'collapsed': True,
                      'children': [{'type': 'CheckBox', 'name': 'showConsole'}]}]}}


def run(data, options, out):
    import platform
    import sys

    out.row("runtime", item="Interpreter", value=sys.executable)
    out.row("runtime", item="Python", value=platform.python_version())
    for module in ("numpy", "scipy"):
        try:
            version = __import__(module).__version__
        except ImportError:
            version = "not available"
            out.warn(f"{module} is not available in this Python, so analyses that need it will fail.")
        out.row("runtime", item=module, value=version)
    out.row("runtime", item="Platform", value=platform.platform())
