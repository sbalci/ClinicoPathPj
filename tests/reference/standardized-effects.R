# Independent base-R noncentral-t inversion, with package and mixture cross-checks.
suppressPackageStartupMessages(library(jsonlite))
input <- read_json("tests/fixtures/estimation-core.json", simplifyVector=FALSE)
vec <- function(x) vapply(x,function(v) if(is.null(v)) NA_real_ else as.numeric(v),numeric(1))
normal_mixture <- function(t,df,ncp) {
  # Condition on standard normal Z, integrating over a bounded region with
  # omitted normal-tail probability below 4e-33. This avoids an endpoint-step
  # singularity in the initial probability-quantile integral at large t.
  stopifnot(t>0)
  integrate(function(z) dnorm(z)*ifelse(z+ncp<=0,1,
      pchisq(df*(pmax(0,z+ncp)/t)^2,df,lower.tail=FALSE)), -12,12,
      rel.tol=2e-11,abs.tol=2e-12,subdivisions=2000L)$value
}
limits <- function(t,df,confidence,cdf=function(nc) pt(t,df,ncp=nc)) {
  tail <- (1-confidence)/2
  bound <- max(10,abs(t)*4+10)
  solve <- function(prob) uniroot(function(nc)cdf(nc)-prob,
      c(-bound,bound),tol=1e-11,maxiter=1000L)$root
  list(ncp_lower=solve(1-tail),ncp_upper=solve(tail))
}
J <- function(df) exp(lgamma(df/2)-lgamma((df-1)/2)-log(df/2)/2)
fixtures <- list(); package_checks <- 0L; max_package_error <- 0
for(f in input$fixtures) {
  paired <- f$design=="paired"
  if(paired) {
    a <- vec(f$a);b <- vec(f$b);keep <- complete.cases(a,b);a<-a[keep];b<-b[keep]
  } else {
    y <- vec(f$values);g<-vec(f$codes);a<-y[!is.na(y)&g==0];b<-y[!is.na(y)&g==1]
  }
  # Independent reference inputs and inferential status were already frozen by base R.
  runs <- Filter(function(r) r$method==if(paired)"paired_t" else "student", f$expected$runs)
  expected <- list()
  for(r in runs) {
    out <- list(confidence=r$confidence,cohens_d=NULL,hedges_g=NULL,correction=NULL,
                standardizer_sd=NULL,df=NULL,ncp_lower=NULL,ncp_upper=NULL,
                delta_lower=NULL,delta_upper=NULL,status=r$status)
    if(r$status=="ok") {
      df<-if(paired) length(a)-1 else length(a)+length(b)-2
      # Scale/translate moments before squaring, independently of target Python.
      magnitude<-max(abs(c(a,b)));rescale<-if(magnitude<1e-50||magnitude>1e50)magnitude else 1
      aa<-a/rescale;bb<-b/rescale
      sd0<-if(paired)sd(aa-bb) else sqrt(((length(a)-1)*var(aa-aa[1])+(length(b)-1)*var(bb-bb[1]))/df)
      diff<-if(paired)mean(aa-bb) else mean(aa)-mean(bb)
      d<-diff/sd0; factor<-if(paired)1/sqrt(length(a)) else sqrt(1/length(a)+1/length(b))
      statistic<-d/factor
      lim<-limits(statistic,df,r$confidence)
      out<-c(list(confidence=r$confidence,cohens_d=d,hedges_g=J(df)*d,correction=J(df),
                  standardizer_sd=sd0*rescale,df=df),lim,
             list(delta_lower=lim$ncp_lower*factor,delta_upper=lim$ncp_upper*factor,status="ok"))
      # Package agreement is a separate cross-check at ordinary magnitudes.
      if(magnitude<1e6 && magnitude>1e-6 && r$confidence==.95) {
        es<-as.data.frame(effectsize::cohens_d(a,b,paired=paired,pooled_sd=TRUE,ci=.95,verbose=FALSE))
        hg<-as.data.frame(effectsize::hedges_g(a,b,paired=paired,pooled_sd=TRUE,ci=.95,verbose=FALSE))
        delta<-max(abs(c(es$Cohens_d-d,hg$Hedges_g-J(df)*d,
                        es$CI_low-out$delta_lower,es$CI_high-out$delta_upper)))
        stopifnot(delta<2e-4);max_package_error<-max(max_package_error,delta);package_checks<-package_checks+4L
        mb<-if(paired) MBESS::ci.sm(sm=d,N=length(a),conf.level=.95) else MBESS::ci.smd(smd=d,n.1=length(a),n.2=length(b),conf.level=.95)
        bounds<-if(paired)c(mb$Lower.Conf.Limit.Standardized.Mean,mb$Upper.Conf.Limit.Standardized.Mean) else c(mb$Lower.Conf.Limit.smd,mb$Upper.Conf.Limit.smd)
        stopifnot(length(bounds)==2L,max(abs(bounds-c(out$delta_lower,out$delta_upper)))<2e-4)
        package_checks<-package_checks+2L
      }
    }
    expected[[length(expected)+1L]]<-out
  }
  f$expected<-NULL;f$runs<-expected;fixtures[[length(fixtures)+1L]]<-f
}
grid<-list()
for(df in c(2,3,10,100,10000,99998)) for(t in c(-12,-4,-.1,0,.1,4,12)) for(confidence in c(.5,.8,.95,.99,.999)) {
  lim<-limits(t,df,confidence)
  grid[[length(grid)+1L]]<-c(list(t=t,df=df,confidence=confidence,oracle="base R pt/uniroot"),lim)
}
# R pt can warn while evaluating the wide root brackets. Audit every final
# endpoint with the independent normal/chi-square representation, including
# negative and zero t, rather than treating a successful uniroot as validation.
mixture_residual <- 0
for(r in grid) {
  cdf <- function(nc) if(r$t==0) pnorm(-nc) else if(r$t>0) {
    normal_mixture(r$t,r$df,nc)
  } else 1-normal_mixture(-r$t,r$df,-nc)
  tail<-(1-r$confidence)/2
  residual<-max(abs(c(cdf(r$ncp_lower),cdf(r$ncp_upper))-c(1-tail,tail)))
  stopifnot(residual<2e-8)
  mixture_residual<-max(mixture_residual,residual)
}
mixture<-list()
for(df in c(2,5,30,10000,99998)) for(t in c(12,40)) for(confidence in c(.95,.999)) {
  lim<-limits(t,df,confidence,function(nc)normal_mixture(t,df,nc))
  mixture[[length(mixture)+1L]]<-c(list(t=t,df=df,confidence=confidence,oracle="normal/chi-square probability mixture integral"),lim)
}
manifest<-list(schema_version=1L,source="Independent base R pt/uniroot; normal/chi-square mixture integration; effectsize/MBESS cross-checks; no target Python called",
 R_version=as.character(getRversion()),effectsize=as.character(packageVersion("effectsize")),MBESS=as.character(packageVersion("MBESS")),
 package_cross_checks=package_checks,maximum_package_difference=max_package_error,
 pt_endpoint_mixture_checks=length(grid)*2L,maximum_mixture_probability_residual=mixture_residual,
 interval_target="Population delta/delta_z; unscaled by J. Hedges g point only; not effectsize J-scaled g CI parity.",
 fixtures=fixtures,inversion_grid=grid,mixture_grid=mixture)
write_json(manifest,"tests/fixtures/standardized-effects.json",auto_unbox=TRUE,null="null",na="null",digits=17,pretty=TRUE)
cat(length(fixtures),"datasets;",sum(vapply(fixtures,function(f)length(f$runs),integer(1))),"configurations;",length(grid),"pt grid;",length(mixture),"mixture grid;",package_checks,"package cross-checks.\n")
