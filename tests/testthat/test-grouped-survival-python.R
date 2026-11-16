grouped_num <- function(x) vapply(x,function(v)if(is.null(v))NA_real_ else as.numeric(v),0)
grouped_data <- function(f) {
    e <- grouped_num(f$inputs$event)
    levels <- vapply(f$inputs$levels,function(x)if(is.null(x))NA_character_ else x,'')
    codes <- unlist(f$inputs$codes)
    labels <- levels[pmax(1L,codes+1L)];labels[codes<0] <- NA_character_
    d <- data.frame(Time=grouped_num(f$inputs$time),
        Status=factor(ifelse(is.na(e),NA,ifelse(e==1,'Event','Censored')),levels=c('Censored','Event','Unused')),
        Group=factor(labels,levels=levels,exclude=NULL))
    rownames(d) <- as.character(seq_len(nrow(d))*7-4)
    d
}

test_that('native grouped survival preserves independent reference tables and group order', {
    refs <- jsonlite::fromJSON(testthat::test_path('..','fixtures','grouped-survival-core.json'),simplifyVector=FALSE)
    fixtures <- Filter(function(f)abs(f$confidence-.95)<1e-12,refs$fixtures)
    expect_length(fixtures,60)
    for(f in fixtures) {
        d <- grouped_data(f);e <- f$expected
        got <- pysurvival(data=d,elapsedtime='Time',outcome='Status',explanatory='Group',outcomeLevel='Event',
            censorLevel='Censored',cutp=paste(sprintf('%.17g',unlist(f$queries)),collapse=','),ciWidth=95,
            timefix=f$timefix,showSteps=TRUE,showCases=TRUE)
        for(pair in list(c('source','n_source'),c('complete','n_complete'),c('excluded','excluded_missing'),
                         c('events','events'),c('censored','censored'),c('normalized','timefix_changed_rows'))) {
            expect_equal(as.numeric(got$cohort$asDF[[pair[1]]]),as.numeric(e[[pair[2]]]),info=f$id)
        }
        expect_equal(got$groups$asDF$group,vapply(e$groups,`[[`,'','label'),info=f$id)
        for(key in c('estimate','lower','upper')) {
            expect_equal(as.numeric(got$medians$asDF[[key]]),grouped_num(lapply(e$groups,function(g)g$median[[key]])),tolerance=2e-10,info=f$id)
        }
        for(pair in list(c('steps','curve'),c('selectedTimes','selected'))) {
            rows <- unlist(lapply(e$groups,`[[`,pair[2]),recursive=FALSE)
            for(key in c('time','events','censored','survival','lower','upper'))
                expect_equal(as.numeric(got$get(pair[1])$asDF[[key]]),grouped_num(lapply(rows,`[[`,key)),tolerance=2e-10,info=f$id)
        }
        for(key in c('statistic','df','p'))expect_equal(as.numeric(got$logrank$asDF[[key]]),grouped_num(list(e$logrank[[key]])),tolerance=2e-10,info=f$id)
        expect_equal(got$logrank$asDF$status,e$logrank$status)
        for(key in c('observed','expected','score'))expect_equal(got$logrankGroups$asDF[[key]],as.numeric(unlist(e$logrank[[key]])),tolerance=2e-10,info=f$id)
        expect_equal(got$covariance$asDF$value,as.numeric(unlist(e$logrank$variance)),tolerance=2e-10,info=f$id)
        expect_equal(got$cases$asDF$sourceID,rownames(d)[unlist(e$retained_indices)+1L])
        expect_equal(got$cases$asDF$effectiveTime,as.numeric(unlist(e$effective_times)))
        expect_null(got$survivalPlot$state)
    }
})

test_that('native grouped survival clears recovers and exports restored state', {
    d <- data.frame(Time=c(0,1,2,2,4,8,NA),
        Status=factor(c('Event','Censored','Event','Censored','Event','Censored','Event')),
        Group=factor(c('B','A','B','A','B','A','B'),levels=c('B','A','Unused')),
        ID=factor(sprintf('S%02d',1:7)))
    opts <- pysurvivalOptions$new(elapsedtime='Time',outcome='Status',explanatory='Group',subject='ID',
        outcomeLevel='Event',censorLevel='Censored',cutp='0,2,8,9',sc=TRUE,ci95=TRUE,
        censored=TRUE,showSteps=TRUE,showCases=TRUE,showExplanations=TRUE)
    a <- pysurvivalClass$new(options=opts)
    a$.setReadDatasetSource(function(...)d);a$.setReadDatasetHeaderSource(function(...)d)
    set <- function(n,v){o<-opts$option(n);o$value<-v}
    run <- function(){a$init();a$run()}
    tables <- c('cohort','mapping','missing','groups','medians','selectedTimes','logrank','logrankGroups','covariance','riskSets','steps','cases')
    run();original <- a$results$steps$asDF
    expect_equal(a$results$cohort$asDF$complete,6)
    expect_equal(a$results$cases$asDF$subjectID,sprintf('S%02d',1:6))
    set('sc',FALSE);set('showSteps',FALSE);set('showCases',FALSE);set('showExplanations',FALSE);run()
    expect_null(a$results$survivalPlot$state)
    for(name in c('steps','cases','covariance','riskSets'))expect_equal(a$results$get(name)$rowCount,0)
    expect_equal(a$results$explanation$content,'')
    for(name in c('elapsedtime','explanatory','outcomeLevel','censorLevel')) {
        value <- opts[[name]];set(name,NULL);run()
        for(table in tables)expect_equal(a$results$get(table)$rowCount,0)
        expect_null(a$results$survivalPlot$state);set(name,value)
    }
    set('sc',TRUE);set('showSteps',TRUE);run();expect_equal(a$results$steps$asDF,original)
    set('cutp','1,,2');a$init();expect_error(a$run(),'empty comma')
    expect_equal(a$results$cohort$rowCount,0);expect_null(a$results$survivalPlot$state)
    set('cutp','0,2,8');run()
    d$Status <- factor(c('Event','Censored','Event','Censored','Event','Censored','Competing'))
    a$init();expect_error(a$run(),'neither');expect_equal(a$results$steps$rowCount,0)
    d$Status[7] <- 'Event';run()
    d$ID[2] <- d$ID[1];a$init();expect_error(a$run(),'[Dd]uplicate|[Uu]nique|repeated')
    d$ID[2] <- 'S02';set('timetypeoutput','years');set('timefix',FALSE);run()
    fresh <- pysurvival(data=d,elapsedtime='Time',outcome='Status',explanatory='Group',subject='ID',
        outcomeLevel='Event',censorLevel='Censored',cutp='0,2,8',sc=TRUE,ci95=TRUE,censored=TRUE,
        showSteps=TRUE,timetypeoutput='years',timefix=FALSE)
    expect_equal(a$results$steps$asDF,fresh$steps$asDF)
    expect_equal(a$results$survivalPlot$state,fresh$survivalPlot$state)
    path <- tempfile(fileext='.rds');saveRDS(a$results$survivalPlot$state,path)
    a$results$survivalPlot$setState(readRDS(path));a$.__enclos_env__$private$.data <- NULL
    output <- '/private/tmp/cpj-grouped-native-restored.png';a$results$survivalPlot$saveAs(output)
    expect_true(file.exists(output));expect_gt(file.info(output)$size,1000)
    set('timefix',TRUE);d$Time[1] <- -1;a$init();expect_error(a$run(),'nonnegative|negative')
    expect_null(a$results$survivalPlot$state)
    d$Time[1] <- 0;run();expect_equal(a$results$cohort$asDF$complete,6)
})
