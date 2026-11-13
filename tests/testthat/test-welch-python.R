# Independent R point references, native lifecycle and model visibility.
welch_native_args <- function(f) {
    nums <- function(x) vapply(x, function(v) if(is.null(v)) NA_real_ else as.numeric(v), numeric(1))
    codes <- as.integer(unlist(f$codes)); labels <- unlist(f$levels)
    d <- data.frame(Outcome=nums(f$values), Group=factor(
        ifelse(codes<0, NA_character_, labels[pmax(1,codes+1)]), levels=labels))
    rownames(d) <- as.character(seq_len(nrow(d))*3+7)
    list(data=d,dep='Outcome',group='Group',firstLevel=f$first,secondLevel=f$second,
         varequal=FALSE,showStandardized=TRUE,showCases=TRUE)
}

test_that('native Welch point-only tables agree with 22 independent R datasets', {
    refs <- jsonlite::fromJSON(testthat::test_path('..','fixtures','welch-standardized-effects.json'),simplifyVector=FALSE)
    for(f in refs$fixtures) {
        args <- welch_native_args(f); got <- do.call(pyjjbetweenstats,args)
        ref <- Filter(function(r)r$confidence==.95,f$runs)[[1]]
        effect <- got$welchEffect$asDF; model <- got$welchStandardizer$asDF
        for(key in c('d_rms','standardizer_sd','welch_df','sd_moment_df')) {
            observed <- switch(key,d_rms=effect$estimate,standardizer_sd=model$sd,
                               welch_df=model$welch_df,sd_moment_df=model$sd_moment_df)
            target <- ref[[key]]
            if(is.null(target))expect_true(is.na(observed),info=paste(f$id,key))
            else expect_true(abs(observed-target)<=if(target==0)0 else abs(target)*1e-10,
                             info=paste(f$id,key))
        }
        expect_equal(effect$first,f$first); expect_equal(effect$second,f$second)
        expect_equal(effect$status,if(ref$status=='degenerate')'degenerate' else 'point_only')
        expect_false(any(c('lower','upper','confidence','correction')%in%names(effect)))
        for(n in c('standardizer','standardized','hedges'))expect_equal(got$get(n)$rowCount,0)
        expect_null(got$standardizedPlot$state)
        off_args<-args;off_args$showStandardized<-FALSE; off<-do.call(pyjjbetweenstats,off_args)
        for(n in c('cohort','missing','descriptives','contrast','cases'))
            expect_equal(got$get(n)$asDF,off$get(n)$asDF,info=f$id)
        expect_equal(off$welchEffect$rowCount,0);expect_equal(off$welchStandardizer$rowCount,0)
    }
})

test_that('native Student Welch off invalid and recovery transitions do not leak results', {
    refs <- jsonlite::fromJSON(testthat::test_path('..','fixtures','welch-standardized-effects.json'),simplifyVector=FALSE)
    f <- refs$fixtures[[1]]; args<-welch_native_args(f);d<-args$data;args$data<-NULL
    opts<-do.call(pyjjbetweenstatsOptions$new,args)
    a<-pyjjbetweenstatsClass$new(options=opts)
    a$.setReadDatasetSource(function(...)d);a$.setReadDatasetHeaderSource(function(...)d)
    set_option<-function(n,v){o<-opts$option(n);o$value<-v}
    a$init();a$run(); welch<-a$results$welchEffect$asDF; model<-a$results$welchStandardizer$asDF
    set_option('varequal',TRUE);a$init();a$run()
    expect_equal(a$results$welchEffect$rowCount,0);expect_equal(a$results$welchStandardizer$rowCount,0)
    expect_equal(a$results$standardized$rowCount,1);expect_equal(a$results$hedges$rowCount,1)
    expect_false(is.null(a$results$standardizedPlot$state))
    set_option('varequal',FALSE);a$init();a$run()
    expect_equal(a$results$welchEffect$asDF,welch);expect_equal(a$results$welchStandardizer$asDF,model)
    expect_equal(a$results$standardized$rowCount,0);expect_equal(a$results$hedges$rowCount,0)
    expect_null(a$results$standardizedPlot$state)
    set_option('conflevel',.8);a$init();a$run()
    expect_equal(a$results$welchEffect$asDF,welch);expect_equal(a$results$welchStandardizer$asDF,model)
    set_option('showStandardized',FALSE);a$init();a$run()
    expect_equal(a$results$welchEffect$rowCount,0);expect_equal(a$results$welchStandardizer$rowCount,0)
    set_option('showStandardized',TRUE);set_option('secondLevel',NULL);a$init();a$run()
    for(n in c('welchEffect','welchStandardizer','standardized','hedges','contrast'))
        expect_equal(a$results$get(n)$rowCount,0)
    set_option('secondLevel',f$second);a$init();a$run()
    expect_equal(a$results$welchEffect$asDF,welch)
    fresh<-do.call(pyjjbetweenstats,c(list(data=d),args,list(conflevel=.8)))
    expect_equal(a$results$welchEffect$asDF,fresh$welchEffect$asDF)
    expect_equal(a$results$welchStandardizer$asDF,fresh$welchStandardizer$asDF)
    expect_true(a$results$welchEffect$visible);expect_false(a$results$standardized$visible)
    set_option('varequal',TRUE);a$init();a$run()
    # jmvcore caches visibility once per ResultsElement. The engine constructs
    # a fresh results tree for changed options; reusing a manually edited R6
    # instance tests table clearing above, not that fresh-tree visibility lifecycle.
    student_args<-args;student_args$varequal<-TRUE;student_args$conflevel<-.8
    student<-do.call(pyjjbetweenstats,c(list(data=d),student_args))
    expect_false(student$welchEffect$visible);expect_true(student$standardized$visible)
    expect_true(fresh$welchEffect$visible);expect_false(fresh$standardized$visible)
})
