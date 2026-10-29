test_that('flow counts and marginals match independent base R masks', {
    d <- data.frame(a = factor(c(rep('A', 12), rep('A', 5), rep('B', 2), 'B', 'A', NA),
                               levels = c('B', 'A', '(Missing)', 'unused')),
                    b = factor(c(rep('X', 12), rep('Y', 5), rep('X', 2), 'Y', NA, 'Y')),
                    c = factor(c(rep('L', 17), rep('H', 3), 'L', 'H')))
    for (exclude in c(FALSE, TRUE)) {
        got <- pyalluvial(data=d, vars=c('a','b','c'), excl=exclude,
                          showFlowTable=TRUE, showCategories=TRUE)
        retained <- if (exclude) d[complete.cases(d), , drop=FALSE] else d
        retained[] <- lapply(retained, function(x) {
            values <- as.character(x); values[is.na(values)] <- '(Missing 2)'; values
        })
        flows <- got$flows$asDF
        expect_equal(sum(flows$n), nrow(retained))
        expect_equal(sum(flows$percent), 1)
        for (i in seq_len(nrow(flows))) {
            path <- unlist(jsonlite::fromJSON(flows$path[i]))
            mask <- rep(TRUE, nrow(retained))
            for (j in seq_along(path)) mask <- mask & retained[[j]] == path[j]
            expect_equal(flows$n[i], sum(mask))
            expect_equal(flows$percent[i], sum(mask)/nrow(retained))
        }
        cats <- got$categories$asDF
        for (i in seq_len(nrow(cats))) {
            expected <- sum(retained[[cats$variable[i]]] == cats$label[i])
            expect_equal(cats$n[i], expected)
            expect_equal(cats$percent[i], expected/nrow(retained))
        }
        expect_match(got$explorer$content, 'Highlighted flow', fixed=TRUE)
        expect_match(got$explorer$content, 'mouseenter', fixed=TRUE)
    }
})

test_that('native lifecycle clears and restores tables, plot and local view', {
    d <- data.frame(a=factor(c('A','A','B',NA)), b=factor(c('X','Y','X','Y')))
    opts <- pyalluvialOptions$new(vars=c('a','b'),showFlowTable=TRUE,showCategories=TRUE)
    analysis <- pyalluvialClass$new(options=opts,data=d)
    analysis$init(); analysis$run()
    before <- analysis$results$flows$asDF
    raster <- ClinicoPathPj:::.cpjRenderPlot(analysis$results$flowPlot$state,1100L,700L,list(palette='jmv'))
    expect_equal(dim(raster)[1:2],c(700L,1100L))
    role <- analysis$options$option('vars'); role$value <- NULL
    analysis$init(); analysis$run()
    expect_equal(analysis$results$flows$rowCount,0)
    expect_equal(analysis$results$categories$rowCount,0)
    expect_null(analysis$results$flowPlot$state)
    expect_false(grepl('Highlighted flow',analysis$results$explorer$content,fixed=TRUE))
    role$value <- c('a','b'); analysis$init(); analysis$run()
    expect_equal(analysis$results$flows$asDF,before)
    exclusion <- analysis$options$option('excl'); exclusion$value <- TRUE
    analysis$init(); analysis$run()
    fresh <- pyalluvial(data=d,vars=c('a','b'),excl=TRUE,showFlowTable=TRUE,showCategories=TRUE)
    expect_equal(analysis$results$flows$asDF,fresh$flows$asDF)
    expect_equal(analysis$results$categories$asDF,fresh$categories$asDF)
    expect_equal(analysis$results$flowPlot$state,fresh$flowPlot$state)
    for (name in c('showPlot','interactive')) {
        opt <- analysis$options$option(name); opt$value <- FALSE
    }
    analysis$init(); analysis$run()
    expect_null(analysis$results$flowPlot$state)
    expect_false(grepl('Highlighted flow',analysis$results$explorer$content,fixed=TRUE))
    expect_equal(analysis$results$flows$asDF,fresh$flows$asDF)
})

test_that('genuine factor NA and literal NA remain distinct', {
    d <- data.frame(a=factor(c('NA',NA,'A'),exclude=NULL),b=factor(c('X','X','X')))
    got <- pyalluvial(data=d,vars=c('a','b'),showFlowTable=TRUE,showCategories=TRUE)
    expect_equal(sum(got$flows$asDF$n),3)
    expect_setequal(got$categories$asDF$label[got$categories$asDF$variable=='a'],c('NA','A','(Missing)'))
    excluded <- pyalluvial(data=d,vars=c('a','b'),excl=TRUE,showFlowTable=TRUE)
    expect_equal(sum(excluded$flows$asDF$n),2)
})
