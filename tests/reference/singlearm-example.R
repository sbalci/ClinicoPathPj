# Independent survival/stats reference for the synthetic native GUI workbook.
suppressPackageStartupMessages(library(survival))
d <- read.csv('data/python_singlearm_examples.csv',na.strings=c('','NA'))
keep <- complete.cases(d[c('Months','Status')]);t <- d$Months[keep];e <- d$Status[keep]=='Event'
fit <- survfit(Surv(t,e)~1,conf.type='log-log',conf.int=.95)
reverse <- survfit(Surv(t,!e)~1,conf.type='log-log',conf.int=.95)
s <- summary(fit,times=c(12,36,60));steps <- summary(fit,censored=TRUE)
num <- function(x)ifelse(is.finite(x),x,NA_real_)
median <- function(f)as.list(num(summary(f)$table[c('median','0.95LCL','0.95UCL')]))
band <- function(values,survival)ifelse(survival %in% c(0,1),NA_real_,values)
rate <- poisson.test(sum(e),T=sum(t),r=sum(e)/sum(t),conf.level=.95)
result <- list(cohort=I(c(nrow(d),sum(keep),sum(!keep),sum(e),sum(!e),0)),
    medians=list(median(fit),median(reverse)),
    selected=lapply(seq_along(s$time),function(i)list(time=s$time[i],risk=s$n.risk[i],events=s$n.event[i],
        censored=s$n.censor[i],survival=s$surv[i],lower=band(s$lower,s$surv)[i],upper=band(s$upper,s$surv)[i])),
    rate=list(events=sum(e),exposure=sum(t),estimate=unname(rate$estimate),lower=rate$conf.int[1],upper=rate$conf.int[2]),
    steps=lapply(seq_along(steps$time),function(i)list(time=steps$time[i],risk=steps$n.risk[i],events=steps$n.event[i],
        censored=steps$n.censor[i],survival=steps$surv[i],se=ifelse(steps$surv[i]==0,NA_real_,steps$std.err[i]),
        lower=band(steps$lower,steps$surv)[i],upper=band(steps$upper,steps$surv)[i])),
    cases=lapply(which(keep),function(i)list(sourceID=as.character(i),subject=d$Subject[i],time=d$Months[i],
        label=d$Status[i],event=as.integer(d$Status[i]=='Event'))))
cat(jsonlite::toJSON(result,auto_unbox=TRUE,digits=17,na='null'),'\n')
