# Independent base-R reference for the packaged CSV and the GUI qualification nulls.
d<-read.csv('data/python_pie_examples.csv',na.strings=c('','NA'))
d$Outcome<-factor(d$Outcome)
complete<-complete.cases(d)
obs<-xtabs(Frequency~Outcome,d[complete,])
result<-list()
for(custom in c(FALSE,TRUE)) {
    probabilities<-if(custom)c(4,2,3,1)/10 else rep(.25,4)
    warnings<-character()
    fit<-withCallingHandlers(chisq.test(obs,p=probabilities,correct=FALSE),
        warning=function(w){warnings<<-c(warnings,conditionMessage(w));invokeRestart('muffleWarning')})
    result[[if(custom)'custom' else 'equal']]<-list(categories=I(names(obs)),
        observed=I(as.numeric(obs)),probability=I(probabilities),expected=I(as.numeric(fit$expected)),
        residual=I(as.numeric(fit$residuals)),contribution=I(as.numeric((obs-fit$expected)^2/fit$expected)),
        statistic=as.numeric(fit$statistic),df=as.numeric(fit$parameter),p=fit$p.value,
        minimum=min(fit$expected),small=sum(fit$expected<5),warnings=as.list(warnings))
}
cat(jsonlite::toJSON(result,auto_unbox=TRUE,digits=17),'\n')
