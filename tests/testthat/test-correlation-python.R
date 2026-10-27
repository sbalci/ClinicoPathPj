test_that('correlation cores agree with independent cor.test and p.adjust', {
 d<-data.frame(a=c(1,2,3,4,NA,6,8,9),b=c(4,1,5,3,4,9,NA,6),c=c(9,7,8,4,3,5,1,2),constant=rep(2,8))
 vars<-names(d)
 for(method in c('parametric','nonparametric'))for(missing in c('listwise','pairwise'))for(adjust in c('holm','bonferroni','BH','none')){
  got<-do.call(pyjjcorrmat,list(data=d,dep=vars,typestatistics=method,naHandling=missing,padjustmethod=adjust,conflevel=.9))
  tab<-got$correlations$asDF;expected.p<-rep(NA_real_,nrow(tab))
  for(i in seq_len(nrow(tab))){
   sub<-if(missing=='listwise')d[complete.cases(d),c(tab$first[i],tab$second[i])]else na.omit(d[c(tab$first[i],tab$second[i])])
   expect_equal(tab$n[i],nrow(sub));expect_equal(tab$excluded[i],nrow(d)-nrow(sub))
   if(length(unique(sub[[1]]))<2||length(unique(sub[[2]]))<2){expect_true(is.na(tab$estimate[i]));next}
   ref<-cor.test(sub[[1]],sub[[2]],method=if(method=='parametric')'pearson'else'spearman',exact=FALSE,conf.level=.9)
   expect_equal(tab$estimate[i],unname(ref$estimate),tolerance=1e-12)
   expect_equal(tab$p[i],ref$p.value,tolerance=1e-11);expected.p[i]<-ref$p.value
   if(method=='parametric')expect_equal(c(tab$lower[i],tab$upper[i]),as.numeric(ref$conf.int),tolerance=1e-11)
   else expect_true(is.na(tab$lower[i])&&is.na(tab$upper[i]))
  }
  expect_equal(tab$adjusted,p.adjust(expected.p,method=adjust,n=nrow(tab)),tolerance=1e-11)
 }
})
test_that('correlation pending selections clear native results and plot states', {
 d<-data.frame(a=1:5,b=c(3,2,4,1,5))
 a<-pyjjcorrmatClass$new(options=pyjjcorrmatOptions$new(dep=names(d)),data=d)
 a$init();a$run();expect_equal(a$results$correlations$rowCount,1)
 selected<-a$options$option('dep');selected$value<-character();a$.__enclos_env__$private$.run()
 expect_equal(a$results$correlations$rowCount,0);expect_null(a$results$matrix$state)
 expect_equal(a$results$explorer$content,'<div></div>')
 selected$value<-names(d);a$.__enclos_env__$private$.run();expect_equal(a$results$correlations$rowCount,1)
 png<-ClinicoPathPj:::.cpjRenderPlot(a$results$matrix$state,800L,650L,list(palette='jmv'))
 expect_equal(dim(png)[1:2],c(650L,800L))
})
