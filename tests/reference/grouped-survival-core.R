# Independent survival-package grouped KM/log-rank references from the released-source contract.
suppressPackageStartupMessages(library(survival))
make <- function(id,t,e,g,levels=c('B','A','Unused'))
    list(id=id,inputs=list(time=I(t),event=I(e),codes=I(g),levels=as.list(levels)))
fixtures <- list(
 make('hand_two',c(1,2,2,3,3,4),c(1,1,0,1,0,1),c(0,1,0,1,0,1)),
 make('three_tied',c(0,0,1,1,2,2,3,4,4),c(1,0,1,0,1,1,0,1,0),rep(0:2,3),c('C','A+B','Ki*67')),
 make('all_censored',c(0,1,2,3),rep(0,4),c(0,1,0,1)),
 make('all_events',c(0,1,2,3,4,5),rep(1,6),rep(0:1,3)),
 make('one_group',c(0,1,2,3),c(1,0,1,0),rep(1,4)),
 make('joint_terminal',rep(2,6),rep(1,6),rep(0:2,2),c('G3','G1','G2')),
 make('zero_expected_group',c(0,0,2,3),c(0,0,1,1),c(0,0,1,1)),
 make('crossing',c(1,2,3,10,1,3,4,5),c(1,1,0,1,0,0,1,1),rep(0:1,each=4)),
 make('missing_roles',c(0,NA,2,3,4,NA,6,7),c(1,0,NA,1,0,NA,1,0),c(0,0,1,-1,1,-1,0,1)),
 make('genuine_NA_level',1:7,c(1,0,1,0,1,0,1),c(0,1,2,3,-1,0,2),c('NA',NA,'A','Unused')),
 make('global_near_tie_chain',c(1e8,1e8+1,1e8+2,1e8+8),c(1,1,0,1),c(0,1,0,1)),
 make('tiny_times',c(0,1e-9,2e-9,1e-7,2e-7,3e-7),c(1,0,1,0,1,0),rep(0:1,3)),
 make('zero_times',rep(0,6),c(1,0,1,0,0,1),rep(0:1,3)),
 make('two_singletons',c(1,2),c(1,1),c(1,0)),
 make('separated_followup',c(1,2,3,30,40,50),c(0,0,0,1,0,1),rep(0:1,each=3)),
 make('half_plateaus',c(1,2,4,8,1,2,7,9),c(1,1,0,1,1,1,0,0),rep(0:1,each=4)),
 make('unequal_support_terminal_zero',c(1,2,3,4,10,20),c(1,1,0,1,0,0),c(0,0,1,1,1,1)),
 make('permuted_declared_order',c(4,1,2,1,0,3,2),c(0,1,0,0,1,1,1),c(2,0,2,0,2,0,2),c('Z','Unused','A')),
 make('imbalanced',c(0,1:50),c(1,rep(c(0,1),25)),c(0,rep(1,50))),
 make('long_times',c(0,1e100,2e100,3e100,4e100,5e100),c(0,1,0,1,0,1),rep(0:1,3)))
set.seed(161126)
for(i in 1:10) {
 k <- 2+i%%4;n <- 12+i*8
 fixtures[[length(fixtures)+1L]] <- make(paste0('seeded_',i),sample(0:(i*4+3),n,TRUE),
     rbinom(n,1,.2+.05*i),sample(0:(k-1),n,TRUE),c(paste0('Group ',seq_len(k)),'Unused'))
}
finite <- function(x)if(length(x)!=1 || !is.finite(x))NULL else unname(x)
curve <- function(f)lapply(seq_along(f$time),function(i)list(time=unname(f$time[i]),n_risk=unname(f$n.risk[i]),
    events=unname(f$n.event[i]),censored=unname(f$n.censor[i]),cumulative_events=sum(f$n.event[1:i]),
    cumulative_censored=sum(f$n.censor[1:i]),survival=unname(f$surv[i]),greenwood=finite(f$std.err[i]^2),
    se=finite(f$std.err[i]*f$surv[i]),lower=finite(f$lower[i]),upper=finite(f$upper[i])))
median_row <- function(f){v<-summary(f)$table;list(estimate=finite(v['median']),
    lower=finite(v[length(v)-1]),upper=finite(v[length(v)]))}
runs <- list()
for(f in fixtures)for(confidence in c(.8,.95,.99))for(timefix in c(TRUE,FALSE)) {
 a<-f$inputs;t<-as.numeric(a$time);e<-as.numeric(a$event);codes<-as.integer(a$codes)
 labels<-vapply(a$levels,function(v)if(is.null(v))NA_character_ else as.character(v),'')
 g<-labels[pmax(1,codes+1L)];g[codes<0]<-NA_character_
 complete<-!is.na(t)&!is.na(e)&!is.na(g);idx<-which(complete)
 active<-which(!is.na(labels)&vapply(seq_along(labels),function(i)any(complete&codes==i-1L),logical(1)))-1L
 inactive<-which(!is.na(labels)&!seq_along(labels)%in%(active+1L))-1L
 tt<-t[complete];ee<-e[complete];gc<-codes[complete];n<-length(tt)
 gg<-factor(g[complete],levels=labels[active+1L]);d<-data.frame(t=tt,e=ee,g=gg)
 y<-Surv(tt,ee);effective<-if(timefix)aeqSurv(y)[,1] else tt
 fit<-survfit(Surv(t,e)~g,data=d,conf.type='log',conf.int=confidence,timefix=timefix)
 queries<-sort(unique(c(0,tt[seq_len(min(8,n))],median(tt),max(tt),max(tt)+1)))
 groups<-list()
 for(j in seq_along(active)) {
  code<-active[j];members<-which(gc==code);ff<-if(is.null(fit$strata))fit else fit[j]
  supported<-queries[queries<=max(tt[members])];selected<-list()
  if(length(supported)) {
   ss<-summary(ff,times=supported,extend=TRUE)
   for(i in seq_along(supported))selected[[i]]<-list(time=supported[i],n_risk=unname(ss$n.risk[i]),
    events=unname(ss$n.event[i]),censored=unname(ss$n.censor[i]),
    cumulative_events=sum(ff$n.event[ff$time<=supported[i]]),cumulative_censored=sum(ff$n.censor[ff$time<=supported[i]]),
    survival=unname(ss$surv[i]),se=finite(ss$std.err[i]),lower=finite(ss$lower[i]),upper=finite(ss$upper[i]),status='within_followup')
  }
  groups[[j]]<-list(code=code,label=labels[code+1L],n=length(members),events=sum(ee[members]),
   censored=sum(1-ee[members]),source_indices=I(idx[members]-1L),maximum=max(tt[members]),
   effective_maximum=max(effective[members]),normalized=sum(tt[members]!=effective[members]),
   curve=curve(ff),median=median_row(ff),selected=selected,omitted_timepoints=I(setdiff(queries,supported)))
 }
 k<-length(active)
 if(k>1) {
  raw<-getFromNamespace('survdiff.fit','survival')(cbind(effective,ee),gg,rep(1,n),rho=0)
  obs<-unname(raw$observed);exp<-unname(raw$expected);variance<-unname(raw$var)
 } else {obs<-exp<-sum(ee);variance<-matrix(0,1,1)}
 eligible<-which(exp>0);test<-list(method='logrank',rho=0,status='available',n_groups=k,
  observed=I(obs),expected=I(exp),score=I(obs-exp),variance=lapply(seq_len(k),function(i)I(variance[i,])),
  eligible_codes=I(active[eligible]),statistic=NULL,df=NULL,p=NULL,trace=list(),trace_truncated=0L)
 if(k<2)test$status<-'unavailable_one_group' else if(sum(ee)==0)test$status<-'unavailable_no_events' else
 if(length(eligible)<2)test$status<-'unavailable_no_between_group_information' else {
  delta<-(obs-exp)[eligible][-1];vv<-variance[eligible,eligible,drop=FALSE][-1,-1,drop=FALSE]
  statistic<-tryCatch(sum(solve(vv,delta)*delta),error=function(e)NULL)
  if(is.null(statistic))test$status<-'unavailable_singular_variance' else {
   test$statistic<-unname(statistic);test$df<-length(eligible)-1L
   test$p<-unname(pchisq(test$statistic,test$df,lower.tail=FALSE))
  }
  if(timefix) {
   # survival 3.8.12 forwards an explicit timefix argument into model.frame.
   # Its default TRUE call is valid; compare the independent lower-level path.
   public<-tryCatch(survdiff(Surv(t,e)~g,data=d,rho=0),error=function(e)NULL)
   stopifnot(is.null(public)==is.null(statistic))
   if(!is.null(public))stopifnot(isTRUE(all.equal(unname(public$chisq),test$statistic)),
       isTRUE(all.equal(unname(public$pvalue),test$p)),
       isTRUE(all.equal(unname(public$obs),obs)),
       isTRUE(all.equal(unname(public$exp),exp)),
       isTRUE(all.equal(unname(public$var),variance)))
  }
 }
 for(at in sort(unique(effective[ee==1]))) {
  risk<-vapply(active,function(code)sum(gc==code & effective>=at),0L)
  deaths<-vapply(active,function(code)sum(gc==code & effective==at & ee==1),0L)
  test$trace[[length(test$trace)+1L]]<-list(time=at,n_risk=sum(risk),events=sum(deaths),
   group_risk=I(risk),group_events=I(deaths),group_expected=I(sum(deaths)*risk/sum(risk)))
 }
 f$confidence<-confidence;f$timefix<-timefix;f$queries<-I(queries)
 f$expected<-list(schema_version=1,status='ok',confidence=confidence,confidence_method='log',timefix=timefix,unit='months',
  n_source=length(t),n_complete=n,excluded_missing=sum(!complete),missing_time=sum(is.na(t)),
  missing_event=sum(is.na(e)),missing_group=sum(is.na(g)),retained_indices=I(idx-1L),retained_subject_ids=NULL,
  active_codes=I(active),inactive_codes=I(inactive),events=sum(ee),censored=sum(1-ee),
  timefix_changed_rows=sum(tt!=effective),effective_times=I(effective),groups=groups,logrank=test)
 runs[[length(runs)+1L]]<-f
}
registry<-jsonlite::fromJSON('inst/python/registry.json',simplifyVector=FALSE)
entry<-Filter(function(e)e$id=='pysurvival',registry$analyses)[[1]]
result<-list(schema_version=1,baseline_hashes=entry$baseline$files,
 versions=list(R=as.character(getRversion()),survival=as.character(packageVersion('survival'))),fixtures=runs)
args<-commandArgs(TRUE);json<-jsonlite::toJSON(result,auto_unbox=TRUE,digits=17,na='null',null='null')
if(length(args))writeLines(json,args[1]) else cat(json,'\n')
