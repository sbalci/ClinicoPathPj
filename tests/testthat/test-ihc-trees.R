test_that('native IHC tree heights agree with independent base R hierarchy fixtures', {
  root<-Sys.getenv('CPJ_ROOT',unset='../..')
  cases<-jsonlite::fromJSON(file.path(root,'tests/fixtures/ihc-tree-oracles.json'),simplifyVector=FALSE)
  for (case in cases) {
    d<-as.data.frame(lapply(case$columns,function(values)
      vapply(values,function(v)if(is.null(v))NA_real_ else as.numeric(v),numeric(1))))
    rownames(d)<-unlist(case$row_ids)
    a<-pyihcheatmap(data=d,markers=names(d),scaling=case$scaling,missing='complete',
                    clusterRows=TRUE,clusterColumns=TRUE,showDendrograms=TRUE)
    merges<-a$merges$asDF
    expect_equal(merges$height[merges$axis=='Source rows'],unlist(case$row_heights),tolerance=1e-12)
    expect_equal(merges$height[merges$axis=='Markers'],unlist(case$marker_heights),tolerance=1e-12)
    expect_equal(max(merges$count[merges$axis=='Source rows']),sum(complete.cases(d)))
    expect_equal(max(merges$count[merges$axis=='Markers']),ncol(d))
    expect_true(all(a$rowDendrogram$state$data$height>=0))
    expect_equal(nrow(a$rowDendrogram$state$data),sum(complete.cases(d))-1L)
  }
})

test_that('tree visibility and state follow both display and clustering options', {
  d<-data.frame(a=c(0,10,1,11),b=c(0,20,2,22),row.names=c('2','4','7','9'))
  options<-pyihcheatmapOptions$new(markers=c('a','b'),clusterRows=TRUE,clusterColumns=TRUE)
  a<-pyihcheatmapClass$new(options=options,data=d);a$init();a$run()
  expect_false(a$results$rowDendrogram$visible)
  expect_null(a$results$rowDendrogram$state)
  display<-options$option('showDendrograms');display$value<-TRUE
  a$.__enclos_env__$private$.run()
  # Native visibility is evaluated during initialization; private reruns only test state.
  enabled<-pyihcheatmap(data=d,markers=c('a','b'),clusterRows=TRUE,clusterColumns=TRUE,showDendrograms=TRUE)
  expect_true(enabled$rowDendrogram$visible)
  expect_true(enabled$markerDendrogram$visible)
  expect_equal(a$results$merges$rowCount,4L)
  state<-unserialize(serialize(a$results$rowDendrogram$state,NULL))
  raster<-ClinicoPathPj:::.cpjRenderPlot(state,900L,450L,list(palette='jmv'))
  expect_equal(dim(raster)[1:2],c(450L,900L))
  clustering<-options$option('clusterRows');clustering$value<-FALSE
  a$.__enclos_env__$private$.run()
  row_disabled<-pyihcheatmap(data=d,markers=c('a','b'),clusterRows=FALSE,clusterColumns=TRUE,showDendrograms=TRUE)
  expect_false(row_disabled$rowDendrogram$visible)
  expect_true(row_disabled$markerDendrogram$visible)
  expect_null(a$results$rowDendrogram$state)
  expect_equal(a$results$merges$rowCount,1L)
  selected<-options$option('markers');selected$value<-character()
  a$.__enclos_env__$private$.run()
  expect_null(a$results$markerDendrogram$state)
  expect_equal(a$results$merges$rowCount,0L)
  selected$value<-c('a','b');clustering$value<-TRUE
  a$.__enclos_env__$private$.run()
  fresh<-pyihcheatmap(data=d,markers=c('a','b'),clusterRows=TRUE,clusterColumns=TRUE,showDendrograms=TRUE)
  expect_equal(a$results$rowDendrogram$state,fresh$rowDendrogram$state)
  expect_equal(a$results$merges$asDF,fresh$merges$asDF)
  display$value<-FALSE;a$.__enclos_env__$private$.run()
  expect_null(a$results$rowDendrogram$state)
  expect_false(pyihcheatmap(data=d,markers=c('a','b'),clusterRows=TRUE)$rowDendrogram$visible)
})
