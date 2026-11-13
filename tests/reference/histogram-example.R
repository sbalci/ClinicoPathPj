# Independent base-R references for the synthetic GUI histogram example.
d<-read.csv('data/python_histogram_examples.csv');x<-d$Measurement[!is.na(d$Measurement)]
rows<-list()
for(reference in c(0,1))for(confidence in c(.9,.95)) {
    tt<-t.test(x,mu=reference,conf.level=confidence,alternative='two.sided')
    rows[[length(rows)+1L]]<-list(reference=reference,confidence=confidence,
        difference=mean(x)-reference,stderr=unname(tt$stderr),df=unname(tt$parameter),
        statistic=unname(tt$statistic),p=tt$p.value,mean_lower=unname(tt$conf.int[1]),
        mean_upper=unname(tt$conf.int[2]),difference_lower=unname(tt$conf.int[1])-reference,
        difference_upper=unname(tt$conf.int[2])-reference)
}
result<-list(summary=list(n=length(x),mean=mean(x),sd=sd(x),minimum=min(x),
    q1=unname(quantile(x,.25,type=7)),median=median(x),q3=unname(quantile(x,.75,type=7)),maximum=max(x)),
    runs=rows,versions=list(R=R.version.string,stats=as.character(packageVersion('stats'))))
cat(jsonlite::toJSON(result,auto_unbox=TRUE,digits=17),'\n')
