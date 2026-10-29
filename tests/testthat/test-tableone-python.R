test_that('standard Table One agrees with independent tableone and base R summaries', {
    skip_if_not_installed('tableone')
    d <- data.frame(x=c(1,2,NA,4,5,6,7,8),code=c(1,2,1,2,1,2,1,2),
                    binary=factor(c('A','B',NA,'B','A','B','A','B'),levels=c('B','A')),
                    many=factor(c('A','A',NA,'B','B','A','A','B'),levels=c('B','A','unused')),
                    txt=c('z','a',NA,'z','a','z','z','a'),flag=c(TRUE,FALSE,NA,TRUE,FALSE,TRUE,TRUE,FALSE),
                    empty=NA_real_,date=as.Date(c('2020-01-01',rep(NA,7))))
    for (exclude in c(FALSE,TRUE)) {
        included <- d[,c('x','code','binary','many','txt','flag')]
        cohort <- if(exclude) included[complete.cases(included),,drop=FALSE] else included
        oracle <- tableone::CreateTableOne(data=cohort,test=FALSE)
        for(display in c('mean','median')) {
            got <- pytableone(data=d,vars=names(d),excl=exclude,cont=display,
                              showSummary=TRUE,showAllLevels=TRUE)
            expect_equal(got$cohort$asDF$retained,nrow(cohort))
            expect_equal(got$cohort$asDF$omitted,2)
            expect_equal(got$cohort$asDF$included,6)
            numeric <- got$continuous$asDF
            reference <- oracle$ContTable[[1]]
            for(i in seq_len(nrow(numeric))) {
                v <- numeric$variable[i];x <- cohort[[v]];valid <- sum(!is.na(x))
                expect_equal(numeric$valid[i],valid)
                expect_equal(numeric$missing[i],sum(is.na(x)))
                expect_equal(numeric$missingPercent[i],mean(is.na(x)))
                if(display=='mean') {
                    expect_equal(numeric$mean[i],unname(reference[v,'mean']),tolerance=1e-12)
                    expect_equal(numeric$sd[i],unname(reference[v,'sd']),tolerance=1e-12)
                } else {
                    expect_equal(c(numeric$q1[i],numeric$median[i],numeric$q3[i]),
                                 unname(reference[v,c('p25','median','p75')]),tolerance=1e-12)
                }
            }
            cats <- got$categories$asDF
            for(i in seq_len(nrow(cats))) {
                v <- cats$variable[i];ref <- oracle$CatTable[[1]][[v]]
                selected <- ref[ref$level==cats$level[i],,drop=FALSE]
                expect_equal(nrow(selected),1)
                expect_equal(cats$n[i],unname(as.numeric(selected$freq)))
                expect_equal(cats$valid[i],sum(!is.na(cohort[[v]])))
                expect_equal(cats$percent[i],unname(as.numeric(selected$percent))/100,tolerance=1e-12)
                expect_equal(cats$missingPercent[i],mean(is.na(cohort[[v]])))
            }
        }
        compact <- pytableone(data=d,vars=names(d),excl=exclude)$categories$asDF
        expect_setequal(compact$level[compact$variable=='binary'],'A')
        expect_setequal(compact$level[compact$variable=='txt'],'z')
        expect_setequal(compact$level[compact$variable=='flag'],'TRUE')
    }
})

test_that('storage metadata prevents silent matrix flattening and retains annotations', {
    encode <- ClinicoPathPj:::.cpjColumn
    x <- c(1,2,3);attr(x,'units') <- 'mm';attr(x,'label') <- 'Tumour size'
    info <- encode(x,'x')$storage
    expect_equal(unclass(info$classes),'numeric')
    expect_null(info$dimensions)
    expect_equal(info$rows,3);expect_equal(unclass(info$units),'mm')
    got <- pytableone(data=data.frame(x=I(x)),vars='x',showSummary=TRUE)
    # AsIs is deliberately unsupported, as in the baseline's class allowlist.
    expect_equal(got$cohort$asDF$omitted,1)
    d <- data.frame(x=c(1,2,3));attr(d$x,'units') <- 'mm';attr(d$x,'label') <- 'Tumour size'
    got <- pytableone(data=d,vars='x',showSummary=TRUE)
    expect_equal(got$eligibility$asDF$units,'mm')
    expect_equal(got$eligibility$asDF$label,'Tumour size')
    m <- data.frame(x=1:3);m$matrix <- matrix(1:6,nrow=3)
    expect_equal(unclass(encode(m$matrix,'matrix')$storage$dimensions),c(3L,2L))
    # R supplies row IDs: the existing alignment guard rejects the flattened
    # matrix even before the analysis-specific structured-column check runs.
    expect_error(pytableone(data=m,vars='matrix'),'Row IDs and columns have unequal lengths')
    l <- data.frame(x=1:3);l$list <- list(1,2,3)
    expect_equal(unclass(encode(l$list,'list')$storage$classes),'list')
    # jmvcore rejects native R list columns during selection, before the bridge.
    expect_error(pytableone(data=l,vars='list'),'row.names')
})

test_that('native lifecycle clears and restores stats, omissions and optional text', {
    d <- data.frame(x=c(1,NA,3),y=c(NA,2,NA),empty=NA_real_,g=factor(c('B','A','B')))
    opts <- pytableoneOptions$new(vars=c('x','y','g','empty'),showSummary=TRUE,
                                  showAbout=TRUE,showReportSentence=TRUE)
    a <- pytableoneClass$new(options=opts,data=d);a$init();a$run()
    before <- a$results$continuous$asDF
    expect_equal(a$results$cohort$asDF$omitted,1)
    expect_match(a$results$report$content,'3 retained records')
    display <- a$options$option('cont');display$value <- 'median';a$init();a$run()
    expect_true('median' %in% names(a$results$continuous$asDF))
    expect_false('mean' %in% names(a$results$continuous$asDF))
    role <- a$options$option('vars');role$value <- 'empty';a$init();a$run()
    expect_equal(a$results$continuous$rowCount,0);expect_equal(a$results$categories$rowCount,0)
    expect_true(is.na(a$results$cohort$asDF$retained))
    expect_match(a$results$report$content,'No descriptive report')
    role$value <- c('x','y');excl <- a$options$option('excl');excl$value <- TRUE;a$init();a$run()
    expect_equal(a$results$cohort$asDF$retained,0)
    expect_equal(a$results$continuous$rowCount,0)
    role$value <- c('x','y','g','empty');excl$value <- FALSE;display$value <- 'mean';a$init();a$run()
    expect_equal(a$results$continuous$asDF,before)
    fresh <- pytableone(data=d,vars=c('x','y','g','empty'),showSummary=TRUE,
                        showAbout=TRUE,showReportSentence=TRUE)
    expect_equal(a$results$cohort$asDF,fresh$cohort$asDF)
    expect_equal(a$results$categories$asDF,fresh$categories$asDF)
    role$value <- NULL;a$init();a$run()
    for(name in c('cohort','continuous','categories','eligibility'))expect_equal(a$results[[name]]$rowCount,0)
    expect_false(grepl('3 retained records',a$results$report$content,fixed=TRUE))
})

test_that('genuine missing levels and literal NA remain separate', {
    d <- data.frame(x=1:4,g=factor(c('NA',NA,'Unknown','NA'),exclude=NULL))
    got <- pytableone(data=d,vars=c('x','g'),showAllLevels=TRUE)
    cat <- got$categories$asDF
    expect_equal(cat$n[cat$level=='NA'],2)
    expect_equal(cat$n[cat$level=='Unknown'],1)
    expect_true(all(cat$valid==3));expect_true(all(cat$missing==1))
})
