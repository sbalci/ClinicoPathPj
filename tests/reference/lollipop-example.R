# Independent base-R reference for the actual desktop CSV; no target engine calls.
d<-read.csv('data/python_lollipop_examples.csv',na.strings=c('','NA'))
d$Category<-factor(d$Category);keep<-complete.cases(d);clean<-d[keep,]
stats<-function(x)I(c(length(x),mean(x),median(x),sd(x),min(x),max(x),diff(range(x)),
    unname(quantile(x,.25,type=7)),unname(quantile(x,.75,type=7))))
result<-list(cohort=I(c(nrow(d),sum(keep),sum(!keep),nlevels(d$Category),nlevels(d$Category))),
    raw=stats(clean$Value),categories=I(levels(d$Category)),
    group_counts=I(as.integer(table(clean$Category))),source_rows=I(which(keep)),
    source_labels=I(as.character(clean$Category)),source_values=I(clean$Value),modes=list())
for(mode in c('mean','sum')) {
    a<-aggregate(clean$Value,list(Category=clean$Category),get(mode));names(a)[2]<-'Value'
    if(mode=='sum')a<-a[order(-a$Value),]
    axis<-if(mode=='sum')rev(as.character(a$Category)) else levels(clean$Category)
    result$modes[[mode]]<-list(summary=stats(a$Value),
        labels=I(as.character(a$Category)),values=I(a$Value),
        counts=I(as.integer(table(clean$Category)[as.character(a$Category)])),
        slots=I(match(as.character(a$Category),axis)),
        source_points=I(match(as.character(clean$Category),as.character(a$Category))),
        source_plotted=I(a$Value[match(as.character(clean$Category),as.character(a$Category))]))
}
cat(jsonlite::toJSON(result,auto_unbox=TRUE,digits=17),'\n')
