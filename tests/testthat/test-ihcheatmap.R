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

test_that('linked scatter preserves source rows, display values and native lifecycle', {
 d<-data.frame(a=c(1,2,3,NA),b=c(2,NA,6,4),id=c('same','same','other','other'),row.names=c('2','7','11','20'))
 options<-pyihcheatmapOptions$new(markers=c('a','b'),subject='id',scaling='zscore',
                                  showScatter=TRUE,scatterX='b',scatterY='a')
 a<-pyihcheatmapClass$new(options=options,data=d);a$init();a$run()
 expect_equal(a$results$scatterRows$asDF$sourceRow,c('2','11'))
 expect_equal(a$results$scatterRows$asDF$x,as.numeric(scale(d$b))[c(1,3)])
 expect_equal(a$results$scatterRows$asDF$y,as.numeric(scale(d$a))[c(1,3)])
 expect_equal(a$results$scatterCohort$asDF$omitted,2)
 expect_equal(a$results$scatter$state$data$x,a$results$scatterRows$asDF$x)
 restored<-unserialize(serialize(a$results$scatter$state,NULL))
 raster<-ClinicoPathPj:::.cpjRenderPlot(restored,650L,450L,list(palette='jmv'))
 expect_equal(dim(raster)[1:2],c(450L,650L))
 enabled<-options$option('showScatter');enabled$value<-FALSE
 a$.__enclos_env__$private$.run()
 expect_null(a$results$scatter$state)
 expect_equal(a$results$scatterRows$rowCount,0)
 enabled$value<-TRUE
 selected<-options$option('markers');selected$value<-character()
 a$.__enclos_env__$private$.run()
 expect_null(a$results$scatter$state)
 expect_equal(a$results$scatterCohort$rowCount,0)
 selected$value<-c('a','b');a$.__enclos_env__$private$.run()
 fresh<-pyihcheatmap(data=d,markers=c('a','b'),subject='id',scaling='zscore',showScatter=TRUE,
                     scatterX='b',scatterY='a')
 expect_equal(a$results$scatter$state,fresh$scatter$state)
 expect_equal(a$results$scatterRows$asDF,fresh$scatterRows$asDF)
})
