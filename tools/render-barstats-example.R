# Export an independently checked synthetic example through the native image bridge.
args <- commandArgs(TRUE)
.libPaths(c(normalizePath(args[[1]],mustWork=TRUE),
    '/Applications/jamovi.app/Contents/Resources/modules/base/R',.libPaths()))
suppressPackageStartupMessages(library(ClinicoPathPj))
jmvcore:::initProtoBuf()
d <- read.csv('data/python_barstats_examples.csv',na.strings=c('', 'NA'))
d$Outcome <- factor(d$Outcome,levels=c('No','Yes'))
d$Group <- factor(d$Group,levels=c('Control','Treatment'))
a <- pyjjbarstats(data=d,dep='Outcome',group='Group',counts='Frequency',
    resultssubtitle=TRUE,showCases=TRUE,barScale='count',label='both')
stopifnot(a$cohort$asDF$total==50,identical(a$groups$asDF$total,c(20,30)))
a$barPlot$saveAs(args[[2]])
stopifnot(file.exists(args[[2]]),file.info(args[[2]])$size>1000)
cat('PASS: native categorical count plot exported\n')
