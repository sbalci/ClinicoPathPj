# Independent base-R frequency reference using the CSV's imported alphabetical levels.
d<-read.csv('data/python_pie_examples.csv',na.strings=c('','NA'))
d$Outcome<-factor(d$Outcome)
complete<-complete.cases(d);positive<-complete & !is.na(d$Frequency) & d$Frequency>0
counts<-xtabs(Frequency~Outcome,d[complete,])
result<-list(categories=I(names(counts)),counts=I(as.numeric(counts)),total=sum(counts),
    proportions=I(as.numeric(counts)/sum(counts)),
    cohort=I(c(nrow(d),sum(complete),sum(!complete),sum(complete & d$Frequency==0,na.rm=TRUE),sum(positive),sum(counts))),
    source_indices=I(which(positive)),source_labels=I(as.character(d$Outcome[positive])),
    source_counts=I(d$Frequency[positive]))
cat(jsonlite::toJSON(result,auto_unbox=TRUE,digits=17),'\n')
