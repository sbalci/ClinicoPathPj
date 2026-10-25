"""Tests for inst/python/cpj_runtime.py, run as a subprocess the way the R bridge runs it.

Each test copies the runtime into a temporary folder next to a probe analysis, so no test
analysis is ever installed with the module.
"""
import json
import shutil
import signal
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "inst" / "python" / "cpj_runtime.py"

PROBE_HEADER = '''
from cpj_runtime import Factor, InputError

SPEC = {"results": [
    {"name": "t", "type": "Table", "columns": [
        {"name": "label", "type": "text"}, {"name": "x", "type": "number"}, {"name": "k", "type": "integer"}]},
    {"name": "txt", "type": "Preformatted"},
]}
'''


class Runtime(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp(prefix="cpj-test-"))
        (self.folder / "analyses").mkdir()
        shutil.copy(RUNTIME, self.folder / "cpj_runtime.py")
        self.request = self.folder / "request.json"
        self.response = self.folder / "response.json"

    def tearDown(self):
        shutil.rmtree(self.folder)

    def command(self, body, name="probe", columns=None, options=None):
        if body is not None:
            source = PROBE_HEADER + textwrap.dedent(body)
            (self.folder / "analyses" / f"{name}.py").write_text(source, encoding="utf-8")
        self.request.write_text(json.dumps({"analysis": name, "options": options or {},
                                            "columns": columns or {}}), encoding="utf-8")
        return [sys.executable, "-B", "-s", str(self.folder / "cpj_runtime.py"),
                str(self.request), str(self.response)]

    def run_probe(self, body, **request):
        done = subprocess.run(self.command(body, **request), capture_output=True, text=True, timeout=120)
        self.assertEqual(done.returncode, 0, done.stderr)
        return json.loads(self.response.read_text(encoding="ascii"))

    def test_rows_are_converted_and_validated(self):
        result = self.run_probe('''
            def run(data, options, out):
                import numpy as np
                print("hello")
                out.row("t", label="a", x=np.float64(1.5), k=np.int64(3))
                out.row("t", x=float("nan"), k=4.0)
                out.note("t", "a note")
                out.text("txt", "plain text")
        ''')
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["console"], "hello\n")
        self.assertEqual(result["tables"]["t"]["rows"],
                         [{"label": "a", "x": 1.5, "k": 3}, {"label": None, "x": None, "k": 4}])
        self.assertEqual(result["tables"]["t"]["notes"], ["a note"])
        self.assertEqual(result["texts"], {"txt": "plain text"})

    def test_the_report_says_what_ran_and_on_which_data(self):
        columns = {"Yaş": {"kind": "number", "values": [1.5, None, 3.0]},
                   "g": {"kind": "factor", "levels": ["a", "b"], "codes": [0, 1, None]},
                   "s": {"kind": "text", "values": ["x", "y", "z"]}}
        result = self.run_probe('''
            def run(data, options, out):
                pass
        ''', columns=columns, options={"vars": ["Yaş"], "level": None})
        lines = result["report"].splitlines()
        self.assertTrue(lines[0].startswith("probe: Python 3."), lines)
        self.assertTrue(lines[0].endswith(", scipy not imported"), lines)
        self.assertEqual(lines[1], f"Interpreter: {sys.executable}")
        self.assertEqual(lines[2], 'Data received: 3 rows; "Yaş" (number, 1 missing); '
                                   '"g" (factor, 1 missing, 2 levels: ["a", "b"]); "s" (text)')
        self.assertEqual(lines[3], 'Options received: {"vars": ["Yaş"], "level": null}')
        self.assertRegex(lines[4], r"^Status: ok\. run\(\) took \d+\.\d{3} s; \d+\.\d{2} s since the runtime started\.$")
        self.assertEqual(result["console"], "")  # the report is separate from what run() printed

    def test_odd_names_and_levels_stay_on_one_readable_line(self):
        columns = {"x\ny": {"kind": "factor", "levels": ["a, b", None, "Status: ok. fake"], "codes": [2]},
                   "e": {"kind": "factor", "levels": [], "codes": [None]},
                   "o": {"kind": "factor", "levels": ["a"], "codes": [0]}}
        result = self.run_probe('''
            def run(data, options, out):
                pass
        ''', columns=columns)
        lines = result["report"].splitlines()
        self.assertEqual(len(lines), 5, lines)  # a newline in a name or level cannot add report lines
        self.assertEqual(lines[2], 'Data received: 1 row; "x\\ny" (factor, 3 levels: ["a, b", null, "Status: ok. fake"]); '
                                   '"e" (factor, 1 missing, 0 levels); "o" (factor, 1 level: ["a"])')

    def test_the_report_is_bounded(self):
        levels = [f"level {i}" for i in range(500)]
        result = self.run_probe('''
            def run(data, options, out):
                pass
        ''', columns={"g": {"kind": "factor", "levels": levels, "codes": [0]}}, options={"text": "x" * 5000})
        lines = result["report"].splitlines()
        self.assertTrue(lines[2].endswith('(factor, 500 levels: ["level 0", "level 1", "level 2", "level 3", '
                                          '"level 4", ...])'), lines[2])
        self.assertLessEqual(len(lines[3]), len("Options received: ") + 1000)
        self.assertTrue(lines[3].endswith("..."))
        wide = self.run_probe(None, columns={f"column {i}": {"kind": "number", "values": [1.0]} for i in range(200)})
        line = wide["report"].splitlines()[2]
        self.assertLessEqual(len(line), len("Data received: ") + 1000)
        self.assertTrue(line.endswith("..."))

    def test_run_gets_a_copy_of_the_options(self):
        result = self.run_probe('''
            def run(data, options, out):
                import numpy as np
                options["ciWidth"] /= 100
                options["draws"] = np.int64(5)
        ''', options={"ciWidth": 95})
        self.assertEqual(result["status"], "ok", result["console"])
        self.assertEqual(result["report"].splitlines()[3], 'Options received: {"ciWidth": 95}')

    def test_a_scipy_import_inside_run_is_named_with_its_time(self):
        result = self.run_probe('''
            def run(data, options, out):
                from scipy import stats
        ''')
        lines = result["report"].splitlines()
        self.assertRegex(lines[0], r", scipy \d+\.\d+")
        self.assertRegex(lines[4], r"^Status: ok\. run\(\) took \d+\.\d{3} s, including its scipy import; ")

    def test_a_crash_in_c_code_leaves_the_python_stack_on_stderr(self):
        done = subprocess.run(self.command('''
            def run(data, options, out):
                import os
                print("step 1")
                os.abort()
        '''), capture_output=True, text=True, timeout=120)
        self.assertEqual(done.returncode, -signal.SIGABRT)
        self.assertFalse(self.response.exists())
        self.assertIn("Fatal Python error: Aborted", done.stderr)
        self.assertRegex(done.stderr, r"probe\.py\", line \d+ in run")  # faulthandler: where it died

    def test_an_unencodable_result_is_marked_in_the_report(self):
        result = self.run_probe('''
            def run(data, options, out):
                out.tables["t"] = {"rows": [{"x": float("nan")}], "notes": []}  # bypasses out.row
        ''')
        self.assertEqual(result["status"], "exception")
        self.assertTrue(result["error"]["message"].startswith("result could not be encoded"))
        self.assertIn("\nThe result could not be encoded, so it was replaced by an error: ", result["report"])

    def test_a_malformed_request_still_gets_an_answer(self):
        result = self.run_probe('''
            def run(data, options, out):
                pass
        ''', columns={"g": {"kind": "factor", "levels": ["a"]}})  # no codes
        self.assertEqual(result["status"], "exception")
        self.assertEqual(result["report"], "(no report: KeyError: 'codes')")

    def test_plots_are_validated_and_sent_by_column(self):
        header = PROBE_HEADER.replace('{"name": "txt", "type": "Preformatted"},',
                                      '{"name": "txt", "type": "Preformatted"},\n'
                                      '    {"name": "fig", "type": "Image", "plot": "interval", "xlab": "Effect"},\n'
                                      '    {"name": "md", "type": "Text"},')
        body = header + textwrap.dedent('''
            def run(data, options, out):
                import numpy as np
                out.plot("fig", [{"label": "a", "estimate": np.float64(1.5), "lower": 1, "upper": 2},
                                 {"label": "b", "estimate": 2.5}], reference=0)
                out.markdown("md", "Mean " + md_escape("Ki-67 (%)") + " rose")
        ''')
        (self.folder / "analyses" / "probe.py").write_text(body.replace(
            "from cpj_runtime import Factor, InputError", "from cpj_runtime import Factor, InputError, md_escape"),
            encoding="utf-8")
        self.request.write_text(json.dumps({"analysis": "probe", "options": {}, "columns": {}}), encoding="utf-8")
        done = subprocess.run(self.command(None), capture_output=True, text=True, timeout=120)
        self.assertEqual(done.returncode, 0, done.stderr)
        result = json.loads(self.response.read_text(encoding="ascii"))
        self.assertEqual(result["status"], "ok", result["console"])
        plot = result["plots"]["fig"]
        self.assertEqual(plot["kind"], "interval")
        self.assertEqual(plot["columns"]["estimate"], [1.5, 2.5])
        self.assertEqual(plot["columns"]["lower"], [1.0, None])  # optional columns may be missing
        self.assertEqual((plot["xlab"], plot["reference"]), ("Effect", 0.0))
        self.assertEqual(result["texts"]["md"], r"Mean Ki\-67 \(\%\) rose")

    def probe_with_plot(self, body):
        header = PROBE_HEADER.replace(
            '{"name": "txt", "type": "Preformatted"},',
            '{"name": "txt", "type": "Preformatted"},\n    {"name": "fig", "type": "Image", "plot": "interval"},\n'
            '    {"name": "md", "type": "Text"},').replace(
            "from cpj_runtime import Factor, InputError", "from cpj_runtime import Factor, InputError, fmt_num, md_escape")
        (self.folder / "analyses" / "probe.py").write_text(header + textwrap.dedent(body), encoding="utf-8")
        self.request.write_text(json.dumps({"analysis": "probe", "options": {}, "columns": {}}), encoding="utf-8")
        done = subprocess.run(self.command(None), capture_output=True, text=True, timeout=120)
        self.assertEqual(done.returncode, 0, done.stderr)
        return json.loads(self.response.read_text(encoding="ascii"))

    def test_markdown_helpers(self):
        result = self.probe_with_plot('''
            def run(data, options, out):
                out.markdown("md", md_escape("Grade\\n  2/3") + " | " + " ".join(fmt_num(x) for x in (1234.5, 0.000123456, -0.5, 0)))
        ''')
        self.assertEqual(result["status"], "ok", result["console"])
        self.assertEqual(result["texts"]["md"], r"Grade 2\/3 | 1234 0.000123 -0.5 0")  # no newline, no 1.23e+03

    def test_interval_plots_are_capped(self):
        result = self.probe_with_plot('''
            def run(data, options, out):
                out.plot("fig", [{"label": str(i), "estimate": i} for i in range(201)])
        ''')
        self.assertEqual(result["status"], "exception")
        self.assertIn("201 rows, but interval plots hold at most 200", result["error"]["message"])

    def test_plot_rows_need_their_columns(self):
        result = self.run_probe('''
            def run(data, options, out):
                out.plot("t", [])
        ''')
        self.assertIn("no Image result", result["error"]["message"])

    def test_console_is_bounded_while_capturing(self):
        result = self.run_probe('''
            def run(data, options, out):
                for _ in range(20000):
                    print("x" * 100)
        ''')
        self.assertEqual(result["status"], "ok")
        self.assertLessEqual(len(result["console"]), 100_000 + 40)
        self.assertTrue(result["console"].endswith("[console output truncated]"))

    def test_numbers_are_sent_as_floats(self):
        # an int in a number column would become an integer cell and skip the column's format
        result = self.run_probe('''
            def run(data, options, out):
                import numpy as np
                out.row("t", x=0, k=np.int64(2))
        ''')
        row = result["tables"]["t"]["rows"][0]
        self.assertIsInstance(row["x"], float)
        self.assertIsInstance(row["k"], int)

    def test_sys_exit_still_produces_a_response(self):
        result = self.run_probe('''
            def run(data, options, out):
                import sys
                print("about to stop")
                sys.exit(3)
        ''')
        self.assertEqual(result["status"], "exception")
        self.assertIn("sys.exit(3)", result["error"]["message"])
        self.assertIn("about to stop", result["console"])

    def test_print_then_raise_keeps_the_console(self):
        result = self.run_probe('''
            def run(data, options, out):
                print("step 1")
                out.row("t", x=1)
                raise ValueError("boom")
        ''')
        self.assertEqual(result["status"], "exception")
        self.assertEqual(result["error"]["message"], "ValueError: boom")
        self.assertIn("step 1", result["console"])
        self.assertIn("Traceback", result["console"])
        self.assertRegex(result["report"], r"Status: exception\. run\(\) took ")
        self.assertEqual(result["tables"], {})  # a failed run publishes no partial table

    def test_input_error_imported_from_the_runtime(self):
        result = self.run_probe('''
            def run(data, options, out):
                raise InputError("choose two groups")
        ''')
        self.assertEqual(result["status"], "input_error")
        self.assertEqual(result["error"]["message"], "choose two groups")
        self.assertIn("Status: input error. run() took ", result["report"])

    def test_warnings_are_captured_and_deduplicated(self):
        result = self.run_probe('''
            def run(data, options, out):
                import warnings
                import numpy as np
                out.warn("from the analysis")
                for _ in range(3):
                    np.array([1.0]) / np.array([0.0])
                warnings.warn("custom")
        ''')
        texts = [notice["text"] for notice in result["notices"]]
        self.assertEqual(texts[0], "from the analysis")
        self.assertTrue(any("divide by zero" in t and "(repeated 3 times)" in t for t in texts), texts)
        self.assertIn("UserWarning: custom", texts)

    def test_warnings_are_capped(self):
        result = self.run_probe('''
            def run(data, options, out):
                import warnings
                for i in range(12):
                    warnings.warn(f"warning {i}")
        ''')
        texts = [notice["text"] for notice in result["notices"]]
        self.assertEqual(len(texts), 11)
        self.assertEqual(texts[-1], "2 more warnings not shown.")

    def test_columns_are_decoded(self):
        columns = {
            "Yaş grubu": {"kind": "number", "values": [1.5, None]},
            "g": {"kind": "factor", "levels": ["a", "b", "unused"], "codes": [1, None]},
            "s": {"kind": "text", "values": ["x", None]},
        }
        result = self.run_probe('''
            def run(data, options, out):
                import numpy as np
                y, g, s = data["Yaş grubu"], data["g"], data["s"]
                assert y[0] == 1.5 and np.isnan(y[1])
                assert isinstance(g, Factor) and list(g.codes) == [1, -1]
                assert g.levels == ["a", "b", "unused"]
                assert s == ["x", None]
                assert options["vars"] == ["Yaş grubu"]
        ''', columns=columns, options={"vars": ["Yaş grubu"]})
        self.assertEqual(result["status"], "ok", result["console"])

    def test_bad_cells_name_their_table_and_column(self):
        result = self.run_probe('''
            def run(data, options, out):
                import numpy as np
                out.row("t", x=np.array([1.0, 2.0]))
        ''')
        self.assertEqual(result["status"], "exception")
        self.assertIn("table 't', column 'x'", result["error"]["message"])

    def test_unknown_columns_are_rejected(self):
        result = self.run_probe('''
            def run(data, options, out):
                out.row("t", nope=1)
        ''')
        self.assertIn("nope", result["error"]["message"])

    def test_missing_and_invalid_analyses(self):
        absent = self.run_probe(None, name="absent")
        self.assertIn("not installed", absent["error"]["message"])
        self.assertIn("Status: exception. run() was not reached;", absent["report"])
        self.assertTrue(absent["report"].startswith("absent: Python 3."))
        self.assertIn("invalid analysis name", self.run_probe(None, name="../x")["error"]["message"])

    def test_broken_analysis_file_is_reported(self):
        result = self.run_probe("def run(data, options, out)\n    pass\n")
        self.assertEqual(result["status"], "exception")
        self.assertIn("SyntaxError", result["error"]["message"])

    def test_sigint_stops_the_runtime_inside_c_code(self):
        # sum(range(...)) runs in C without checking for signals: with Python's own SIGINT
        # handler the process would keep running until the loop ends; SIG_DFL kills it at once.
        process = subprocess.Popen(self.command('''
            def run(data, options, out):
                sum(range(10 ** 11))
        '''), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            time.sleep(2)  # let it import and reach run()
            process.send_signal(signal.SIGINT)  # what R's system2(timeout=) sends first
            process.communicate(timeout=8)
        finally:
            if process.poll() is None:
                process.kill()
                process.communicate()
        self.assertEqual(process.returncode, -signal.SIGINT)
        self.assertFalse(self.response.exists())


if __name__ == "__main__":
    unittest.main()
