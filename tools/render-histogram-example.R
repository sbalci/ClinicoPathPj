# Render the synthetic unequal-count example through the isolated native library.
args<-commandArgs(TRUE)
lib<-if(length(args))args[[1]] else '/private/tmp/cpj-histogram-native-library'
output<-if(length(args)>1)args[[2]] else '/private/tmp/cpj-histogram-example.png'
.libPaths(c(normalizePath(lib,mustWork=TRUE),
    '/Applications/jamovi.app/Contents/Resources/modules/base/R',.libPaths()))
suppressPackageStartupMessages(library(ClinicoPathPj))
jmvcore:::initProtoBuf()
d<-read.csv('data/python_histogram_examples.csv')
a<-pyjjhistostats(data=d,dep='Measurement',subject='Case',changebinwidth=TRUE,
    binwidth=2,showBins=TRUE,resultssubtitle=TRUE,centralityline=TRUE)
stopifnot(identical(a$bins$asDF$count,c(5L,7L,4L,1L,1L,1L,0L,0L,0L,1L)),
    a$cohort$asDF$retained==20L,a$cohort$asDF$excluded==2L)
a$histogramPlot$saveAs(output)
stopifnot(file.exists(output),file.info(output)$size>1000)
cat('PASS: synthetic native histogram exported to',output,'\n')
