std_native_args <- function(f) {
    nums<-function(x)vapply(x,function(v)if(is.null(v))NA_real_ else as.numeric(v),numeric(1))
    paired<-f$design=='paired'
    if(paired) {
        d<-data.frame(First=nums(f$a),Second=nums(f$b))
        args<-list(dep1='First',dep2='Second')
    } else {
        codes<-as.integer(unlist(f$codes));labels<-unlist(f$levels)
        d<-data.frame(Outcome=nums(f$values),Group=factor(ifelse(codes<0,NA_character_,labels[pmax(1,codes+1)]),levels=labels))
        args<-list(dep='Outcome',group='Group',firstLevel=f$first,secondLevel=f$second,varequal=TRUE)
    }
    rownames(d)<-as.character(seq_len(nrow(d))*3+7)
    c(list(data=d),args,list(showStandardized=TRUE,showCases=TRUE,showPlot=TRUE))
}

test_that('native standardized outputs match independent R references', {
    refs<-jsonlite::fromJSON(testthat::test_path('..','fixtures','standardized-effects.json'),simplifyVector=FALSE)
    for(f in refs$fixtures) {
        args<-std_native_args(f);paired<-f$design=='paired'
        got<-do.call(if(paired)pyjjwithinstats else pyjjbetweenstats,args)
        ref<-Filter(function(r)r$confidence==.95,f$runs)[[1]]
        row<-got$standardized$asDF
        for(key in c(estimate='cohens_d',sd='standardizer_sd',df='df',lower='delta_lower',upper='delta_upper')) {
            column<-names(c(estimate='cohens_d',sd='standardizer_sd',df='df',lower='delta_lower',upper='delta_upper'))[
                c(estimate='cohens_d',sd='standardizer_sd',df='df',lower='delta_lower',upper='delta_upper')==key]
            expected<-ref[[key]];observed<-if(column%in%c('sd','df'))got$standardizer$asDF[[column]][1] else row[[column]][1]
            if(is.null(expected))expect_true(is.na(observed),info=paste(f$id,key))
            else expect_true(abs(observed-expected)<=2e-7*max(1,abs(expected)),info=paste(f$id,key))
        }
        expect_equal(row$status,ref$status,info=f$id)
        expect_equal(row$metric,if(paired)'Cohen d_z' else 'Cohen d')
        expect_equal(got$standardizer$asDF$denominator,if(paired)'Within-row difference SD' else 'Sample-size-weighted pooled SD')
        for(key in c(estimate='hedges_g',correction='correction')) {
            column<-if(key=='hedges_g')'estimate' else 'correction'
            expected<-ref[[key]];observed<-got$hedges$asDF[[column]][1]
            if(is.null(expected))expect_true(is.na(observed),info=f$id)
            else expect_true(abs(observed-expected)<=abs(expected)*1e-10,info=f$id)
        }
        expect_false(any(c('lower','upper')%in%names(got$hedges$asDF)))
        expect_equal(got$hedges$asDF$metric,if(paired)'Hedges g_z (point only)' else 'Hedges g (point only)')
        roles<-if(paired)c('First','Second') else c('Outcome','Group')
        expect_equal(got$cases$asDF$sourceID,rownames(args$data)[complete.cases(args$data[roles])])
        if(ref$status=='degenerate')expect_null(got$standardizedPlot$state)
        else expect_false(is.null(got$standardizedPlot$state))
    }
})

test_that('native standardized options clear only their own output and recover', {
    refs<-jsonlite::fromJSON(testthat::test_path('..','fixtures','standardized-effects.json'),simplifyVector=FALSE)
    for(paired in c(FALSE,TRUE)) {
        f<-Filter(function(f)(f$design=='paired')==paired,refs$fixtures)[[1]]
        args<-std_native_args(f);d<-args$data;args$data<-NULL
        d$Subject<-sprintf('S%03d',seq_len(nrow(d)));args$subject<-'Subject'
        prefix<-if(paired)'pyjjwithinstats' else 'pyjjbetweenstats'
        fn<-get(prefix)
        opts<-do.call(get(paste0(prefix,'Options'))$new,args)
        a<-get(paste0(prefix,'Class'))$new(options=opts)
        a$.setReadDatasetSource(function(...)d);a$.setReadDatasetHeaderSource(function(...)d)
        set_option<-function(n,v){o<-opts$option(n);o$value<-v}
        a$init();a$run()
        original_raw<-a$results$contrast$asDF
        original_std<-a$results$standardized$asDF;original_g<-a$results$hedges$asDF
        original_cases<-a$results$cases$asDF
        set_option('showStandardized',FALSE);a$init();a$run()
        expect_equal(a$results$standardized$rowCount,0);expect_equal(a$results$standardizer$rowCount,0)
        expect_equal(a$results$hedges$rowCount,0);expect_null(a$results$standardizedPlot$state)
        expect_equal(a$results$contrast$asDF,original_raw)
        expect_equal(a$results$cases$asDF,original_cases)
        set_option('showStandardized',TRUE);a$init();a$run()
        expect_equal(a$results$standardized$asDF,original_std)
        fresh<-do.call(fn,c(list(data=d),args))
        expect_equal(a$results$standardized$asDF,fresh$standardized$asDF)
        if(!paired) {
            set_option('varequal',FALSE);a$init();a$run()
            expect_equal(a$results$standardized$rowCount,0);expect_equal(a$results$standardizer$rowCount,0)
            expect_equal(a$results$hedges$rowCount,0);expect_null(a$results$standardizedPlot$state)
            expect_equal(a$results$contrast$asDF$method,'Welch independent t-test')
            fresh_args<-args;fresh_args$varequal<-FALSE;fresh_args$showStandardized<-FALSE
            fresh<-do.call(fn,c(list(data=d),fresh_args))
            expect_equal(a$results$contrast$asDF,fresh$contrast$asDF)
            set_option('varequal',TRUE);a$init();a$run()
            expect_equal(a$results$standardized$asDF,original_std)
        }
        role<-if(paired)'dep2' else 'secondLevel';previous<-args[[role]]
        set_option(role,NULL);a$init();a$run()
        for(n in c('standardizer','standardized','hedges','contrast','cases'))expect_equal(a$results$get(n)$rowCount,0)
        expect_null(a$results$standardizedPlot$state);expect_null(a$results$differencePlot$state)
        set_option(role,previous);a$init();a$run()
        expect_equal(a$results$standardized$asDF,original_std)
        d$Subject[]<-'repeated';a$init();expect_error(a$run(),'unique')
        expect_equal(a$results$standardized$rowCount,0);expect_equal(a$results$standardizer$rowCount,0);expect_null(a$results$standardizedPlot$state)
        d$Subject<-sprintf('S%03d',seq_len(nrow(d)));a$init();a$run()
        expect_equal(a$results$hedges$asDF,original_g)
        preserved_data<-d
        if(paired)d$First<-d$Second+1 else {
            d$Outcome<-ifelse(d$Group==args$firstLevel,1,3)
        }
        a$init();a$run()
        expect_equal(a$results$standardized$asDF$status,'degenerate')
        expect_null(a$results$standardizedPlot$state)
        expect_true(is.na(a$results$hedges$asDF$estimate))
        d<-preserved_data;a$init();a$run()
        expect_equal(a$results$standardized$asDF,original_std)
        set_option('showPlot',FALSE);a$init();a$run()
        expect_null(a$results$differencePlot$state)
        expect_false(is.null(a$results$standardizedPlot$state))
        set_option('showPlot',TRUE);a$init();a$run()
        set_option('conflevel',.8);a$init();a$run()
        expect_equal(a$results$standardized$asDF$confidence,.8)
        expect_lt(a$results$standardized$asDF$upper-a$results$standardized$asDF$lower,original_std$upper-original_std$lower)
        expect_equal(a$results$standardized$asDF$estimate,original_std$estimate)
        expect_equal(a$results$hedges$asDF,original_g)
        saved<-tempfile(fileext='.rds');saveRDS(a$results$standardizedPlot$state,saved)
        a$results$standardizedPlot$setState(readRDS(saved));a$.__enclos_env__$private$.data<-NULL
        path<-tempfile(fileext='.png');a$results$standardizedPlot$saveAs(path)
        expect_true(file.exists(path));expect_gt(file.info(path)$size,1000)
    }
})

test_that('unavailable native limits retain finite points without fabricated intervals', {
    d<-data.frame(a=c(101,103,107),b=c(0,1,4))
    result<-pyjjwithinstats(data=d,dep1='a',dep2='b',showStandardized=TRUE)
    expect_equal(result$standardized$asDF$status,'interval_unavailable')
    expect_true(is.finite(result$standardized$asDF$estimate))
    expect_true(is.na(result$standardized$asDF$lower));expect_true(is.na(result$standardized$asDF$upper))
    expect_equal(result$hedges$asDF$status,'point_available')
    expect_false(is.null(result$standardizedPlot$state))
    path<-tempfile(fileext='.png');result$standardizedPlot$saveAs(path)
    expect_gt(file.info(path)$size,1000)
    d$a<-c(1,2,4);d$b<-c(0,1,3)
    result<-pyjjwithinstats(data=d,dep1='a',dep2='b',showStandardized=TRUE)
    expect_equal(result$standardized$asDF$status,'degenerate')
    expect_true(is.na(result$standardized$asDF$estimate));expect_null(result$standardizedPlot$state)
})
