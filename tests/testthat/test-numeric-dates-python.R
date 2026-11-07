test_that('numeric interval encodings agree with independent base R date arithmetic', {
    a <- as.POSIXct(c('2024-01-31','2023-01-31'),tz='UTC')
    b <- as.POSIXct(c('2024-02-29','2023-02-28'),tz='UTC')
    for(fmt in c('packed_ymd','excel_serial','excel_serial_1904','unix_epoch')) {
        encode <- function(x) switch(fmt,
            packed_ymd=as.numeric(format(x,'%Y%m%d',tz='UTC')),
            unix_epoch=as.numeric(x),
            excel_serial=as.numeric(difftime(x,as.POSIXct('1899-12-30',tz='UTC'),units='days')),
            excel_serial_1904=as.numeric(difftime(x,as.POSIXct('1904-01-01',tz='UTC'),units='days')))
        d <- data.frame(a=c(encode(a),NA),b=c(encode(b),encode(b)[1]))
        for(basis in c('standardized','calendar')) {
            got <- pytimeinterval(data=d,dx_date='a',fu_date='b',time_format=fmt,time_basis=basis)
            ref <- if(basis=='calendar') c(1,1,NA) else c(as.numeric(difftime(b,a,units='days'))/30.4375,NA)
            expect_equal(got$preview$asDF$value,ref,tolerance=1e-10)
            expect_equal(got$cohort$asDF$used,2)
            expect_equal(got$cohort$asDF$missing,1)
        }
    }
})

test_that('packed converter matches base R and preserves invalid/missing saved positions', {
    x <- c(20240229,20230229,NA,20000229)
    opts <- pydatetimeconverterOptions$new(datetime_var='x',datetime_format='packed_ymd',show_quality_metrics=TRUE)
    output <- opts$option('corrected_datetime_numeric');output$value <- list(value=TRUE,vars=list())
    a <- pydatetimeconverterClass$new(options=opts,data=data.frame(x=x));a$init();a$run()
    jmvcore:::initProtoBuf()
    saved <- as.numeric(a$results$corrected_datetime_numeric$asProtoBuf(incAsText=TRUE)$outputs$outputs[[1]]$d)
    ref <- as.POSIXct(as.character(x),format='%Y%m%d',tz='UTC')
    expect_equal(saved,as.numeric(ref),tolerance=1e-6)
    expect_equal(a$results$quality$asDF$parsed,2)
    expect_equal(a$results$quality$asDF$invalid,1)
    expect_equal(a$results$quality$asDF$missing,1)
})

test_that('changing numeric encoding clears interval output on failure and recovers', {
    opts <- pytimeintervalOptions$new(dx_date='a',fu_date='b',time_format='packed_ymd',output_unit='days')
    output <- opts$option('calculated_time');output$value <- list(value=TRUE,vars=list())
    a <- pytimeintervalClass$new(options=opts,data=data.frame(a=c(20240131,20240229,NA),b=c(20240229,20240301,20240301)))
    a$init();a$run();jmvcore:::initProtoBuf()
    saved <- function() as.numeric(a$results$calculated_time$asProtoBuf(incAsText=TRUE)$outputs$outputs[[1]]$d)
    expect_equal(saved(),c(29,1,NA))
    fmt <- opts$option('time_format');fmt$value <- 'ymd';a$init();expect_error(a$run(),'numeric column')
    expect_equal(a$results$statistics$rowCount,0)
    expect_true(all(is.na(saved())))
    fmt$value <- 'packed_ymd';a$init();a$run()
    expect_equal(saved(),c(29,1,NA))
})
