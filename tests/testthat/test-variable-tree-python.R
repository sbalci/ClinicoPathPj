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

test_that('node means and sample SD agree with independent base R masks', {
 set.seed(818)
 d<-data.frame(a=factor(rep(c('X','Y'),each=15)),b=factor(rep(c('P','Q','R'),10)),score=rnorm(30))
 d$score[c(2,5,8,17,29)]<-NA;d$a[30]<-NA
 for(location in c('leafonly','allnodes')){
  got<-pyvartree(data=d,vars=c('a','b'),showPaths=TRUE,showNodeSummary=TRUE,summaryvar='score',summarylocation=location)
  nodes<-got$nodes$asDF;stats<-got$nodeSummary$asDF;cohort<-d[complete.cases(d[,c('a','b')]),]
  target<-if(location=='leafonly')nodes$node[nodes$leaf=='Yes'] else nodes$node
  expect_equal(stats$node,target)
  for(i in seq_len(nrow(stats))){
   node<-nodes[nodes$node==stats$node[i],];path<-jsonlite::fromJSON(node$path,simplifyVector=FALSE)
   mask<-rep(TRUE,nrow(cohort))
   for(pair in path)mask<-mask & as.character(cohort[[pair[[1]]]])==pair[[2]]
   x<-cohort$score[mask];valid<-x[!is.na(x)]
   expect_equal(stats$nodeN[i],length(x));expect_equal(stats$valid[i],length(valid))
   expect_equal(stats$missing[i],sum(is.na(x)))
   expect_equal(stats$mean[i],mean(valid),tolerance=1e-12)
   expect_equal(stats$sd[i],sd(valid),tolerance=1e-12)
  }
 }
})

test_that('node-local numeric missingness leaves categorical results unchanged', {
 d<-read.csv(file.path(Sys.getenv('CPJ_ROOT'),'data','python_tree_node_summary_examples.csv'),stringsAsFactors=TRUE,na.strings=c('','NA'))
 base<-pyvartree(data=d,vars=c('Tumor','Grade'),showPlot=TRUE)
 opts<-pyvartreeOptions$new(vars=c('Tumor','Grade'),showNodeSummary=TRUE,summaryvar='MarkerScore',summarylocation='allnodes',showPlot=TRUE)
 a<-pyvartreeClass$new(options=opts,data=d);a$init();a$run()
 tab<-a$results$nodeSummary$asDF
 expect_equal(a$results$nodes$asDF,base$nodes$asDF)
 expect_equal(a$results$leafPlot$state,base$leafPlot$state)
 expect_equal(tab$nodeN[1],7);expect_equal(tab$valid[1],4);expect_equal(tab$missing[1],3)
 expect_equal(tab$mean[1],18.5);expect_equal(tab$sd[1],sqrt(227/3),tolerance=1e-12)
 expect_true(any(tab$valid==0 & is.na(tab$mean) & is.na(tab$sd)))
 role<-a$options$option('summaryvar');role$value<-NULL;a$init();a$run()
 expect_equal(a$results$nodeSummary$rowCount,0);expect_equal(a$results$nodes$asDF,base$nodes$asDF)
 expect_false(grepl('valid n=',a$results$explorer$content,fixed=TRUE))
 role$value<-'MarkerScore';a$init();a$run();expect_equal(a$results$nodeSummary$asDF,tab)
 display<-a$options$option('showNodeSummary');display$value<-FALSE;a$init();a$run()
 expect_equal(a$results$nodeSummary$rowCount,0);expect_equal(a$results$nodes$asDF,base$nodes$asDF)
 expect_false(grepl('valid n=',a$results$explorer$content,fixed=TRUE))
 expect_equal(names(formals(pyvartree))[1:5],c('data','vars','showTree','showPlot','showPaths'))
})

test_that('reference percentages agree with node-local valid-value denominators', {
 d<-read.csv(file.path(Sys.getenv('CPJ_ROOT'),'data','python_tree_reference_examples.csv'),stringsAsFactors=TRUE,na.strings=c('','NA'))
 got<-pyvartree(data=d,vars=c('Tumor','Grade'),showPaths=TRUE,pct=TRUE,percvar='MarkerStatus',percvarLevel='Positive',showNodeSummary=TRUE,summaryvar='MarkerScore',summarylocation='allnodes')
 nodes<-got$nodes$asDF;ref<-got$referenceSummary$asDF
 cohort<-d[complete.cases(d[,c('Tumor','Grade')]),]
 for(i in seq_len(nrow(ref))){
  node<-nodes[nodes$node==ref$node[i],];path<-jsonlite::fromJSON(node$path,simplifyVector=FALSE)
  keep<-rep(TRUE,nrow(cohort))
  for(pair in path)keep<-keep & as.character(cohort[[pair[[1]]]])==pair[[2]]
  values<-as.character(cohort$MarkerStatus[keep]);valid<-sum(!is.na(values));matches<-sum(values=='Positive',na.rm=TRUE)
  expect_equal(ref$nodeN[i],length(values));expect_equal(ref$valid[i],valid)
  expect_equal(ref$missing[i],sum(is.na(values)));expect_equal(ref$matches[i],matches)
  if(valid)expect_equal(ref$percent[i],matches/valid) else expect_true(is.na(ref$percent[i]))
 }
 expect_equal(ref$percent[1],.5);expect_equal(ref$nodeN[1],7)
 expect_equal(got$nodeSummary$asDF$mean[1],18.5)
 expect_match(got$explorer$content,'MarkerStatus=Positive',fixed=TRUE)
 expect_match(got$explorer$content,'MarkerScore:',fixed=TRUE)
 # Public vtree 5.7 output uses valid-reference n: group A is 2/3, not 2/4.
 if(requireNamespace('vtree',quietly=TRUE)){
  fixture<-data.frame(G=c(rep('A',4),rep('B',2)),R=c('Y','Y','N',NA,'N',NA))
  widget<-vtree::vtree(fixture,'G',summary='R=Y Reference: %npct%')
  expect_match(widget$x$diagram,'Reference: 2 (50%) mv=2',fixed=TRUE)
  expect_match(widget$x$diagram,'Reference: 2 (67%) mv=1',fixed=TRUE)
  python<-pyvartree(data=fixture,vars='G',pct=TRUE,percvar='R',percvarLevel='Y')
  expect_equal(python$referenceSummary$asDF$percent,c(.5,2/3,0))
 }
})

test_that('optional reference roles retain old calls and clear without changing cohorts', {
 d<-data.frame(a=factor(c('A','A','B')),ref=factor(c('Y',NA,'N')))
 opts<-pyvartreeOptions$new(vars='a',pct=TRUE,percvar='ref',percvarLevel='Y')
 a<-pyvartreeClass$new(options=opts,data=d);a$init();a$run()
 before<-a$results$nodes$asDF;tab<-a$results$referenceSummary$asDF
 level<-a$options$option('percvarLevel');level$value<-NULL;a$init();a$run()
 expect_equal(a$results$referenceSummary$rowCount,0);expect_equal(a$results$nodes$asDF,before)
 expect_false(grepl('ref=Y:',a$results$explorer$content,fixed=TRUE))
 level$value<-'Y';a$init();a$run();expect_equal(a$results$referenceSummary$asDF,tab)
 toggle<-a$options$option('pct');toggle$value<-FALSE;a$init();a$run()
 expect_equal(a$results$referenceSummary$rowCount,0);expect_equal(a$results$nodes$asDF,before)
 old<-pyvartree(data=d,vars='a')
 expect_equal(old$nodes$asDF,before)
 expect_null(formals(pyvartree)$percvarLevel)
 expect_equal(names(formals(pyvartree))[1:8],c('data','vars','showTree','showPlot','showPaths','showNodeSummary','summaryvar','summarylocation'))
 shared<-pyvartree(data=d,vars='a',pct=TRUE,percvar='a',percvarLevel='A')
 expect_equal(shared$referenceSummary$asDF$percent,c(2/3,1,0))
})

test_that('literal NA reference labels remain distinct from missing factor levels', {
 d<-data.frame(a=factor(c('A','A','B','B')),ref=factor(c('NA',NA,'Y','Y'),exclude=NULL))
 got<-pyvartree(data=d,vars='a',pct=TRUE,percvar='ref',percvarLevel='NA')
 root<-got$referenceSummary$asDF[1,]
 expect_equal(root$nodeN,4);expect_equal(root$valid,3);expect_equal(root$missing,1)
 expect_equal(root$matches,1);expect_equal(root$percent,1/3)
})
