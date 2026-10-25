"""ClinicoPathPj runtime: python cpj_runtime.py <request.json> <response.json>

Loads inst/python/analyses/<name>.py, decodes the request's columns, calls
run(data, options, out) and writes one JSON response. Analyses import InputError and
Factor from this module. stdout/stderr and warnings raised during run() are captured;
the process exits 0 whenever a response was written.
"""
import faulthandler
import signal
import sys
import time

_STARTED = time.perf_counter()  # for the console report's total time

# R's system2(timeout=) sends SIGINT first; with the default action Python dies at once,
# even inside numpy/scipy C code, instead of raising KeyboardInterrupt later.
signal.signal(signal.SIGINT, signal.SIG_DFL)
# A crash in C code (segfault, abort) would end Python without a word: faulthandler writes the Python
# stack to the real stderr, which R reads, even while run()'s own output is captured in memory.
faulthandler.enable()
# Run as a script this module is __main__; make "from cpj_runtime import InputError" in an
# analysis return these same classes instead of importing a second copy of the file.
sys.modules.setdefault("cpj_runtime", sys.modules[__name__])

import contextlib  # noqa: E402
import copy  # noqa: E402
import importlib.util  # noqa: E402
import io  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import traceback  # noqa: E402
import warnings  # noqa: E402
from collections import namedtuple  # noqa: E402
from pathlib import Path  # noqa: E402

MAX_WARNINGS = 10
MAX_CONSOLE = 100_000
SELF_LIMIT = 75  # seconds; R stops runs after 60 s, this only matters if R itself was killed


MAX_PLOT_ROWS = {"interval": 200, "line": 20_000, "box": 20_000, "bar": 2_000}  # image state is saved in the .omv
PLOT_COLUMNS = {  # column -> (type, required); drawn by R/utils-plots.R
    "interval": {"label": ("text", True), "estimate": ("number", True),
                 "lower": ("number", False), "upper": ("number", False)},
    "line": {"x": ("number", True), "y": ("number", True), "group": ("text", False)},
    "box": {"group": ("text", True), "value": ("number", True)},
    "bar": {"label": ("text", True), "value": ("number", True), "group": ("text", True)},
}


class InputError(Exception):
    """A problem with the user's data or options; jamovi shows the message as the error."""


Factor = namedtuple("Factor", "codes levels")  # codes: int ndarray (-1 = missing); levels: list of str


def md_escape(text):
    """Escape user text (column names, level labels) for a Markdown result. Whitespace is collapsed
    first: a newline in a label would otherwise start a paragraph or a code block."""
    return re.sub(r"([!-/:-@\[-`{-~])", r"\\\1", re.sub(r"\s+", " ", str(text)))


def fmt_num(x, digits=3):
    """x to `digits` significant digits, never in scientific notation (R's formatC 'fg'):
    1234.5 -> '1234', 0.000123456 -> '0.000123'. For narrative text."""
    if x == 0 or abs(x) >= 10 ** digits:
        return f"{x:.0f}"
    text = f"{x:.{max(digits - 1 - math.floor(math.log10(abs(x))), 0)}f}"
    return text.rstrip("0").rstrip(".") if "." in text else text


class _BoundedText(io.StringIO):
    """Console capture that stops storing at MAX_CONSOLE characters instead of growing without limit."""

    truncated = False

    def write(self, text):
        room = MAX_CONSOLE - self.tell()
        if len(text) > room:
            self.truncated = True
            text = text[:max(room, 0)]
        super().write(text)
        return len(text)


def _cell(value, kind, where):
    """Convert one table value to a JSON scalar for a column of type text/integer/number."""
    if getattr(value, "ndim", 0) != 0 or isinstance(value, (list, tuple, dict, set)):
        raise TypeError(f"{where}: expected a single value, got {type(value).__name__}")
    if hasattr(value, "item") and not isinstance(value, (str, bytes)):
        value = value.item()  # numpy scalar -> Python scalar
    if value is None:
        return None
    if kind == "text":
        return str(value)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{where}: expected a number, got {type(value).__name__}")
    if isinstance(value, float) and not math.isfinite(value):
        return None  # shown as jamovi's missing mark "."
    if kind == "integer":
        if isinstance(value, float) and not value.is_integer():
            raise TypeError(f"{where}: expected a whole number, got {value!r}")
        return int(value)
    return float(value)  # an int would reach jamovi as an integer cell and skip the column format


class Output:
    """What run() reports, checked against the analysis SPEC as it is reported."""

    def __init__(self, spec):
        self._tables = {r["name"]: {c["name"]: c["type"] for c in r["columns"]}
                        for r in spec["results"] if r["type"] == "Table"}
        self._texts = {r["name"] for r in spec["results"] if r["type"] == "Preformatted"}
        self._markdown = {r["name"] for r in spec["results"] if r["type"] == "Text"}
        self._html = {r["name"] for r in spec["results"] if r["type"] == "Html"}
        self.htmls = {}
        self._plots = {r["name"]: r for r in spec["results"] if r["type"] == "Image"}
        self.tables = {}
        self.texts = {}
        self.plots = {}
        self.notices = []

    def _table(self, name):
        if name not in self._tables:
            raise KeyError(f"SPEC declares no table named {name!r}")
        return self.tables.setdefault(name, {"rows": [], "notes": []})

    def row(self, table, **values):
        """Append a row; columns left out show jamovi's missing mark "."."""
        entry = self._table(table)
        unknown = sorted(set(values) - set(self._tables[table]))
        if unknown:
            raise KeyError(f"table {table!r} has no column(s) {unknown}")
        entry["rows"].append({column: _cell(values.get(column), kind, f"table {table!r}, column {column!r}")
                              for column, kind in self._tables[table].items()})

    def note(self, table, text):
        self._table(table)["notes"].append(str(text))

    def text(self, name, content):
        if name not in self._texts:
            raise KeyError(f"SPEC declares no Preformatted result named {name!r}")
        self.texts[name] = str(content)

    def markdown(self, name, content):
        """Fill a Text result. Pass user strings through md_escape() first."""
        if name not in self._markdown:
            raise KeyError(f"SPEC declares no Text result named {name!r}")
        self.texts[name] = str(content)

    def html(self, name, content):
        """Trusted module-authored HTML only; escape every user value before embedding it."""
        if name not in self._html:
            raise KeyError(f"SPEC declares no Html result named {name!r}")
        if not isinstance(content, str) or len(content.encode("utf-8")) > 1_500_000:
            raise ValueError("HTML must be a string of at most 1.5 MB")
        self.htmls[name] = content

    def plot(self, name, rows, *, xlab=None, ylab=None, reference=None, step=False):
        """Data for an Image result; R draws it. rows: list of dicts with the plot kind's columns."""
        if name not in self._plots:
            raise KeyError(f"SPEC declares no Image result named {name!r}")
        kind = self._plots[name]["plot"]
        spec = PLOT_COLUMNS[kind]
        rows = list(rows)
        if len(rows) > MAX_PLOT_ROWS[kind]:
            raise ValueError(f"plot {name!r}: {len(rows)} rows, but {kind} plots hold at most "
                             f"{MAX_PLOT_ROWS[kind]}; summarise first")
        columns = {column: [] for column in spec}
        for row in rows:
            unknown = sorted(set(row) - set(spec))
            missing = sorted(c for c, (_, needed) in spec.items() if needed and row.get(c) is None)
            if unknown or missing:
                raise KeyError(f"plot {name!r} ({kind}): unknown {unknown}, missing {missing}")
            for column, (kind_of, _) in spec.items():
                columns[column].append(_cell(row.get(column), kind_of, f"plot {name!r}, column {column!r}"))
        if reference is not None:
            reference = _cell(reference, "number", f"plot {name!r}, reference")
        self.plots[name] = {
            "kind": kind, "columns": columns, "step": bool(step), "reference": reference,
            "xlab": str(xlab) if xlab is not None else self._plots[name].get("xlab", ""),
            "ylab": str(ylab) if ylab is not None else self._plots[name].get("ylab", ""),
        }

    def warn(self, text):
        self.notices.append({"type": "WARNING", "text": str(text)})

    def info(self, text):
        self.notices.append({"type": "INFO", "text": str(text)})


def _decode(columns):
    import numpy as np
    data = {}
    for name, column in (columns or {}).items():  # R sends [] for a dataset without columns
        if column["kind"] == "number":
            data[name] = np.array([np.nan if v is None else v for v in column["values"]], dtype=float)
        elif column["kind"] == "factor":
            codes = np.array([-1 if c is None else c for c in column["codes"]], dtype=int)
            data[name] = Factor(codes, list(column["levels"]))
        else:
            data[name] = list(column["values"])
    return data


def _load(name):
    if not isinstance(name, str) or not re.fullmatch(r"[a-z][a-z0-9]*", name):
        raise ValueError(f"invalid analysis name {name!r}")
    path = Path(__file__).resolve().parent / "analyses" / f"{name}.py"
    if not path.is_file():
        raise FileNotFoundError(f"analysis {name!r} is not installed ({path})")
    spec = importlib.util.spec_from_file_location(f"cpj_analysis_{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _warning_notices(caught):
    counts = {}
    for item in caught:
        text = f"{item.category.__name__}: {item.message}"
        counts[text] = counts.get(text, 0) + 1
    texts = [text if n == 1 else f"{text} (repeated {n} times)" for text, n in counts.items()]
    notices = [{"type": "WARNING", "text": text} for text in texts[:MAX_WARNINGS]]
    if len(texts) > MAX_WARNINGS:
        notices.append({"type": "WARNING", "text": f"{len(texts) - MAX_WARNINGS} more warnings not shown."})
    return notices


def _clip(text, limit):
    return text if len(text) <= limit else text[:limit - 3] + "..."


def _plural(n, word):
    return f"{n} {word}" + ("" if n == 1 else "s")


def _data_line(columns):
    """What Python received, for the console report: rows, then each column's kind, missing count and
    levels. Names and levels are JSON-quoted, so a comma, a newline or an NA level (null) stays readable."""
    parts, rows = [], 0
    for name, column in (columns or {}).items():  # R sends [] for a dataset without columns
        values = column["codes"] if column["kind"] == "factor" else column["values"]
        rows, missing = len(values), values.count(None)
        details = [column["kind"]] + ([f"{missing} missing"] if missing else [])
        if column["kind"] == "factor":
            levels = column["levels"]
            shown = ", ".join(json.dumps(level, ensure_ascii=False) for level in levels[:5])
            details.append(_plural(len(levels), "level") + (f": [{shown}" + (", ...]" if len(levels) > 5 else "]")
                                                             if levels else ""))
        parts.append(f"{json.dumps(name, ensure_ascii=False)} ({', '.join(details)})")
    return _clip(f"{_plural(rows, 'row')}; " + "; ".join(parts), 1000) if parts else "no columns"


def _report(request, module, status, seconds, scipy_in_run):
    """The head of the console: what ran, in which Python, on which data and options, how it ended."""
    import numpy as np
    spec = getattr(module, "SPEC", None)
    version = spec.get("version") if isinstance(spec, dict) else None
    title = f"{request.get('analysis')} {version}" if version else str(request.get("analysis"))
    scipy = sys.modules.get("scipy")  # imported by the analysis, if at all
    libraries = [f"Python {sys.version.split()[0]}", f"numpy {np.__version__}",
                 f"scipy {scipy.__version__}" if scipy else "scipy not imported"]
    if seconds is None:
        timing = "run() was not reached"
    else:
        timing = f"run() took {seconds:.3f} s" + (", including its scipy import" if scipy_in_run else "")
    return "\n".join([
        f"{title}: " + ", ".join(libraries),
        f"Interpreter: {sys.executable}",
        f"Data received: {_data_line(request.get('columns'))}",
        "Options received: " + _clip(json.dumps(request.get("options") or {}, ensure_ascii=False), 1000),
        f"Status: {status.replace('_', ' ')}. {timing}; {time.perf_counter() - _STARTED:.2f} s since the runtime started.",
    ])


def _describe(error):
    if isinstance(error, SystemExit):
        return f"the analysis called sys.exit({error.code!r}); return from run() instead"
    return f"{type(error).__name__}: {error}"


def execute(request):
    """Run the requested analysis; return the response dict. Never raises."""
    response = {"status": "exception", "error": None, "tables": {}, "texts": {}, "plots": {},
                "notices": [], "console": "", "report": ""}
    console = _BoundedText()
    module = started = scipy_before = None
    # Loading happens inside the capture too, so import-time output and warnings are reported.
    with contextlib.redirect_stdout(console), contextlib.redirect_stderr(console), \
            warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        out = None
        try:
            module = _load(request.get("analysis"))
            out = Output(module.SPEC)
            data = _decode(request.get("columns"))
            scipy_before = "scipy" in sys.modules
            started = time.perf_counter()
            # a copy: the report shows the options as received, whatever run() does with its own
            module.run(data, copy.deepcopy(request.get("options") or {}), out)
            response.update(status="ok", tables=out.tables, texts=out.texts, plots=out.plots, htmls=out.htmls)
        except InputError as error:
            response.update(status="input_error", error={"message": str(error)})
        except (Exception, SystemExit) as error:  # SystemExit would otherwise lose the response
            response["error"] = {"message": _describe(error)}
            traceback.print_exc(file=console)
        response["notices"] = (out.notices if out else []) + _warning_notices(caught)
    seconds = None if started is None else time.perf_counter() - started
    response["console"] = console.getvalue() + ("\n[console output truncated]" if console.truncated else "")
    try:
        response["report"] = _report(request, module, response["status"], seconds,
                                     scipy_before is False and "scipy" in sys.modules)
    except Exception as error:  # a diagnostic must never cost the analysis its result
        response["report"] = f"(no report: {_describe(error)})"
    return response


def write(response, path):
    try:
        payload = json.dumps(response, ensure_ascii=True, allow_nan=False)
    except (TypeError, ValueError) as error:  # should not happen: values are converted in Output.row
        payload = json.dumps({"status": "exception", "error": {"message": f"result could not be encoded: {error}"},
                              "tables": {}, "texts": {}, "plots": {}, "notices": [],
                              "console": response.get("console", ""),
                              "report": response.get("report", "") + "\nThe result could not be encoded, so it "
                                        f"was replaced by an error: {error}"},
                             ensure_ascii=True)
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="ascii") as stream:
        stream.write(payload)
    os.replace(tmp, path)  # R never reads a half-written response


def main(argv):
    if len(argv) != 2:
        print("usage: cpj_runtime.py <request.json> <response.json>", file=sys.stderr)
        return 2
    signal.alarm(SELF_LIMIT)  # default SIGALRM action ends the process if no parent stops it
    with open(argv[0], encoding="utf-8") as stream:
        request = json.load(stream)
    write(execute(request), argv[1])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
