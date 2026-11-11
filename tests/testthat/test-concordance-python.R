test_that('CCC native coefficients preserve population moments and source identities', {
    d <- data.frame('Method A' = c(0:9, NA, 11, NA),
                    'Method+B' = c(1:10, 10, NA, NA),
                    Case = c('NA', '01', as.character(2:9), '01', NA, '01'),
                    check.names = FALSE)
    rownames(d) <- as.character(100 + 3 * (0:12))
    got <- pyagreement(d, vars=c('Method A', 'Method+B'), subject='Case',
                       method='ccc', showCCCPairs=TRUE, cccPlot=TRUE)
    expect_equal(got$cccStatistics$asDF$estimate, c(16.5/17.5, 1, 16.5/17.5), tolerance=1e-12)
    expect_equal(unname(as.numeric(got$cccAudit$asDF[1,])), c(13,10,3,1,1,1))
    expect_equal(got$cccPairs$asDF$sourceID, rownames(d)[1:10])
    expect_equal(got$cccPairs$asDF$case, d$Case[1:10])
    expect_equal(got$cccFigure$state$data$x, as.numeric(0:9))
    expect_equal(got$cccFigure$state$data$y, as.numeric(1:10))
    expect_equal(got$statistics$rowCount, 0)
    expect_equal(got$iccStatistics$rowCount, 0)
    expect_null(got$plot$state)
    expect_match(got$summary$content, 'point estimates only')
    expect_equal(names(got$cccStatistics$asDF), c('measure','estimate'))
})

test_that('CCC native table agrees with frozen independent R fixtures', {
    fixtures <- jsonlite::fromJSON(testthat::test_path('..','fixtures','concordance-points.json'),
                                   simplifyVector=FALSE)$cases
    count <- 0L
    for (f in fixtures) {
        if (f$n_complete < 10) next
        # JSON null cells are genuine missing measurements, not omitted positions.
        decode <- function(x) vapply(x, function(v) if (is.null(v)) NA_real_ else v, numeric(1))
        d <- data.frame(a=decode(f$x), b=decode(f$y))
        got <- pyagreement(d, vars=c('a','b'), method='ccc')
        expected <- unlist(f$expected[c('ccc','precision','bias_correction')], use.names=FALSE)
        expect_equal(got$cccStatistics$asDF$estimate, expected, tolerance=1e-12, info=f$id)
        count <- count + 1L
    }
    expect_gt(count, 5L)
})

test_that('CCC switching and incomplete or rejected data clear all stale results', {
    d <- data.frame(a=0:9, b=1:10, c=c(2:10,12), id=letters[1:10])
    opts <- pyagreementOptions$new(vars=c('a','b'), subject='id', method='ccc',
                                  showCCCPairs=TRUE, cccPlot=TRUE,
                                  showPairs=TRUE, blandAltmanPlot=TRUE, showICCCases=TRUE)
    a <- pyagreementClass$new(options=opts)
    a$.setReadDatasetSource(function(...) d)
    a$.setReadDatasetHeaderSource(function(...) d)
    method <- opts$option('method')
    variables <- opts$option('vars')
    plot <- opts$option('cccPlot')
    pairs <- opts$option('showCCCPairs')
    rerun <- function() { a$init(); a$run() }
    ccc_empty <- function() {
        expect_equal(a$results$cccAudit$rowCount,0)
        expect_equal(a$results$cccStatistics$rowCount,0)
        expect_equal(a$results$cccPairs$rowCount,0)
        expect_null(a$results$cccFigure$state)
    }
    rerun()
    expect_equal(a$results$cccStatistics$rowCount,3)
    expect_equal(a$results$cccPairs$rowCount,10)
    method$value <- 'blandaltman'; rerun(); ccc_empty()
    expect_equal(a$results$statistics$rowCount,4)
    method$value <- 'icc'; rerun(); ccc_empty()
    expect_equal(a$results$iccStatistics$rowCount,1)
    method$value <- 'ccc'; rerun()
    expect_equal(a$results$iccStatistics$rowCount,0)
    expect_equal(a$results$statistics$rowCount,0)
    expect_null(a$results$plot$state)
    variables$value <- 'a'; rerun(); ccc_empty()
    variables$value <- c('a','b'); d$b[10] <- NA; a$init()
    expect_error(a$run(),'at least 10'); ccc_empty()
    d$b <- 1:10; d$id[2] <- 'a'; a$init()
    expect_error(a$run(),'unique case IDs'); ccc_empty()
    d$id <- letters[1:10]; rerun()
    expect_equal(a$results$cccStatistics$rowCount,3)
    plot$value <- FALSE
    pairs$value <- FALSE; rerun()
    expect_null(a$results$cccFigure$state)
    expect_equal(a$results$cccPairs$rowCount,0)
    expect_equal(a$results$cccStatistics$rowCount,3)
})

test_that('constant CCC cells remain undefined without fabricated estimates', {
    got <- pyagreement(data.frame(a=rep(2,10),b=rep(2,10)), vars=c('a','b'),method='ccc')
    expect_true(all(is.na(got$cccStatistics$asDF$estimate)))
    got <- pyagreement(data.frame(a=rep(2,10),b=rep(3,10)), vars=c('a','b'),method='ccc')
    expect_equal(got$cccStatistics$asDF$estimate,c(0,NA_real_,0))
})

test_that('legacy public R positional arguments and defaults remain stable', {
    legacy <- c('data','vars','subject','baConfidenceLevel','confLevel','showPairs',
                'blandAltmanPlot','method','iccType','showICCCases','showConsole')
    expect_equal(names(formals(pyagreement))[seq_along(legacy)],legacy)
    expect_equal(formals(pyagreement)$method,'blandaltman')
    d <- data.frame(a=0:9,b=1:10)
    # Last TRUE is the original showConsole position, not a new CCC display flag.
    result <- pyagreement(d,c('a','b'),NULL,.95,.95,FALSE,FALSE,'ccc','icc21',FALSE,TRUE)
    expect_equal(result$cccStatistics$rowCount,3)
    expect_equal(result$cccPairs$rowCount,0)
    expect_null(result$cccFigure$state)
})
