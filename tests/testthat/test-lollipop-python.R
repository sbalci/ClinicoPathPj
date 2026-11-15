test_that('native lollipop tables match independent R fixtures in both orientations', {
    refs<-jsonlite::fromJSON(testthat::test_path('..','fixtures','lollipop-core.json'),simplifyVector=FALSE)
    for(f in refs$fixtures) {
        inp<-f$inputs
        labels<-vapply(inp$levels,function(v)if(is.null(v))NA_character_ else v,'')
        codes<-as.integer(unlist(inp$codes));values<-labels[pmax(1,codes+1)];values[codes<0]<-NA_character_
        d<-data.frame(Value=vapply(inp$values,function(v)if(is.null(v))NA_real_ else as.numeric(v),0),
            Group=factor(values,levels=labels,exclude=NULL))
        rownames(d)<-as.character(seq_len(nrow(d))*7+3)
        for(run in Filter(function(r)r$sorting=='original',f$runs)) {
            e<-run$expected
            got<-pylollipop(data=d,dep='Value',group='Group',aggregation=run$aggregation,
                orientation=run$orientation,baseline=inp$baseline,showMean=TRUE,showCases=TRUE)
            expect_equal(got$cohort$asDF$complete,as.integer(e$n_complete),info=f$id)
            actual<-got$descriptives$asDF
            for(j in 1:2) {
                reference<-e[[if(j==1)'raw_summary' else 'plotted_summary']]
                for(k in names(reference)) {
                    target<-if(is.null(reference[[k]]))NA_real_ else as.numeric(reference[[k]])
                    expect_equal(as.numeric(actual[[k]][j]),target,tolerance=2e-12,info=paste(f$id,k))
                }
            }
            expect_equal(got$cases$asDF$sourceID,rownames(d)[unlist(e$retained_indices)+1],info=f$id)
            expect_equal(got$points$asDF$value,vapply(e$points,function(p)as.numeric(p$value),0),tolerance=2e-12)
            expect_equal(unlist(got$lollipopPlot$state$data$slot),vapply(e$points,function(p)as.integer(p$slot),0L))
            expect_equal(as.numeric(got$lollipopPlot$state$reference),as.numeric(e$reference_mean),tolerance=2e-12)
        }
    }
})

test_that('native lollipop clears, recovers, changes design and exports restored states', {
    d<-data.frame(Value=c(10,10,10,50,52,52,NA),Group=factor(c('A','A','A','B','C','C','A')))
    original<-d
    opts<-pylollipopOptions$new(dep='Value',group='Group',showCases=TRUE,showMean=TRUE)
    a<-pylollipopClass$new(options=opts)
    a$.setReadDatasetSource(function(...)d);a$.setReadDatasetHeaderSource(function(...)d)
    set_option<-function(n,v){o<-opts$option(n);o$value<-v}
    a$init();a$run();initial<-a$results$descriptives$asDF
    expect_equal(initial$mean,c(184/6,112/3))
    set_option('sortBy','value_desc');set_option('orientation','horizontal')
    set_option('aggregation','median');a$init();a$run()
    fresh<-pylollipop(data=d,dep='Value',group='Group',sortBy='value_desc',
        orientation='horizontal',aggregation='median',showMean=TRUE,showCases=TRUE)
    expect_equal(a$results$points$asDF,fresh$points$asDF)
    expect_equal(a$results$lollipopPlot$state,fresh$lollipopPlot$state)
    set_option('showPoints',FALSE);set_option('showCases',FALSE);set_option('showPlot',FALSE)
    a$init();a$run()
    expect_equal(a$results$points$rowCount,0);expect_equal(a$results$cases$rowCount,0)
    expect_null(a$results$lollipopPlot$state)
    set_option('dep',NULL);a$init();a$run()
    for(n in c('cohort','missing','descriptives','groups','points','cases'))expect_equal(a$results$get(n)$rowCount,0)
    set_option('dep','Value');set_option('showPlot',TRUE);set_option('showPoints',TRUE)
    d$Value[1]<-Inf;a$init();expect_error(a$run(),'infinite')
    expect_equal(a$results$descriptives$rowCount,0);expect_null(a$results$lollipopPlot$state)
    d<-original;a$init();a$run()
    expect_equal(a$results$points$asDF,fresh$points$asDF)
    for(orientation in c('horizontal','vertical')) {
        set_option('orientation',orientation);a$init();a$run()
        f<-tempfile(fileext='.rds');saveRDS(a$results$lollipopPlot$state,f)
        a$results$lollipopPlot$setState(readRDS(f));a$.__enclos_env__$private$.data<-NULL
        out<-paste0('/private/tmp/cpj-lollipop-native-',orientation,'.png')
        a$results$lollipopPlot$saveAs(out)
        expect_true(file.exists(out));expect_gt(file.info(out)$size,1000)
    }
})
