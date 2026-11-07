# Run against a completed build; do not rebuild its library while these tests run.
# PYTHONHOME=/Applications/jamovi.app/Contents/Resources Rscript --vanilla \
#   tools/check-first-event-native.R [isolated-library-directory]
args <- commandArgs(TRUE)
lib <- if (length(args)) args[[1]] else "build/R4.6.0-arm64-macos"
.libPaths(c(normalizePath(lib, mustWork = TRUE), .libPaths()))
stopifnot(nzchar(Sys.getenv("PYTHONHOME")))
library(ClinicoPathPj)
library(testthat)

# The desktop engine normally injects this protobuf constructor. Initialize it
# only in this standalone test process so output serialization can be inspected.
jmvcore:::initProtoBuf()
if (is.null(get("RProtoBuf_new", asNamespace("jmvcore"))))
    assignInNamespace("RProtoBuf_new", RProtoBuf::new, "jmvcore")
env <- new.env(parent = globalenv())
for (name in c("pyfirstevent", "pyfirsteventClass", "pyfirsteventOptions"))
    assign(name, get(name, asNamespace("ClinicoPathPj")), env)
result <- testthat::test_file("tests/testthat/test-first-event-python.R", env = env)
rows <- as.data.frame(result)
summary <- list(passed = sum(rows$passed), failed = sum(rows$failed),
                errors = sum(rows$error), warnings = sum(rows$warning),
                skipped = sum(rows$skipped))
cat(jsonlite::toJSON(summary, auto_unbox = TRUE, pretty = TRUE), "\n")
stopifnot(summary$failed == 0, summary$errors == 0, summary$warnings == 0,
          summary$skipped == 0)
