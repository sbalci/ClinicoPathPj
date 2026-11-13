#!/usr/bin/env Rscript
# Independent frozen oracle: reads the contract and archived baseline, never the Python engine.
# Numeric JSON atoms use 17 significant digits to preserve neighboring IEEE doubles.
args <- commandArgs(trailingOnly = TRUE)
output <- if (length(args)) args[[1]] else 'tests/fixtures/histogram-core.json'
stopifnot(requireNamespace('jsonlite', quietly = TRUE))
registry_code <- paste0(
  "import json,tarfile,hashlib; r=json.load(open('inst/python/registry.json')); ",
  "items=r if isinstance(r,list) else r.get('analyses',[]); ",
  "walk=lambda x: ([x] if isinstance(x,dict) and x.get('id')=='pyjjhistostats' else ",
  "sum((walk(v) for v in x.values()),[]) if isinstance(x,dict) else ",
  "sum((walk(v) for v in x),[]) if isinstance(x,list) else []); ",
  "b=walk(r)[0]['baseline']['files']; t=tarfile.open('docs/baselines/released-2026-10-25.tar.gz'); ",
  "actual={p:hashlib.sha256(t.extractfile('jjstatsplot/'+p).read()).hexdigest() for p in b}; ",
  "assert actual==b,(actual,b); print(json.dumps(actual,sort_keys=True))")
hashes <- jsonlite::fromJSON(paste(system2('python3', c('-c', shQuote(registry_code)), stdout=TRUE), collapse='\n'))
stopifnot(length(hashes) == 4L)
# Summaries and primary inference use base R. Separate equations check every available test.
close <- function(a,b, tol=2e-12) stopifnot(isTRUE(all.equal(a,b,tolerance=tol,check.attributes=FALSE)))
fixtures <- list()
add <- function(id, values, breaks) fixtures[[length(fixtures)+1L]] <<- list(id=id, values=values, breaks=breaks)
add('hand_three', c(0,1,2), c(0,1,2))
add('outer_and_internal_ties', c(-2,-1,0,1,2,0,1), c(-2,-1,0,1,2))
add('edge_neighbors', c(-.Machine$double.eps,0,.Machine$double.eps,1-.Machine$double.eps/2,1,1+.Machine$double.eps,2), c(-1,0,1,2))
add('tiny_edge_neighbors', c(-1e-100,0,1e-100,1-2^-53,1,1+2^-52), c(-1,0,1,2))
add('nonuniform_sparse', c(-8,-3,-3,-.5,0,1,8,9), c(-10,-3,-1,0,2,3,10))
add('negative_only', c(-9,-8,-7,-4,-2), c(-10,-8,-5,-2))
add('all_zero', rep(0,6), c(-1,0,1))
add('constant_nonzero', rep(3,5), c(0,2,3,4,6))
add('singleton', 1.25, c(0,1,2))
add('n_two', c(-2,4), c(-3,0,4))
add('missing', c(NA,1,NA,2,4,NA,8), c(0,2,4,8))
add('missing_singleton', c(NA,NA,0,NA), c(-1,0,1))
add('asymmetric', c(-1,0,0,0,1,2,3,20), c(-2,0,1,5,25))
add('small_scale', c(-3,-1,0,1,2,7)*1e-100, c(-4,0,1,8)*1e-100)
add('large_scale', c(-3,-1,0,1,2,7)*1e100, c(-4,0,1,8)*1e100)
add('large_offset', 1e12+c(-4,-2,-1,0,1,3,6), 1e12+c(-5,0,2,7))
add('offset_degenerate', 1e15+c(-2,-1,0,1,2), 1e15+c(-3,0,3))
add('fractional', c(-.75,-.5,-.25,0,.25,.5,.75), c(-1,-.5,0,.5,1))
set.seed(12012026)
normal <- rnorm(37,2,1.5)
add('seeded_normal', normal, c(-5,0,1,2,3,4,8))
skew <- rexp(41, .7)
add('seeded_skew', skew, c(0,.5,1,2,4,8,20))
add('shifted_reference', c(8,9,10,11,13), c(7,9,10,12,14))
confidences <- c(.50,.80,.95,.99,.999)
oracle_warnings <- list()
package_discrepancies <- list()
make_fixture <- function(f) {
  source <- f$values; x <- source[!is.na(source)]; n <- length(x)
  mu <- mean(x); s <- if(n>1L) sd(x) else NA_real_
  qs <- quantile(x,c(.25,.5,.75),type=7,names=FALSE)
  # Scale before squaring: secondary moment identity stays valid at extreme units.
  centered <- x-mu; scale <- max(abs(centered))
  secondary_sd <- if(n<2L) NA_real_ else if(scale==0) 0 else scale*sqrt(sum((centered/scale)^2)/(n-1))
  if(n>1L) close(s,secondary_sd)
  histograms <- lapply(c('right','left'),function(closure) {
    right <- closure=='right'
    h <- hist(x,breaks=f$breaks,right=right,include.lowest=TRUE,fuzz=0,plot=FALSE)
    k <- length(f$breaks)-1L
    rows <- lapply(seq_len(k),function(i) {
      lo <- f$breaks[i]; hi <- f$breaks[i+1L]
      lc <- !right || i==1L; uc <- right || i==k
      membership <- (if(lc) x>=lo else x>lo) & (if(uc) x<=hi else x<hi)
      count <- sum(membership)
      stopifnot(count==h$counts[i])
      list(lower=lo,upper=hi,lower_closed=lc,upper_closed=uc,count=count,
           proportion=count/n,density=count/(n*(hi-lo)))
    })
    stopifnot(sum(h$counts)==n)
    close(sum(vapply(rows,function(r)r$proportion,0)),1)
    close(sum(vapply(rows,function(r)r$density*(r$upper-r$lower),0)),1)
    list(closure=closure,rows=rows)
  })
  runs <- list()
  for(ref in c(0,.75)) for(conf in confidences) {
    delta <- mu-ref; se <- if(n>1L) s/sqrt(n) else NA_real_
    status <- if(n<2L) 'insufficient_n' else if(se==0 || se<10*.Machine$double.eps*abs(mu)) 'degenerate' else 'ok'
    run <- list(reference=ref,confidence=conf,status=status,difference=delta,stderr=NULL,df=NULL,
      statistic=NULL,p=NULL,mean_lower=NULL,mean_upper=NULL,difference_lower=NULL,difference_upper=NULL)
    if(status=='ok') {
      tt <- withCallingHandlers(t.test(x,mu=ref,conf.level=conf,alternative='two.sided'),
        warning=function(w) {oracle_warnings[[length(oracle_warnings)+1L]] <<- list(id=f$id,reference=ref,confidence=conf,message=conditionMessage(w));invokeRestart('muffleWarning')})
      statistic <- delta/se; p <- 2*pt(-abs(statistic),df=n-1)
      margin <- qt((1+conf)/2,n-1)*se
      close(unname(tt$statistic),statistic); close(tt$p.value,p)
      # R t.test computes limits as (t +/- quantile)*SE + mu.
      close(as.numeric(tt$conf.int), c(mu-margin,mu+margin),tol=2e-7)
      run$stderr <- unname(tt$stderr); run$df <- unname(tt$parameter)
      run$statistic <- unname(tt$statistic); run$p <- tt$p.value
      run$mean_lower <- unname(tt$conf.int[1]);run$mean_upper <- unname(tt$conf.int[2])
      run$difference_lower <- run$mean_lower-ref;run$difference_upper <- run$mean_upper-ref
    } else {
      attempt <- tryCatch(t.test(x,mu=ref,conf.level=conf),error=function(e)e)
      if(!inherits(attempt,'error')) {
        stopifnot(se==0)
        package_discrepancies[[length(package_discrepancies)+1L]] <<- list(id=f$id,reference=ref,confidence=conf,message='Base R t.test returns a result at mean=SE=0; frozen contract explicitly marks zero SE degenerate.')
      }
    }
    runs[[length(runs)+1L]] <- run
  }
  list(id=f$id,values=source,breaks=f$breaks,histograms=histograms,
       summary=list(n=n,mean=mu,sd=if(n>1L)s else NULL,minimum=min(x),q1=qs[1],median=qs[2],q3=qs[3],maximum=max(x)),
       retained_indices=which(!is.na(source))-1L,n_source=length(source),n_complete=n,
       excluded_missing=sum(is.na(source)),runs=runs)
}
result <- lapply(fixtures,make_fixture)
manifest <- list(schema_version=1L,versions=list(R=R.version.string,stats=as.character(packageVersion('stats')),jsonlite=as.character(packageVersion('jsonlite'))),
  baseline_hashes_verified=hashes,oracle_warnings=oracle_warnings,package_discrepancies=package_discrepancies,
  baseline_discrepancy='YAML statistic-selector help excludes Shapiro-Wilk; archived backend conditionally computes it. No normality classifier is implemented in this core.',
  fixtures=result)
# Encode atomic vectors as arrays even at length one; list scalars retain JSON scalar types.
encode <- function(x, force_array=FALSE) {
  if(is.null(x)) return('null')
  if(is.list(x)) {
    if(!is.null(names(x))) return(paste0('{',paste(vapply(names(x),function(k)paste0(jsonlite::toJSON(k,auto_unbox=TRUE),':',encode(x[[k]],force_array=k %in% c('values','breaks','retained_indices'))),''),collapse=','),'}'))
    return(paste0('[',paste(vapply(x,encode,''),collapse=','),']'))
  }
  atom <- function(v) {
    if(is.na(v)) return('null')
    if(is.character(v)) return(as.character(jsonlite::toJSON(v,auto_unbox=TRUE)))
    if(is.logical(v)) return(if(v)'true' else 'false')
    stopifnot(is.finite(v)); sprintf('%.17g',v)
  }
  if(force_array || length(x)!=1L) paste0('[',paste(vapply(x,atom,''),collapse=','),']') else atom(x)
}
writeLines(encode(manifest), output, useBytes=TRUE)
parsed <- jsonlite::fromJSON(output,simplifyVector=FALSE)
for(i in seq_along(result)) for(field in c('values','breaks')) {
  restored <- vapply(parsed$fixtures[[i]][[field]],function(v)if(is.null(v)) NA_real_ else v,0)
  stopifnot(identical(as.double(restored),as.double(result[[i]][[field]])))
}
cat(sprintf('PASS: %d fixtures, %d histograms, %d test runs; exact double input round-trip; %d warnings.\n',length(result),2*length(result),10*length(result),length(oracle_warnings)))
