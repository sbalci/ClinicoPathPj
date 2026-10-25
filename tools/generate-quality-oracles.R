# Independent base-R quality accounting; developer-only, no R computation at runtime.
script <- sub('^--file=', '', grep('^--file=', commandArgs(FALSE), value=TRUE))
root <- dirname(dirname(normalizePath(script)))
encode <- function(x) {
 if (is.factor(x)) return(list(kind='factor',levels=I(levels(x)),ordered=is.ordered(x),codes=I(as.integer(x)-1L)))
 list(kind=if(is.numeric(x))'number' else 'text',values=I(x))
}
fixtures <- list()
add <- function(d,threshold=10) {
 rows <- lapply(names(d),function(name) {
  x <- d[[name]];clean <- x[!is.na(x)];n<-length(x);v<-length(clean);u<-length(unique(clean))
  outlier <- NULL
  if(is.numeric(x)&&v>10) {
   q<-unname(quantile(clean,c(.25,.75)));iqr<-diff(q)
   outlier<-if(iqr>0)sum(clean<q[1]-1.5*iqr|clean>q[2]+1.5*iqr) else 0L
  }
  list(variable=name,kind=if(is.numeric(x))'Numeric' else if(is.ordered(x))'Ordinal' else if(is.factor(x))'Categorical' else 'Text',
   n=n,valid=v,missing=n-v,missingRate=(n-v)/n,unique=u,repeats=v-u,repeatRate=if(v)(v-u)/v else NULL,
   constant=v>0&&u<=1,highCardinality=!is.numeric(x)&&u>50&&u>.5*v,
   aboveThreshold=(n-v)>n*threshold/100,outliers=outlier,outlierRate=if(!is.null(outlier))outlier/v else NULL)
 })
 # Independent native row equality, with true NA values equal and strings kept literal.
 excess <- sum(duplicated(d));unique_rows<-nrow(unique(d))
 groups <- list()
 representatives<-which(duplicated(d,fromLast=TRUE)&!duplicated(d))
 for(i in representatives) {
  equal<-vapply(seq_len(nrow(d)),function(j)all(vapply(d,function(x) {
   a<-x[i];b<-x[j];if(is.na(a)&&is.na(b))TRUE else if(is.na(a)||is.na(b))FALSE else a==b
  },logical(1))),logical(1))
  if(sum(equal)>1)groups[[length(groups)+1]]<-c(i-1L,sum(equal))
 }
 if(length(groups))groups<-groups[order(-vapply(groups,`[`,numeric(1),2),vapply(groups,`[`,numeric(1),1))]
 fixtures[[length(fixtures)+1L]] <<- list(columns=lapply(d,encode),threshold=threshold,summaries=rows,
  complete=sum(complete.cases(d)),missingCells=sum(is.na(d)),rowMissing=I(rowSums(is.na(d))),
  duplicate=list(unique=unique_rows,excess=excess,groups=length(groups),patterns=groups[seq_len(min(5,length(groups)))]))
}
add(data.frame(x=c(1,1,2,NA,NA,3),g=factor(c('NA','NA','x',NA,NA,'x'),levels=c('x','NA','unused')),
 text=c('a||b','a||b','a',NA,NA,'a'),check.names=FALSE))
add(data.frame(ordered=ordered(c('low','high',NA,'low'),levels=c('low','high','unused')),constant=rep(2,4),empty=rep(NA_real_,4)))
add(data.frame(a=c(1:10,100,NA),b=c(rep(0,10),100,NA)))
add(data.frame(a=c(1:9,100),b=rep(0,10)))
add(data.frame(a=seq_len(80),id=as.character(seq_len(80))))
# Delimiter-bearing values must not collide when checking full rows.
add(data.frame(sep=c('a||b','a','a||b','NA',NA),collapse=c('c','b||c','c',NA,'NA')))
add(data.frame(x=c(rep(NA_real_,251),seq_len(2249))),10)
set.seed(20261025)
for(i in 1:25) {
 n<-sample(5:80,1)
 add(data.frame(x=sample(c(-3:3,NA),n,TRUE),y=sample(c(0:5,NA),n,TRUE),
  g=factor(sample(c('A','B','NA',NA),n,TRUE),levels=c('A','B','NA','unused'))),sample(c(0,10,50,100),1))
}
jsonlite::write_json(list(provenance=R.version.string,cases=fixtures),file.path(root,'tests/fixtures/quality-oracles.json'),
 auto_unbox=TRUE,null='null',na='null',digits=17,pretty=TRUE)
cat(length(fixtures),'quality fixtures\n')
