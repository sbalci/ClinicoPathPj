bar_numbers<-function(x)vapply(x,function(v)if(is.null(v))NA_real_ else as.numeric(v),0)
bar_factor<-function(codes,labels) {
    levels<-vapply(labels,function(v)if(is.null(v))NA_character_ else as.character(v),'')
    code<-as.integer(unlist(codes));values<-levels[pmax(1,code+1)];values[code<0]<-NA_character_
    factor(values,levels=levels,exclude=NULL)
}
bar_data<-function(f) {
    a<-f$inputs
    d<-data.frame(Outcome=bar_factor(a$outcome_codes,a$outcome_levels),Group=bar_factor(a$group_codes,a$group_levels))
    if(!is.null(a$weights))d$Frequency<-bar_numbers(a$weights)
    rownames(d)<-as.character(seq_len(nrow(d))*3+7)
    d
}

test_that('native bar tables match independent R fixtures and explicit denominators', {
    refs<-jsonlite::fromJSON(testthat::test_path('..','fixtures','barstats-core.json'),simplifyVector=FALSE)
    for(f in refs$fixtures) {
        if(f$expected$status!='ok')next
        d<-bar_data(f);e<-f$expected
        args<-list(data=d,dep='Outcome',group='Group',resultssubtitle=TRUE,showCases=TRUE)
        if('Frequency'%in%names(d))args$counts<-'Frequency'
        got<-do.call(pyjjbarstats,args)
        expect_equal(got$cohort$asDF$total,as.numeric(e$n_total),info=f$id)
        expect_equal(got$cohort$asDF$complete,as.integer(e$n_complete),info=f$id)
        expect_equal(got$cohort$asDF$contributing,as.integer(e$n_contributing),info=f$id)
        expect_equal(got$cases$asDF$sourceID,rownames(d)[unlist(e$retained_indices)+1],info=f$id)
        expect_equal(got$cells$rowCount,length(e$cells),info=f$id)
        for(key in c('count','expected','group_total','group_proportion','overall_proportion')) {
            target<-vapply(e$cells,function(c)c[[key]],0);observed<-got$cells$asDF[[key]]
            expect_true(all(abs(observed-target)<=ifelse(target==0,1e-12,abs(target)*1e-10)),info=paste(f$id,key))
        }
        a<-e$association
        expect_equal(got$association$asDF$method,if(a$primary_method=='fisher_exact')'Fisher exact (two-sided)' else 'Pearson chi-square',info=f$id)
        expect_true(abs(got$association$asDF$p-a$primary_p)<=max(1e-12,abs(a$primary_p)*1e-10),info=f$id)
        for(key in c('statistic','df','p')) {
            target<-switch(key,statistic=a$pearson_statistic,df=a$df,p=a$pearson_p)
            expect_true(abs(got$pearson$asDF[[key]]-target)<=max(1e-12,abs(target)*1e-10),info=paste(f$id,key))
        }
        expect_true(abs(got$effects$asDF$raw-a$cramers_v_raw)<=1e-10,info=f$id)
        if(is.null(a$cramers_v_corrected))expect_true(is.na(got$effects$asDF$corrected),info=f$id)
        else expect_true(abs(got$effects$asDF$corrected-a$cramers_v_corrected)<=1e-10,info=f$id)
        expect_false(any(c('lower','upper','confidence')%in%names(got$effects$asDF)))
        expect_false(is.null(got$barPlot$state),info=f$id)
    }
})

test_that('native bar state clears and recovers with factor, scale and output changes', {
    d<-data.frame(Outcome=factor(c('No','Yes','No','Yes',NA,'No'),levels=c('Yes','No','Unused')),
        Group=factor(c('A','A','B','B','A',NA),levels=c('B','A')),ID=c('001','01','1','B',NA,NA))
    rownames(d)<-as.character(seq_len(nrow(d))*5+2)
    opts<-pyjjbarstatsOptions$new(dep='Outcome',group='Group',subject='ID',resultssubtitle=TRUE,showCases=TRUE)
    a<-pyjjbarstatsClass$new(options=opts)
    a$.setReadDatasetSource(function(...)d);a$.setReadDatasetHeaderSource(function(...)d)
    set_option<-function(n,v){o<-opts$option(n);o$value<-v}
    a$init();a$run();original<-a$results$cells$asDF
    expect_equal(a$results$cases$asDF$subjectID,c('001','01','1','B'))
    expect_equal(a$results$dropped$asDF$label,'Unused')
    set_option('barScale','count');a$init();a$run()
    expect_equal(a$results$cells$asDF,original)
    expect_equal(unique(unlist(a$results$barPlot$state$data$scale)),'count')
    set_option('resultssubtitle',FALSE);set_option('showCells',FALSE);set_option('showCases',FALSE);set_option('showPlot',FALSE)
    a$init();a$run()
    for(key in c('association','pearson','effects','cells','cases'))expect_equal(a$results$get(key)$rowCount,0)
    expect_null(a$results$barPlot$state)
    set_option('group',NULL);a$init();a$run()
    for(key in c('cohort','missing','groups','dropped'))expect_equal(a$results$get(key)$rowCount,0)
    set_option('group','Group');set_option('showCells',TRUE);set_option('showPlot',TRUE)
    a$init();a$run();expect_equal(a$results$cells$asDF,original)
    d$ID[2]<-'001';a$init();expect_error(a$run(),'unique')
    expect_equal(a$results$cohort$rowCount,0);expect_null(a$results$barPlot$state)
    d$ID[2]<-'01';a$init();a$run()
    state<-a$results$barPlot$state;file<-tempfile(fileext='.rds');saveRDS(state,file)
    a$results$barPlot$setState(readRDS(file));a$.__enclos_env__$private$.data<-NULL
    output<-file.path('/private/tmp','cpj-barstats-native-count.png')
    a$results$barPlot$saveAs(output);expect_true(file.exists(output));expect_gt(file.info(output)$size,1000)
})

test_that('native synthetic weighted bars distinguish percentages and group totals', {
    d<-read.csv(testthat::test_path('..','..','data','python_barstats_examples.csv'),na.strings=c('','NA'))
    for(scale in c('percentage','count')) {
        got<-pyjjbarstats(data=d,dep='Outcome',group='Group',counts='Frequency',barScale=scale,resultssubtitle=TRUE,label='both')
        expect_equal(got$cohort$asDF$total,50);expect_equal(got$cohort$asDF$zero,1L)
        expect_equal(got$cohort$asDF$excluded,2L);expect_equal(got$groups$asDF$total,c(20,30))
        got$barPlot$saveAs(paste0('/private/tmp/cpj-barstats-example-',scale,'.png'))
    }
    expect_error(pyjjbarstats(data=d,dep='Outcome',group='Outcome'),'distinct')
})
