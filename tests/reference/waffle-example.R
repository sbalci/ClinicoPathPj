d<-read.csv('data/python_waffle_examples.csv',na.strings=c('','NA'))
make<-function(faceted) {
  complete<-!is.na(d$Category)&!is.na(d$Frequency)
  if(faceted)complete<-complete&!is.na(d$Panel)
  keep<-which(complete&d$Frequency>0)
  groups<-sort(unique(d$Category[!is.na(d$Category)]))
  panels<-if(faceted)sort(unique(d$Panel[!is.na(d$Panel)])) else 'All observations'
  cells<-list();pn<-list()
  for(panel in panels) {
    selected<-keep[if(faceted)d$Panel[keep]==panel else rep(TRUE,length(keep))]
    counts<-vapply(groups,function(g)sum(d$Frequency[selected[d$Category[selected]==g]]),0)
    total<-sum(counts)
    pn[[length(pn)+1L]]<-list(panel=panel,total=total,sourceRows=length(selected),tiles=if(total>0)100 else 0,
      status=if(total>0)'Active' else 'No positive complete frequency')
    if(!total)next
    allocated<-floor(100*counts/total);extras<-100-sum(allocated)
    if(extras>0) {winners<-tail(order(100*counts-allocated*total),extras);allocated[winners]<-allocated[winners]+1}
    for(j in seq_along(groups))cells[[length(cells)+1L]]<-list(panel=panel,category=groups[j],count=counts[j],
      denominator=total,proportion=counts[j]/total,tiles=allocated[j],represented=allocated[j]/100,
      error=allocated[j]/100-counts[j]/total,status=if(counts[j]==0)'Zero count' else
        if(allocated[j]==0)'Positive count; no tile' else 'Represented')
  }
  list(cohort=I(c(nrow(d),sum(complete),sum(!complete),sum(complete&d$Frequency==0),length(keep),sum(d$Frequency[keep]))),
    panels=pn,cells=cells,cases=lapply(keep,function(i)list(sourceID=as.character(i),category=d$Category[i],
      panel=if(faceted)d$Panel[i] else 'All observations',frequency=d$Frequency[i])))
}
cat(jsonlite::toJSON(list(faceted=make(TRUE),single=make(FALSE)),auto_unbox=TRUE,digits=17),'\n')
