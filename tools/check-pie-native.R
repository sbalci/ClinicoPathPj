args<-commandArgs(TRUE)
lib<-if(length(args))args[[1]] else '/private/tmp/cpj-pie-native-library'
.libPaths(c(normalizePath(lib,mustWork=TRUE),
    '/Applications/jamovi.app/Contents/Resources/modules/base/R',.libPaths()))
suppressPackageStartupMessages({library(ClinicoPathPj);library(testthat)})
jmvcore:::initProtoBuf()
env<-new.env(parent=globalenv())
for(suffix in c('','Options','Class')) {
    name<-paste0('pyjjpiestats',suffix)
    assign(name,get(name,asNamespace('ClinicoPathPj')),env)
}
results<-lapply(c('tests/testthat/test-pie-python.R','tests/testthat/test-pie-gof-python.R'),
    function(path)testthat::test_file(path,env=env,reporter='summary'))
d<-do.call(rbind,lapply(results,as.data.frame))
summary<-list(passed=sum(d$passed),failed=sum(d$failed),errors=sum(d$error),
    warnings=sum(d$warning),skipped=sum(d$skipped))
cat(jsonlite::toJSON(summary,auto_unbox=TRUE,pretty=TRUE),'\n')
stopifnot(summary$failed==0,summary$errors==0,summary$warnings==0,summary$skipped==0)
