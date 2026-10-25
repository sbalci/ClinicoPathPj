#!/bin/bash
# ClinicoPathPj checks. Run tools/build.R first: the R tests use the INSTALLED module.
#  1. Python unit tests (generator + runtime), in jamovi's bundled Python.
#  2. testthat against the installed module, in an environment like jamovi's engine:
#     empty PATH, cwd Contents/MacOS, jamovi's PYTHONHOME/PYTHONPATH and R library first.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP=/Applications/jamovi.app/Contents
RSCRIPT=/Library/Frameworks/R.framework/Versions/4.6/Resources/bin/Rscript

echo "== Python unit tests (jamovi's bundled Python)"
# The bundled standard library ships without unittest/__main__, so "-m unittest" cannot run.
(cd "$ROOT" && PYTHONHOME="$APP/Resources" "$APP/MacOS/python" -B -c '
import sys, unittest
result = unittest.main(module=None, argv=["check", "discover", "-s", "tests/python", "-v"], exit=False).result
sys.exit(not result.wasSuccessful())')

echo "== R tests against the installed module (engine-like environment)"
cd "$APP/MacOS"
# R cannot remove its temp directory with an empty PATH ("sh: rm: ..."); jamovi's engine
# behaves the same, so that one line is filtered out.
env -i HOME="$HOME" LC_CTYPE=C.UTF-8 PATH= \
    PYTHONHOME="$APP/Resources" PYTHONPATH="$APP/Resources/jamovi/server" PYTHONIOENCODING=utf-8 \
    CPJ_ROOT="$ROOT" \
    "$RSCRIPT" --vanilla -e '
        .libPaths(c(path.expand("~/Library/Application Support/jamovi/modules/ClinicoPathPj/R"),
                    "/Applications/jamovi.app/Contents/Resources/modules/base/R", .libPaths()))
        suppressPackageStartupMessages({ library(testthat); library(ClinicoPathPj) })
        testthat::test_dir(file.path(Sys.getenv("CPJ_ROOT"), "tests", "testthat"), stop_on_failure = TRUE)
    ' 2>&1 | grep -v "^sh: rm: No such file or directory$"
