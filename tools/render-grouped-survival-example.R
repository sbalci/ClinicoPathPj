# Native synthetic example; use the built/installed library supplied by the caller.
args <- commandArgs(TRUE)
.libPaths(c(normalizePath(args[[1]],mustWork=TRUE),'/Applications/jamovi.app/Contents/Resources/modules/base/R',.libPaths()))
suppressPackageStartupMessages(library(ClinicoPathPj));jmvcore:::initProtoBuf()
d <- read.csv('data/python_grouped_survival_examples.csv',na.strings='')
d$Status <- factor(d$Status);d$Subject <- factor(d$Subject);d$Group <- factor(d$Group)
a <- pysurvival(data=d,elapsedtime='Months',outcome='Status',explanatory='Group',subject='Subject',
    outcomeLevel='Event',censorLevel='Censored',sc=TRUE,ci95=TRUE,censored=TRUE,
    showSteps=TRUE,showCases=TRUE,showExplanations=TRUE)
ref <- jsonlite::fromJSON(system2('Rscript',c('--vanilla','tests/reference/grouped-survival-example.R'),stdout=TRUE),simplifyVector=FALSE)
for(k in names(ref$cohort))stopifnot(identical(as.numeric(a$cohort$asDF[[k]]),as.numeric(ref$cohort[[k]])))
for(k in c('statistic','df','p'))stopifnot(isTRUE(all.equal(a$logrank$asDF[[k]],as.numeric(ref$logrank[[k]]),tolerance=2e-12)))
stopifnot(identical(a$cases$asDF$subjectID,sprintf('S%02d',1:9)))
for(g in ref$groups) {
    selected <- a$selectedTimes$asDF;selected <- selected[selected$group==g$label,]
    for(k in c('time','risk','events','censored','survival','lower','upper'))
        stopifnot(isTRUE(all.equal(as.numeric(selected[[k]]),vapply(g$selected,function(row)if(is.null(row[[k]]))NA_real_ else as.numeric(row[[k]]),0),tolerance=2e-12)))
}
if(length(args)>=4L) {
    grDevices::png(args[[2]],width=as.integer(args[[3]]),height=as.integer(args[[4]]),res=144,type='cairo')
    a$survivalPlot$print();invisible(grDevices::dev.off())
} else a$survivalPlot$saveAs(args[[2]])
stopifnot(file.exists(args[[2]]),file.info(args[[2]])$size>1000)
cat('PASS: independent synthetic cohort/log-rank/horizon/ID checks and native PNG export.\n')
