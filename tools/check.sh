#!/bin/bash
# ClinicoPathPj checks. Run tools/build.R first: the R tests use the INSTALLED module.
#  1. Python unit tests (generator + runtime), in jamovi's bundled Python.
#  2. testthat against the installed module, in an environment like jamovi's engine:
#     empty PATH, cwd Contents/MacOS, jamovi's PYTHONHOME/PYTHONPATH and R library first.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP=/Applications/jamovi.app/Contents
R_HOME="$APP/Frameworks/R.framework/Resources"
R_EXEC="$R_HOME/bin/exec/R"
# Optional local oracle/test dependencies; these are not bundled-module qualification.
CPJ_TEST_LIBRARY="${CPJ_TEST_LIBRARY:-/Library/Frameworks/R.framework/Versions/4.6/Resources/library}"
CPJ_LIBRARY="${CPJ_LIBRARY:-$HOME/Library/Application Support/jamovi/modules/ClinicoPathPj/R}"
if [[ ! -f "$CPJ_LIBRARY/ClinicoPathPj/DESCRIPTION" ]]; then
    echo "No installed ClinicoPathPj package in CPJ_LIBRARY=$CPJ_LIBRARY" >&2
    exit 2
fi

if [[ "${1:-}" != "--r-only" ]]; then
echo "== Python unit tests (jamovi's bundled Python)"
# The bundled standard library ships without unittest/__main__, so "-m unittest" cannot run.
(cd "$ROOT" && PYTHONHOME="$APP/Resources" "$APP/MacOS/python" -B -c '
import sys, unittest
result = unittest.main(module=None, argv=["check", "discover", "-s", "tests/python", "-v"], exit=False).result
sys.exit(not result.wasSuccessful())')
fi

echo "== R tests against the installed module (engine-like environment)"
cd "$APP/MacOS"
# R cannot remove its temp directory with an empty PATH ("sh: rm: ..."); jamovi's engine
# behaves the same, so that one line is filtered out.
env -i HOME="$HOME" LC_CTYPE=C.UTF-8 PATH= \
    R_HOME="$R_HOME" DYLD_LIBRARY_PATH="$R_HOME/lib" \
    PYTHONHOME="$APP/Resources" PYTHONPATH="$APP/Resources/jamovi/server" PYTHONIOENCODING=utf-8 \
    CPJ_ROOT="$ROOT" \
    CPJ_TEST_LIBRARY="$CPJ_TEST_LIBRARY" \
    CPJ_TEST_FILTER="${CPJ_TEST_FILTER:-.*}" \
    CPJ_LIBRARY="$CPJ_LIBRARY" \
    "$R_EXEC" --vanilla --slave -e '
        .libPaths(c(Sys.getenv("CPJ_LIBRARY"),
                    "/Applications/jamovi.app/Contents/Resources/modules/base/R", .libPaths(),
                    Sys.getenv("CPJ_TEST_LIBRARY")))
        suppressPackageStartupMessages({ library(testthat); library(ClinicoPathPj) })
        cat("R home:", R.home(), "\n")
        jmvcore:::initProtoBuf()
        expected <- read.dcf(file.path(Sys.getenv("CPJ_ROOT"), "DESCRIPTION"))[1, "Version"]
        if (as.character(packageVersion("ClinicoPathPj")) != expected)
            stop("The test package version does not match the source DESCRIPTION")
        testthat::test_dir(file.path(Sys.getenv("CPJ_ROOT"), "tests", "testthat"),
                          filter = Sys.getenv("CPJ_TEST_FILTER", unset = ".*"),
                          stop_on_failure = TRUE)
    ' 2>&1 | grep -v "^sh: rm: No such file or directory$"
