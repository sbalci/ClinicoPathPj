test_that('IHC transforms and missingness agree with independent base R fixtures', {
  set.seed(414)
  for (fixture in seq_len(6)) {
    d<-data.frame(a=rnorm(8),b=rnorm(8,20,4),constant=rep(2,8),g=factor(rep(c('A','B'),4)))
    d$a[c(2,8)]<-NA;d$b[c(3,8)]<-NA
    rownames(d)<-as.character(seq(5,40,5))
    for (mode in c('raw','zscore')) for (missing in c('available','complete')) {
      got<-pyihcheatmap(data=d,markers=c('a','b','constant'),group='g',scaling=mode,missing=missing)
      x<-as.matrix(d[c('a','b','constant')]);keep<-if(missing=='complete')complete.cases(x) else rowSums(!is.na(x))>0
      x<-x[keep,,drop=FALSE]
      expect_equal(got$rowOrder$asDF$sourceRow,rownames(d)[keep])
      expect_equal(got$markerSummary$asDF$mean,unname(colMeans(x,na.rm=TRUE)))
      expect_equal(got$markerSummary$asDF$sd,unname(apply(x,2,sd,na.rm=TRUE)))
      if(mode=='zscore'){
        x<-sweep(x,2,colMeans(x,na.rm=TRUE),'-')
        scales<-apply(x,2,sd,na.rm=TRUE)
        x[,scales==0]<-0;x[,scales!=0]<-sweep(x[,scales!=0,drop=FALSE],2,scales[scales!=0],'/')
      }
      expect_equal(got$heatmap$state$data$value,as.vector(t(x)),tolerance=1e-12)
    }
  }
})

test_that('IHC original identities and native lifecycle remain aligned', {
 d<-data.frame(a=c(1,2,3),b=c(2,NA,4),id=c('same','same','other'),g=factor(c('NA',NA,'B'),exclude=NULL),row.names=c('2','7','11'))
 a<-pyihcheatmapClass$new(options=pyihcheatmapOptions$new(markers=c('a','b'),subject='id',group='g'),data=d)
 a$init();a$run()
 expect_equal(a$results$rowOrder$asDF$sourceRow,c('2','7','11'))
 expect_equal(a$results$rowOrder$asDF$subject,c('same','same','other'))
 expect_equal(a$results$rowOrder$asDF$group,c('NA',NA,'B'))
 selected<-a$options$option('markers');selected$value<-character()
 a$.__enclos_env__$private$.run()
 expect_equal(a$results$rowOrder$rowCount,0)
 expect_null(a$results$heatmap$state)
 expect_equal(a$results$explorer$content,'<div></div>')
 selected$value<-c('a','b');a$.__enclos_env__$private$.run()
 expect_equal(a$results$rowOrder$rowCount,3)
 raster<-ClinicoPathPj:::.cpjRenderPlot(a$results$heatmap$state,900L,650L,list(palette='jmv'))
 expect_equal(dim(raster)[1:2],c(650L,900L))
})
