args<-commandArgs(TRUE)
.libPaths(c(normalizePath(args[[1]],mustWork=TRUE),'/Applications/jamovi.app/Contents/Resources/modules/base/R',.libPaths()))
suppressPackageStartupMessages(library(ClinicoPathPj));jmvcore:::initProtoBuf()
d<-read.csv('data/python_waffle_examples.csv',na.strings=c('','NA'))
d$Category<-factor(d$Category);d$Panel<-factor(d$Panel)
a<-pyjwaffle(data=d,groups='Category',counts='Frequency',facet='Panel',rows=7L,flip=TRUE,
 show_legend=TRUE,mytitle='Equal grids; different populations',legendtitle='Category',showCases=TRUE,showExplanations=TRUE)
stopifnot(a$cohort$asDF$total==1004,identical(a$allocation$asDF$count,c(899,100,1,1,3,0)))
if(length(args)>=4L) {
    # Match the saved Results viewport size separately from the full-size export.
    grDevices::png(args[[2]],width=as.integer(args[[3]]),height=as.integer(args[[4]]),
                   res=144,type='cairo')
    a$wafflePlot$print()
    invisible(grDevices::dev.off())
} else a$wafflePlot$saveAs(args[[2]])
stopifnot(file.exists(args[[2]]),file.info(args[[2]])$size>1000)
