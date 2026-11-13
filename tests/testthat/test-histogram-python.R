# Native contracts; numerical expectations come from frozen R references.
hist_values <- function(x) vapply(x,function(v)if(is.null(v))NA_real_ else as.numeric(v),numeric(1))

test_that('native histogram and optional Student tables agree with R references', {
    refs <- jsonlite::fromJSON(testthat::test_path('..','fixtures','histogram-core.json'),simplifyVector=FALSE)
    for(f in refs$fixtures) {
        d <- data.frame(Measurement=hist_values(f$values))
        rownames(d) <- as.character(seq_len(nrow(d))*3+7)
        got <- pyjjhistostats(data=d,dep='Measurement',resultssubtitle=TRUE,showCases=TRUE,
            changebinwidth=f$id=='offset_degenerate',binwidth=if(f$id=='offset_degenerate')1e15 else 1.1)
        ref <- Filter(function(r)r$confidence==.95 && r$reference==0,f$runs)[[1]]
        expect_equal(got$cohort$asDF$retained,as.integer(f$n_complete),info=f$id)
        expect_equal(got$cohort$asDF$excluded,as.integer(f$excluded_missing),info=f$id)
        expect_equal(got$cases$asDF$sourceID,rownames(d)[unlist(f$retained_indices)+1],info=f$id)
        for(key in c('difference','stderr','df','statistic','p')) {
            target <- ref[[key]]; observed <- got$meanTest$asDF[[key]][1]
            if(is.null(target))expect_true(is.na(observed),info=paste(f$id,key))
            else expect_true(abs(observed-target)<=(if(target==0)1e-12 else abs(target)*1e-10),info=paste(f$id,key))
        }
        expect_equal(got$meanTest$asDF$status,ref$status,info=f$id)
        limits <- got$meanLimits$asDF
        for(i in 1:2)for(suffix in c('lower','upper')) {
            target <- ref[[paste0(if(i==1)'mean_' else 'difference_',suffix)]]
            if(is.null(target))expect_true(is.na(limits[[suffix]][i]),info=f$id)
            else expect_true(abs(limits[[suffix]][i]-target)<=2e-7*max(1,abs(target)),info=f$id)
        }
    }
    geometry <- jsonlite::fromJSON(testthat::test_path('..','fixtures','histogram-geometry.json'),simplifyVector=FALSE)
    for(f in geometry$fixtures)for(ref in f$runs) {
        d <- data.frame(Measurement=hist_values(f$values))
        if(ref$geometry_status=='error') {
            expect_error(pyjjhistostats(data=d,dep='Measurement',changebinwidth=!ref$automatic,
                binwidth=if(ref$automatic)1.1 else ref$width));next
        }
        got <- pyjjhistostats(data=d,dep='Measurement',changebinwidth=!ref$automatic,
            binwidth=if(ref$automatic)1.1 else ref$width,showBins=TRUE)
        expect_equal(got$binning$asDF$status,ref$geometry_status,info=f$id)
        expect_equal(got$bins$rowCount,length(ref$bins),info=f$id)
        if(length(ref$bins)) {
            expect_equal(got$bins$asDF$count,as.integer(vapply(ref$bins,function(b)b$count,0)),info=f$id)
            for(key in c('lower','upper','proportion','density')) {
                target<-vapply(ref$bins,function(b)b[[key]],0);observed<-got$bins$asDF[[key]]
                expect_true(all(abs(observed-target)<=ifelse(target==0,1e-12,abs(target)*1e-10)),info=paste(f$id,key))
            }
            expect_false(is.null(got$histogramPlot$state),info=f$id)
        } else expect_null(got$histogramPlot$state,info=f$id)
    }
})

test_that('native histogram clears optional results and recovers after incomplete or invalid requests', {
    d<-data.frame(Measurement=c(NA,0,1,2,4,8),ID=c(NA,'01','1','001','A','B'))
    rownames(d)<-c('2','7','9','14','22','35')
    opts<-pyjjhistostatsOptions$new(dep='Measurement',subject='ID',resultssubtitle=TRUE,
        showCases=TRUE,showBins=TRUE,centralityline=TRUE)
    a<-pyjjhistostatsClass$new(options=opts)
    a$.setReadDatasetSource(function(...)d);a$.setReadDatasetHeaderSource(function(...)d)
    set_option<-function(n,v){o<-opts$option(n);o$value<-v}
    a$init();a$run();original<-a$results$meanTest$asDF
    expect_equal(a$results$cases$asDF$sourceID,rownames(d)[-1])
    expect_equal(a$results$cases$asDF$subjectID,d$ID[-1])
    set_option('testValue',2);a$init();a$run()
    expect_equal(a$results$meanTest$asDF,original) # disabled custom null remains zero
    set_option('enableOneSampleTest',TRUE);a$init();a$run()
    expect_equal(a$results$meanTest$asDF$reference,2)
    expect_equal(a$results$meanTest$asDF$difference,mean(d$Measurement,na.rm=TRUE)-2)
    set_option('conflevel',.8);a$init();a$run()
    expect_equal(a$results$meanLimits$asDF$confidence,c(.8,.8))
    set_option('resultssubtitle',FALSE);a$init();a$run()
    for(n in c('meanTest','meanLimits'))expect_equal(a$results$get(n)$rowCount,0)
    set_option('showBins',FALSE);set_option('showCases',FALSE);set_option('showPlot',FALSE)
    a$init();a$run()
    expect_equal(a$results$bins$rowCount,0);expect_equal(a$results$cases$rowCount,0)
    expect_null(a$results$histogramPlot$state)
    set_option('dep',NULL);a$init();a$run()
    for(n in c('cohort','descriptives','binning','bins','cases','meanTest','meanLimits'))
        expect_equal(a$results$get(n)$rowCount,0)
    expect_null(a$results$histogramPlot$state)
    set_option('dep','Measurement');set_option('showPlot',TRUE)
    set_option('resultssubtitle',TRUE);a$init();a$run()
    expect_equal(a$results$meanTest$asDF$reference,2)
    d$ID[3]<-'01';a$init();expect_error(a$run(),'unique')
    expect_equal(a$results$cohort$rowCount,0);expect_null(a$results$histogramPlot$state)
    d$ID[3]<-'1';a$init();a$run()
    state<-a$results$histogramPlot$state
    artifact<-tempfile(fileext='.rds');saveRDS(state,artifact)
    a$results$histogramPlot$setState(readRDS(artifact));a$.__enclos_env__$private$.data<-NULL
    png<-file.path('/private/tmp','cpj-histogram-native.png')
    a$results$histogramPlot$saveAs(png)
    expect_true(file.exists(png));expect_gt(file.info(png)$size,1000)
})

test_that('constant automatic data recover with explicit positive manual width', {
    d<-data.frame(Measurement=rep(3,5))
    opts<-pyjjhistostatsOptions$new(dep='Measurement',resultssubtitle=TRUE,showBins=TRUE)
    a<-pyjjhistostatsClass$new(options=opts)
    a$.setReadDatasetSource(function(...)d);a$.setReadDatasetHeaderSource(function(...)d)
    a$init();a$run()
    expect_equal(a$results$binning$asDF$status,'constant_auto')
    expect_equal(a$results$descriptives$asDF$mean,3)
    expect_equal(a$results$meanTest$asDF$status,'degenerate')
    expect_null(a$results$histogramPlot$state)
    o<-opts$option('changebinwidth');o$value<-TRUE;a$init();a$run()
    expect_equal(a$results$bins$asDF$count,5L)
    expect_false(is.null(a$results$histogramPlot$state))
    o$value<-FALSE;a$init();a$run()
    expect_equal(a$results$bins$rowCount,0);expect_null(a$results$histogramPlot$state)
    d$Measurement<-seq_len(5);a$init();a$run()
    expect_equal(a$results$meanTest$asDF$status,'ok')
    expect_false(is.null(a$results$histogramPlot$state))
})


test_that('synthetic data have unequal counts and exact cancellation means remain accurate', {
    d<-read.csv(testthat::test_path('..','..','data','python_histogram_examples.csv'))
    got<-pyjjhistostats(data=d,dep='Measurement',subject='Case',changebinwidth=TRUE,
        binwidth=2,showBins=TRUE,centralityline=TRUE)
    expect_equal(got$bins$asDF$count,c(5L,7L,4L,1L,1L,1L,0L,0L,0L,1L))
    expect_equal(got$cohort$asDF$retained,20L);expect_equal(got$cohort$asDF$excluded,2L)
    expect_equal(got$meanTest$rowCount,0)
    refs<-jsonlite::fromJSON(testthat::test_path('..','fixtures','histogram-geometry.json'),simplifyVector=FALSE)
    f<-Filter(function(f)f$id=='fuzzy_edge_neighbors',refs$fixtures)[[1]]
    accurate<-pyjjhistostats(data=data.frame(Measurement=hist_values(f$values)),dep='Measurement')
    # Independently frozen exact rational mean, distinct from R cancellation error.
    expect_identical(accurate$descriptives$asDF$mean,1080863913/144115188075855872)
    # Mirror the GUI dataset callbacks: jmvcore's direct wrapper selection of
    # a data.frame with zero requested columns has a separate row.names error.
    empty<-pyjjhistostatsClass$new(options=pyjjhistostatsOptions$new())
    empty$.setReadDatasetSource(function(...)d)
    empty$.setReadDatasetHeaderSource(function(...)d)
    empty$init();empty$run()
    expect_equal(empty$results$cohort$rowCount,0);expect_null(empty$results$histogramPlot$state)
})
