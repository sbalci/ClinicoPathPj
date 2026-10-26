# Independent base-R screening fixtures; never used by the runtime.
args <- commandArgs(FALSE)
root <- dirname(dirname(normalizePath(sub('^--file=', '', args[grepl('^--file=', args)]))))
cases <- list()
add <- function(x, transform='none') {
 clean <- x[!is.na(x)]; n <- length(clean); y <- clean; applied <- 'none'
 if(n>=3 && transform=='log' && all(clean>0)) { y<-log(clean);applied<-'log' }
 if(n>=3 && transform=='sqrt' && all(clean>=0)) { y<-sqrt(clean);applied<-'sqrt' }
 z <- rep(NA_real_, n); modified <- z; flags <- matrix(FALSE,n,3); available<-FALSE
 if(n>=3) {
  z <- as.numeric(scale(y)); q<-quantile(y,c(.25,.75)); fence<-1.5*diff(q)
  flags[,1] <- !is.na(z)&abs(z)>3
  flags[,2] <- y<q[1]-fence|y>q[2]+fence
  sigma<-mad(y,constant=1.4826)
  available<-n>3&&sigma>0
  if(available) {modified<-(y-median(y))/sigma;flags[,3]<-abs(modified)>3.5}
 }
 votes<-rowSums(flags);selected<-votes >= if(n<10)1 else 2
 cases[[length(cases)+1L]] <<- list(x=I(x),transform=transform,applied=applied,z=I(z),modified=I(modified),mad_available=available,
  flags=unname(split(flags,row(flags))),votes=I(votes),selected=I(selected),q=if(n)I(unname(quantile(clean,c(.25,.5,.75)))) else NULL)
}
for(n in c(0,1,2,3,4,9,10,11,30))add(c(if(n)seq_len(n) else numeric(),NA_real_))
add(c(rep(0,10),100));add(rep(7,20));add(c(1,2,3,NA,1e3),'log');add(c(0,1,2,4,100),'log');add(c(-1,2,3,100),'sqrt')
add(c(0,1,4,9,NA,100),'sqrt');add(c(rep(NA_real_,5)))
set.seed(20261025)
for(i in 1:25) {n<-sample(4:100,1);x<-c(rnorm(n),runif(3,-15,15),NA);add(x);add(exp(x),'log')}
jsonlite::write_json(list(cases=cases),file.path(root,'tests/fixtures/single-quality-oracles.json'),auto_unbox=TRUE,na='null',null='null',digits=17,pretty=TRUE)
cat(length(cases),'fixtures\n')
