test_that('composite status agrees with frozen R logic and independent nine-row truth table', {
    source(file.path(Sys.getenv('CPJ_ROOT'),'tests/reference/outcome-composite-status.R'),local=TRUE)
    y <- c(0,0,0,1,1,1,NA,NA,NA)
    recurrence <- c(0,1,NA,0,1,NA,0,1,NA)
    d <- data.frame(y=y,r=factor(ifelse(is.na(recurrence),NA,ifelse(recurrence==1,'Yes','No')),levels=c('Yes','No','Unused')))
    truth <- c(0,1,NA,1,1,1,NA,1,NA)
    for(mode in c('rfs','pfs','dfs','ttp')) {
        got <- pyoutcomeorganizer(data=d,outcome='y',recurrence='r',recurrenceLevel='Yes',
                    analysistype=mode,diagnostics=TRUE,visualization=TRUE)
        ref <- composite_status_reference(y,recurrence,mode)
        expect_equal(got$preview$asDF$code,ref)
        expect_equal(got$preview$asDF$code,if(mode=='ttp') recurrence else truth)
        expect_equal(got$frequencies$asDF$n,if(mode=='ttp') c(3,3) else c(1,5))
        expect_equal(got$cohort$asDF$valid,6)
        expect_equal(got$cohort$asDF$missing,3)
        expect_equal(got$compositeAudit$asDF$overrides,if(mode=='ttp') 0 else 2)
        expect_equal(got$distribution$state$data$value,got$frequencies$asDF$n)
        expect_equal(nrow(got$components$asDF),if(mode=='ttp') 3 else 5)
    }
})

test_that('progression ignores missing outcome and composite handles all-unknown rows', {
    d <- data.frame(y=rep(NA_real_,3),r=factor(c('Yes','No',NA),levels=c('Yes','No')))
    got <- pyoutcomeorganizer(data=d,outcome='y',recurrence='r',recurrenceLevel='Yes',
                             analysistype='ttp',outcomeLevel='stale',diagnostics=TRUE)
    expect_equal(got$preview$asDF$code,c(1,0,NA))
    got <- pyoutcomeorganizer(data=d,outcome='y',recurrence='r',recurrenceLevel='Yes',
                             analysistype='rfs',diagnostics=TRUE)
    expect_equal(got$preview$asDF$code,c(1,NA,NA))
    d$r <- factor(rep(NA_character_,3),levels=c('Yes','No'))
    got <- pyoutcomeorganizer(data=d,outcome='y',recurrence='r',recurrenceLevel='Yes',
                             analysistype='rfs',diagnostics=TRUE)
    expect_true(all(is.na(got$preview$asDF$code)))
    expect_true(all(is.na(got$frequencies$asDF$percent)))
})

test_that('composite saved rows clear for incomplete mapping and recover across methods', {
    d <- data.frame(y=c(0,1,NA),r=factor(c('No',NA,'Yes'),levels=c('No','Yes')),row.names=c('2','8','20'))
    opts <- pyoutcomeorganizerOptions$new(outcome='y',recurrence='r',recurrenceLevel='Yes',
                                         analysistype='rfs',diagnostics=TRUE)
    out <- opts$option('addOutcome');out$value <- list(value=TRUE,vars=list())
    a <- pyoutcomeorganizerClass$new(options=opts,data=d);a$init();a$run();jmvcore:::initProtoBuf()
    saved <- function() a$results$addOutcome$asProtoBuf(incAsText=TRUE)$outputs
    expect_equal(as.integer(saved()$rowNums),c(1,7,19))
    expect_equal(as.integer(saved()$outputs[[1]]$i),c(1,2,2))
    level <- opts$option('recurrenceLevel');level$value <- NULL;a$init();a$run()
    expect_equal(a$results$components$rowCount,0)
    expect_true(all(is.na(saved()$outputs[[1]]$i)|saved()$outputs[[1]]$i == -2147483648))
    level$value <- 'Yes';a$init();a$run();expect_equal(as.integer(saved()$outputs[[1]]$i),c(1,2,2))
    method <- opts$option('analysistype');method$value <- 'ttp';a$init();a$run()
    s <- as.integer(saved()$outputs[[1]]$i);expect_equal(s[c(1,3)],c(1,2))
    expect_true(is.na(s[2]) || s[2] == -2147483648)
    method$value <- 'os';a$init();a$run()
    expect_equal(a$results$components$rowCount,0)
    expect_equal(a$results$preview$asDF$code,c(0,1,NA))
})
