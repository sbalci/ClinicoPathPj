args<-commandArgs(TRUE)
.libPaths(c(normalizePath(args[[1]],mustWork=TRUE),
    '/Applications/jamovi.app/Contents/Resources/modules/base/R',.libPaths()))
suppressPackageStartupMessages(library(ClinicoPathPj))
jmvcore:::initProtoBuf()
d<-read.csv('data/python_waffle_examples.csv',na.strings=c('','NA'))
d$Category<-factor(d$Category,levels=c('Negative','Positive','Rare'))
d$Panel<-factor(d$Panel,levels=c('Small','Large','Zero'))
a<-pyjwaffle(data=d,groups='Category',counts='Frequency',facet='Panel',show_legend=TRUE,
    mytitle='Equal tile grids; different population sizes',showCases=TRUE)
stopifnot(a$cohort$asDF$total==1004,a$cohort$asDF$complete==7L,a$cohort$asDF$excluded==2L,
    a$cohort$asDF$zero==2L,identical(a$panels$asDF$total,c(4,1000,0)),
    identical(a$allocation$asDF$count,c(1,3,0,899,100,1)),
    identical(a$allocation$asDF$tiles,c(25L,75L,0L,90L,10L,0L)))
a$wafflePlot$saveAs(args[[2]])
stopifnot(file.exists(args[[2]]),file.info(args[[2]])$size>1000)
cat('PASS: independent panel denominators and omitted rare category exported\n')
