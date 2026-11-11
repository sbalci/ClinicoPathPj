test_that('native ROC wrapper agrees with all independent frozen R fixtures', {
    ref <- jsonlite::fromJSON(testthat::test_path('..','fixtures','roc-delong.json'), simplifyVector=FALSE)
    decode <- function(x) vapply(x,function(v) if(identical(v,'NA')) NA_real_ else as.numeric(v),numeric(1))
    for(f in ref$fixtures) {
        codes <- as.integer(unlist(f$codes)); labels <- unlist(f$levels)
        d <- data.frame(Reference=factor(ifelse(codes<0,NA_character_,labels[pmax(1,codes+1)]),levels=labels))
        for(name in names(f$markers)) d[[name]] <- decode(f$markers[[name]])
        args <- list(data=d,reference='Reference',positive=f$positive,
                     showCases=TRUE,showThresholds=TRUE,showROC=TRUE,showComparisons=TRUE)
        directions <- unlist(f$directions)
        for(i in seq_along(f$markers)) {
            args[[paste0('marker',i)]] <- names(f$markers)[i]
            args[[paste0('direction',i)]] <- directions[i]
        }
        got <- do.call(pyenhancedroc,args)
        expect_equal(got$cohort$asDF$retained,as.integer(f$expected$n_complete),info=f$id)
        expect_equal(got$auc$rowCount,length(f$expected$models),info=f$id)
        for(i in seq_along(f$expected$models)) {
            expected <- f$expected$models[[i]]
            interval <- Filter(function(x) x$confidence==.95,expected$intervals)[[1]]
            expect_equal(got$auc$asDF$estimate[i],expected$auc,tolerance=1e-12,info=f$id)
            for(field in c('se','lower','upper')) {
                value <- interval[[field]]
                if(is.null(value)) expect_true(is.na(got$auc$asDF[[field]][i]),info=f$id)
                else expect_equal(got$auc$asDF[[field]][i],value,tolerance=1e-12,info=f$id)
            }
        }
        expect_equal(got$comparisons$rowCount,length(f$expected$comparisons),info=f$id)
        for(i in seq_along(f$expected$comparisons)) {
            expected <- f$expected$comparisons[[i]]
            interval <- Filter(function(x) x$confidence==.95,expected$intervals)[[1]]
            expect_equal(got$comparisons$asDF$difference[i],expected$difference,tolerance=1e-12,info=f$id)
            if(is.null(interval$p)) expect_true(is.na(got$comparisons$asDF$p[i]),info=f$id)
            else expect_equal(got$comparisons$asDF$p[i],interval$p,tolerance=1e-12,info=f$id)
        }
        expect_equal(got$cases$asDF$sourceID,as.character(unlist(f$expected$retained_indices)+1),info=f$id)
        expect_equal(got$thresholds$rowCount,sum(vapply(f$expected$models,function(x) length(x$points),integer(1))),info=f$id)
        expect_false(is.null(got$rocPlot$state),info=f$id)
    }
})

roc_data <- function() {
    d <- data.frame(Reference=factor(c(rep('N',4),rep('P',4)),levels=c('N','P')),
                    A=c(1,2,3,4,2,3,3,5),B=c(1,4,2,3,2,3,5,4))
    rownames(d) <- as.character(seq(2,16,2));d
}

test_that('native ROC clears and recovers all optional outputs on the same instance', {
    d <- roc_data()
    opts <- pyenhancedrocOptions$new(reference='Reference',positive='P',marker1='A',marker2='B',
                                     showCases=TRUE,showThresholds=TRUE,showROC=TRUE)
    a <- pyenhancedrocClass$new(options=opts)
    set_option <- function(name,value) { option <- opts$option(name); option$value <- value }
    a$.setReadDatasetSource(function(...) d);a$.setReadDatasetHeaderSource(function(...) d)
    a$init();a$run();before <- a$results$auc$asDF
    expect_equal(a$results$cases$asDF$sourceID,rownames(d))
    expect_equal(a$results$comparisons$rowCount,1)
    set_option('marker1',NULL);a$init();a$run()
    for(name in c('cohort','auc','comparisons','thresholds','cases')) expect_equal(a$results$get(name)$rowCount,0)
    expect_null(a$results$rocPlot$state)
    set_option('marker1','A');a$init();a$run()
    expect_equal(a$results$auc$asDF,before)
    set_option('marker2','A');a$init()
    expect_error(a$run(),'distinct score')
    for(name in c('cohort','auc','comparisons','thresholds','cases')) expect_equal(a$results$get(name)$rowCount,0)
    expect_null(a$results$rocPlot$state)
    set_option('marker2','B');a$init();a$run()
    expect_equal(a$results$auc$asDF,before)
    set_option('showCases',FALSE);set_option('showThresholds',FALSE)
    set_option('showComparisons',FALSE);set_option('showROC',FALSE)
    a$init();a$run()
    for(name in c('comparisons','thresholds','cases')) expect_equal(a$results$get(name)$rowCount,0)
    expect_null(a$results$rocPlot$state)
    set_option('showComparisons',TRUE);set_option('marker2',NULL);a$init();a$run()
    expect_equal(a$results$auc$rowCount,1);expect_equal(a$results$comparisons$rowCount,0)
    set_option('marker3','B');set_option('direction3','lower');a$init();a$run()
    expect_equal(a$results$auc$asDF$estimate,c(21/32,1-before$estimate[2]),tolerance=1e-12)
    set_option('positive',NULL);a$init();a$run()
    expect_equal(a$results$auc$rowCount,0);expect_null(a$results$rocPlot$state)
})

test_that('native ROC confidence changes and missing-pair source rows stay aligned', {
    d <- roc_data();d$A[1] <- NA;d$B[7] <- NA
    got <- pyenhancedroc(d,reference='Reference',positive='P',marker1='A',marker2='B',showCases=TRUE)
    expect_equal(got$cases$asDF$sourceID,rownames(d)[c(2,3,4,5,6,8)])
    expect_equal(got$cohort$asDF$retained,6)
    wide <- pyenhancedroc(d,reference='Reference',positive='P',marker1='A',marker2='B',confLevel=.99)
    expect_equal(wide$auc$asDF$estimate,got$auc$asDF$estimate)
    expect_true(all(wide$auc$asDF$lower<=got$auc$asDF$lower))
    expect_true(all(wide$auc$asDF$upper>=got$auc$asDF$upper))
    expect_equal(wide$comparisons$asDF$p,got$comparisons$asDF$p)
})

test_that('native ROC plot renders from serialized state with analysis data cleared', {
    d <- roc_data()
    opts <- pyenhancedrocOptions$new(reference='Reference',positive='P',marker1='A',marker2='B')
    a <- pyenhancedrocClass$new(options=opts,data=d);a$run()
    saved <- tempfile(fileext='.rds');saveRDS(a$results$rocPlot$state,saved)
    a$results$rocPlot$setState(readRDS(saved));a$.__enclos_env__$private$.data <- NULL
    file <- tempfile(fileext='.png');a$results$rocPlot$saveAs(file)
    expect_true(file.exists(file));expect_gt(file.info(file)$size,1000)
    picture <- png::readPNG(file)
    expect_gt(dim(picture)[1],100);expect_gt(dim(picture)[2],100)
    expect_match(a$results$summary$content,'large')
})

test_that('genuine missing factor levels are excluded while literal NA labels remain events', {
    d <- roc_data();d[9,] <- list(NA,9,9)
    d$Reference <- factor(c(rep('N',4),rep('P',4),NA),levels=c('N','P',NA),exclude=NULL)
    expect_false(is.na(d$Reference[9]))
    got <- pyenhancedroc(d,reference='Reference',positive='P',marker1='A',showCases=TRUE)
    expect_equal(got$cohort$asDF$retained,8)
    expect_equal(got$cohort$asDF$excluded,1)
    expect_equal(got$auc$asDF$estimate,21/32)
    d <- roc_data();d$Reference <- ordered(c(rep('N',4),rep('NA',4)),levels=c('NA','N'))
    got <- pyenhancedroc(d,reference='Reference',positive='NA',marker1='A',showCases=TRUE)
    expect_equal(got$cohort$asDF$cases,4)
    expect_equal(got$auc$asDF$estimate,21/32)
    expect_equal(tail(got$cases$asDF$reference,4),rep('NA',4))
})
