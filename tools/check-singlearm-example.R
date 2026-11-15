# Synthetic single-cohort example; accepts an isolated R library, never installs globally.
args <- commandArgs(TRUE)
stopifnot(length(args)>=1L)
.libPaths(c(normalizePath(args[[1]],mustWork=TRUE),
    '/Applications/jamovi.app/Contents/Resources/modules/base/R',.libPaths()))
suppressPackageStartupMessages(library(ClinicoPathPj))
jmvcore:::initProtoBuf()
d <- read.csv('data/python_singlearm_examples.csv',stringsAsFactors=FALSE)
d$Status <- factor(d$Status,levels=c('Censored','Event'))
d$Subject <- factor(d$Subject)
r <- pysinglearm(data=d,elapsedtime='Months',outcome='Status',subject='Subject',
    outcomeLevel='Event',censorLevel='Censored',person_time=TRUE,showCases=TRUE,
    sc=TRUE,ci95=TRUE,censored=TRUE)
checks <- list(
    source=identical(as.numeric(r$cohort$asDF$source),11),
    complete=identical(as.numeric(r$cohort$asDF$complete),9),
    excluded=identical(as.numeric(r$cohort$asDF$excluded),2),
    events=identical(as.numeric(r$cohort$asDF$events),4),
    censored=identical(as.numeric(r$cohort$asDF$censored),5),
    medians=isTRUE(all.equal(r$medians$asDF$estimate,c(36,48))),
    horizons=isTRUE(all.equal(r$selectedTimes$asDF$time,c(12,36,60))),
    risk=isTRUE(all.equal(r$selectedTimes$asDF$risk,c(7,3,1))),
    survival=isTRUE(all.equal(r$selectedTimes$asDF$survival,c(16/21,128/315,128/315))),
    interval_events=isTRUE(all.equal(r$selectedTimes$asDF$events,c(2,2,0))),
    interval_censors=isTRUE(all.equal(r$selectedTimes$asDF$censored,c(2,1,2))),
    exposure=isTRUE(all.equal(r$personTime$asDF$exposure,216)),
    rate=isTRUE(all.equal(r$personTime$asDF$estimate,4/216)),
    subjects=identical(r$cases$asDF$subjectID,sprintf('S%02d',1:9)))
stopifnot(all(unlist(checks)))
output <- if(length(args)>=2L)args[[2]] else '/private/tmp/cpj-singlearm-synthetic.png'
r$survivalPlot$saveAs(output)
stopifnot(file.exists(output),file.info(output)$size>1000)
cat('PASS:',length(checks),'independent hand-example assertions and native PNG export.\n')
