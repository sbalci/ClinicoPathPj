args<-commandArgs(TRUE)
lib<-if(length(args))args[[1]] else '/private/tmp/cpj-standardized-native-library'
.libPaths(c(normalizePath(lib,mustWork=TRUE),
 '/Applications/jamovi.app/Contents/Resources/modules/base/R',.libPaths()))
suppressPackageStartupMessages({library(ClinicoPathPj);library(testthat)})
jmvcore:::initProtoBuf()
env<-new.env(parent=globalenv())
for(prefix in c('pyjjbetweenstats','pyjjwithinstats'))for(suffix in c('','Options','Class')) {
 name<-paste0(prefix,suffix);assign(name,get(name,asNamespace('ClinicoPathPj')),env)
}
file<-if(length(args)>1)args[[2]] else 'tests/testthat/test-standardized-python.R'
result<-testthat::test_file(file,env=env)
d<-as.data.frame(result)
summary<-list(passed=sum(d$passed),failed=sum(d$failed),errors=sum(d$error),
 warnings=sum(d$warning),skipped=sum(d$skipped))
cat(jsonlite::toJSON(summary,auto_unbox=TRUE,pretty=TRUE),'\n')
stopifnot(summary$failed==0,summary$errors==0,summary$warnings==0,summary$skipped==0)
