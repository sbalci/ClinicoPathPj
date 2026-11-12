# Freeze independent base-R references before implementing the Python engine.
suppressPackageStartupMessages(library(jsonlite))
fixtures <- list()
add_between <- function(id, a, b, levels=c("First", "Second", "unused")) {
  fixtures[[length(fixtures)+1L]] <<- list(id=id, design="independent",
    values=c(a,b), codes=c(rep(0L,length(a)),rep(1L,length(b))), levels=levels,
    first=levels[1],second=levels[2])
}
add_within <- function(id,a,b) {
  fixtures[[length(fixtures)+1L]] <<- list(id=id,design="paired",a=a,b=b)
}
add_between("hand_unequal_variance",c(2,4,6,8,10),c(1,1,2,3,4,6,9,15))
add_between("one_constant",rep(4,6),c(-1,0,2,4,8))
add_between("equal_means",c(-2,-1,0,1,2),c(-6,-3,0,3,6))
add_between("both_constant",rep(1,4),rep(3,5))
add_between("both_zero",rep(0,3),rep(0,4))
add_between("two_per_group",c(1,5),c(3,8))
add_between("missing_outcomes",c(1,NA,4,9),c(2,3,NA,8,10))
add_between("unicode_literal_NA",c(1,3,5,7),c(0,2,3,6,10),c("NA","測定 B","unused"))
add_between("large_offset",1e9+c(1,3,4,8,10),1e9+c(-2,0,2,3,5,7))
add_between("small_scale",1e-100*c(1,2,5,7),1e-100*c(2,4,6,8,11))
add_between("large_scale",1e100*c(1,2,5,7),1e100*c(2,4,6,8,11))
add_between("essentially_constant",1e15+c(0,.125,.25,.375),1e15+c(.125,.25,.375,.5))
f <- list(id="missing_factor_and_outcome",design="independent",values=c(2,4,NA,7,8,1,NA,5,9,10),
          codes=c(0L,-1L,0L,0L,0L,1L,1L,1L,1L,1L),levels=c("A","B","unused"),first="A",second="B")
fixtures[[length(fixtures)+1L]] <- f
add_within("hand_paired",c(10,12,8,15,9,18),c(8,11,9,12,7,14))
add_within("paired_missing_alignment",c(NA,10,12,8,15,NA,18,9),c(1,8,11,NA,12,7,14,7))
add_within("three_pairs",c(1,2,5),c(2,1,3))
add_within("zero_mean_difference",c(1,4,2,5),c(2,3,3,4))
add_within("constant_difference",c(1,2,4,8),c(0,1,3,7))
add_within("identical_measurements",c(1,2,4,8),c(1,2,4,8))
add_within("paired_one_constant",rep(4,5),c(1,2,4,6,9))
add_within("paired_large_offset",1e9+c(0,2,4,6,8,11),1e9+c(1,0,5,3,7,6))
add_within("paired_small_scale",1e-100*c(1,2,4,8),1e-100*c(0,3,2,5))
add_within("paired_large_scale",1e100*c(1,2,4,8),1e100*c(0,3,2,5))
set.seed(20261111)
for(n in c(5,17,100)) {
  add_between(paste0("normal_n",n),rnorm(n,1,2),rnorm(n+3,2,5))
  add_between(paste0("skewed_n",n),rexp(n),rexp(n+5,.3))
  a <- rnorm(n,10,3);b <- a+rnorm(n,.5,1)
  add_within(paste0("correlated_n",n),a,b)
}

describe <- function(x) list(n=length(x),mean=mean(x),sd=sd(x-x[1]))
reference <- function(a,b,paired,equal,confidence) {
  difference <- if(paired) mean(a-b) else mean(a)-mean(b)
  se <- if(paired) sd(a-b)/sqrt(length(a)) else if(equal) {
    sqrt(((length(a)-1)*var(a)+(length(b)-1)*var(b))/(length(a)+length(b)-2))*
      sqrt(1/length(a)+1/length(b))
  } else sqrt(var(a)/length(a)+var(b)/length(b))
  scale <- if(paired) abs(difference) else max(abs(mean(a)),abs(mean(b)))
  degenerate <- se==0 || se < 10*.Machine$double.eps*scale
  out <- list(difference=difference,stderr=NULL,df=NULL,statistic=NULL,p=NULL,lower=NULL,upper=NULL,
              status=if(degenerate) "degenerate" else "ok")
  if(!degenerate) {
    # Raw Welch's fourth-power denominator under/overflows at 1e-100/1e100.
    # t, df and p are scale-invariant; restore units to SE and CI endpoints.
    magnitude <- max(abs(c(a,b)))
    rescale <- if(magnitude < 1e-50 || magnitude > 1e50) magnitude else 1
    fit <- t.test(a/rescale,b/rescale,paired=paired,var.equal=equal,conf.level=confidence)
    out$stderr <- unname(fit$stderr)*rescale;out$df <- unname(fit$parameter)
    out$statistic <- unname(fit$statistic);out$p <- fit$p.value
    out$lower <- unname(fit$conf.int[1])*rescale;out$upper <- unname(fit$conf.int[2])*rescale
  }
  out
}
for(i in seq_along(fixtures)) {
  f <- fixtures[[i]];paired <- f$design=="paired"
  if(paired) {
    keep <- complete.cases(f$a,f$b);a <- f$a[keep];b <- f$b[keep]
    missing <- list(first=sum(is.na(f$a)),second=sum(is.na(f$b)))
    first_indices <- second_indices <- which(keep)-1L
  } else {
    keep <- !is.na(f$values) & f$codes>=0
    first_indices <- which(keep & f$codes==0L)-1L
    second_indices <- which(keep & f$codes==1L)-1L
    a <- f$values[first_indices+1L];b <- f$values[second_indices+1L]
    missing <- list(outcome=sum(is.na(f$values)),group=sum(f$codes<0))
  }
  expected <- list(n_source=length(keep),n_complete=sum(keep),excluded_missing=sum(!keep),
    retained_indices=as.integer(which(keep)-1L),first_indices=as.integer(first_indices),
    second_indices=as.integer(second_indices),missing_by_role=missing,
    summaries=list(first=describe(a),second=describe(b)),runs=list())
  for(confidence in c(.5,.8,.95,.99,.999)) for(equal in if(paired) FALSE else c(FALSE,TRUE)) {
    expected$runs[[length(expected$runs)+1L]] <- c(list(confidence=confidence,
      method=if(paired) "paired_t" else if(equal) "student" else "welch"),
      reference(a,b,paired,equal,confidence))
  }
  f$expected <- expected;fixtures[[i]] <- f
}
manifest <- list(schema_version=1L,source="Independent base R stats::t.test and explicit complete-case indexing; no target Python called",
  extreme_scale_reference="At magnitude below 1e-50 or above 1e50, t.test uses a common scale divisor; SE/CI endpoints restored to original units. Summary SD uses translation-invariant centering because raw R sd loses precision near 1e15 with 0.125 increments. Raw initial reference is retained locally; no Python values generate targets.",
  R_version=as.character(getRversion()),baseline=list(commit="4c3cbe8de39d6259ee61d5fde28704f45e9cc8ed",
    jjbetweenstats_backend_sha256="0c93805b31adac65d59d29f54cbebdf9b374c34f4fd140e0c8283ac7d98bd9f0",
    jjwithinstats_backend_sha256="a32fecc07edce644ed57f305181f5e39b255fd0cf407f706a6cf539fbe7cafc2"),fixtures=fixtures)
write_json(manifest,"tests/fixtures/estimation-core.json",auto_unbox=TRUE,null="null",na="null",digits=17,pretty=TRUE)
cat(length(fixtures),"datasets frozen;",sum(vapply(fixtures,function(f)length(f$expected$runs),integer(1))),"method/confidence configurations.\n")
