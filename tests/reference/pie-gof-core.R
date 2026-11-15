# Independent base-R and ggstatsplot subtitle oracle; written before Python GOF.
args<-commandArgs(TRUE)
base<-jsonlite::fromJSON('tests/fixtures/pie-core.json',simplifyVector=FALSE)
fixtures<-base$fixtures
make<-function(id,counts,labels=paste0('L',seq_along(counts)))list(id=id,
    inputs=list(codes=as.list(seq_along(counts)-1L),levels=as.list(labels),weights=as.list(counts),ordered=FALSE))
fixtures<-c(fixtures,list(make('expected_exactly_five',c(5,5)),
    make('expected_below_five',c(4,5)),make('df_two_closed_form',c(1,2,3)),
    make('perfect_custom_fit',c(20,40,60)),make('one_active_three_declared',c(0,30,0)),
    make('R_manual_example',c(89,37,30,28,2),LETTERS[1:5])))
subtitle_checks<-list()
for(i in seq_along(fixtures)) {
    a<-fixtures[[i]]$inputs
    codes<-as.integer(unlist(a$codes))
    labels<-vapply(a$levels,function(v)if(is.null(v))NA_character_ else v,'')
    w<-if(is.null(a$weights))rep(1,length(codes)) else vapply(a$weights,function(v)if(is.null(v))NA_real_ else v,0)
    missing<-codes<0L;missing[!missing]<-is.na(labels[codes[!missing]+1L])
    keep<-!missing & !is.na(w);valid<-which(!is.na(labels))
    obs<-vapply(valid,function(k)sum(w[keep & codes==k-1L]),0)
    n<-sum(obs);k<-length(obs)
    runs<-list()
    for(mode in c('equal','custom','scaled')) {
        ratio<-if(mode=='equal')rep(1,k) else seq_len(k)
        if(fixtures[[i]]$id=='R_manual_example' && mode!='equal')ratio<-c(40,20,20,15,5)
        if(mode=='scaled')ratio<-ratio*1e200
        supplied<-if(mode=='equal')NULL else stats::setNames(as.list(ratio),labels[valid])
        prob<-ratio/max(ratio);prob<-prob/sum(prob)
        warnings<-character()
        fit<-withCallingHandlers(tryCatch(stats::chisq.test(obs,p=prob,rescale.p=FALSE,correct=FALSE),error=identity),
            warning=function(w){warnings<<-c(warnings,conditionMessage(w));invokeRestart('muffleWarning')})
        if(k==1L) {
            stopifnot(inherits(fit,'error'))
            expected<-list(enabled=TRUE,status='unavailable',reason='one_declared_category',
                method=NULL,statistic=NULL,df=NULL,p=NULL,minimum_expected=n,expected_below5=as.integer(n<5),
                sparse_warning=n<5,rows=list(list(code=valid-1L,label=labels[valid],observed=obs,
                probability=1,expected=n,pearson_residual=NULL,contribution=NULL)))
        } else {
            stopifnot(!inherits(fit,'error'))
            rows<-lapply(seq_len(k),function(j)list(code=valid[j]-1L,label=labels[valid[j]],observed=obs[j],
                probability=prob[j],expected=as.numeric(fit$expected[j]),
                pearson_residual=as.numeric(fit$residuals[j]),contribution=as.numeric((obs[j]-fit$expected[j])^2/fit$expected[j])))
            expected<-list(enabled=TRUE,status=if(any(fit$expected<5))'sparse_approximation' else 'approximation',
                reason=NULL,method='pearson_chi_square_gof',statistic=as.numeric(fit$statistic),
                df=as.numeric(fit$parameter),p=fit$p.value,minimum_expected=min(fit$expected),
                expected_below5=sum(fit$expected<5),sparse_warning=any(fit$expected<5),rows=rows)
        }
        runs[[length(runs)+1L]]<-list(mode=mode,ratios=supplied,expected=expected,R_warnings=as.list(warnings))
    }
    fixtures[[i]]$runs<-runs
    fixtures[[i]]$expected<-NULL
    # Bounded baseline route: ggpiestats expands frequencies, so keep it small.
    if(k>=2L && k<=4L && n<=1000 && sum(obs>0)>=2L) {
        f<-factor(labels[codes[keep]+1L],levels=labels[valid],ordered=isTRUE(a$ordered))
        d<-data.frame(category=f,frequency=w[keep])
        p<-suppressWarnings(ggstatsplot::ggpiestats(d,x=category,counts=frequency,
            results.subtitle=TRUE,proportion.test=FALSE,bf.message=FALSE))
        actual<-ggstatsplot::extract_stats(p)$subtitle_data
        ref<-runs[[1]]$expected
        stopifnot(abs(actual$statistic-ref$statistic)<1e-10,actual$df==ref$df,
            abs(actual$p.value-ref$p)<1e-10)
        subtitle_checks[[length(subtitle_checks)+1L]]<-list(id=fixtures[[i]]$id,
            statistic=actual$statistic,df=actual$df,p=actual$p.value)
    }
}
result<-list(schema_version=1,baseline_hashes=base$baseline_hashes,
    versions=list(R=as.character(getRversion()),statsExpressions=as.character(packageVersion('statsExpressions')),
        ggstatsplot=as.character(packageVersion('ggstatsplot'))),
    fixtures=fixtures,subtitle_checks=subtitle_checks)
out<-jsonlite::toJSON(result,auto_unbox=TRUE,digits=17,na='null',null='null')
if(length(args))writeLines(out,args[[1]]) else cat(out,'\n')
