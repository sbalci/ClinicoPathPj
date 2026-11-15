# Independent base-R reference for the saved frequency example; no module imports.
d <- read.csv('data/python_barstats_examples.csv', na.strings=c('', 'NA'))
keep <- complete.cases(d)
m <- xtabs(Frequency ~ Outcome + Group, d[keep, ])
test <- chisq.test(m, correct=FALSE)
n <- sum(m); r <- nrow(m); c <- ncol(m)
phi <- as.numeric(test$statistic)/n
denom <- min(r-1-(r-1)^2/(n-1), c-1-(c-1)^2/(n-1))
result <- list(counts=as.numeric(m), expected=as.numeric(test$expected),
    groups=colnames(m), outcomes=rownames(m), totals=as.numeric(colSums(m)),
    group_proportions=as.numeric(sweep(m,2,colSums(m),'/')),
    overall_proportions=as.numeric(m/n), statistic=as.numeric(test$statistic),
    df=as.numeric(test$parameter), p=test$p.value,
    raw=sqrt(phi/min(r-1,c-1)),
    corrected=sqrt(max(0,phi-(r-1)*(c-1)/(n-1))/denom))
cat(jsonlite::toJSON(result,auto_unbox=TRUE,digits=17), '\n')
