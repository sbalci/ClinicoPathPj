interval_data <- function(days) {
    data.frame(start=rep('2024-01-01',length(days)),
               end=as.character(as.Date('2024-01-01')+days))
}
interval_run <- function(days,...) {
    pytimeinterval(data=interval_data(days),dx_date='start',fu_date='end',...)
}

test_that('standardized intervals and summaries agree with independent base R', {
    days <- c(0,1,2,6,10,30,31,60,365,366,NA_real_)
    d <- interval_data(days)
    elapsed <- as.numeric(difftime(as.POSIXct(d$end,tz='UTC'),
                                  as.POSIXct(d$start,tz='UTC'),units='days'))
    divisors <- c(days=1,weeks=7,months=30.4375,years=365.25)
    for(unit in names(divisors)) {
        got <- interval_run(days,output_unit=unit,include_quality_metrics=TRUE)
        ref <- elapsed[!is.na(elapsed)]/divisors[[unit]]
        s <- got$statistics$asDF
        expect_equal(got$preview$asDF$value,elapsed/divisors[[unit]],tolerance=1e-10)
        expect_equal(c(s$n,s$total,s$mean,s$sd,s$minimum,s$q1,s$median,s$q3,s$maximum),
                     c(length(ref),sum(ref),mean(ref),sd(ref),min(ref),
                       unname(quantile(ref,c(.25,.5,.75),type=7)),max(ref)),tolerance=1e-10)
        ci <- got$uncertainty$asDF
        margin <- qt(.975,length(ref)-1)*sd(ref)/sqrt(length(ref))
        expect_equal(c(ci$lower,ci$upper,ci$rawLower),
                     c(max(0,mean(ref)-margin),mean(ref)+margin,mean(ref)-margin),tolerance=1e-10)
        expect_equal(got$cohort$asDF$used,10)
        expect_equal(got$cohort$asDF$missing,1)
    }
})

test_that('landmark ties, exclusions and type-7 flags match independent rules', {
    x <- c(0,1,2,6,10,30,31,60,365,366)
    got <- interval_run(x,output_unit='days',use_landmark=TRUE,landmark_time=6)
    expect_equal(got$preview$asDF$value,ifelse(x>=6,x-6,NA_real_))
    expect_equal(got$statistics$asDF$total,826)
    expect_equal(got$cohort$asDF$landmarkRemoved,3)
    for(x in list(c(rep(1,100),10000),c(rep(1,50),10000),c(rep(0,200),10))) {
        got <- interval_run(x,output_unit='days',remove_extreme=TRUE,
                            include_quality_metrics=TRUE,preview_rows=100)
        q <- unname(quantile(x,.99,type=7))
        keep <- if(q>0) x<=2*q else rep(TRUE,length(x))
        expect_equal(got$statistics$asDF$total,sum(x[keep]))
        expect_equal(got$cohort$asDF$extremeRemoved,sum(!keep))
        expect_equal(got$rawQuality$asDF$q99,q)
    }
    got <- interval_run(c(-1,1,6),output_unit='days',remove_negative=TRUE)
    expect_equal(got$preview$asDF$value,c(NA,1,6))
    expect_equal(got$cohort$asDF$negativeRemoved,1)
    got <- interval_run(c(0,4),output_unit='days')
    expect_equal(got$uncertainty$asDF$lower,0)
    expect_equal(got$uncertainty$asDF$rawLower,2-qt(.975,1)*2,tolerance=1e-10)
    got <- interval_run(c(1,2),output_unit='days',use_landmark=TRUE,landmark_time=10)
    expect_equal(got$cohort$asDF$used,0)
    expect_true(is.na(got$statistics$asDF$total))
})

test_that('saved numeric output and reusable input-error lifecycle stay aligned', {
    opts <- pytimeintervalOptions$new(dx_date='start',fu_date='end',output_unit='days')
    output <- opts$option('calculated_time');output$value <- list(value=TRUE,vars=list())
    a <- pytimeintervalClass$new(options=opts,data=interval_data(c(0,1,6,10,NA)))
    a$init();a$run();jmvcore:::initProtoBuf()
    saved <- function() a$results$calculated_time$asProtoBuf(incAsText=TRUE)$outputs$outputs
    expect_equal(as.numeric(saved()[[1]]$d),c(0,1,6,10,NA))
    opt <- opts$option('use_landmark');opt$value <- TRUE
    a$init();a$run()
    expect_equal(as.numeric(saved()[[1]]$d),c(NA,NA,0,4,NA))
    # Change the interpretation, making every date invalid; recover on the same object.
    opt <- opts$option('time_format');opt$value <- 'dmy'
    a$init();expect_error(a$run(),'80%')
    expect_equal(a$results$statistics$rowCount,0)
    if(length(saved())) expect_true(all(is.na(as.numeric(saved()[[1]]$d))))
    opt$value <- 'ymd';a$init();a$run()
    expect_equal(a$results$statistics$asDF$total,4)
    expect_equal(as.numeric(saved()[[1]]$d),c(NA,NA,0,4,NA))
})
