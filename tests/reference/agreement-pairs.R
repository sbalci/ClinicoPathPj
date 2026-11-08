# Independent base-R oracle: no Python helper and no analysis backend called.
fixtures <- list()
sets <- list(small=list(x=c(1,2,4),y=c(0,3,2)),
             varied=list(x=c(10,20,30,40,50,60,70,80),y=c(9,18,31,37,55,59,75,76)),
             constant=list(x=1:8,y=(1:8)-2),
             zero=list(x=rep(0,8),y=rep(0,8)),
             larger=list(x=seq_len(40)*1.7,y=seq_len(40)*1.6+sin(seq_len(40))))
for (name in names(sets)) for (coverage in c(.5,.95,.99)) for (confidence in c(.8,.95,.99)) {
    x <- sets[[name]]$x;y <- sets[[name]]$y;d <- x-y;n <- length(d)
    bias <- mean(d);s <- sd(d);z <- qnorm((1+coverage)/2);tc <- qt((1+confidence)/2,n-1)
    loa <- bias+c(-1,1)*z*s
    mean_ci <- bias+c(-1,1)*tc*s/sqrt(n)
    half <- tc*s*sqrt(1/n+z^2/(2*(n-1)))
    fixtures[[length(fixtures)+1L]] <- list(name=name,x=x,y=y,coverage=coverage,confidence=confidence,
       expected=as.list(c(bias=bias,sd=s,lower=loa[1],upper=loa[2],biasLower=mean_ci[1],biasUpper=mean_ci[2],
                  lowerLower=loa[1]-half,lowerUpper=loa[1]+half,upperLower=loa[2]-half,upperUpper=loa[2]+half)))
}
jsonlite::write_json(fixtures,'tests/fixtures/agreement-pairs.json',auto_unbox=TRUE,digits=17,pretty=TRUE)
