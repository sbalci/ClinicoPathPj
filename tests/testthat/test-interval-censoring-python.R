test_that('interval2 types agree with survival across finite, infinite and missing bounds', {
    skip_if_not_installed('survival')
    grid <- expand.grid(left=c(-Inf,-3,0,1,4,Inf,NA_real_),right=c(-Inf,-3,0,1,4,Inf,NA_real_))
    ref <- suppressWarnings(unclass(survival::Surv(grid$left,grid$right,type='interval2')))[,'status']
    got <- pyintervalcensoring(data=grid,left='left',right='right',preview_rows=100)
    expect_equal(got$preview$asDF$code,as.numeric(ref))
    expect_equal(got$cohort$asDF$retained,sum(!is.na(ref)))
    expect_equal(got$cohort$asDF$input,nrow(grid))
    expect_equal(got$counts$asDF$n,as.numeric(table(factor(ref,levels=0:3))))
    expect_equal(sum(got$counts$asDF$percent),1)
    roundtrip <- suppressWarnings(unclass(survival::Surv(got$preview$asDF$left,got$preview$asDF$right,type='interval2')))[,'status']
    expect_equal(as.numeric(roundtrip),as.numeric(ref))
})

test_that('manual interval truth table and original row-aligned output match', {
    d <- data.frame(a=c(1,NA,1,5,NA),b=c(1,3,NA,2,NA),row.names=c('2','8','20','40','51'))
    opts <- pyintervalcensoringOptions$new(left='a',right='b',showReport=TRUE,showPlot=TRUE)
    for(name in c('leftOut','rightOut','kindOut')) {opt<-opts$option(name);opt$value<-list(value=TRUE,vars=list())}
    a <- pyintervalcensoringClass$new(options=opts,data=d);a$init();a$run();jmvcore:::initProtoBuf()
    output <- function(name) a$results$get(name)$asProtoBuf(incAsText=TRUE)$outputs
    expect_equal(as.integer(output('leftOut')$rowNums),c(1,7,19,39,50))
    expect_equal(as.numeric(output('leftOut')$outputs[[1]]$d),c(1,NA,1,NA,NA))
    expect_equal(as.numeric(output('rightOut')$outputs[[1]]$d),c(1,3,NA,NA,NA))
    kinds <- as.integer(output('kindOut')$outputs[[1]]$i)
    expect_equal(kinds[1:3],c(2,3,1));expect_true(all(is.na(kinds[4:5])|kinds[4:5] == -2147483648))
    expect_equal(a$results$preview$asDF$source,rownames(d))
    expect_equal(a$results$cohort$asDF$retained,3)
    expect_equal(a$results$cohort$asDF$invalid,1)
    expect_equal(a$results$cohort$asDF$unknown,1)
    expect_equal(a$results$distribution$state$data$value,c(1,1,1,0))
    expect_match(a$results$summary$content,'NO third event')
})

test_that('same-column reuse, unavailable percentages and incomplete lifecycle are explicit', {
    d <- data.frame(a=c(1,NA,1),b=c(1,3,NA))
    opts <- pyintervalcensoringOptions$new(left='a',right='b')
    for(name in c('leftOut','rightOut','kindOut')) {opt<-opts$option(name);opt$value<-list(value=TRUE,vars=list())}
    a <- pyintervalcensoringClass$new(options=opts,data=d);a$init();a$run();jmvcore:::initProtoBuf()
    right <- opts$option('right');right$value <- NULL;a$init();a$run()
    expect_equal(a$results$cohort$rowCount,0);expect_equal(a$results$preview$rowCount,0)
    saved <- a$results$leftOut$asProtoBuf(incAsText=TRUE)$outputs$outputs[[1]]$d
    expect_true(all(is.na(saved)))
    right$value <- 'a';a$init();a$run()
    expect_equal(a$results$preview$asDF$code,c(1,NA,1))
    right$value <- 'b';a$init();a$run()
    expect_equal(a$results$preview$asDF$code,c(1,2,0))
    got <- pyintervalcensoring(data=data.frame(a=c(NA_real_,NA_real_),b=c(NA_real_,NA_real_)),left='a',right='b')
    expect_true(all(is.na(got$counts$asDF$percent)))
    expect_equal(got$cohort$asDF$retained,0)
})

test_that('infinity encoding is opt-in and strict JSON preserves signed bounds', {
    encode <- ClinicoPathPj:::.cpjColumn
    expect_error(encode(c(1,Inf),'ordinary'),'infinite values')
    encoded <- encode(c(-Inf,Inf,NA_real_,1),'bounds',allowInfinite=TRUE)
    wire <- jsonlite::toJSON(encoded,auto_unbox=TRUE,na='null',null='null')
    expect_match(wire,'-Infinity',fixed=TRUE)
    expect_match(wire,'Infinity',fixed=TRUE)
    expect_equal(jsonlite::fromJSON(wire)$values,c('-Infinity','Infinity',NA,'1'))
    # An ordinary analysis retains its existing rejection policy.
    expect_error(pydescriptives(data=data.frame(x=c(1,Inf)),vars='x'),'infinite values')
})
