test_that('Python status agrees with the frozen shared R event coder', {
    env <- new.env(parent=globalenv())
    sys.source(file.path(Sys.getenv('CPJ_ROOT'),'tests/reference/outcome-eventindicator.R'),env)
    oracle <- env$.defineEventIndicator
    y <- factor(c('N','D','X','O',NA,'N','X'),levels=c('O','X','D','N','Unused'))
    for (mode in c('os','cause','compete')) {
        ref <- oracle(y,multievent=TRUE,analysistype=if(mode=='os') 'overall' else mode,
                      awod='N',awd='D',dod='X',dooc='O')
        got <- pyoutcomeorganizer(data=data.frame(y=y),outcome='y',multievent=TRUE,
                                 analysistype=mode,awod='N',awd='D',dod='X',dooc='O',diagnostics=TRUE,
                                 visualization=TRUE,showNaturalSummary=TRUE)
        expect_null(ref$error)
        expect_equal(got$preview$asDF$code,ref$status)
        expect_equal(got$cohort$asDF$valid,sum(!is.na(y)))
        expect_equal(got$cohort$asDF$missing,sum(is.na(y)))
        for(i in seq_len(nrow(got$frequencies$asDF))) {
            row <- got$frequencies$asDF[i,]
            expect_equal(row$n,sum(ref$status==row$code,na.rm=TRUE))
            expect_equal(row$percent,mean(ref$status[!is.na(ref$status)]==row$code))
        }
        expect_equal(got$mapping$asDF$n,as.integer(table(y)))
        state <- got$distribution$state
        expect_equal(state$data$value,got$frequencies$asDF$n)
        raster <- ClinicoPathPj:::.cpjRenderPlot(state,800L,500L,list(palette='jmv'))
        expect_equal(dim(raster)[1:2],c(500L,800L))
    }
    for(event in c('N','X','Unused')) {
        ref <- oracle(y,outcomeLevel=event)
        got <- pyoutcomeorganizer(data=data.frame(y=y),outcome='y',outcomeLevel=event,diagnostics=TRUE)
        expect_equal(got$preview$asDF$code,ref$status)
    }
    for(event in c('Event','Competing')) {
        y <- factor(c('Event','Censored','Competing',NA),levels=c('Competing','Event','Censored'))
        got <- pyoutcomeorganizer(data=data.frame(y=y),outcome='y',outcomeLevel=event,diagnostics=TRUE)
        expect_equal(got$preview$asDF$code,oracle(y,outcomeLevel=event)$status)
    }
    y <- c(0,1,NA,0)
    for(event in list(NULL,'0','1')) {
        got <- pyoutcomeorganizer(data=data.frame(y=y),outcome='y',outcomeLevel=event,diagnostics=TRUE)
        expect_equal(got$preview$asDF$code,oracle(y,outcomeLevel=event)$status)
    }
})

test_that('multistate snapshot and exact missing encodings remain explicit', {
    y <- factor(c('N','D','X','O',NA),levels=c('N','D','X','O'))
    got <- pyoutcomeorganizer(data=data.frame(y=y),outcome='y',multievent=TRUE,
             analysistype='multistate',awod='N',awd='D',dod='X',dooc='O',diagnostics=TRUE)
    expect_equal(got$preview$asDF$code,c(0,1,2,3,NA))
    expect_equal(got$frequencies$asDF$n,rep(1,4))
    expect_match(got$summary$content,'snapshot')
    y <- factor(c('NA',NA,'Unknown',NA),levels=c('NA',NA,'Unknown'),exclude=NULL)
    got <- pyoutcomeorganizer(data=data.frame(y=y),outcome='y',outcomeLevel='NA',diagnostics=TRUE)
    expect_equal(got$preview$asDF$code,c(1,NA,0,NA))
    expect_equal(got$cohort$asDF$missing,2)
})

test_that('saved statuses keep sparse source IDs and clear through incomplete input', {
    d <- data.frame(y=factor(c('N','X',NA,'O','N')),row.names=c('2','5','9','12','20'))
    opts <- pyoutcomeorganizerOptions$new(outcome='y',multievent=TRUE,analysistype='compete',
                    awod='N',dod='X',dooc='O',diagnostics=TRUE,visualization=TRUE,showNaturalSummary=TRUE)
    saved <- opts$option('addOutcome');saved$value <- list(value=TRUE,vars=list())
    a <- pyoutcomeorganizerClass$new(options=opts,data=d);a$init();a$run();jmvcore:::initProtoBuf()
    pb <- a$results$addOutcome$asProtoBuf(incAsText=TRUE)$outputs
    expect_equal(as.integer(pb$rowNums),c(1,4,8,11,19))
    expect_equal(as.integer(pb$outputs[[1]]$i)[c(1,2,4,5)],c(1,2,3,1))
    expect_true(is.na(pb$outputs[[1]]$i[3]) || pb$outputs[[1]]$i[3] == -2147483648)
    expect_equal(a$results$preview$asDF$source,rownames(d))
    expected <- a$results$frequencies$asDF
    level <- a$options$option('dooc');level$value <- NULL
    expect_error({a$init();a$run()},'unassigned')
    expect_equal(a$results$mapping$rowCount,0);expect_equal(a$results$preview$rowCount,0)
    expect_null(a$results$distribution$state)
    expect_false(grepl('5 supplied rows',a$results$report$content,fixed=TRUE))
    cleared <- a$results$addOutcome$asProtoBuf(incAsText=TRUE)$outputs$outputs[[1]]$i
    expect_true(all(is.na(cleared)|cleared == -2147483648))
    level$value <- 'O';a$init();a$run();expect_equal(a$results$frequencies$asDF,expected)
    # Successful-but-incomplete Python answers must also clear saved values.
    multi <- a$options$option('multievent');mode <- a$options$option('analysistype')
    multi$value <- FALSE;mode$value <- 'os';a$init();a$run()
    expect_match(a$results$summary$content,'Choose the event')
    expect_equal(a$results$cohort$rowCount,0)
    pending <- a$results$addOutcome$asProtoBuf(incAsText=TRUE)$outputs$outputs[[1]]$i
    expect_true(all(is.na(pending)|pending == -2147483648))
    multi$value <- TRUE;mode$value <- 'compete';a$init();a$run()
    expect_equal(a$results$frequencies$asDF,expected)
    role <- a$options$option('outcome');role$value <- NULL;a$init();a$run()
    expect_equal(a$results$cohort$rowCount,0);expect_null(a$results$distribution$state)
    role$value <- 'y';a$init();a$run();expect_equal(a$results$frequencies$asDF,expected)
})

test_that('incomplete factor level waits and ambiguous mappings reject', {
    d <- data.frame(y=factor(c('Alive','Dead')))
    got <- pyoutcomeorganizer(data=d,outcome='y')
    expect_equal(got$cohort$rowCount,0);expect_match(got$summary$content,'Choose the event')
    expect_error(pyoutcomeorganizer(data=d,outcome='y',multievent=TRUE,dod='Dead',awod='Dead'),'only one')
    expect_error(pyoutcomeorganizer(data=data.frame(y=c(1,2)),outcome='y'),'only 0 and 1')
    expect_error(pyoutcomeorganizer(data=data.frame(y=NA_real_),outcome='y'),'only missing')
})
