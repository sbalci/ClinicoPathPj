"""Test helper: run a shipped analysis through inst/python/cpj_runtime.py exactly as the R bridge does.

    from cpjtest import run_analysis, number, factor, text
    result = run_analysis("pywelch", columns={"y": number([1.0, 2.0]), "g": factor(["a", "b"])},
                          options={"dep": "y", "group": "g", "refLevel": None, "ciWidth": 95})
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "inst" / "python" / "cpj_runtime.py"


def run_analysis(name, columns=None, options=None, timeout=300):
    """Return the runtime's response (status, tables, texts, plots, notices, console, error)."""
    with tempfile.TemporaryDirectory(prefix="cpj-test-") as folder:
        request, response = Path(folder) / "request.json", Path(folder) / "response.json"
        request.write_text(json.dumps({"analysis": name, "options": options or {}, "columns": columns or {}}),
                           encoding="utf-8")
        done = subprocess.run([sys.executable, "-B", "-s", str(RUNTIME), str(request), str(response)],
                              capture_output=True, text=True, timeout=timeout)
        if done.returncode != 0:
            raise AssertionError(f"runtime exited with {done.returncode}: {done.stderr}")
        return json.loads(response.read_text(encoding="ascii"))


def number(values):
    """A numeric column; None = missing."""
    return {"kind": "number", "values": list(values)}


def factor(labels, levels=None):
    """A factor column from labels (None = missing); levels default to the sorted distinct labels."""
    levels = list(levels) if levels is not None else sorted({x for x in labels if x is not None})
    return {"kind": "factor", "levels": levels, "codes": [None if x is None else levels.index(x) for x in labels]}


def text(values):
    """A text (ID) column; None = missing."""
    return {"kind": "text", "values": list(values)}


def rows(result, table):
    return result["tables"][table]["rows"]
