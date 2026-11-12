# Run with PYTHONHOME=/Applications/jamovi.app/Contents/Resources Rscript --vanilla ...
# For engine-like bundled R, use tools/check.sh --r-only with CPJ_TEST_FILTER=decisioncompare-python.
args <- commandArgs(TRUE)
lib <- if(length(args))args[[1]] else 'build/R4.6.0-arm64-macos'
.libPaths(c(normalizePath(lib,mustWork=TRUE),
            '/Applications/jamovi.app/Contents/Resources/modules/base/R',.libPaths()))
suppressPackageStartupMessages({library(ClinicoPathPj);library(testthat)})
jmvcore:::initProtoBuf()
env <- new.env(parent=globalenv())
for(name in c('pydecisioncompare','pydecisioncompareOptions','pydecisioncompareClass'))
    assign(name,get(name,asNamespace('ClinicoPathPj')),env)
result <- testthat::test_file('tests/testthat/test-decisioncompare-python.R',env=env)
d<-as.data.frame(result)
summary<-list(passed=sum(d$passed),failed=sum(d$failed),errors=sum(d$error),
              warnings=sum(d$warning),skipped=sum(d$skipped))
cat(jsonlite::toJSON(summary,auto_unbox=TRUE,pretty=TRUE),'\n')
stopifnot(summary$failed==0,summary$errors==0,summary$warnings==0,summary$skipped==0)
