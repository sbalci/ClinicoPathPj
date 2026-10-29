test_that('univariate summaries and flags agree with base R and performance', {
 set.seed(917)
 d<-data.frame(a=c(rnorm(30),8,NA,3),b=c(rnorm(30),-7,4,NA))
 complete<-apply(d,1,function(x)all(is.finite(x)));x<-d[complete,,drop=FALSE]
 for(method in c('zscore_robust','zscore','iqr')){
  got<-pyoutlierdetection(data=d,vars=c('a','b'),method=method,showRows=TRUE,showPlot=TRUE)
  tab<-got$variables$asDF
  for(j in seq_len(ncol(x))){
   v<-x[[j]]
   if(method=='iqr'){
    q<-quantile(v,c(.25,.75));limits<-c(q[1]-1.7*diff(q),q[2]+1.7*diff(q));flag<-v<limits[1]|v>limits[2]
   }else{
    center<-if(method=='zscore')mean(v) else median(v);spread<-if(method=='zscore')sd(v) else mad(v)
    limits<-center+c(-1,1)*3.29*spread;flag<-abs((v-center)/spread)>3.29
   }
   expect_equal(tab$lower[j],unname(limits[1]),tolerance=1e-12)
   expect_equal(tab$upper[j],unname(limits[2]),tolerance=1e-12)
   expect_equal(tab$flagged[j],sum(flag));expect_equal(tab$n[j],nrow(x))
  }
  if(requireNamespace('performance',quietly=TRUE)){
   threshold<-setNames(list(if(method=='iqr')1.7 else 3.29),method)
   reference<-as.logical(performance::check_outliers(x,method=method,threshold=threshold))
   expect_equal(got$rowPreview$asDF$status[complete]=='Flagged',reference)
  }
  expect_equal(sum(got$rowPreview$asDF$status=='Excluded: missing/nonfinite'),2)
 }
})

test_that('saved flags retain sparse source IDs and clear on incomplete input', {
 d<-data.frame(x=c(0,1,2,3,4,20,NA),row.names=c('2','5','9','12','15','20','30'))
 opts<-pyoutlierdetectionOptions$new(vars='x',method='iqr',showRows=TRUE,showPlot=TRUE)
 saved<-opts$option('screenFlags');saved$value<-list(value=TRUE,vars=list())
 a<-pyoutlierdetectionClass$new(options=opts,data=d);a$init();a$run();jmvcore:::initProtoBuf()
 pb<-a$results$screenFlags$asProtoBuf(incAsText=TRUE)$outputs
 expect_equal(as.integer(pb$rowNums),c(1L,4L,8L,11L,14L,19L,29L))
 expect_equal(as.integer(pb$outputs[[1]]$i[1:6]),c(rep(1L,5),2L))
 expect_equal(a$results$rowPreview$asDF$row,rownames(d))
 raster<-ClinicoPathPj:::.cpjRenderPlot(a$results$countPlot$state,800L,500L,list(palette='jmv'))
 expect_equal(dim(raster)[1:2],c(500L,800L))
 role<-a$options$option('vars');role$value<-NULL;a$init();a$run()
 expect_equal(a$results$variables$rowCount,0);expect_equal(a$results$rowPreview$rowCount,0);expect_null(a$results$countPlot$state)
 clear<-a$results$screenFlags$asProtoBuf(incAsText=TRUE)$outputs$outputs[[1]]$i
 expect_equal(length(clear),7L);expect_true(all(is.na(clear)|clear == -2147483648))
 role$value<-'x';a$init();a$run();expect_equal(a$results$variables$asDF$flagged,1)
})

test_that('zero spread preserves undefined versus infinite Z-score classification', {
 got<-pyoutlierdetection(data=data.frame(x=c(0,0,0,0,10)),vars='x',showRows=TRUE)
 expect_equal(got$variables$asDF$unavailable,4)
 expect_equal(got$rowPreview$asDF$status,c(rep('Undefined',4),'Flagged'))
 got<-pyoutlierdetection(data=data.frame(x=rep(1,5)),vars='x',method='iqr',showRows=TRUE)
 expect_equal(got$variables$asDF$unavailable,0);expect_true(all(got$rowPreview$asDF$status=='Not flagged'))
})


test_that('the native host rejects infinite source values before the Python bridge', {
 expect_error(pyoutlierdetection(data=data.frame(x=c(1,2,Inf)),vars='x'),'infinite values')
})

test_that('flagged measurement details preserve observed values and saved classification', {
 d<-data.frame(x=c(0,1,2,3,4,20,NA),row.names=c('2','5','9','12','15','20','30'))
 opts<-pyoutlierdetectionOptions$new(vars='x',method='iqr',showFlaggedValues=TRUE)
 saved<-opts$option('screenFlags');saved$value<-list(value=TRUE,vars=list())
 a<-pyoutlierdetectionClass$new(options=opts,data=d);a$init();a$run();jmvcore:::initProtoBuf()
 details<-a$results$flaggedValues$asDF
 expect_equal(details$row,'20');expect_equal(details$variable,'x');expect_equal(details$value,20)
 expect_equal(details$lower,-3);expect_equal(details$upper,8);expect_equal(details$basis,'IQR fences')
 before<-a$results$screenFlags$asProtoBuf(incAsText=TRUE)$outputs$outputs[[1]]$i
 control<-a$options$option('showFlaggedValues');control$value<-FALSE;a$init();a$run()
 expect_equal(a$results$flaggedValues$rowCount,0)
 expect_equal(a$results$screenFlags$asProtoBuf(incAsText=TRUE)$outputs$outputs[[1]]$i,before)
 control$value<-TRUE;role<-a$options$option('vars');role$value<-NULL;a$init();a$run()
 expect_equal(a$results$flaggedValues$rowCount,0)
 role$value<-'x';a$init();a$run();expect_equal(a$results$flaggedValues$rowCount,1)
 empty<-pyoutlierdetection(data=data.frame(x=0:4),vars='x',method='iqr',showFlaggedValues=TRUE)
 expect_equal(empty$flaggedValues$rowCount,0)
 zero<-pyoutlierdetection(data=data.frame(x=c(0,0,0,0,10)),vars='x',showFlaggedValues=TRUE)
 expect_equal(zero$flaggedValues$asDF$basis,'Infinite Z (zero spread)')
 expect_equal(zero$flaggedValues$asDF$value,10)
})

test_that('measurement details do not shift existing scientific wrapper arguments', {
 expect_equal(names(formals(pyoutlierdetection))[1:7],c('data','vars','method','zscore_threshold','iqr_multiplier','showRows','showPlot'))
})

test_that('distribution state uses complete cohorts and clears through native lifecycle', {
 d<-data.frame(x=c(0:4,20,NA),y=c(10,20,30,40,50,60,999))
 opts<-pyoutlierdetectionOptions$new(vars=c('x','y'),method='iqr',showDistribution=TRUE)
 a<-pyoutlierdetectionClass$new(options=opts,data=d);a$init();a$run()
 state<-a$results$distributionPlot$state
 expect_equal(nrow(state$data),202L)
 expect_equal(state$data$percentile,rep(0:100,2))
 expect_equal(state$data$value[1:101],unname(quantile(d$x[1:6],seq(0,1,.01))))
 expect_equal(state$data$value[102:202],unname(quantile(d$y[1:6],seq(0,1,.01))))
 expect_equal(unique(state$data$lower[1:101]),-3)
 expect_equal(unique(state$data$upper[1:101]),8)
 raster<-ClinicoPathPj:::.cpjRenderPlot(state,1000L,800L,list(palette='jmv'))
 expect_equal(dim(raster)[1:2],c(800L,1000L))
 control<-a$options$option('showDistribution');control$value<-FALSE;a$init();a$run()
 expect_null(a$results$distributionPlot$state)
 control$value<-TRUE;role<-a$options$option('vars');role$value<-NULL;a$init();a$run()
 expect_null(a$results$distributionPlot$state)
 role$value<-c('x','y');a$init();a$run()
 expect_equal(a$results$distributionPlot$state$data,state$data)
})
