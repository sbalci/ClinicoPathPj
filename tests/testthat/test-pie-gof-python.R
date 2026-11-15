gof_data<-function(f) {
    a<-f$inputs
    labels<-vapply(a$levels,function(v)if(is.null(v))NA_character_ else v,'')
    codes<-as.integer(unlist(a$codes));values<-labels[pmax(1,codes+1L)]
    values[codes<0L]<-NA_character_
    d<-data.frame(Outcome=factor(values,levels=labels,exclude=NULL,ordered=isTRUE(a$ordered)))
    if(!is.null(a$weights))d$Frequency<-vapply(a$weights,function(v)if(is.null(v))NA_real_ else as.numeric(v),0)
    rownames(d)<-as.character(seq_len(nrow(d))*9L+4L)
    d
}

test_that('native fixed-null tables match all independent reference configurations', {
    refs<-jsonlite::fromJSON(testthat::test_path('..','fixtures','pie-gof-core.json'),simplifyVector=FALSE)
    for(f in refs$fixtures)for(run in f$runs) {
        d<-gof_data(f);ref<-run$expected
        args<-list(data=d,dep='Outcome',resultssubtitle=TRUE,
            customRatios=!is.null(run$ratios),ratio=if(is.null(run$ratios))'' else
                as.character(jsonlite::toJSON(run$ratios,auto_unbox=TRUE,digits=17)))
        if('Frequency'%in%names(d))args$counts<-'Frequency'
        got<-do.call(pyjjpiestats,args);test<-got$gof$asDF;expected<-got$expected$asDF
        for(key in c('statistic','df','p')) {
            if(is.null(ref[[key]]))expect_true(is.na(test[[key]]),info=paste(f$id,key))
            else expect_true(abs(test[[key]]-ref[[key]])<=max(1e-12,abs(ref[[key]])*1e-10),info=paste(f$id,key))
        }
        expect_equal(test$small,as.integer(ref$expected_below5),info=f$id)
        expect_equal(test$null,if(is.null(run$ratios))'Equal probabilities' else 'Custom labelled ratios')
        labels<-vapply(ref$rows,function(v)v$label,'')
        if(f$id=='ordinal_unicode')labels[3]<-'< A & B>'
        expect_equal(expected$category,labels,info=f$id)
        # The R bridge removes genuine missing levels before transporting the factor.
        expect_equal(expected$code,seq_along(ref$rows)-1L,info=f$id)
        expect_equal(got$frequencies$asDF$code,expected$code,info=f$id)
        for(pair in list(c('observed','observed'),c('probability','probability'),c('expected','expected'),
                         c('residual','pearson_residual'),c('contribution','contribution'))) {
            want<-vapply(ref$rows,function(v)if(is.null(v[[pair[2]]]))NA_real_ else as.numeric(v[[pair[2]]]),0)
            expect_equal(as.numeric(expected[[pair[1]]]),want,tolerance=2e-12,info=paste(f$id,pair[1]))
        }
        expect_equal(got$cohort$asDF$total,sum(expected$observed),info=f$id)
        expect_false(is.null(got$piePlot$state),info=f$id)
    }
})

test_that('native custom mapping errors clear results and recover without stale inference', {
    d<-data.frame(Outcome=factor(c('A','B',NA),levels=c('A','B','Zero')),Frequency=c(12,8,2))
    opts<-pyjjpiestatsOptions$new(dep='Outcome',counts='Frequency',resultssubtitle=TRUE,
        customRatios=TRUE,ratio='{"A":3,"B":2,"Zero":1}',showCases=TRUE)
    a<-pyjjpiestatsClass$new(options=opts)
    a$.setReadDatasetSource(function(...)d);a$.setReadDatasetHeaderSource(function(...)d)
    set_option<-function(n,v){o<-opts$option(n);o$value<-v}
    a$init();a$run();original<-a$results$gof$asDF;frequencies<-a$results$frequencies$asDF
    plot<-a$results$piePlot$state
    set_option('ratio','{"B":2,"Zero":1,"A":3}');a$init();a$run()
    expect_equal(a$results$gof$asDF,original);expect_equal(a$results$piePlot$state,plot)
    for(value in c('{"A":1,"A":2,"B":1,"Zero":1}','{"A":1,"B":1}',
                  '{"A":0,"B":1,"Zero":1}','1,2,3')) {
        set_option('ratio',value);a$init();expect_error(a$run())
        for(name in c('cohort','frequencies','gof','expected','cases'))expect_equal(a$results$get(name)$rowCount,0)
        expect_null(a$results$piePlot$state)
    }
    set_option('resultssubtitle',FALSE);a$init();a$run()
    expect_equal(a$results$frequencies$asDF,frequencies)
    expect_equal(a$results$gof$rowCount,0);expect_equal(a$results$expected$rowCount,0)
    expect_equal(a$results$piePlot$state,plot)
    set_option('resultssubtitle',TRUE);set_option('customRatios',FALSE);a$init();a$run()
    expect_equal(a$results$gof$asDF$null,'Equal probabilities')
    set_option('showExpected',FALSE);a$init();a$run()
    expect_equal(a$results$expected$rowCount,0);expect_equal(a$results$gof$rowCount,1)
    set_option('dep',NULL);a$init();a$run()
    for(name in c('cohort','frequencies','gof','expected','cases'))expect_equal(a$results$get(name)$rowCount,0)
    set_option('dep','Outcome');set_option('showExpected',TRUE);set_option('customRatios',TRUE)
    set_option('ratio','{"A":3,"B":2,"Zero":1}');a$init();a$run()
    expect_equal(a$results$gof$asDF,original)
    # Restore the drawing state without analysis data: inference cannot be rerun by rendering.
    file<-tempfile(fileext='.rds');saveRDS(a$results$piePlot$state,file)
    a$results$piePlot$setState(readRDS(file));a$.__enclos_env__$private$.data<-NULL
    output<-'/private/tmp/cpj-pie-gof-restored.png'
    a$results$piePlot$saveAs(output);expect_true(file.exists(output));expect_gt(file.info(output)$size,1000)
})
