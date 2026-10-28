sets_run<-function(d,extra=list()){
 args<-list(data=d,var1='a',var2='b',var1true='Y',var2true='Y',var3true=NULL,var4true=NULL,showZero=TRUE)
 for(name in names(extra))args[name]<-extra[name]
 do.call(pyvenn,args)
}

test_that('exact set patterns agree with independent base-R predicates', {
 for(k in 2:4){
  grid<-expand.grid(rep(list(c('N','Y')),k),stringsAsFactors=FALSE);names(grid)<-letters[seq_len(k)]
  d<-rbind(grid,grid[seq_len(min(5,nrow(grid))),,drop=FALSE],grid[1,,drop=FALSE]);d[nrow(d),1]<-NA
  d[]<-lapply(d,factor,levels=c('Y','N','unused'))
  extra<-list();if(k>=3)extra<-c(extra,list(var3='c',var3true='Y'));if(k==4)extra<-c(extra,list(var4='d',var4true='Y'))
  got<-sets_run(d,extra);tab<-got$intersections$asDF
  complete<-complete.cases(d);binary<-as.data.frame(lapply(d[complete,,drop=FALSE],function(v)v=='Y'))
  signatures<-apply(binary,1,function(v)paste0(as.integer(v),collapse=''))
  expect_equal(nrow(tab),2^k)
  for(i in seq_len(nrow(tab))){expect_equal(tab$n[i],sum(signatures==tab$pattern[i]));expect_equal(tab$percent[i],mean(signatures==tab$pattern[i]))}
  sets<-got$sets$asDF;expect_equal(sets$members,as.numeric(colSums(binary)));expect_equal(sets$n,rep(sum(complete),k));expect_equal(sets$missing,c(1L,rep(0L,k-1)))
  expect_equal(sum(tab$n),sum(complete))
 }
})

test_that('genuine NA levels are missing and literal NA labels are preserved', {
 d<-data.frame(a=factor(c('N',NA,'Y','NA'),exclude=NULL),b=factor(rep('Y',4)))
 got<-sets_run(d,list(var1true='NA'));tab<-got$intersections$asDF
 expect_equal(sum(tab$n),3);expect_equal(got$sets$asDF$members,c(1L,3L))
})

test_that('saved membership preserves sparse original rows and none differs from missing', {
 d<-data.frame(a=factor(c('N','Y','N','Y',NA)),b=factor(c('N','N','Y','Y','Y')),row.names=c('2','5','9','12','15'))
 options<-pyvennOptions$new(var1='a',var2='b',var1true='Y',var2true='Y',showMembershipTable=TRUE)
 saved_option<-options$option('membershipGroups');saved_option$value<-list(value=TRUE,vars=list())
 a<-pyvennClass$new(options=options,data=d);a$init();a$run();jmvcore:::initProtoBuf()
 pb<-a$results$membershipGroups$asProtoBuf(incAsText=TRUE)$outputs
 expect_equal(as.integer(pb$rowNums),c(1L,4L,8L,11L,14L))
 saved<-pb$outputs[[1]];expect_equal(vapply(saved$levels,function(x)x$label,character(1)),c('00','10','01','11'))
 expect_equal(as.integer(saved$i[1:4]),1:4);expect_true(is.na(saved$i[5])||saved$i[5]==-2147483648)
 expect_equal(a$results$membershipTable$asDF$row,c('2','5','9','12','15'))
 selected<-a$options$option('var2');selected$value<-NULL;a$init();a$run()
 expect_equal(a$results$intersections$rowCount,0);expect_equal(a$results$sets$rowCount,0);expect_null(a$results$intersectionPlot$state)
 expect_equal(a$results$explorer$content,'<div></div>')
 cleared<-a$results$membershipGroups$asProtoBuf(incAsText=TRUE)$outputs$outputs[[1]]$i
 expect_equal(length(cleared),5L);expect_true(all(is.na(cleared)|cleared == -2147483648))
 selected$value<-'b';positive<-a$options$option('var2true');positive$value<-'Y';a$init();a$run();expect_equal(sum(a$results$intersections$asDF$n),4)
 raster<-ClinicoPathPj:::.cpjRenderPlot(a$results$intersectionPlot$state,800L,500L,list(palette='jmv'))
 expect_equal(dim(raster)[1:2],c(500L,800L))
})
