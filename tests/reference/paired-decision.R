# Independent base-R oracle, frozen before the Python paired-comparison engine.
# Mid-p: Fagerland et al. 2013 eqs (5)-(6), directly summing binomial masses.
suppressPackageStartupMessages(library(jsonlite))

mcnemar_reference <- function(b, c, method) {
  m <- b + c
  if (!m) return(list(statistic=NULL, p=1, discordant=0L, status="no_discordance"))
  mass <- dbinom(0:min(b,c), m, .5)
  exact <- min(1, 2*sum(mass))
  if (method == "midp") {
    p <- if (b == c) 1 - tail(mass,1)/2 else exact - tail(mass,1)
    statistic <- NULL
  } else if (method == "exact") {
    p <- binom.test(b, m, p=.5)$p.value
    statistic <- NULL
    stopifnot(abs(p-exact) < 1e-12)
  } else {
    tab <- matrix(c(0,b,c,0),2,byrow=TRUE)
    r <- suppressWarnings(mcnemar.test(tab,correct=FALSE))
    statistic <- unname(r$statistic); p <- r$p.value
  }
  list(statistic=statistic,p=unname(p),discordant=as.integer(m),status="ok")
}
grid <- expand.grid(b=0:20,c=0:20)
grid <- unique(rbind(grid,data.frame(b=c(1,6,0,500,999,10000),
                                   c=c(7,16,1000,500,1,9999))))
discordance <- lapply(seq_len(nrow(grid)),function(i) {
  b <- grid$b[i];c <- grid$c[i]
  list(b=b,c=c,expected=setNames(lapply(c("midp","asymptotic","exact"),
    function(m) mcnemar_reference(b,c,m)),c("midp","asymptotic","exact")))
})
fixtures <- list()
add <- function(id, reference, tests, levels=c("Negative","Positive","Other","unused"),
                positive="Positive",negative="Negative",exclude=FALSE) {
  fixtures[[length(fixtures)+1L]] <<- list(id=id,reference=as.integer(reference),
    tests=lapply(tests,as.integer),levels=levels,positive=positive,negative=negative,
    exclude=exclude)
}
add("hand_correctness_not_positivity",c(rep(0,8),rep(1,8)),
    list(A=c(0,0,0,1,1,0,1,0,1,1,1,1,0,0,1,0),
         B=c(1,1,0,1,1,1,1,0,1,1,1,0,0,0,0,0),
         C=c(rep(0,8),rep(1,8))))
add("different_missingness",c(0,0,0,0,1,1,1,1,-1,1),
    list(A=c(0,-1,1,0,1,1,-1,0,1,1),B=c(0,1,0,0,-1,1,0,1,0,1)))
add("explicit_other_exclusion",c(0,0,1,1,2,1,-1,0),
    list(A=c(0,1,1,0,1,2,2,0),B=c(0,0,0,1,1,1,0,2)),exclude=TRUE)
add("no_discordance",c(0,0,1,1,1,0),list(A=c(0,1,1,1,0,0),B=c(0,1,1,1,0,0)))
add("one_class_positive",rep(1,5),list(A=c(0,0,1,1,1),B=c(0,1,0,1,1)))
add("one_class_negative",rep(0,5),list(A=c(0,0,1,1,1),B=c(0,1,0,1,1)))
add("one_case",1,list(A=1,B=0))
add("reordered_literal_NA_labels",c(1,1,0,0,0,1),
    list(`測定 A`=c(1,0,0,1,0,1),`Test B`=c(0,0,1,1,0,1)),
    levels=c("NA","Other","unused"),positive="NA",negative="Other")
add("holm_excludes_duplicate",c(rep(0,12),rep(1,12)),
    list(A=c(rep(0,12),rep(1,12)),B=c(rep(0,12),rep(1,12)),C=c(rep(1,10),0,0,rep(0,10),1,1)))
set.seed(20261111)
for (n in c(8,23,100,500)) {
  ref <- rbinom(n,1,.4);a <- rbinom(n,1,.5);b <- rbinom(n,1,.6);c <- rbinom(n,1,.7)
  add(paste0("random_n",n),ref,list(A=a,B=b,C=c))
}

proportions <- function(truth,pred,confidence) {
  counts <- c(sum(truth & pred),sum(!truth & pred),sum(truth & !pred),sum(!truth & !pred))
  numerator <- c(counts[1],counts[4],counts[1],counts[4],counts[1]+counts[4])
  denominator <- c(sum(truth),sum(!truth),sum(pred),sum(!pred),length(truth))
  rows <- lapply(seq_along(numerator),function(i) {
    ci <- if(denominator[i]) binom.test(numerator[i],denominator[i],conf.level=confidence)$conf.int else c(NA,NA)
    list(estimate=if(denominator[i]) numerator[i]/denominator[i] else NULL,
         lower=if(is.na(ci[1])) NULL else unname(ci[1]),upper=if(is.na(ci[2])) NULL else unname(ci[2]))
  })
  list(counts=as.integer(counts),proportions=rows)
}
pair_reference <- function(x,y,method) {
  n <- length(x)
  if(!n) return(list(n=0L,first=NULL,second=NULL,difference=NULL,
                    counts=as.integer(c(0,0,0,0)),discordant=0L,
                    statistic=NULL,p=NULL,status="absent_class"))
  counts <- as.integer(c(sum(x & y),sum(x & !y),sum(!x & y),sum(!x & !y)))
  c(list(n=as.integer(n),first=mean(x),second=mean(y),difference=mean(as.integer(x)-as.integer(y)),
         counts=counts),mcnemar_reference(counts[2],counts[3],method))
}
for(i in seq_along(fixtures)) {
  f <- fixtures[[i]];vectors <- c(list(reference=f$reference),f$tests)
  pos <- match(f$positive,f$levels)-1L;neg <- match(f$negative,f$levels)-1L
  missing <- Reduce(`|`,lapply(vectors,function(v) v<0))
  outside <- Reduce(`|`,lapply(vectors,function(v) v>=0 & !v %in% c(pos,neg)))
  keep <- !missing & !outside;truth <- f$reference[keep]==pos
  pred <- lapply(f$tests,function(v) v[keep]==pos)
  expected <- list(n_source=length(keep),n_complete=sum(keep),n_positive=sum(truth),
    n_negative=sum(!truth),retained_indices=as.integer(which(keep)-1),
    excluded_missing=sum(missing),excluded_indeterminate=sum(!missing & outside),
    missing_by_role=lapply(vectors,function(v)sum(v<0)),
    indeterminate_by_role=lapply(vectors,function(v)sum(v>=0 & !v %in% c(pos,neg))))
  expected$runs <- list()
  for(confidence in c(.8,.95,.99)) for(method in c("midp","asymptotic","exact")) {
    models <- lapply(pred,function(v)proportions(truth,v,confidence))
    pairs <- list()
    for(pair in combn(names(pred),2,simplify=FALSE)) {
      x <- pred[[pair[1]]];y <- pred[[pair[2]]]
      pairs[[length(pairs)+1L]] <- list(first_name=pair[1],second_name=pair[2],
        accuracy=pair_reference(x==truth,y==truth,method),
        sensitivity=pair_reference(x[truth],y[truth],method),
        specificity=pair_reference(!x[!truth],!y[!truth],method))
    }
    active <- which(vapply(pairs,function(p)p$accuracy$discordant>0,logical(1)))
    adjusted <- vapply(pairs,function(p)p$accuracy$p,numeric(1))
    if(length(active)) adjusted[active] <- p.adjust(adjusted[active],method="holm")
    for(k in seq_along(pairs)) pairs[[k]]$accuracy$p_holm <- adjusted[k]
    expected$runs[[length(expected$runs)+1L]] <- list(confidence=confidence,method=method,
      models=models,pairs=pairs,holm_family=length(active))
  }
  fixtures[[i]]$expected <- expected
}
report <- list(schema_version=1L,source="Independent base R and literal binomial mass enumeration; no target Python called",
               baseline_backend_sha256="752f0325ac1b725e7ddf5ed16a5806ad108217277b177d3302de792e9904c110",
               R_version=as.character(getRversion()),discordance=discordance,fixtures=fixtures)
write_json(report,"tests/fixtures/paired-decision.json",auto_unbox=TRUE,null="null",na="null",digits=17,pretty=TRUE)
cat(length(discordance),"discordance cases;",length(fixtures),"paired datasets; references frozen.\n")
