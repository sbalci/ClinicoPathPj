# Same calculation/UI workload, two transports. Run against stable installed libraries.
args <- commandArgs(TRUE)
if (length(args) < 2L) stop("Supply ClinicoPathPj and Pj R-library directories")
root <- normalizePath(dirname(dirname(sub("^--file=", "", grep("^--file=", commandArgs(), value=TRUE)))))
.libPaths(c(normalizePath(args[1]), normalizePath(args[2]),
 "/Applications/jamovi.app/Contents/Resources/modules/base/R", .libPaths()))
Sys.setenv(PYTHONHOME="/Applications/jamovi.app/Contents/Resources", PYTHONPATH="/Applications/jamovi.app/Contents/Resources/jamovi/server")
setwd("/Applications/jamovi.app/Contents/MacOS")
suppressPackageStartupMessages(library(ClinicoPathPj))
jmvcore:::initProtoBuf()
service <- ClinicoPathPj:::.cpjPjService()
stopifnot(service$info$api_version==1L, utils::compareVersion(service$info$module_version,"1.3.0")>=0)
before <- .libPaths()
d <- read.csv(file.path(root,"data/python_d3_cutoff_examples.csv"))
d$Reference <- factor(d$Reference,levels=c("Negative","Positive"))
records <- list()
for(direction in c("ge","le")) for(method in c("exact","wilson")) for(criterion in c("errors","youden","cost")) {
 cutoff <- switch(criterion,errors="4",youden="",cost="2")
 options <- list(data=d,marker="Measurement",reference="Reference",positive="Positive",
    direction=direction,criterion=criterion,cutoff=cutoff,ciMethod=method,ciWidth=90)
 start <- proc.time()[["elapsed"]];a <- do.call(pybridgecompare,c(options,list(execution="processx"))); ta<-proc.time()[["elapsed"]]-start
 start <- proc.time()[["elapsed"]];b <- do.call(pybridgecompare,c(options,list(execution="pj"))); tb<-proc.time()[["elapsed"]]-start
 stopifnot(identical(a$counts$asDF,b$counts$asDF),isTRUE(all.equal(a$metrics$asDF,b$metrics$asDF,tolerance=1e-12)),
           identical(a$rocSummary$asDF,b$rocSummary$asDF))
 applied <- a$rocSummary$asDF$value[a$rocSummary$asDF$metric=="Applied cutoff"]
 positive <- d$Reference=="Positive";pred <- if(direction=="ge")d$Measurement>=applied else d$Measurement<=applied
 counts <- c(sum(positive&pred),sum(!positive&pred),sum(positive&!pred),sum(!positive&!pred))
 stopifnot(identical(as.integer(b$counts$asDF$n),as.integer(counts)))
 tp<-counts[1];fp<-counts[2];fn<-counts[3];tn<-counts[4]
 for(i in seq_len(5)) {
  yes<-c(tp,tn,tp,tn,tp+tn)[i]; n<-c(tp+fn,tn+fp,tp+fp,tn+fn,sum(counts))[i]
  if(n>0 && method=="exact") stopifnot(max(abs(unlist(b$metrics$asDF[i,c("lower","upper")])-binom.test(yes,n,conf.level=.9)$conf.int))<1e-10)
 }
 records[[length(records)+1L]] <- data.frame(direction,method,criterion,cutoff=applied,processx_seconds=ta,pj_seconds=tb)
 cat(direction,method,criterion,"independent counts and matched native results PASSED\n")
}
# Ties, missing pairs, unused levels and literal labels traverse the identical encoded request.
e <- data.frame(x=c(1,2,2,4,5,6,NA,8),g=factor(c("N","N","P","N","P","P","P",NA),levels=c("N","P")))
rownames(e)<-as.character(c(2,5,7,9,13,17,21,25))
a<-pybridgecompare(e,"x","g","P",cutoff="2",execution="processx")
b<-pybridgecompare(e,"x","g","P",cutoff="2",execution="pj")
stopifnot(identical(a$counts$asDF,b$counts$asDF),identical(b$counts$asDF$n,c(3L,2L,0L,1L)),
          grepl('"row": "7"',b$explorer$content,fixed=TRUE),identical(.libPaths(),before))
# A service-side input error must not prevent the next valid call.
failed<-try(pybridgecompare(e,"x","g","P",cutoff="nan",execution="pj"),silent=TRUE)
stopifnot(inherits(failed,"try-error"))
recovered<-pybridgecompare(e,"x","g","P",cutoff="3",execution="pj")
stopifnot(identical(recovered$counts$asDF$n,c(2L,1L,1L,2L)))
output<-file.path(root,"docs/validation-exports/pj-matched-route-timings.csv")
write.csv(do.call(rbind,records),output,row.names=FALSE)
cat("12 matched configurations, independent counts/intervals, original-row transport, error recovery and unchanged library paths PASSED\n")
cat("Timing CSV:",output,"\n")
