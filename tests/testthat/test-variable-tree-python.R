test_that('tree prefixes agree with independently filtered base R counts', {
 d<-data.frame(a=factor(c('X','X','X','Y','Y',NA),levels=c('Y','X','unused')),
               b=factor(c('P','P','Q','P',NA,'Q'),levels=c('Q','P')),
               c=factor(c('NA','real','NA','real','NA','real')))
 for(vars in list('a',c('a','b'),c('a','b','c'))){
  got<-do.call(pyvartree,list(data=d,vars=vars,showPlot=TRUE,showPaths=TRUE))
  tab<-got$nodes$asDF;cohort<-d[complete.cases(d[,vars,drop=FALSE]),,drop=FALSE]
  for(i in seq_len(nrow(tab))){
   path<-jsonlite::fromJSON(tab$path[i],simplifyVector=FALSE)
   mask<-rep(TRUE,nrow(cohort))
   for(pair in path)mask<-mask & as.character(cohort[[pair[[1]]]])==pair[[2]]
   expect_equal(tab$n[i],sum(mask))
   expect_equal(tab$cohortPercent[i],sum(mask)/nrow(cohort))
   if(!is.na(tab$parent[i])){
    parent<-tab[tab$node==tab$parent[i],,drop=FALSE]
    expect_equal(tab$parentPercent[i],tab$n[i]/parent$n)
   }
   children<-tab[!is.na(tab$parent)&tab$parent==tab$node[i],,drop=FALSE]
   if(nrow(children))expect_equal(sum(children$n),tab$n[i])
  }
  expect_equal(sum(tab$n[tab$leaf=='Yes']),nrow(cohort))
  expect_match(got$explorer$content,'<details open>',fixed=TRUE)
 }
})

test_that('native tree lifecycle clears and restores all optional results', {
 d<-data.frame(a=factor(c('X','X','Y',NA)),b=factor(c('P','Q','P','P')))
 opts<-pyvartreeOptions$new(vars=c('a','b'),showPlot=TRUE)
 a<-pyvartreeClass$new(options=opts,data=d);a$init();a$run()
 before<-a$results$nodes$asDF
 raster<-ClinicoPathPj:::.cpjRenderPlot(a$results$leafPlot$state,1000L,650L,list(palette='jmv'))
 expect_equal(dim(raster)[1:2],c(650L,1000L))
 role<-a$options$option('vars');role$value<-NULL;a$init();a$run()
 expect_equal(a$results$nodes$rowCount,0);expect_null(a$results$leafPlot$state)
 expect_false(grepl('<details',a$results$explorer$content,fixed=TRUE))
 role$value<-c('a','b');a$init();a$run();expect_equal(a$results$nodes$asDF,before)
 control<-a$options$option('showTree');control$value<-FALSE
 plot<-a$options$option('showPlot');plot$value<-FALSE;a$init();a$run()
 expect_false(grepl('<details',a$results$explorer$content,fixed=TRUE))
 expect_null(a$results$leafPlot$state);expect_equal(a$results$nodes$asDF,before)
})

test_that('the shipped CSV retains its intended cohort under blank/NA token parsing', {
 path<-file.path(Sys.getenv('CPJ_ROOT'),'data','python_variable_tree_examples.csv')
 d<-read.csv(path,stringsAsFactors=TRUE,na.strings=c("", "NA"))
 expect_equal(nrow(d),38);expect_equal(sum(complete.cases(d)),36)
 expect_setequal(levels(d$Tumor),c('Type A','Type B','Type C'))
 got<-pyvartree(data=d,vars=c('Tumor','Grade','Stage'))
 expect_equal(got$nodes$asDF$n[1],36)
 expect_equal(sort(got$nodes$asDF$n[got$nodes$asDF$leaf=='Yes']),sort(c(12,6,4,5,7,2)))
})

test_that('compact paths remain stored and visible toggles preserve results', {
 d<-data.frame(a=factor(c('X / Y','X / Y','Z',NA)),b=factor(c('P','Q','P','P')))
 opts<-pyvartreeOptions$new(vars=c('a','b'),showPlot=TRUE)
 a<-pyvartreeClass$new(options=opts,data=d);a$init();a$run()
 compact<-a$results$nodes$asDF;plot_before<-a$results$leafPlot$state
 expect_false('path' %in% names(compact))
 stored<-lapply(a$results$nodes$columns,function(x)unlist(as.list(x),use.names=FALSE))
 expect_true('path' %in% names(stored));expect_equal(length(stored$path),nrow(compact))
 expect_equal(stored$path[3],'[["a", "X / Y"], ["b", "P"]]')
 control<-a$options$option('showPaths');control$value<-TRUE;a$init();a$run()
 expanded<-a$results$nodes$asDF
 expect_equal(expanded$path,stored$path)
 expect_equal(expanded[,names(compact)],compact)
 expect_equal(a$results$leafPlot$state,plot_before)
 fresh<-pyvartree(data=d,vars=c('a','b'),showPlot=TRUE,showPaths=TRUE)
 expect_equal(expanded,fresh$nodes$asDF)
 control$value<-FALSE;a$init();a$run();expect_equal(a$results$nodes$asDF,compact)
 role<-a$options$option('vars');role$value<-NULL;a$init();a$run()
 expect_equal(a$results$nodes$rowCount,0)
 role$value<-c('a','b');a$init();a$run();expect_equal(a$results$nodes$asDF,compact)
 expect_equal(names(formals(pyvartree))[1:4],c('data','vars','showTree','showPlot'))
})
