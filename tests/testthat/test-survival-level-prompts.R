# Shared bridge gate: explicit event/censor choices and unchanged valid results.
test_that('event and censor gates describe their own roles and recover native results', {
    ns <- asNamespace('ClinicoPathPj')
    d <- data.frame(Time=c(0,1,2,2,4,8),
        Status=factor(c('Event','Censored','Event','Censored','Event','Censored'),
            levels=c('Censored','Event')),
        Group=factor(c('B','A','B','A','B','A')))
    make <- function(name,event=NULL,censor=NULL) {
        args <- list(elapsedtime='Time',outcome='Status',outcomeLevel=event,censorLevel=censor,
            cutp='0,2,8',showSteps=TRUE,showCases=TRUE,showExplanations=TRUE,
            sc=TRUE,ci95=TRUE,censored=TRUE)
        if(name=='pysurvival')args$explanatory <- 'Group'
        opts <- do.call(get(paste0(name,'Options'),ns)$new,args)
        a <- get(paste0(name,'Class'),ns)$new(options=opts)
        a$.setReadDatasetSource(function(...)d);a$.setReadDatasetHeaderSource(function(...)d)
        list(a=a,opts=opts)
    }
    run <- function(x){x$a$init();x$a$run()}
    set <- function(x,name,value){o<-x$opts$option(name);o$value<-value}
    event <- 'Choose which level of Status is the event: Censored (3 rows), Event (3 rows).'
    censor <- 'Choose which level of Status indicates censoring: Censored (3 rows), Event (3 rows).'
    for(name in c('pysinglearm','pysurvival')) {
        x <- make(name);run(x)
        expect_equal(x$a$results$get('cpjNotice1')$content,event,info=name)
        expect_equal(x$a$results$console$content,'Python was not started: choose which level of Status is the event.')
        set(x,'outcomeLevel','Event');run(x)
        expect_equal(x$a$results$get('cpjNotice1')$content,censor,info=name)
        expect_equal(x$a$results$console$content,'Python was not started: choose which level of Status indicates censoring.')
        set(x,'censorLevel','Censored');run(x)
        expect_equal(x$a$results$cohort$asDF$complete,6)
        expect_false(is.null(x$a$results$survivalPlot$state))
        table_names <- vapply(Filter(function(item)inherits(item,'Table'),x$a$results$items),function(item)item$name,'')
        original <- lapply(table_names,function(k)x$a$results$get(k)$asDF)
        summary <- x$a$results$summary$content;plot <- x$a$results$survivalPlot$state
        for(missing in c('censorLevel','outcomeLevel')) {
            value <- x$opts[[missing]];set(x,missing,NULL);run(x)
            expected <- if(missing=='censorLevel')censor else event
            expect_equal(x$a$results$get('cpjNotice1')$content,expected)
            for(k in table_names)expect_equal(x$a$results$get(k)$rowCount,0,info=paste(name,k))
            expect_equal(x$a$results$summary$content,'');expect_equal(x$a$results$explanation$content,'')
            expect_null(x$a$results$survivalPlot$state)
            run(x)
            expect_equal(sum(vapply(x$a$results$items,function(item)identical(item$name,'cpjNotice1'),FALSE)),1)
            set(x,missing,value);run(x)
            expect_equal(lapply(table_names,function(k)x$a$results$get(k)$asDF),original)
            expect_equal(x$a$results$summary$content,summary);expect_equal(x$a$results$survivalPlot$state,plot)
        }
        fresh <- make(name,'Event','Censored');run(fresh)
        expect_equal(lapply(table_names,function(k)x$a$results$get(k)$asDF),
            lapply(table_names,function(k)fresh$a$results$get(k)$asDF))
        expect_equal(x$a$results$survivalPlot$state,fresh$a$results$survivalPlot$state)
    }
})

test_that('legacy event-only bridge callers keep their exact pending prompt', {
    ns <- asNamespace('ClinicoPathPj')
    d <- data.frame(g=factor(c('A','A','A','B','B','B')),
        y=factor(c('yes','no','yes','no','yes','no'),levels=c('no','yes')))
    a <- get('pyexacttestsClass',ns)$new(
        options=get('pyexacttestsOptions',ns)$new(group='g',outcome='y'),data=d)
    a$init();a$run()
    expect_false(a$errored)
    expect_equal(a$results$get('cpjNotice1')$content,
        'Choose which level of y is the event: no (3 rows), yes (3 rows).')
    expect_equal(a$results$console$content,'Python was not started: choose which level of y is the event.')
    expect_equal(a$results$tests$rowCount,0)
})
