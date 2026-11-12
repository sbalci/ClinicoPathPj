estimation_args <- function(f, equal=FALSE) {
    numeric_values <- function(x) vapply(x,function(v)if(is.null(v))NA_real_ else as.numeric(v),numeric(1))
    if(f$design=='paired') {
        data<-data.frame(First=numeric_values(f$a),Second=numeric_values(f$b))
        args<-list(dep1='First',dep2='Second')
    } else {
        labels<-unlist(f$levels);codes<-as.integer(unlist(f$codes))
        data<-data.frame(Outcome=numeric_values(f$values),Group=factor(ifelse(codes<0,NA_character_,labels[pmax(1,codes+1)]),levels=labels))
        args<-list(dep='Outcome',group='Group',firstLevel=f$first,secondLevel=f$second,varequal=equal)
    }
    rownames(data)<-as.character(seq_len(nrow(data))*3+7)
    c(list(data=data),args,list(showCases=TRUE,showPlot=TRUE))
}

test_that('native estimation tables match independent R fixtures', {
    ref<-jsonlite::fromJSON(testthat::test_path('..','fixtures','estimation-core.json'),simplifyVector=FALSE)
    for(f in ref$fixtures) for(equal in if(f$design=='paired')FALSE else c(FALSE,TRUE)) {
        args<-estimation_args(f,equal)
        fn<-if(f$design=='paired')pyjjwithinstats else pyjjbetweenstats
        got<-do.call(fn,args)
        method<-if(f$design=='paired')'paired_t' else if(equal)'student' else 'welch'
        e<-Filter(function(r)r$confidence==.95 && r$method==method,f$expected$runs)[[1]]
        expect_equal(got$cohort$asDF$retained,as.integer(f$expected$n_complete),info=f$id)
        expect_equal(got$cohort$asDF$excluded,as.integer(f$expected$excluded_missing),info=f$id)
        for(key in c('difference','stderr','df','statistic','p','lower','upper')) {
            value<-e[[key]];observed<-got$contrast$asDF[[key]][1]
            if(is.null(value)) expect_true(is.na(observed),info=paste(f$id,key))
            else if(key=='p') expect_true(abs(observed-value)<=1e-12,info=f$id)
            else if(value==0) expect_equal(observed,0,info=f$id)
            else expect_true(abs(observed-value)/abs(value)<=1e-11,info=paste(f$id,key))
        }
        expect_equal(got$contrast$asDF$status,e$status,info=f$id)
        expect_equal(got$cases$asDF$sourceID,rownames(args$data)[unlist(f$expected$retained_indices)+1],info=f$id)
        expect_equal(got$descriptives$rowCount,2)
        expect_equal(got$missing$rowCount,2)
        expect_false(is.null(got$differencePlot$state),info=f$id)
    }
})

test_that('both native estimation lifecycles clear and recover', {
    ref<-jsonlite::fromJSON(testthat::test_path('..','fixtures','estimation-core.json'),simplifyVector=FALSE)
    for(paired in c(FALSE,TRUE)) {
        f<-Filter(function(f)(f$design=='paired')==paired,ref$fixtures)[[1]]
        args<-estimation_args(f);d<-args$data;args$data<-NULL
        prefix<-if(paired)'pyjjwithinstats' else 'pyjjbetweenstats'
        opts<-do.call(get(paste0(prefix,'Options'))$new,args)
        a<-get(paste0(prefix,'Class'))$new(options=opts)
        a$.setReadDatasetSource(function(...)d);a$.setReadDatasetHeaderSource(function(...)d)
        set_option<-function(n,v){o<-opts$option(n);o$value<-v}
        a$init();a$run();original<-a$results$contrast$asDF
        role<-if(paired)'dep2' else 'secondLevel';previous<-args[[role]]
        set_option(role,NULL);a$init();a$run()
        for(n in c('cohort','missing','descriptives','contrast','cases'))expect_equal(a$results$get(n)$rowCount,0)
        expect_null(a$results$differencePlot$state)
        set_option(role,previous);a$init();a$run()
        expect_equal(a$results$contrast$asDF,original)
        if(paired)set_option('dep2','First') else set_option('secondLevel',args$firstLevel)
        a$init();expect_error(a$run(),'distinct')
        expect_equal(a$results$contrast$rowCount,0);expect_null(a$results$differencePlot$state)
        set_option(role,previous);a$init();a$run()
        expect_equal(a$results$contrast$asDF,original)
        d$Subject<-factor(rep('repeated',nrow(d)));set_option('subject','Subject')
        a$init();expect_error(a$run(),'unique')
        expect_equal(a$results$cases$rowCount,0);expect_null(a$results$differencePlot$state)
        set_option('subject',NULL);a$init();a$run()
        expect_equal(a$results$contrast$asDF,original)
        set_option('showCases',FALSE);set_option('showPlot',FALSE);a$init();a$run()
        expect_equal(a$results$cases$rowCount,0);expect_null(a$results$differencePlot$state)
        set_option('conflevel',.8);a$init();a$run()
        expect_equal(a$results$contrast$asDF$confidence,.8)
        expect_lt(a$results$contrast$asDF$upper-a$results$contrast$asDF$lower,original$upper-original$lower)
        set_option('showPlot',TRUE);a$init();a$run()
        file<-tempfile(fileext='.rds');saveRDS(a$results$differencePlot$state,file)
        a$results$differencePlot$setState(readRDS(file));a$.__enclos_env__$private$.data<-NULL
        png<-tempfile(fileext='.png');a$results$differencePlot$saveAs(png)
        expect_true(file.exists(png));expect_gt(file.info(png)$size,1000)
    }
})

test_that('genuine NA factor levels and date storage do not become valid measurements', {
    d<-data.frame(y=c(1,3,5,2,4,8,11),g=factor(c('NA','NA','NA','B','B','B',NA),
        levels=c('NA','B',NA),exclude=NULL))
    expect_false(is.na(d$g[7]))
    got<-pyjjbetweenstats(data=d,dep='y',group='g',firstLevel='NA',secondLevel='B')
    expect_equal(got$cohort$asDF$retained,6)
    expect_equal(got$cohort$asDF$excluded,1)
    expect_equal(got$descriptives$asDF$label,c('NA','B'))
    d$date<-as.Date('2026-01-01')+seq_len(nrow(d))
    expect_error(pyjjwithinstats(data=d,dep1='date',dep2='y'),'requires a numeric variable|scalar numeric')
})
