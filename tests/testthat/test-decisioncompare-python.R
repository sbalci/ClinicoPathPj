paired_fixture_args <- function(f) {
    labels <- unlist(f$levels)
    factor_codes <- function(codes) {
        codes <- as.integer(unlist(codes))
        factor(ifelse(codes < 0, NA_character_, labels[pmax(1,codes+1)]), levels=labels)
    }
    d <- data.frame(Reference=factor_codes(f$reference))
    args <- list(gold='Reference',goldPositive=f$positive,goldNegative=f$negative,
                 test3Positive=NULL,test3Negative=NULL,referenceType='disease',
                 statComp=TRUE,ci=TRUE,plot=TRUE,showCases=TRUE,showPairCounts=TRUE,
                 excludeIndeterminate=f$exclude)
    for(i in seq_along(f$tests)) {
        name <- names(f$tests)[i];d[[name]] <- factor_codes(f$tests[[name]])
        args[[paste0('test',i)]] <- name
        args[[paste0('test',i,'Positive')]] <- f$positive
        args[[paste0('test',i,'Negative')]] <- f$negative
    }
    rownames(d) <- as.character(seq_len(nrow(d))*3+7)
    c(list(data=d),args)
}

test_that('native paired tables match every independent R fixture', {
    ref <- jsonlite::fromJSON(testthat::test_path('..','fixtures','paired-decision.json'),simplifyVector=FALSE)
    for(f in ref$fixtures) {
        args <- paired_fixture_args(f)
        got <- do.call(pydecisioncompare,args)
        expected <- Filter(function(x)x$confidence==.95 && x$method=='midp',f$expected$runs)[[1]]
        expect_equal(got$cohort$asDF$retained,as.integer(f$expected$n_complete),info=f$id)
        expect_equal(got$cohort$asDF$missing,as.integer(f$expected$excluded_missing),info=f$id)
        expect_equal(got$cohort$asDF$outside,as.integer(f$expected$excluded_indeterminate),info=f$id)
        expect_equal(got$mapping$rowCount,1+length(f$tests),info=f$id)
        for(i in seq_along(expected$models)) {
            model <- expected$models[[i]];row <- got$counts$asDF[i,]
            expect_equal(as.integer(unlist(row[c('pp','np','pn','nn')])),as.integer(unlist(model$counts)),info=f$id)
            for(j in seq_along(model$proportions)) for(key in c('estimate','lower','upper')) {
                value <- model$proportions[[j]][[key]]
                observed <- got$estimates$asDF[[key]][(i-1)*5+j]
                if(is.null(value)) expect_true(is.na(observed),info=f$id)
                else expect_true(abs(observed-value)<=1e-12,info=f$id)
            }
        }
        rows <- got$comparisons$asDF
        expect_equal(nrow(rows),3*length(expected$pairs),info=f$id)
        for(i in seq_along(expected$pairs)) for(j in 1:3) {
            metric <- c('accuracy','sensitivity','specificity')[j]
            e <- expected$pairs[[i]][[metric]];k <- (i-1)*3+j
            expect_equal(rows$n[k],as.integer(e$n),info=f$id)
            for(key in c('difference','p')) {
                if(is.null(e[[key]])) expect_true(is.na(rows[[key]][k]),info=f$id)
                else expect_true(abs(rows[[key]][k]-e[[key]])<=1e-12,info=f$id)
            }
            if(metric=='accuracy') expect_true(abs(rows$adjusted[k]-e$p_holm)<=1e-12,info=f$id)
            else expect_true(is.na(rows$adjusted[k]),info=f$id)
        }
        expect_equal(got$discordance$rowCount,nrow(rows),info=f$id)
        expect_equal(got$cases$asDF$sourceID,rownames(args$data)[unlist(f$expected$retained_indices)+1],info=f$id)
        expect_false(is.null(got$proportionPlot$state),info=f$id)
    }
})

test_that('paired native lifecycle clears invalid and incomplete states and recovers', {
    ref <- jsonlite::fromJSON(testthat::test_path('..','fixtures','paired-decision.json'),simplifyVector=FALSE)
    args <- paired_fixture_args(ref$fixtures[[1]]);d<-args$data;args$data<-NULL
    opts <- do.call(pydecisioncompareOptions$new,args)
    a <- pydecisioncompareClass$new(options=opts)
    set_option <- function(name,value) {o<-opts$option(name);o$value<-value}
    a$.setReadDatasetSource(function(...)d);a$.setReadDatasetHeaderSource(function(...)d)
    a$init();a$run();original<-a$results$estimates$asDF
    tables<-c('cohort','mapping','counts','estimates','comparisons','discordance','cases')
    expect_equal(a$results$comparisons$rowCount,9)
    set_option('test2Negative',NULL);a$init();a$run()
    for(name in tables) expect_equal(a$results$get(name)$rowCount,0)
    expect_null(a$results$proportionPlot$state)
    set_option('test2Negative',args$test2Negative);a$init();a$run()
    expect_equal(a$results$estimates$asDF,original)
    set_option('test3Positive',NULL);a$init();a$run()
    expect_equal(a$results$comparisons$rowCount,0);expect_null(a$results$proportionPlot$state)
    set_option('test3Positive',args$test3Positive);a$init();a$run()
    set_option('test2',args$test1);a$init();expect_error(a$run(),'distinct reference and test')
    for(name in tables) expect_equal(a$results$get(name)$rowCount,0)
    expect_null(a$results$proportionPlot$state)
    set_option('test2',args$test2);a$init();a$run()
    expect_equal(a$results$estimates$asDF,original)
    set_option('goldNegative',args$goldPositive);a$init();expect_error(a$run(),'distinct positive and negative')
    expect_equal(a$results$estimates$rowCount,0)
    set_option('goldNegative',args$goldNegative);a$init();a$run()
    expect_equal(a$results$estimates$asDF,original)
    set_option('statComp',FALSE);set_option('ci',FALSE);set_option('plot',FALSE);set_option('showCases',FALSE)
    a$init();a$run()
    for(name in c('comparisons','discordance','cases')) expect_equal(a$results$get(name)$rowCount,0)
    expect_true(all(is.na(a$results$estimates$asDF$lower)));expect_null(a$results$proportionPlot$state)
    set_option('statComp',TRUE);set_option('mcnemarMethod','asymptotic');set_option('test3',NULL)
    a$init();a$run()
    expect_equal(a$results$comparisons$rowCount,3)
    expect_match(a$results$comparisons$asDF$status[1],'Asymptotic')
    set_option('test3',args$test3);a$init();a$run()
    expect_equal(a$results$comparisons$rowCount,9)
})

test_that('paired static plot survives serialization without analysis data', {
    ref <- jsonlite::fromJSON(testthat::test_path('..','fixtures','paired-decision.json'),simplifyVector=FALSE)
    args <- paired_fixture_args(ref$fixtures[[1]]);d<-args$data;args$data<-NULL
    opts<-do.call(pydecisioncompareOptions$new,args)
    a<-pydecisioncompareClass$new(options=opts,data=d);a$run()
    file<-tempfile(fileext='.rds');saveRDS(a$results$proportionPlot$state,file)
    a$results$proportionPlot$setState(readRDS(file));a$.__enclos_env__$private$.data<-NULL
    image<-tempfile(fileext='.png');a$results$proportionPlot$saveAs(image)
    expect_true(file.exists(image));expect_gt(file.info(image)$size,1000)
    pixels<-png::readPNG(image);expect_gt(dim(pixels)[1],100)
})

test_that('paired comparator wording and genuine NA levels preserve denominators', {
    ref <- jsonlite::fromJSON(testthat::test_path('..','fixtures','paired-decision.json'),simplifyVector=FALSE)
    args<-paired_fixture_args(ref$fixtures[[1]])
    original<-do.call(pydecisioncompare,args)
    args$referenceType<-'consensus';other<-do.call(pydecisioncompare,args)
    expect_equal(other$counts$asDF,original$counts$asDF)
    expect_equal(other$estimates$asDF$estimate,original$estimates$asDF$estimate)
    expect_false(any(grepl('predictive value',other$estimates$asDF$metric)))
    expect_match(other$summary$content,'does not establish disease')
    d<-args$data;d[17,]<-NA
    d$Reference<-factor(c(as.character(args$data$Reference),NA),
                        levels=c(levels(args$data$Reference),NA),exclude=NULL)
    expect_false(is.na(d$Reference[17]))
    args$data<-d;got<-do.call(pydecisioncompare,args)
    expect_equal(got$cohort$asDF$retained,16)
    expect_equal(got$cohort$asDF$missing,1)
    expect_equal(got$estimates$asDF$estimate,other$estimates$asDF$estimate)
})
