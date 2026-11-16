# Independent installed-R reference for the synthetic grouped GUI dataset.
suppressPackageStartupMessages(library(survival))
d <- read.csv('data/python_grouped_survival_examples.csv',na.strings='',stringsAsFactors=FALSE)
keep <- complete.cases(d[,c('Months','Status','Group')]);complete <- d[keep,]
complete$Group <- factor(complete$Group)
z <- survdiff(Surv(Months,Status=='Event')~Group,data=complete)
groups <- lapply(levels(complete$Group),function(label) {
    g <- complete[complete$Group==label,];fit <- survfit(Surv(Months,Status=='Event')~1,g,conf.type='log')
    horizons <- c(12,36,60);horizons <- horizons[horizons<=max(g$Months)]
    selected <- summary(fit,times=horizons)
    steps <- data.frame(time=fit$time,risk=fit$n.risk,events=fit$n.event,censored=fit$n.censor,
        survival=fit$surv,se=fit$std.err*fit$surv,lower=fit$lower,upper=fit$upper)
    median <- summary(fit)$table[c('median','0.95LCL','0.95UCL')]
    list(label=label,n=nrow(g),events=sum(g$Status=='Event'),censored=sum(g$Status=='Censored'),
        maximum=max(g$Months),median=as.list(median),steps=steps,
        selected=data.frame(time=selected$time,risk=selected$n.risk,events=selected$n.event,
            censored=selected$n.censor,survival=selected$surv,lower=selected$lower,upper=selected$upper))
})
result <- list(cohort=list(source=nrow(d),complete=sum(keep),excluded=sum(!keep),events=sum(complete$Status=='Event'),
    censored=sum(complete$Status=='Censored'),groups=nlevels(complete$Group)),groups=groups,
    logrank=list(statistic=unname(z$chisq),df=length(z$n)-1,p=pchisq(z$chisq,length(z$n)-1,lower.tail=FALSE),
        observed=as.list(setNames(as.numeric(z$obs),levels(complete$Group))),
        expected=as.list(setNames(as.numeric(z$exp),levels(complete$Group))),variance=unname(z$var)))
cat(jsonlite::toJSON(result,auto_unbox=TRUE,null='null',na='null',digits=17))
