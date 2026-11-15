pie_factor<-function(codes,labels) {
    levels<-vapply(labels,function(v)if(is.null(v))NA_character_ else as.character(v),'')
    code<-as.integer(unlist(codes));values<-levels[pmax(1,code+1)];values[code<0]<-NA_character_
    factor(values,levels=levels,exclude=NULL)
}

test_that('native pie tables preserve independent frequencies and declared categories', {
    refs<-jsonlite::fromJSON(testthat::test_path('..','fixtures','pie-core.json'),simplifyVector=FALSE)
    for(f in refs$fixtures) {
        inp<-f$inputs;e<-f$expected
        d<-data.frame(Outcome=pie_factor(inp$codes,inp$levels))
        rownames(d)<-as.character(seq_len(nrow(d))*7+3)
        args<-list(data=d,dep='Outcome',showCases=TRUE)
        if(!is.null(inp$weights)) {
            d$Frequency<-vapply(inp$weights,function(v)if(is.null(v))NA_real_ else as.numeric(v),0)
            args$data<-d;args$counts<-'Frequency'
        }
        got<-do.call(pyjjpiestats,args)
        for(pair in list(c('source','n_source'),c('complete','n_complete'),c('total','n_total'),
                         c('zero','zero_frequency'),c('excluded','excluded_missing'))) {
            expect_equal(as.numeric(got$cohort$asDF[[pair[1]]]),as.numeric(e[[pair[2]]]),info=f$id)
        }
        cells<-got$frequencies$asDF
        labels<-vapply(e$cells,function(c)c$label,'')
        displayed_labels<-labels
        # Existing bridge prevents native table cells from being read as markup.
        if(f$id=='ordinal_unicode')displayed_labels[3]<-'< A & B>'
        expect_equal(cells$category,displayed_labels,info=f$id)
        expect_equal(unlist(got$piePlot$state$data$category),labels,info=f$id)
        expect_equal(cells$count,vapply(e$cells,function(c)as.numeric(c$count),0),info=f$id)
        expect_equal(cells$proportion,vapply(e$cells,function(c)as.numeric(c$proportion),0),info=f$id)
        expect_equal(cells$denominator,rep(as.numeric(e$n_total),nrow(cells)),info=f$id)
        expect_equal(got$cases$asDF$sourceID,rownames(d)[unlist(e$retained_indices)+1],info=f$id)
        expect_equal(unlist(got$piePlot$state$data$lower),vapply(e$cells,function(c)as.numeric(c$lower),0),info=f$id)
        expect_equal(unlist(got$piePlot$state$data$upper),vapply(e$cells,function(c)as.numeric(c$upper),0),info=f$id)
    }
})

test_that('native pie optional outputs and required inputs clear and recover', {
    d<-data.frame(Outcome=factor(c('A',NA,'B','A'),levels=c('B','A','Unused')),ID=c('001',NA,'01','1'))
    opts<-pyjjpiestatsOptions$new(dep='Outcome',subject='ID',showCases=TRUE)
    a<-pyjjpiestatsClass$new(options=opts)
    a$.setReadDatasetSource(function(...)d);a$.setReadDatasetHeaderSource(function(...)d)
    set_option<-function(n,v){o<-opts$option(n);o$value<-v}
    a$init();a$run();original<-a$results$frequencies$asDF
    expect_equal(a$results$cases$asDF$subjectID,c('001','01','1'))
    expect_equal(original$count,c(1,2,0))
    set_option('label','both');set_option('digitsperc',2L);a$init();a$run()
    expect_equal(a$results$frequencies$asDF,original)
    expect_equal(unlist(a$results$piePlot$state$data$annotation),c('1\n(33.33%)','2\n(66.67%)',NA_character_))
    set_option('showCases',FALSE);set_option('showPlot',FALSE);a$init();a$run()
    expect_equal(a$results$cases$rowCount,0);expect_null(a$results$piePlot$state)
    set_option('dep',NULL);a$init();a$run()
    for(name in c('cohort','missing','frequencies','cases'))expect_equal(a$results$get(name)$rowCount,0)
    set_option('dep','Outcome');set_option('showPlot',TRUE);a$init();a$run()
    expect_equal(a$results$frequencies$asDF,original)
    d$ID[3]<-'001';a$init();expect_error(a$run(),'unique')
    expect_equal(a$results$cohort$rowCount,0);expect_null(a$results$piePlot$state)
    d$ID[3]<-'01';a$init();a$run()
    file<-tempfile(fileext='.rds');saveRDS(a$results$piePlot$state,file)
    a$results$piePlot$setState(readRDS(file));a$.__enclos_env__$private$.data<-NULL
    output<-'/private/tmp/cpj-pie-native-restored.png'
    a$results$piePlot$saveAs(output);expect_true(file.exists(output));expect_gt(file.info(output)$size,1000)
})
