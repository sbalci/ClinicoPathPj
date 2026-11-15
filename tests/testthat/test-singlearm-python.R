singlearm_num <- function(x) vapply(x,function(v)if(is.null(v))NA_real_ else as.numeric(v),0)
singlearm_data <- function(f) {
    e <- singlearm_num(f$inputs$event)
    d <- data.frame(Time=singlearm_num(f$inputs$time),
        Status=factor(ifelse(is.na(e),NA,ifelse(e==1,'Event','Censored')),
                      levels=c('Censored','Event','Unused')))
    rownames(d) <- as.character(seq_len(nrow(d))*7-4)
    d
}

test_that('native singlearm matches independent right-censoring references', {
    refs <- jsonlite::fromJSON(testthat::test_path('..','fixtures','kaplan-meier-core.json'),simplifyVector=FALSE)
    fixtures <- Filter(function(f)abs(f$confidence-.95)<1e-12,refs$fixtures)
    expect_length(fixtures,52)
    for(f in fixtures) {
        d <- singlearm_data(f);e <- f$expected
        got <- pysinglearm(data=d,elapsedtime='Time',outcome='Status',outcomeLevel='Event',
            censorLevel='Censored',cutp=paste(sprintf('%.17g',unlist(f$queries)),collapse=','),ciWidth=95,
            timefix=f$timefix,showSteps=TRUE,showCases=TRUE,person_time=TRUE)
        for(pair in list(c('source','n_source'),c('complete','n_complete'),c('excluded','excluded_missing'),
                         c('events','events'),c('censored','censored'),c('normalized','timefix_changed_rows'))) {
            expect_equal(as.numeric(got$cohort$asDF[[pair[1]]]),as.numeric(e[[pair[2]]]),info=f$id)
        }
        for(key in c('estimate','lower','upper')) {
            expect_equal(as.numeric(got$medians$asDF[[key]]),singlearm_num(list(e$median[[key]],e$reverse$median[[key]])),
                tolerance=2e-12,info=f$id)
            expect_equal(as.numeric(got$personTime$asDF[[key]]),singlearm_num(list(e$rate[[key]])),tolerance=2e-12,info=f$id)
        }
        expect_equal(got$personTime$asDF$exposure,as.numeric(e$rate$person_time),tolerance=2e-12)
        for(key in c('time','survival','lower','upper','events','censored')) {
            expect_equal(as.numeric(got$steps$asDF[[key]]),singlearm_num(lapply(e$curve,`[[`,key)),tolerance=2e-12,info=f$id)
            expect_equal(as.numeric(got$selectedTimes$asDF[[key]]),singlearm_num(lapply(e$selected,`[[`,key)),tolerance=2e-12,info=f$id)
        }
        expect_equal(got$steps$asDF$risk,singlearm_num(lapply(e$curve,`[[`,'n_risk')))
        expect_equal(got$cases$asDF$sourceID,rownames(d)[unlist(e$retained_indices)+1L])
        expect_equal(got$cases$asDF$effectiveTime,as.numeric(unlist(e$effective_times)))
        expect_null(got$survivalPlot$state)
    }
})

test_that('native singlearm clears incomplete invalid and optional outputs and exports restored state', {
    d <- data.frame(Time=c(0,1,2,2,4,8,NA),
        Status=factor(c('Event','Censored','Event','Censored','Event','Censored','Event')),
        ID=factor(sprintf('S%02d',1:7)))
    opts <- pysinglearmOptions$new(elapsedtime='Time',outcome='Status',subject='ID',
        outcomeLevel='Event',censorLevel='Censored',cutp='0,2,8,9',sc=TRUE,ci95=TRUE,
        censored=TRUE,person_time=TRUE,showSteps=TRUE,showCases=TRUE,showExplanations=TRUE)
    a <- pysinglearmClass$new(options=opts)
    a$.setReadDatasetSource(function(...)d);a$.setReadDatasetHeaderSource(function(...)d)
    set <- function(n,v){o<-opts$option(n);o$value<-v}
    run <- function(){a$init();a$run()}
    run();original <- a$results$steps$asDF
    expect_equal(a$results$cohort$asDF$complete,6)
    expect_equal(a$results$cases$asDF$subjectID,sprintf('S%02d',1:6))
    set('sc',FALSE);set('showSteps',FALSE);set('showCases',FALSE)
    set('person_time',FALSE);set('showExplanations',FALSE);set('showFollowup',FALSE);run()
    expect_null(a$results$survivalPlot$state)
    for(name in c('steps','cases','personTime'))expect_equal(a$results$get(name)$rowCount,0)
    expect_equal(a$results$explanation$content,'');expect_equal(a$results$medians$rowCount,1)
    for(name in c('elapsedtime','outcomeLevel','censorLevel')) {
        value <- opts[[name]];set(name,NULL);run()
        for(table in c('cohort','mapping','missing','medians','selectedTimes','steps','cases','personTime'))
            expect_equal(a$results$get(table)$rowCount,0)
        expect_null(a$results$survivalPlot$state);set(name,value)
    }
    set('sc',TRUE);set('showSteps',TRUE);run()
    expect_equal(a$results$steps$asDF,original)
    set('cutp','1,,2');a$init();expect_error(a$run(),'empty comma')
    expect_equal(a$results$cohort$rowCount,0);expect_null(a$results$survivalPlot$state)
    set('cutp','0,2,8');run()
    d$Status <- factor(c('Event','Censored','Event','Censored','Event','Censored','Competing'))
    a$init();expect_error(a$run(),'neither');expect_equal(a$results$steps$rowCount,0)
    d$Status[7] <- 'Event';run()
    d$ID[2] <- d$ID[1];a$init();expect_error(a$run(),'[Dd]uplicate|[Uu]nique|repeated')
    d$ID[2] <- 'S02';set('timetypeoutput','years');set('timefix',FALSE);run()
    fresh <- pysinglearm(data=d,elapsedtime='Time',outcome='Status',subject='ID',
        outcomeLevel='Event',censorLevel='Censored',cutp='0,2,8',sc=TRUE,ci95=TRUE,censored=TRUE,
        showFollowup=FALSE,showSteps=TRUE,timetypeoutput='years',timefix=FALSE)
    expect_equal(a$results$steps$asDF,fresh$steps$asDF)
    expect_equal(a$results$survivalPlot$state,fresh$survivalPlot$state)
    path <- tempfile(fileext='.rds');saveRDS(a$results$survivalPlot$state,path)
    a$results$survivalPlot$setState(readRDS(path));a$.__enclos_env__$private$.data <- NULL
    output <- '/private/tmp/cpj-singlearm-native-restored.png'
    a$results$survivalPlot$saveAs(output)
    expect_true(file.exists(output));expect_gt(file.info(output)$size,1000)
    set('timefix',TRUE);d$Time[1] <- -1;a$init();expect_error(a$run(),'nonnegative|negative')
    expect_null(a$results$survivalPlot$state)
    d$Time[1] <- 0;run();expect_equal(a$results$cohort$asDF$complete,6)
})
