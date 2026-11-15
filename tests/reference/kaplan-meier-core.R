# Independent survival-package/Poisson oracle, frozen before the Python core.
suppressPackageStartupMessages(library(survival))
make<-function(id,time,event)list(id=id,inputs=list(time=I(time),event=I(event)))
fixtures<-list(
 make('mixed',1:6,c(1,0,1,0,1,0)),
 make('event_censor_ties',c(1,1,1,2,2,3,4,4),c(1,0,1,0,1,0,1,0)),
 make('origin_events',c(0,0,1,2,3),c(1,0,1,0,1)),
 make('all_censored',c(0,1,2,3),c(0,0,0,0)),
 make('all_events',c(0,1,2,3),c(1,1,1,1)),
 make('singleton_event',0,1),make('singleton_censored',0,0),
 make('terminal_event_tie',c(1,2,2,3,3),c(0,0,0,1,1)),
 make('half_plateau',c(1,2,4,8),c(1,1,0,1)),
 make('terminal_half_plateau',c(1,2,7,9),c(1,1,0,0)),
 make('missing_pairs',c(0,1,NA,2,3,NA,4),c(1,NA,1,0,1,NA,0)),
 make('permuted',c(4,1,2,1,0,3,2),c(0,1,0,0,1,1,1)),
 make('close_decimal',c(0,.1,.1+1e-10,.2,.3,.3+1e-8),c(0,1,0,1,0,1)),
 make('relative_tie_chain',c(1e8,1e8+1,1e8+2,1e8+8,1e8+20),c(1,0,1,0,1)),
 make('tiny_times_collapse',c(0,1e-9,2e-9,1e-7),c(1,0,1,0)),
 make('long_tail',c(1,2,3,100,1000,1e6),c(1,1,0,0,0,0)))
set.seed(7184)
for(i in 1:10)fixtures[[length(fixtures)+1L]]<-make(paste0('seeded_',i),
 sample(0:(i*3+1),8+i*7,replace=TRUE),rbinom(8+i*7,1,.4))
finite<-function(x)if(length(x)!=1 || !is.finite(x))NULL else unname(x)
curve<-function(f)lapply(seq_along(f$time),function(j)list(time=unname(f$time[j]),
 n_risk=unname(f$n.risk[j]),events=unname(f$n.event[j]),censored=unname(f$n.censor[j]),
 cumulative_events=sum(f$n.event[1:j]),cumulative_censored=sum(f$n.censor[1:j]),
 survival=unname(f$surv[j]),greenwood=finite(f$std.err[j]^2),
 se=finite(f$std.err[j]*f$surv[j]),
 lower=if(f$surv[j]>0 && f$surv[j]<1)finite(f$lower[j]) else NULL,
 upper=if(f$surv[j]>0 && f$surv[j]<1)finite(f$upper[j]) else NULL))
median_row<-function(f){v<-summary(f)$table;list(estimate=finite(v['median']),lower=finite(v[length(v)-1L]),upper=finite(v[length(v)]))}
runs<-list()
for(f in fixtures)for(confidence in c(.8,.95,.99))for(timefix in c(TRUE,FALSE)) {
 a<-f$inputs;t<-as.numeric(a$time);e<-as.numeric(a$event);complete<-!is.na(t)&!is.na(e)
 tt<-t[complete];ee<-e[complete];y<-Surv(tt,ee)
 effective<-if(timefix)aeqSurv(y)[,1] else tt
 d<-data.frame(t=tt,e=ee)
 fit<-survfit(Surv(t,e)~1,d,conf.type='log-log',conf.int=confidence,timefix=timefix)
 reverse<-survfit(Surv(t,1-e)~1,d,conf.type='log-log',conf.int=confidence,timefix=timefix)
 q<-sort(unique(c(0,min(tt)/2,tt[seq_len(min(8,length(tt)))],median(tt),max(tt),max(tt)+1)))
 supported<-q[q<=max(tt) | tail(fit$surv,1)==0]
 selected<-list()
 if(length(supported)) {
   ss<-summary(fit,times=supported,extend=TRUE)
   for(j in seq_along(supported))selected[[j]]<-list(time=supported[j],n_risk=unname(ss$n.risk[j]),
     events=unname(ss$n.event[j]),censored=unname(ss$n.censor[j]),
     cumulative_events=sum(fit$n.event[fit$time<=supported[j]]),
     cumulative_censored=sum(fit$n.censor[fit$time<=supported[j]]),survival=unname(ss$surv[j]),
     se=finite(ss$std.err[j]),lower=if(ss$surv[j]>0 && ss$surv[j]<1)finite(ss$lower[j]) else NULL,
     upper=if(ss$surv[j]>0 && ss$surv[j]<1)finite(ss$upper[j]) else NULL,
     status=if(supported[j]>max(tt))'terminal_zero_extension' else 'within_followup')
 }
 exposure<-sum(tt);events<-sum(ee)
 rate<-list(person_time=exposure,events=events,estimate=NULL,lower=NULL,upper=NULL,
   status='unavailable_zero_person_time')
 if(exposure>0) {
   # The interval is independent of the null rate. Avoid computing an unrelated
   # enormous-tail p-value under the default r=1 for long observation totals.
   test<-poisson.test(events,T=exposure,r=if(events>0)events/exposure else 1/exposure,
                     conf.level=confidence)
   lower<-if(events==0)0 else qchisq((1-confidence)/2,2*events)/(2*exposure)
   upper<-qchisq(1-(1-confidence)/2,2*(events+1))/(2*exposure)
   stopifnot(isTRUE(all.equal(unname(test$estimate),events/exposure)),
             isTRUE(all.equal(as.numeric(test$conf.int),c(lower,upper))))
   rate<-list(person_time=exposure,events=events,estimate=events/exposure,
     lower=lower,upper=upper,status='available')
 }
 f$confidence<-confidence;f$timefix<-timefix;f$queries<-I(q)
 f$expected<-list(schema_version=1,status='ok',confidence=confidence,timefix=timefix,
   unit='months',n_source=length(t),n_complete=sum(complete),excluded_missing=sum(!complete),
   missing_time=sum(is.na(t)),missing_event=sum(is.na(e)),retained_indices=I(which(complete)-1L),
   events=events,censored=length(tt)-events,event_proportion=events/length(tt),
   max_time=max(tt),effective_max_time=max(effective),timefix_changed_rows=sum(tt!=effective),
   effective_times=I(effective),curve=curve(fit),median=median_row(fit),
   selected=selected,omitted_timepoints=I(setdiff(q,supported)),
   reverse=list(curve=curve(reverse),median=median_row(reverse)),rate=rate)
 runs[[length(runs)+1L]]<-f
}
registry<-jsonlite::fromJSON('inst/python/registry.json',simplifyVector=FALSE)
entry<-Filter(function(e)e$id=='pysinglearm',registry$analyses)[[1]]
result<-list(schema_version=1,baseline_hashes=entry$baseline$files,
 versions=list(R=as.character(getRversion()),survival=as.character(packageVersion('survival'))),fixtures=runs)
args<-commandArgs(TRUE);json<-jsonlite::toJSON(result,auto_unbox=TRUE,digits=17,na='null',null='null')
if(length(args))writeLines(json,args[[1]]) else cat(json,'\n')
