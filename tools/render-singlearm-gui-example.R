args<-commandArgs(TRUE)
.libPaths(c(normalizePath(args[[1]],mustWork=TRUE),'/Applications/jamovi.app/Contents/Resources/modules/base/R',.libPaths()))
suppressPackageStartupMessages(library(ClinicoPathPj));jmvcore:::initProtoBuf()
d<-read.csv('data/python_singlearm_examples.csv',na.strings=c('','NA'))
d$Status<-factor(d$Status);d$Subject<-factor(d$Subject)
a<-pysinglearm(data=d,elapsedtime='Months',outcome='Status',subject='Subject',
 outcomeLevel='Event',censorLevel='Censored',sc=TRUE,ci95=TRUE,censored=TRUE,
 person_time=TRUE,showSteps=TRUE,showCases=TRUE,showExplanations=TRUE)
stopifnot(a$cohort$asDF$complete==9,a$cohort$asDF$events==4)
if(length(args)>=4L) {
    # Match the saved Results viewport size separately from the full-size export.
    grDevices::png(args[[2]],width=as.integer(args[[3]]),height=as.integer(args[[4]]),
                   res=144,type='cairo')
    a$survivalPlot$print()
    invisible(grDevices::dev.off())
} else a$survivalPlot$saveAs(args[[2]])
stopifnot(file.exists(args[[2]]),file.info(args[[2]])$size>1000)
