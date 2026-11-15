args<-commandArgs(TRUE)
.libPaths(c(args[[1]],'/Applications/jamovi.app/Contents/Resources/modules/base/R',.libPaths()))
suppressPackageStartupMessages(library(ClinicoPathPj));jmvcore:::initProtoBuf()
d<-read.csv('data/python_lollipop_examples.csv',na.strings=c('','NA'));d$Category<-factor(d$Category)
clean<-d[complete.cases(d),];ref<-aggregate(clean$Value,list(Category=clean$Category),sum)
ref<-ref[order(-ref$x),]
r<-pylollipop(data=d,dep='Value',group='Category',aggregation='sum',sortBy='value_desc',
    orientation='horizontal',showMean=TRUE,showValues=TRUE,showCases=TRUE)
stopifnot(identical(r$points$asDF$category,as.character(ref$Category)),
    isTRUE(all.equal(r$points$asDF$value,ref$x)),
    abs(r$descriptives$asDF$mean[1]-mean(clean$Value))<1e-12,
    abs(r$descriptives$asDF$mean[2]-mean(ref$x))<1e-12,
    identical(r$cases$asDF$sourceID,rownames(clean)))
r$lollipopPlot$saveAs(args[[2]])
stopifnot(file.exists(args[[2]]),file.info(args[[2]])$size>1000)
cat('PASS: native CSV values agree with independent R; reference PNG exported.\n')
