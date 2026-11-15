args<-commandArgs(TRUE)
.libPaths(c(normalizePath(args[[1]],mustWork=TRUE),
    '/Applications/jamovi.app/Contents/Resources/modules/base/R',.libPaths()))
suppressPackageStartupMessages(library(ClinicoPathPj))
jmvcore:::initProtoBuf()
d<-read.csv('data/python_pie_examples.csv',na.strings=c('','NA'))
d$Outcome<-factor(d$Outcome,levels=c('No','Yes','Other','Zero'))
a<-pyjjpiestats(data=d,dep='Outcome',counts='Frequency',showCases=TRUE,label='both')
stopifnot(a$cohort$asDF$total==25,a$cohort$asDF$complete==4L,
    a$cohort$asDF$excluded==2L,a$cohort$asDF$zero==1L,
    identical(a$frequencies$asDF$count,c(12,8,5,0)))
a$piePlot$saveAs(args[[2]])
stopifnot(file.exists(args[[2]]),file.info(args[[2]])$size>1000)
cat('PASS: synthetic pie with retained zero legend exported\n')
