test_that('explicit UTC formats agree with independent lubridate parsers', {
    skip_if_not_installed('lubridate')
    fixtures <- list(ymd='2024-02-29',dmy='29/02/2024',mdy='02/29/2024',
        ydm='2024-29-02',myd='02-2024-29',dym='29-2024-02',
        ymdhms='2024-02-29 23:59:58.125',dmyhms='29-02-2024 23:59:58.125',
        mdyhms='02-29-2024 23:59:58.125',ymdhm='2024-02-29 23:59',
        dmyhm='29-02-2024 23:59',mdyhm='02-29-2024 23:59')
    for(fmt in names(fixtures)) {
        parser <- get(switch(fmt,ymdhms='ymd_hms',dmyhms='dmy_hms',mdyhms='mdy_hms',
                       ymdhm='ymd_hm',dmyhm='dmy_hm',mdyhm='mdy_hm',fmt),asNamespace('lubridate'))
        x <- c(fixtures[[fmt]],NA_character_)
        ref <- parser(x,tz='UTC',quiet=TRUE)
        got <- pydatetimeconverter(data=data.frame(x=x),datetime_var='x',datetime_format=fmt,
                 show_quality_metrics=TRUE,extract_year=TRUE,extract_month=TRUE,extract_day=TRUE,
                 extract_hour=TRUE,extract_minute=TRUE,extract_second=TRUE,extract_weeknum=TRUE,
                 extract_quarter=TRUE,extract_dayofyear=TRUE)
        p <- got$preview$asDF
        expect_equal(got$quality$asDF$parsed,1)
        expect_equal(got$quality$asDF$missing,1)
        expect_equal(p$year,lubridate::year(ref))
        expect_equal(p$month,lubridate::month(ref))
        expect_equal(p$day,lubridate::day(ref))
        expect_equal(p$hour,lubridate::hour(ref))
        expect_equal(p$minute,lubridate::minute(ref))
        expect_equal(p$second,lubridate::second(ref),tolerance=1e-6)
        expect_equal(p$weeknum,lubridate::week(ref))
        expect_equal(p$quarter,lubridate::quarter(ref))
        expect_equal(p$dayofyear,lubridate::yday(ref))
    }
})

test_that('numeric epochs and every Excel minute agree with base R conversion', {
    skip_if_not_installed('lubridate')
    for(fmt in c('excel_serial','excel_serial_1904','unix_epoch')) {
        x <- if(fmt=='unix_epoch') c(0,1.125,-.25,1709164800,NA) else c(0,60,61,45000+5/1440,NA)
        origin <- switch(fmt,excel_serial='1899-12-30',excel_serial_1904='1904-01-01',unix_epoch='1970-01-01')
        ref <- as.POSIXct(if(fmt=='unix_epoch') x else round(x*86400),origin=origin,tz='UTC')
        opts <- pydatetimeconverterOptions$new(datetime_var='x',datetime_format=fmt,
                         extract_year=TRUE,extract_second=TRUE,show_quality_metrics=TRUE)
        for(name in c('corrected_datetime_numeric','year_out','second_out')) {
            opt <- opts$option(name);opt$value <- list(value=TRUE,vars=list())
        }
        a <- pydatetimeconverterClass$new(options=opts,data=data.frame(x=x));a$init();a$run()
        jmvcore:::initProtoBuf()
        saved <- a$results$corrected_datetime_numeric$asProtoBuf(incAsText=TRUE)$outputs$outputs[[1]]$d
        expect_equal(as.numeric(saved),as.numeric(ref),tolerance=1e-6)
        expect_equal(a$results$preview$asDF$year,lubridate::year(ref))
        expect_equal(a$results$preview$asDF$second,lubridate::second(ref),tolerance=1e-6)
    }
    x <- 45000+(0:1439)/1440
    opts <- pydatetimeconverterOptions$new(datetime_var='x',datetime_format='excel_serial')
    for(name in c('hour_out','minute_out','second_out')) {
        opt <- opts$option(name);opt$value <- list(value=TRUE,vars=list())
    }
    a <- pydatetimeconverterClass$new(options=opts,data=data.frame(x=x));a$init();a$run()
    jmvcore:::initProtoBuf()
    for(name in c('hour','minute','second')) {
        output <- a$results$get(paste0(name,'_out'))$asProtoBuf(incAsText=TRUE)$outputs$outputs[[1]]$d
        expected <- switch(name,hour=(0:1439)%/%60,minute=(0:1439)%%60,second=rep(0,1440))
        expect_equal(as.numeric(output),as.numeric(expected))
    }
})

test_that('quality denominators and true/literal missing values remain distinct', {
    x <- factor(c('2024-02-29','2023-02-29',NA,'','NA','Unknown','2021-01-01'),exclude=NULL)
    got <- pydatetimeconverter(data=data.frame(x=x),datetime_var='x',show_quality_metrics=TRUE,
                extract_dayname=TRUE,extract_weeknum=TRUE,show_summary=TRUE)
    q <- got$quality$asDF
    expect_equal(c(q$input,q$parsed,q$invalid,q$missing),c(7,2,3,2))
    expect_equal(q$success,.4)
    expect_equal(got$preview$asDF$status,c('Parsed','Invalid','Missing','Missing','Invalid','Invalid','Parsed'))
    expect_equal(got$preview$asDF$dayname[c(1,7)],c('Thursday','Friday'))
    expect_equal(got$preview$asDF$weeknum[c(1,7)],c(9,1))
    expect_match(got$report$content,'2 of 7 supplied records')
    expect_error(pydatetimeconverter(data=data.frame(x=c(1,2)),datetime_var='x'),'numeric column')
    expect_error(pydatetimeconverter(data=data.frame(x=as.Date('2024-01-01')),datetime_var='x'),'native Date/POSIX')
})

test_that('saved columns preserve sparse source identities and recover from failed parsing', {
    d <- data.frame(x=factor(c('2024-02-29','2023-02-29',NA,'2021-01-01')),
                    row.names=c('2','5','9','20'))
    opts <- pydatetimeconverterOptions$new(datetime_var='x',show_quality_metrics=TRUE,
                    extract_year=TRUE,extract_weeknum=TRUE,show_summary=TRUE)
    for(name in c('corrected_datetime_numeric','corrected_datetime_char','year_out')) {
        opt <- opts$option(name);opt$value <- list(value=TRUE,vars=list())
    }
    a <- pydatetimeconverterClass$new(options=opts,data=d);a$init();a$run();jmvcore:::initProtoBuf()
    pb <- a$results$corrected_datetime_numeric$asProtoBuf(incAsText=TRUE)$outputs
    expect_equal(as.integer(pb$rowNums),c(1,4,8,19))
    expect_equal(as.numeric(pb$outputs[[1]]$d),c(1709164800,NA,NA,1609459200))
    expect_equal(a$results$preview$asDF$source,rownames(d))
    before <- a$results$preview$asDF
    fmt <- a$options$option('datetime_format');fmt$value <- 'unix_epoch';a$init();a$run()
    expect_equal(a$results$quality$asDF$parsed,0)
    expect_equal(a$results$quality$asDF$invalid,3)
    cleared <- a$results$corrected_datetime_numeric$asProtoBuf(incAsText=TRUE)$outputs$outputs[[1]]$d
    expect_true(all(is.na(cleared)))
    fmt$value <- 'ymd';a$init();a$run();expect_equal(a$results$preview$asDF,before)
    role <- a$options$option('datetime_var');role$value <- NULL;a$init();a$run()
    expect_equal(a$results$preview$rowCount,0);expect_equal(a$results$quality$rowCount,0)
    expect_false(grepl('2 of 4',a$results$report$content,fixed=TRUE))
    role$value <- 'x';a$init();a$run();expect_equal(a$results$preview$asDF,before)
})
