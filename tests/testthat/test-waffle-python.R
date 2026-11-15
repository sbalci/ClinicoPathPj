waffle_factor<-function(codes,labels) {
    levels<-vapply(labels,function(v)if(is.null(v))NA_character_ else as.character(v),'')
    codes<-as.integer(unlist(codes));values<-levels[pmax(1,codes+1L)];values[codes<0]<-NA_character_
    factor(values,levels=levels,exclude=NULL)
}

test_that('native waffle matches independent panels, counts, allocation and geometry', {
    refs<-jsonlite::fromJSON(testthat::test_path('..','fixtures','waffle-core.json'),simplifyVector=FALSE)
    selected<-Filter(function(f)f$rows %in% c(5L,7L),refs$fixtures)
    for(f in selected) {
        inp<-f$inputs;e<-f$expected
        d<-data.frame(Category=waffle_factor(inp$codes,inp$levels))
        rownames(d)<-as.character(seq_len(nrow(d))*7-4)
        args<-list(data=d,groups='Category',rows=f$rows,flip=f$flip,showCases=TRUE)
        if(!is.null(inp$weights)) {
            d$Count<-vapply(inp$weights,function(v)if(is.null(v))NA_real_ else as.numeric(v),0)
            args$counts<-'Count'
        }
        if(!is.null(inp$facets)) {
            d$Panel<-waffle_factor(inp$facets,inp$facet_levels);args$facet<-'Panel'
        }
        args$data<-d;got<-do.call(pyjwaffle,args)
        for(pair in list(c('source','n_source'),c('complete','n_complete'),c('excluded','excluded_missing'),
                         c('zero','zero_frequency'),c('total','n_total'),c('contributing','n_contributing'))) {
            expect_equal(as.numeric(got$cohort$asDF[[pair[1]]]),as.numeric(e[[pair[2]]]),info=f$id)
        }
        cells<-do.call(c,lapply(e$panels,function(p)p$cells))
        expect_equal(got$allocation$asDF$count,vapply(cells,function(c)as.numeric(c$count),0),info=f$id)
        expect_equal(got$allocation$asDF$tiles,vapply(cells,function(c)as.integer(c$tiles),0L),info=f$id)
        expect_equal(got$allocation$asDF$proportion,vapply(cells,function(c)as.numeric(c$proportion),0),info=f$id)
        expect_equal(got$allocation$asDF$denominator,unlist(lapply(e$panels,function(p)rep(p$n_total,length(p$cells)))),info=f$id)
        expect_equal(got$cases$asDF$sourceID,rownames(d)[unlist(e$retained_indices)+1L],info=f$id)
        payload<-jsonlite::fromJSON(got$wafflePlot$state$data$payload[[1]],simplifyVector=FALSE)
        # The established R bridge removes genuine missing levels before transport,
        # so geometry codes index that normalized order, while labels stay exact.
        declared<-which(!vapply(inp$levels,is.null,logical(1)))-1L
        expected_geometry<-lapply(e$panels,function(p)lapply(p$geometry,function(t) {
            t$code<-match(t$code,declared)-1L;t
        }))
        expect_equal(lapply(payload$panels,function(p)lapply(p$cells,function(c)c$label)),
                     lapply(e$panels,function(p)lapply(p$cells,function(c)c$label)),info=f$id)
        expect_equal(lapply(payload$panels,function(p)p$geometry),expected_geometry,info=f$id)
        expect_equal(length(payload$panels),length(e$panels))
        expect_equal(got$panels$rowCount,length(e$panels)+length(e$inactive_facet_codes))
    }
})

test_that('native waffle clears incomplete invalid and optional results then recovers', {
    d<-data.frame(Category=factor(c('A','B','A',NA),levels=c('A','B','Zero')),
                  Panel=factor(c('Small','Small','Large','Large')),Count=c(1,3,9,2))
    opts<-pyjwaffleOptions$new(groups='Category',counts='Count',facet='Panel',showCases=TRUE,showExplanations=TRUE)
    a<-pyjwaffleClass$new(options=opts)
    a$.setReadDatasetSource(function(...)d);a$.setReadDatasetHeaderSource(function(...)d)
    set<-function(n,v){o<-opts$option(n);o$value<-v}
    a$init();a$run();original<-a$results$allocation$asDF
    expect_equal(a$results$cohort$asDF$total,13)
    set('showPlot',FALSE);set('showCases',FALSE);set('showExplanations',FALSE);a$init();a$run()
    expect_null(a$results$wafflePlot$state);expect_equal(a$results$cases$rowCount,0)
    expect_equal(a$results$explanation$content,'')
    set('groups',NULL);a$init();a$run()
    for(name in c('cohort','missing','panels','allocation','cases'))expect_equal(a$results$get(name)$rowCount,0)
    set('groups','Category');set('showPlot',TRUE);a$init();a$run()
    expect_equal(a$results$allocation$asDF,original)
    d$Count[1]<--1;a$init();expect_error(a$run(),'nonnegative')
    expect_equal(a$results$allocation$rowCount,0);expect_null(a$results$wafflePlot$state)
    d$Count[1]<-1;set('rows',7L);set('flip',TRUE);set('show_legend',TRUE);a$init();a$run()
    fresh<-pyjwaffle(data=d,groups='Category',counts='Count',facet='Panel',rows=7L,flip=TRUE,show_legend=TRUE)
    expect_equal(a$results$allocation$asDF,fresh$allocation$asDF)
    expect_equal(a$results$wafflePlot$state,fresh$wafflePlot$state)
    path<-tempfile(fileext='.rds');saveRDS(a$results$wafflePlot$state,path)
    a$results$wafflePlot$setState(readRDS(path));a$.__enclos_env__$private$.data<-NULL
    output<-'/private/tmp/cpj-waffle-native-restored.png'
    a$results$wafflePlot$saveAs(output)
    expect_true(file.exists(output));expect_gt(file.info(output)$size,1000)
    set('facet',NULL);set('flip',FALSE);a$init();a$run()
    expect_equal(a$results$panels$rowCount,1)
    expect_equal(a$results$allocation$rowCount,3)
    a$results$wafflePlot$saveAs('/private/tmp/cpj-waffle-native-single.png')
})
