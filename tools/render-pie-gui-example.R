# Native rendering with the CSV's imported factor order and the GUI fixture's labels.
args<-commandArgs(TRUE)
.libPaths(c(normalizePath(args[[1]],mustWork=TRUE),
    '/Applications/jamovi.app/Contents/Resources/modules/base/R',.libPaths()))
suppressPackageStartupMessages(library(ClinicoPathPj))
jmvcore:::initProtoBuf()
d<-read.csv('data/python_pie_examples.csv',na.strings=c('','NA'))
d$Outcome<-factor(d$Outcome)
ref<-xtabs(Frequency~Outcome,d[complete.cases(d),])
a<-pyjjpiestats(data=d,dep='Outcome',counts='Frequency',showCases=TRUE,label='both',digitsperc=2)
stopifnot(identical(a$frequencies$asDF$category,names(ref)),
    identical(a$frequencies$asDF$count,as.numeric(ref)),a$cohort$asDF$total==sum(ref))
a$piePlot$saveAs(args[[2]])
stopifnot(file.exists(args[[2]]),file.info(args[[2]])$size>1000)
cat('PASS: independently checked native CSV pie exported\n')
