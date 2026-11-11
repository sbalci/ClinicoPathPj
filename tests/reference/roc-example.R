# Independent literal case/control kernel for the synthetic GUI CSV.
d <- read.csv('data/python_roc_examples.csv',stringsAsFactors=FALSE)
d <- d[complete.cases(d[,c('Reference','Measurement_A','Measurement_B')]) & nzchar(d$Reference),]
y <- d$Reference=='Positive'
placements <- lapply(d[c('Measurement_A','Measurement_B')],function(x) {
    kernel <- outer(x[y],x[!y],function(a,b) (a>b)+.5*(a==b))
    list(auc=mean(kernel),case=rowMeans(kernel),control=colMeans(kernel))
})
v10 <- do.call(rbind,lapply(placements,`[[`,'case'));v01 <- do.call(rbind,lapply(placements,`[[`,'control'))
S <- cov(t(v10))/sum(y)+cov(t(v01))/sum(!y)
auc <- vapply(placements,`[[`,numeric(1),'auc');delta <- auc[1]-auc[2]
se <- sqrt(S[1,1]+S[2,2]-2*S[1,2]);z <- delta/se
result <- list(auc=auc,covariance=S,delta=unname(delta),se=unname(se),z=unname(z),p=unname(2*pnorm(-abs(z))),lower=unname(delta-qnorm(.975)*se),upper=unname(delta+qnorm(.975)*se))
jsonlite::write_json(result,'docs/validation-exports/python-roc-example-reference-20261111.json',auto_unbox=TRUE,pretty=TRUE,digits=17)
