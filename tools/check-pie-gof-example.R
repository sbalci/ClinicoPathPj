args<-commandArgs(TRUE)
.libPaths(c(normalizePath(args[[1]],mustWork=TRUE),
    '/Applications/jamovi.app/Contents/Resources/modules/base/R',.libPaths()))
suppressPackageStartupMessages(library(ClinicoPathPj))
jmvcore:::initProtoBuf()
d<-read.csv('data/python_pie_examples.csv',na.strings=c('','NA'))
d$Outcome<-factor(d$Outcome)
observed<-xtabs(Frequency~Outcome,d[complete.cases(d),])
off<-pyjjpiestats(data=d,dep='Outcome',counts='Frequency',label='both',digitsperc=2)
rows<-list()
for(custom in c(FALSE,TRUE)) {
    r<-pyjjpiestats(data=d,dep='Outcome',counts='Frequency',label='both',digitsperc=2,
        resultssubtitle=TRUE,customRatios=custom,ratio='{"No":4,"Other":2,"Yes":3,"Zero":1}')
    probabilities<-if(custom)c(4,2,3,1)/10 else rep(.25,4)
    ref<-suppressWarnings(chisq.test(observed,p=probabilities,correct=FALSE))
    stopifnot(identical(r$frequencies$asDF,off$frequencies$asDF),
        identical(r$piePlot$state,off$piePlot$state),
        abs(r$gof$asDF$statistic-as.numeric(ref$statistic))<1e-12,
        r$gof$asDF$df==as.numeric(ref$parameter),abs(r$gof$asDF$p-ref$p.value)<1e-12,
        all(abs(r$expected$asDF$expected-as.numeric(ref$expected))<1e-12))
    rows[[length(rows)+1L]]<-list(custom=custom,native=r$gof$asDF,
        reference=list(statistic=as.numeric(ref$statistic),df=as.numeric(ref$parameter),p=ref$p.value))
}
output<-if(length(args)>1)args[[2]] else '/private/tmp/cpj-pie-gof-native-compatibility.png'
r$piePlot$saveAs(output)
stopifnot(file.exists(output),file.info(output)$size>1000)
cat(jsonlite::toJSON(list(scope='Isolated native example; GUI and new package pending',
    unchanged_descriptive_rows_and_plot_state=TRUE,runs=rows,plot=output),auto_unbox=TRUE,digits=17,pretty=TRUE),'\n')
