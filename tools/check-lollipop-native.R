args<-commandArgs(TRUE)
lib<-if(length(args))args[[1]] else '/private/tmp/cpj-lollipop-native-library'
.libPaths(c(normalizePath(lib,mustWork=TRUE),
    '/Applications/jamovi.app/Contents/Resources/modules/base/R',.libPaths()))
suppressPackageStartupMessages({library(ClinicoPathPj);library(testthat)})
jmvcore:::initProtoBuf()
env<-new.env(parent=globalenv())
for(suffix in c('','Options','Class')) {
    name<-paste0('pylollipop',suffix)
    assign(name,get(name,asNamespace('ClinicoPathPj')),env)
}
r<-as.data.frame(testthat::test_file('tests/testthat/test-lollipop-python.R',env=env,reporter='summary'))
summary<-list(passed=sum(r$passed),failed=sum(r$failed),errors=sum(r$error),warnings=sum(r$warning),skipped=sum(r$skipped))
cat(jsonlite::toJSON(summary,auto_unbox=TRUE,pretty=TRUE),'\n')
stopifnot(summary$failed==0,summary$errors==0,summary$warnings==0,summary$skipped==0)
