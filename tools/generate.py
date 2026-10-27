"""Generate the jamovi files of every ClinicoPathPj analysis from its Python file.

Each registered family source holds one literal SPEC dict and a run() function.
SPEC is read with ast (the analysis is never imported), validated, and written out as
jamovi/<name>.a.yaml, .r.yaml, .u.yaml (JSON, which is valid YAML) and R/<name>.b.R.
jmvtools creates R/<name>.h.R on the next build.

    python tools/generate.py           write the generated files
    python tools/generate.py --check   write nothing; exit 1 when any generated file is stale
"""
import ast
import copy
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANALYSES = ROOT / "inst" / "python" / "analyses"
sys.path.insert(0, str(ANALYSES.parent))
from cpj_registry import read_registry

ANALYSIS_NAME = re.compile(r"[a-z][A-Za-z0-9]*\Z")
NAME = re.compile(r"[a-z][A-Za-z0-9_]*\Z")
VERSION = re.compile(r"\d+\.\d+\.\d+\Z")
RESERVED = {"data", "showConsole", "console"}
# Names jmvtools turns into R formals and R6 members: an R keyword does not parse, and a member of
# jmvcore's Options (for options) or Group/ResultsElement (for results) breaks the analysis in jamovi.
R_WORDS = {"if", "else", "repeat", "while", "function", "for", "in", "next", "break", "TRUE", "FALSE",
           "NULL", "NA", "Inf", "NaN"}
OPTION_MEMBERS = {"analysis", "asProtoBuf", "check", "clone", "compProtoBuf", "decSymbol", "eval",
                  "fromJSON", "fromProtoBuf", "get", "gtg", "has", "initialize", "levels", "names", "option",
                  "options", "palette", "ppi", "read", "requiresData", "theme", "translate", "values",
                  "varsRequired"}
RESULT_MEMBERS = {"add", "analysis", "asDF", "asProtoBuf", "asString", "clear", "clone", "fromProtoBuf", "get",
                  "getBoundVars", "getRefs", "index", "initialize", "insert", "isFilled", "isNotFilled",
                  "itemNames", "items", "key", "name", "options", "parent", "path", "print", "remove",
                  "requiresData", "resetVisible", "root", "saveAs", "setError", "setRefs", "setState",
                  "setStatus", "setTitle", "setVisible", "state", "status", "title", "visible"}
SPEC_KEYS = {"name", "title", "menuGroup", "menuSubgroup", "version", "options", "results", "ui", "executionOption", "timingResult"}
OPTION_KEYS = {  # keys an option may carry besides name/type/title
    "Variable": {"permitted", "suggested", "required", "coerceNumeric"},
    "Variables": {"permitted", "suggested", "required", "coerceNumeric"},
    "Level": {"variable", "allowNone", "role"},
    "Number": {"default", "min", "max"},
    "Integer": {"default", "min", "max"},
    "Bool": {"default"},
    "List": {"options", "default"},
    "String": {"default"},
    "Terms": {"default"},
    "Action": {"action"},
    "Output": set(),
}
PERMITTED = {"numeric", "factor", "id"}
SUGGESTED = {"continuous", "nominal", "ordinal", "id"}
COLUMN_KEYS = {"name", "title", "type", "format", "superTitle", "visible"}
COLUMN_TYPES = {"text", "integer", "number"}
FORMAT_TOKENS = {"zto", "pvalue", "pc", "log10"}
PLOT_KINDS = {"interval", "line", "box", "bar", "scatter", "points", "histogram", "pyramid", "qualitymap", "ihcheatmap", "dendrogram"}
IMAGE_KEYS = {"name", "type", "title", "plot", "width", "height", "xlab", "ylab", "visible"}


class SpecError(Exception):
    pass


def read_spec(path):
    """Return the literal SPEC of an analysis file without executing it."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    nodes = [node.value for node in tree.body
             if isinstance(node, ast.Assign) and len(node.targets) == 1
             and isinstance(node.targets[0], ast.Name) and node.targets[0].id == "SPEC"]
    if len(nodes) != 1:
        raise SpecError(f"{path.name}: expected exactly one top-level 'SPEC = {{...}}', found {len(nodes)}")
    for node in ast.walk(nodes[0]):  # literal_eval silently keeps the last of two equal keys
        if isinstance(node, ast.Dict):
            keys = [key.value for key in node.keys if isinstance(key, ast.Constant)]
            duplicates = sorted({key for key in keys if keys.count(key) > 1}, key=str)
            if duplicates:
                raise SpecError(f"{path.name}: duplicate key(s) {duplicates} in SPEC")
    try:
        return ast.literal_eval(nodes[0])
    except ValueError as error:
        raise SpecError(f"{path.name}: SPEC must be a plain literal ({error})") from None


def validate(spec, stem):
    where = f"{stem}.py"

    def fail(message):
        raise SpecError(f"{where}: {message}")

    def check_name(value, what, pattern=NAME, members=frozenset()):
        if not isinstance(value, str) or not pattern.match(value):
            fail(f"{what} {value!r} must match {pattern.pattern}")
        if value in RESERVED or value.startswith("cpjNotice") or value in R_WORDS or value in members:
            fail(f"{what} {value!r} is reserved (by ClinicoPathPj, R or jmvcore)")

    def check_text(text, what, evaluated=False):
        # The compiler pastes titles into R strings, and jamovi translates them (a trailing
        # " [word]" is cut as a context); result titles are also evaluated by jmvcore.
        if not isinstance(text, str):
            fail(f"{what} must be a string")
        if any(ord(c) < 32 or ord(c) == 127 or 0xD800 <= ord(c) <= 0xDFFF for c in text) or '"' in text or "\\" in text:
            fail(f"{what} {text!r} must not contain quotes, backslashes or control characters")
        if re.search(r" \[[a-z]+\]$", text):
            fail(f"{what} {text!r} must not end in ' [word]' (jamovi reads it as a translation context)")
        if evaluated and (re.search(r"[{}`]", text) or re.fullmatch(r"\(.*\)", text)):
            fail(f"{what} {text!r} must not contain {{, }}, backticks or be wrapped in parentheses")

    def check_title(item, what, evaluated=False):
        check_text(item.get("title"), f"{what} title", evaluated)

    if not isinstance(spec, dict):
        fail("SPEC must be a dict")
    unknown = set(spec) - SPEC_KEYS
    missing = SPEC_KEYS - {"menuSubgroup", "ui", "executionOption", "timingResult"} - set(spec)
    if unknown or missing:
        fail(f"SPEC keys: unknown {sorted(unknown)}, missing {sorted(missing)}")
    check_name(spec["name"], "analysis name", ANALYSIS_NAME)
    for key in ("title", "menuGroup") + (("menuSubgroup",) if "menuSubgroup" in spec else ()):
        check_text(spec[key], key)
        if not spec[key].strip():
            fail(f"{key} must not be empty")
    if not isinstance(spec["version"], str) or not VERSION.match(spec["version"]):
        fail("version must look like '0.1.0'")
    if not isinstance(spec["options"], list) or not isinstance(spec["results"], list):
        fail("options and results must be lists")

    names, variables, seen_other = set(), {}, False
    for option in spec["options"]:
        if not isinstance(option, dict):
            fail("every option must be a dict")
        kind = option.get("type")
        if kind not in OPTION_KEYS:
            fail(f"option type {kind!r} is not supported (use {sorted(OPTION_KEYS)})")
        check_name(option.get("name"), "option name", members=OPTION_MEMBERS)
        name = option["name"]
        check_title(option, f"option {name!r}")
        if name in names:
            fail(f"option {name!r} is defined twice")
        names.add(name)
        extra = set(option) - {"name", "type", "title"} - OPTION_KEYS[kind]
        if extra:
            fail(f"option {name!r} ({kind}) does not support {sorted(extra)}")
        if kind in ("Variable", "Variables"):
            if seen_other:  # jmvtools would open a second variable list for it
                fail(f"variable option {name!r} must come before all other options")
            variables[name] = kind
            if not set(option.get("permitted", [])) <= PERMITTED:
                fail(f"option {name!r}: permitted must be a subset of {sorted(PERMITTED)}")
            if "id" in option.get("permitted", []) and "factor" not in option["permitted"]:
                fail(f"option {name!r}: 'id' needs 'factor' in permitted too (jmvcore checks it as numeric otherwise)")
            if not set(option.get("suggested", [])) <= SUGGESTED:
                fail(f"option {name!r}: suggested must be a subset of {sorted(SUGGESTED)}")
            if not isinstance(option.get("required", False), bool):
                fail(f"option {name!r}: required must be True or False")
        else:
            seen_other = True
        if kind == "Level":
            match = re.fullmatch(r"\(([a-z][A-Za-z0-9_]*)\)", str(option.get("variable", "")))
            if not match or variables.get(match.group(1)) != "Variable":
                fail(f"Level {name!r} needs variable: '(x)' naming an earlier single Variable option")
            if not isinstance(option.get("allowNone", False), bool):
                fail(f"Level {name!r}: allowNone must be True or False")
            if option.get("role", "event") != "event":
                fail(f"Level {name!r}: role must be 'event' (the user must choose it; nothing is preselected)")
        if "coerceNumeric" in option:
            if not isinstance(option["coerceNumeric"], bool) or "numeric" not in option.get("permitted", []):
                fail(f"{kind} {name!r}: coerceNumeric requires a boolean and permitted numeric input")
        if kind in ("Number", "Integer"):
            numbers = (int,) if kind == "Integer" else (int, float)
            values = [option.get("default")] + [option[key] for key in ("min", "max") if key in option]
            if any(isinstance(v, bool) or not isinstance(v, numbers) or not math.isfinite(v) for v in values):
                fail(f"{kind} {name!r} needs a finite {'whole-number ' if kind == 'Integer' else ''}default and finite supplied bounds")
            if not option.get("min", -math.inf) <= option["default"] <= option.get("max", math.inf):
                fail(f"{kind} {name!r}: default must lie between min and max")
        if kind == "Bool" and not isinstance(option.get("default"), bool):
            fail(f"Bool {name!r} needs default True or False")
        if kind == "List":
            choices = option.get("options")
            if not isinstance(choices, list) or len(choices) < 2:
                fail(f"List {name!r} needs at least two options")
            seen_choices = set()
            for choice in choices:
                if not isinstance(choice, dict) or set(choice) != {"name", "title"}:
                    fail(f"List {name!r}: each option is {{'name': ..., 'title': ...}}")
                if not isinstance(choice["name"], str) or not re.fullmatch(r"[A-Za-z0-9_]+", choice["name"]) \
                        or choice["name"] in seen_choices:
                    fail(f"List {name!r}: option name {choice['name']!r} is invalid or repeated")
                seen_choices.add(choice["name"])
                check_text(choice["title"], f"List {name!r} option title")
            if option.get("default") not in seen_choices:
                fail(f"List {name!r}: default must be one of {sorted(seen_choices)}")
        if kind == "String":
            check_text(option.get("default"), f"String {name!r} default")
        if kind == "Terms":
            value = option.get("default", [])
            if not isinstance(value, list) or any(not isinstance(t, list) or not t or
                    any(not isinstance(v, str) or not v for v in t) for t in value):
                fail(f"Terms {name!r}: default must be a list of non-empty lists of variable names")
        if kind == "Action" and option.get("action") not in ("open", "openExternal"):
            fail(f"Action {name!r}: action must be open or openExternal")

    validate_ui(spec)
    if not spec["results"]:
        fail("SPEC needs at least one result")
    bools = {o["name"] for o in spec["options"] if o["type"] == "Bool"}
    results = set()
    for result in spec["results"]:
        if not isinstance(result, dict):
            fail("every result must be a dict")
        check_name(result.get("name"), "result name", members=RESULT_MEMBERS)
        rname = result["name"]
        check_title(result, f"result {rname!r}", evaluated=True)
        if rname in results or (rname in names and result.get("type") != "Output"):
            fail(f"result name {rname!r} is already used")
        results.add(rname)
        if result.get("type") == "Output":
            if not any(o["name"] == rname and o["type"] == "Output" for o in spec["options"]):
                fail(f"Output {rname!r} needs an Output option with the same name")
            if set(result) - {"name", "type", "title", "varTitle", "varDescription", "measureType"}:
                fail(f"Output {rname!r}: unsupported properties")
            if result.get("measureType") not in ("continuous", "nominal", "ordinal"):
                fail(f"Output {rname!r}: choose continuous, nominal or ordinal")
            for key in ("varTitle", "varDescription"):
                if key in result: check_text(result[key], key)
            continue
        if "visible" in result:  # one Bool or the conjunction of two Bool options
            match = re.fullmatch(r"\(([a-z][A-Za-z0-9_]*)(?: && ([a-z][A-Za-z0-9_]*))?\)", str(result["visible"]))
            if not match or any(name not in bools for name in match.groups() if name is not None):
                fail(f"result {rname!r}: visible must be '(x)' naming a Bool option or '(x && y)' naming Bool options")
        if result.get("type") in ("Preformatted", "Text", "Html", "Svg"):
            allowed = {"name", "type", "title", "visible"}
            if result["type"] == "Svg":
                allowed.add("scripts")
                scripts = result.get("scripts", [])
                if not isinstance(scripts, list) or not all(isinstance(s, str) for s in scripts) or len(scripts) != len(set(scripts)):
                    fail("Svg scripts must be a list of unique local JavaScript paths")
                for script in scripts:
                    if not isinstance(script, str) or not re.fullmatch(r"js/[A-Za-z0-9_/-]+\.js", script) or \
                            ".." in Path(script).parts or not (ROOT / "inst" / script).is_file():
                        fail("Svg scripts must exist under inst/js with safe local paths")
            if set(result) - allowed:
                fail(f"{result['type']} {rname!r} takes only name, type, title and visible")
            continue
        if result.get("type") == "Image":
            if set(result) - IMAGE_KEYS:
                fail(f"Image {rname!r} takes only {sorted(IMAGE_KEYS)}")
            if result.get("plot") not in PLOT_KINDS:
                fail(f"Image {rname!r}: plot must be one of {sorted(PLOT_KINDS)}")
            for key in ("width", "height"):
                value = result.get(key, 500 if key == "width" else 400)
                if isinstance(value, bool) or not isinstance(value, int) or not 200 <= value <= 2000:
                    fail(f"Image {rname!r}: {key} must be a whole number of pixels between 200 and 2000")
            for key in ("xlab", "ylab"):
                if key in result:
                    check_text(result[key], f"Image {rname!r} {key}")
            continue
        if result.get("type") != "Table":
            fail(f"result {rname!r}: type must be 'Table', 'Image', 'Html', 'Text' or 'Preformatted'")
        if set(result) - {"name", "type", "title", "columns", "visible"} or not result.get("columns"):
            fail(f"Table {rname!r} takes name, type, title, visible and a non-empty columns list")
        columns = set()
        for column in result["columns"]:
            if not isinstance(column, dict) or set(column) - COLUMN_KEYS:
                fail(f"Table {rname!r}: a column may only have {sorted(COLUMN_KEYS)}")
            cname = column.get("name")
            if not isinstance(cname, str) or not NAME.match(cname) or cname in columns:
                fail(f"Table {rname!r}: column name {cname!r} is invalid or repeated")
            columns.add(cname)
            check_title(column, f"column {rname}.{cname}")
            if column.get("type") not in COLUMN_TYPES:
                fail(f"column {rname}.{cname}: type must be one of {sorted(COLUMN_TYPES)}")
            if "format" in column:  # jamovi drops unknown tokens silently, so refuse them here
                tokens = str(column["format"]).split(",")
                if not set(tokens) <= FORMAT_TOKENS:
                    fail(f"column {rname}.{cname}: format must be comma-separated {sorted(FORMAT_TOKENS)}")
            if "superTitle" in column:
                check_text(column["superTitle"], f"column {rname}.{cname} superTitle")
            # False keeps an exact value next to a formatted text column: sent with the results but not
            # shown, and left out of asDF (jmvcore skips hidden columns; read it with table$columns$<name>)
            if "visible" in column:
                shown = column["visible"]
                match = re.fullmatch(r"\(([a-z][A-Za-z0-9_]*)\)", shown) if isinstance(shown, str) else None
                if not (isinstance(shown, bool) or (match and match.group(1) in bools)):
                    fail(f"column {rname}.{cname}: visible must be True, False or '(x)' naming a Bool option")


    if "executionOption" in spec:
        route = next((o for o in spec["options"] if o["name"] == spec["executionOption"]), {})
        if route.get("type") != "List" or {o["name"] for o in route.get("options", [])} != {"processx", "pj", "pjSystem"}:
            fail("executionOption must name a List selecting processx, pj and pjSystem")
    if "timingResult" in spec:
        result = next((r for r in spec["results"] if r["name"] == spec["timingResult"]), {})
        if result.get("type") != "Preformatted":
            fail("timingResult must name a Preformatted result")


def validate_ui(spec):
    """Check bindings and completeness before asking the real compiler to validate controls."""
    if "ui" not in spec:
        return
    ui = spec["ui"]
    if not isinstance(ui, dict) or set(ui) != {"children"} or not isinstance(ui["children"], list):
        raise SpecError("ui must contain a children list")
    options = {o["name"]: o for o in spec["options"]}
    options["showConsole"] = {"type": "Bool"}
    bindings, controls = set(), set()
    containers = {"VariableSupplier", "Supplier", "CollapseBox", "Label", "LayoutBox", "TargetLayoutBox"}
    types = {"Variable": {"VariablesListBox"}, "Variables": {"VariablesListBox"},
             "Level": {"LevelSelector"}, "Number": {"TextBox"}, "Integer": {"TextBox"},
             "String": {"TextBox"}, "Bool": {"CheckBox"}, "List": {"ComboBox", "RadioButton"},
             "Output": {"Output"}, "Terms": {"ListBox"}, "Action": {"ActionButton"}}

    def visit(children):
        for control in children:
            if not isinstance(control, dict) or "type" not in control:
                raise SpecError("Every UI control needs a type")
            name = control.get("name")
            if name:
                if name in controls:
                    raise SpecError(f"Duplicate UI control {name!r}")
                controls.add(name)
            if control["type"] not in containers:
                binding = control.get("optionName", name)
                if binding not in options:
                    raise SpecError(f"Unbound UI control {binding!r}")
                if control["type"] not in types[options[binding]["type"]]:
                    raise SpecError(f"Wrong UI type for {binding!r}")
                if binding in bindings and "optionPart" not in control:
                    raise SpecError(f"Repeated UI binding {binding!r}")
                bindings.add(binding)
            if "enable" in control:
                expression = control["enable"]
                if not isinstance(expression, str) or not re.fullmatch(r"[()!&|: A-Za-z0-9_]+", expression):
                    raise SpecError("Invalid UI enable expression")
                for reference in re.findall(r"(?<![A-Za-z0-9_:])[A-Za-z][A-Za-z0-9_]*", expression):
                    if reference not in options:
                        raise SpecError(f"UI enable references unknown option {reference!r}")
            if "children" in control:
                visit(control["children"])
    visit(ui["children"])
    if bindings != set(options):
        raise SpecError(f"UI omits options {sorted(set(options) - bindings)}")


def u_yaml(spec):
    validate_ui(spec)
    if "ui" not in spec:
        raise SpecError(f"{spec['name']}: explicit ui is required for generation")
    return dict(name=spec["name"], title=spec["title"], jus="3.0", stage=0,
                compilerMode="tame", children=copy.deepcopy(spec["ui"]["children"]))


def a_yaml(spec):
    options = [{"name": "data", "type": "Data"}]
    for option in spec["options"]:
        out = {"name": option["name"], "title": option["title"], "type": option["type"]}
        # required stays out of the .a.yaml: jamovi would skip .run() while the box is empty,
        # and the bridge reports partly filled boxes instead (generated .b.R, required = ...).
        out.update((k, v) for k, v in option.items() if k not in ("name", "title", "type", "required", "role", "coerceNumeric"))
        if option["type"] in ("Variable", "Variables"):
            out["default"] = None  # optional wrapper argument
        if option.get("role") == "event":
            out["allowNone"] = True  # the dropdown starts at '- None -': an event level is never guessed
        options.append(out)
    options.append({"name": "showConsole", "title": "Python console output", "type": "Bool", "default": False})
    head = {key: spec[key] for key in ("name", "title", "menuGroup", "menuSubgroup", "menuTitle", "version") if key in spec}
    return dict(head, jas="1.2", options=options)


def r_yaml(spec):
    items = []
    for result in spec["results"]:
        item = {"name": result["name"], "title": result["title"], "type": result["type"]}
        if "visible" in result:
            item["visible"] = result["visible"]
        if result["type"] == "Table":
            item["rows"] = 0
            item["columns"] = [dict(column) for column in result["columns"]]
        if result["type"] == "Image":  # the renderer reads only image$state, never self$data
            item.update(width=result.get("width", 500), height=result.get("height", 400),
                        renderFun=".plot", requiresData=False)
        if result["type"] == "Output":
            item.update({key: result[key] for key in ("varTitle", "varDescription", "measureType") if key in result})
            item["clearWith"] = [o["name"] for o in spec["options"]]
        items.append(item)
    items.append({"name": "console", "title": "Python console", "type": "Preformatted",
                  "visible": "(showConsole)"})
    return {"name": spec["name"], "title": spec["title"], "jrs": "1.1", "items": items}


def r_string(value):
    return json.dumps(value, ensure_ascii=True)  # a JSON string literal is also a valid R one


def b_r(spec, header):
    name = spec["name"]
    options = [option["name"] for option in spec["options"]]
    arrays = [option["name"] for option in spec["options"] if option["type"] == "Variables"]
    terms = [option["name"] for option in spec["options"] if option["type"] == "Terms"]
    # jamovi lets integer Nominal/Ordinal columns into numeric-only boxes as factors carrying their
    # values; the bridge converts the columns of these options back to numbers.
    numeric = [option["name"] for option in spec["options"] if option["type"] in ("Variable", "Variables")
               and (option.get("coerceNumeric", False) or (option.get("permitted") and "factor" not in option["permitted"]))]
    required = [option for option in spec["options"] if option.get("required")]
    events = [option for option in spec["options"] if option.get("role") == "event"]
    plots = any(result["type"] == "Image" for result in spec["results"])

    def vector(items):
        items = list(items)
        return "c(" + ", ".join(items) + ")" if items else "character(0)"

    execution = (f"                backend = self$options${spec['executionOption']},\n" if "executionOption" in spec else "")
    timing = (f"                timing = {r_string(spec['timingResult'])},\n" if "timingResult" in spec else "")
    plot_method = (",\n        .plot = function(image, ggtheme, theme, ...) .cpjPlot(image, ggtheme, theme)"
                   if plots else "")
    scripts = "".join(
        f"            self$results${result['name']}$setScripts({vector(r_string(s) for s in result.get('scripts', []))})\n"
        for result in spec["results"] if result["type"] == "Svg")
    return (
        f"# {header}\n\n"
        f"{name}Class <- R6::R6Class(\n"
        f"    \"{name}Class\",\n"
        f"    inherit = {name}Base,\n"
        f"    private = list(\n"
        + (f"        .init = function() {{\n{scripts}        }},\n" if scripts else "")
        + f"        .run = function() {{\n"
        f"{scripts}"
        f"            .cpjRun(self, \"{name}\",\n"
        f"{execution}{timing}"
        f"                options = {vector(r_string(o) for o in options)},\n"
        f"                arrays = {vector(r_string(o) for o in arrays)},\n"
        f"                terms = {vector(r_string(o) for o in terms)},\n"
        f"                numeric = {vector(r_string(o) for o in numeric)},\n"
        f"                required = {vector(o['name'] + ' = ' + r_string(o['title']) for o in required)},\n"
        f"                events = {vector(o['name'] + ' = ' + r_string(o['variable'][1:-1]) for o in events)},\n"
        f"                checkpoint = function() private$.checkpoint(flush = FALSE))\n"
        f"        }}{plot_method}\n"
        f"    )\n"
        f")\n"
    )


def render(path):
    """Return {output path: content} for one analysis file."""
    spec = read_spec(path)
    validate(spec, path.stem)
    header = f"Generated by tools/generate.py from {path.relative_to(ROOT)} - do not edit."

    def as_yaml(obj):
        return f"# {header}\n" + json.dumps(obj, indent=2, ensure_ascii=True, allow_nan=False) + "\n"

    entry = next((e for e in read_registry(ANALYSES.parent)["analyses"]
                  if e["id"] == spec["name"]), None)
    if entry is None or entry.get("source") != str(path.relative_to(ANALYSES.parent)):
        raise SpecError(f"{path.name}: source/name must agree with the registry")
    files = {}
    for name in [entry["id"]] + entry.get("aliases", []):
        variant = copy.deepcopy(spec)
        variant["name"] = name
        if spec["menuGroup"] != entry["menu_group"] or spec.get("menuSubgroup") != entry["menu"]:
            raise SpecError(f"{spec['name']}: menu routing must agree with the registry")
        variant["menuTitle"] = entry.get("menu_title", entry["title"])
        if name != entry["id"]:
            variant["title"] = entry["legacy_title"]
        files.update({
            ROOT / "jamovi" / f"{name}.a.yaml": as_yaml(a_yaml(variant)),
            ROOT / "jamovi" / f"{name}.r.yaml": as_yaml(r_yaml(variant)),
            ROOT / "jamovi" / f"{name}.u.yaml": as_yaml(u_yaml(variant)),
            ROOT / "R" / f"{name}.b.R": b_r(variant, header),
        })
    return files


def main(argv):
    check = "--check" in argv
    files = {}
    try:
        entries = read_registry(ANALYSES.parent)["analyses"]
        registered = {ANALYSES.parent / e["source"] for e in entries if e.get("source")}
        discovered = set(ANALYSES.rglob("*.py"))
        if registered != discovered:
            raise SpecError("Analysis sources must match registry entries exactly")
        for path in sorted(registered):
            rendered = render(path)
            if files.keys() & rendered.keys():
                raise SpecError("Duplicate generated entry point")
            files.update(rendered)  # validate everything before writing anything
    except (SpecError, ValueError) as error:
        print(f"generate.py: {error}", file=sys.stderr)
        return 2
    stale = [path for path, text in files.items()
             if not path.exists() or path.read_text(encoding="utf-8") != text]
    if check:
        for path in stale:
            print(f"stale: {path.relative_to(ROOT)}", file=sys.stderr)
        return 1 if stale else 0
    for path in stale:
        path.write_text(files[path], encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")
    print(f"{len(files) // 4} entry points, {len(stale)} file(s) updated")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
