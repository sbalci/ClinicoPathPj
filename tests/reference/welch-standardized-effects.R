# Independent references; no target Python calls. Run from module root.
suppressPackageStartupMessages(library(jsonlite))
input <- read_json('tests/fixtures/estimation-core.json',simplifyVector=FALSE)
vec <- function(x) vapply(x,function(v) if(is.null(v)) NA_real_ else as.numeric(v),numeric(1))
J <- function(df) if(df<=1) NULL else exp(lgamma(df/2)-lgamma((df-1)/2)-log(df/2)/2)
limits <- function(t,df,confidence) {
  bound<-max(10,abs(t)*4+10);tail<-(1-confidence)/2
  root<-function(p) uniroot(function(nc) suppressWarnings(pt(t,df,ncp=nc))-p,
                           c(-bound,bound),tol=1e-11,maxiter=1000L)$root
  c(root(1-tail),root(tail))
}
fixtures<-Filter(function(f)f$design=='independent',input$fixtures)
extra<-function(id,a,b) list(id=id,design='independent',values=as.list(c(a,b)),
  codes=as.list(c(rep(0L,length(a)),rep(1L,length(b)))),levels=list('First','Second','unused'),
  first='First',second='Second',expected=NULL)
fixtures<-c(fixtures,list(extra('one_constant_df1',c(2,2),c(1,5)),
  extra('unequal_n_variance',c(1,4,9),c(-2,0,1,2,3,4,5,6,8,9)),
  extra('dominant_variance',c(-20,0,20),c(1,1.001,1.002,1.003))))
package_checks<-0L;maximum_package_difference<-0
for(i in seq_along(fixtures)) {
  f<-fixtures[[i]];y<-vec(f$values);codes<-vec(f$codes)
  keep<-!is.na(y)&codes>=0;a<-y[keep & codes==0];b<-y[keep & codes==1]
  # Respect the frozen raw engine's essentially-constant guard, independently.
  scale<-max(abs(c(a,b)));rescale<-if(scale>0&&(scale>1e50||scale<1e-50))scale else 1
  aa<-a/rescale;bb<-b/rescale;v1<-var(aa-aa[1]);v2<-var(bb-bb[1]);n1<-length(a);n2<-length(b)
  difference<-mean(aa)-mean(bb);se<-sqrt(v1/n1+v2/n2);sd0<-sqrt((v1+v2)/2)
  degenerate<-se==0||se<10*.Machine$double.eps*max(abs(c(mean(aa),mean(bb))))
  runs<-list()
  for(confidence in c(.5,.8,.95,.99,.999)) {
    r<-list(confidence=confidence,d_rms=NULL,standardizer_sd=NULL,welch_df=NULL,sd_moment_df=NULL,
      welch_J=NULL,welch_J_point=NULL,ncp_lower=NULL,ncp_upper=NULL,delta_lower=NULL,
      delta_upper=NULL,status='degenerate')
    if(!degenerate) {
      u<-v1/n1;v<-v2/n2;df<-(u+v)^2/(u^2/(n1-1)+v^2/(n2-1))
      sd_df<-(v1+v2)^2/(v1^2/(n1-1)+v2^2/(n2-1));d<-difference/sd0;t<-difference/se
      r$d_rms<-d;r$standardizer_sd<-sd0*rescale;r$welch_df<-df;r$sd_moment_df<-sd_df
      r$welch_J<-J(df);r$welch_J_point<-if(df<=1)NULL else J(df)*d
      r$status<-'interval_unavailable'
      if(df>=2&&df<=100000&&abs(t)<=40) {
        lim<-limits(t,df,confidence);r$ncp_lower<-lim[1];r$ncp_upper<-lim[2]
        r$delta_lower<-lim[1]*se/sd0;r$delta_upper<-lim[2]*se/sd0;r$status<-'ok'
      }
      if(scale>1e-6&&scale<1e6&&confidence==.95&&df>1) {
        es<-as.data.frame(effectsize::cohens_d(a,b,pooled_sd=FALSE,ci=.95,verbose=FALSE))
        hg<-as.data.frame(effectsize::hedges_g(a,b,pooled_sd=FALSE,ci=.95,verbose=FALSE))
        errors<-c(es$Cohens_d-d,hg$Hedges_g-r$welch_J_point)
        if(r$status=='ok')errors<-c(errors,es$CI_low-r$delta_lower,es$CI_high-r$delta_upper)
        stopifnot(max(abs(errors))<2e-4)
        maximum_package_difference<-max(maximum_package_difference,max(abs(errors)))
        package_checks<-package_checks+length(errors)
        tt<-t.test(a,b);stopifnot(abs(unname(tt$statistic)-t)<1e-10,
                                 abs(unname(tt$parameter)-df)<1e-10)
        package_checks<-package_checks+2L
      }
    }
    runs[[length(runs)+1L]]<-r
  }
  f$expected<-NULL;f$runs<-runs;fixtures[[i]]<-f
}
write_json(list(schema_version=1L,source='Independent R formulas, pt/uniroot, stats::t.test and effectsize; no target Python',
 R_version=as.character(getRversion()),effectsize_version=as.character(packageVersion('effectsize')),
 package_cross_checks=package_checks,maximum_package_difference=maximum_package_difference,fixtures=fixtures),
 'tests/fixtures/welch-standardized-effects.json',auto_unbox=TRUE,null='null',na='null',digits=17,pretty=TRUE)

# Prespecified screen in docs/python-welch-standardized-effects.md.
set.seed(12112026);designs<-list(c(5,5,1,1),c(5,20,4,1),c(20,5,4,1),
 c(5,20,1,4),c(20,5,1,4),c(30,30,4,1));profiles<-list();draws<-list();k<-0L
for(design in designs)for(delta in c(0,1.5)) {
  k<-k+1L;n1<-design[1];n2<-design[2];s1<-design[3];s2<-design[4];N<-2000L
  z<-rnorm(N);q1<-rchisq(N,n1-1);q2<-rchisq(N,n2-1)
  v1<-s1^2*q1/(n1-1);v2<-s2^2*q2/(n2-1)
  observed<-delta*sqrt((s1^2+s2^2)/2)+sqrt(s1^2/n1+s2^2/n2)*z
  se<-sqrt(v1/n1+v2/n2);sd0<-sqrt((v1+v2)/2);t<-observed/se
  df<-(v1/n1+v2/n2)^2/((v1/n1)^2/(n1-1)+(v2/n2)^2/(n2-1))
  p<-pt(t,df,ncp=delta*sd0/se)
  supported<-df>=2&df<=100000&abs(t)<=40;included<-supported&p>=.025&p<=.975
  successes<-sum(included);tail<-.05/(2*12)
  lower<-if(successes==0)0 else qbeta(tail,successes,N-successes+1)
  upper<-if(successes==N)1 else qbeta(1-tail,successes+1,N-successes)
  status<-if(upper<.925)'fail' else if(lower>=.925)'pass' else 'inconclusive'
  profiles[[k]]<-list(id=k,n1=n1,n2=n2,sigma1=s1,sigma2=s2,delta=delta,
    N=N,successes=successes,unsupported=sum(!supported),coverage=successes/N,
    lower=lower,upper=upper,status=status)
  draws[[k]]<-data.frame(profile=k,z=z,q1=q1,q2=q2,R_probability=p)
}
write.table(do.call(rbind,draws),'tests/fixtures/welch-standardized-coverage.csv',
 sep=',',row.names=FALSE,col.names=TRUE,quote=FALSE)
write_json(list(schema_version=1L,seed=12112026L,confidence=.95,minimum=.925,
 family_confidence=.95,profiles=profiles),'tests/fixtures/welch-standardized-coverage.json',
 auto_unbox=TRUE,digits=17,pretty=TRUE)
cat(length(fixtures),'datasets;',length(fixtures)*5,'configurations;',package_checks,'package checks; coverage:',
 paste(vapply(profiles,function(p)p$status,character(1)),collapse=', '),'\n')
