# Run only after the build finishes; an optional library path selects an isolated copy.
args <- commandArgs(TRUE)
lib <- if (length(args)) args[[1]] else "build/R4.6.0-arm64-macos"
.libPaths(c(normalizePath(lib, mustWork=TRUE),.libPaths()))
stopifnot(nzchar(Sys.getenv("PYTHONHOME")))
library(ClinicoPathPj)
library(testthat)
env <- new.env(parent=globalenv())
for (name in c("pydiagnosticmeta","pydiagnosticmetaClass","pydiagnosticmetaOptions"))
    assign(name,get(name,asNamespace("ClinicoPathPj")),env)
result <- testthat::test_file("tests/testthat/test-diagnostic-studies-python.R",env=env)
d <- as.data.frame(result)
summary <- list(passed=sum(d$passed),failed=sum(d$failed),errors=sum(d$error),
                warnings=sum(d$warning),skipped=sum(d$skipped))
cat(jsonlite::toJSON(summary,auto_unbox=TRUE,pretty=TRUE),"\n")
stopifnot(summary$failed==0,summary$errors==0,summary$warnings==0,summary$skipped==0)
