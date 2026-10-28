test_that('correlation cores agree with independent cor.test and p.adjust', {
 d<-data.frame(a=c(1,2,3,4,NA,6,8,9),b=c(4,1,5,3,4,9,NA,6),c=c(9,7,8,4,3,5,1,2),constant=rep(2,8))
 vars<-names(d)
 for(method in c('parametric','nonparametric'))for(missing in c('listwise','pairwise'))for(adjust in c('holm','bonferroni','BH','none','BY','hochberg','hommel')){
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
 expect_equal(a$results$correlations$rowCount,0);expect_equal(a$results$cohorts$rowCount,0);expect_null(a$results$matrix$state)
 expect_equal(a$results$explorer$content,'<div></div>')
 selected$value<-names(d);a$.__enclos_env__$private$.run();expect_equal(a$results$correlations$rowCount,1)
 png<-ClinicoPathPj:::.cpjRenderPlot(a$results$matrix$state,800L,650L,list(palette='jmv'))
 expect_equal(dim(png)[1:2],c(650L,800L))
})

test_that('partial Pearson agrees with independent base-R residual regressions', {
 set.seed(142)
 d<-data.frame(a=rnorm(45),b=rnorm(45),c=rnorm(45),z=rnorm(45))
 d$a<-d$a+2*d$z;d$b<-d$b+3*d$z;d$a[2]<-NA;d$c[4]<-NA
 clean<-na.omit(d);vars<-names(d);k<-length(vars)-2L;n<-nrow(clean);df<-n-k-2
 for(adjust in c('holm','bonferroni','BH','BY','hochberg','hommel','none')){
  got<-do.call(pyjjcorrmat,list(data=d,dep=vars,partial=TRUE,padjustmethod=adjust,conflevel=.9))
  tab<-got$correlations$asDF;raw<-numeric(nrow(tab))
  for(i in seq_len(nrow(tab))){
   controls<-setdiff(vars,c(tab$first[i],tab$second[i]));design<-cbind(1,as.matrix(clean[controls]))
   a<-lm.fit(design,clean[[tab$first[i]]])$residuals;b<-lm.fit(design,clean[[tab$second[i]]])$residuals
   r<-cor(a,b);p<-2*pt(-abs(r)*sqrt(df/(1-r*r)),df);raw[i]<-p
   limits<-tanh(atanh(r)+c(-1,1)*qnorm(.95)/sqrt(n-k-3))
   expect_equal(tab$n[i],n);expect_equal(tab$excluded[i],2L)
   expect_equal(tab$controls[i],k);expect_equal(tab$df[i],df)
   expect_equal(tab$estimate[i],r,tolerance=1e-11);expect_equal(tab$p[i],p,tolerance=1e-11)
   expect_equal(c(tab$lower[i],tab$upper[i]),limits,tolerance=1e-11)
  }
  expect_equal(tab$adjusted,p.adjust(raw,adjust,n=6),tolerance=1e-11)
 }
})

test_that('partial Spearman agrees with independent ranked residual regressions', {
 set.seed(147)
 d<-data.frame(a=sample(1:8,45,TRUE),b=sample(1:12,45,TRUE),c=sample(1:6,45,TRUE),z=sample(1:15,45,TRUE))
 d$a[2]<-NA;d$c[4]<-NA
 clean<-na.omit(d);ranked<-as.data.frame(lapply(clean,rank,ties.method='average'))
 vars<-names(d);k<-length(vars)-2L;n<-nrow(clean);df<-n-k-2
 for(adjust in c('holm','bonferroni','BH','BY','hochberg','hommel','none')){
  got<-do.call(pyjjcorrmat,list(data=d,dep=vars,partial=TRUE,typestatistics='nonparametric',padjustmethod=adjust))
  tab<-got$correlations$asDF;raw<-numeric(nrow(tab))
  for(i in seq_len(nrow(tab))){
   controls<-setdiff(vars,c(tab$first[i],tab$second[i]));design<-cbind(1,as.matrix(ranked[controls]))
   a<-lm.fit(design,ranked[[tab$first[i]]])$residuals;b<-lm.fit(design,ranked[[tab$second[i]]])$residuals
   r<-cor(a,b);raw[i]<-2*pt(-abs(r)*sqrt(df/(1-r*r)),df)
   expect_equal(tab$n[i],n);expect_equal(tab$excluded[i],2L)
   expect_equal(tab$controls[i],k);expect_equal(tab$df[i],df)
   expect_equal(tab$estimate[i],r,tolerance=1e-11);expect_equal(tab$p[i],raw[i],tolerance=1e-11)
   expect_true(is.na(tab$lower[i])&&is.na(tab$upper[i]))
  }
  expect_equal(tab$adjusted,p.adjust(raw,adjust,n=6),tolerance=1e-11)
 }
})

test_that('split correlations agree with independent within-group R analyses', {
 set.seed(187)
 d<-data.frame(x=sample(1:8,40,TRUE),y=sample(1:12,40,TRUE),z=sample(1:5,40,TRUE),
               group=factor(rep(c('B','A'),20),levels=c('unused','B','A')))
 d$group[39]<-NA;d$x[2]<-NA;d$y[5]<-NA;d$z[8]<-NA
 vars<-c('x','y','z')
 for(method in c('parametric','nonparametric'))for(mode in c('listwise','pairwise','partial'))for(adjust in c('holm','BY')){
  partial<-mode=='partial';missing<-if(mode=='pairwise')'pairwise'else'listwise'
  got<-do.call(pyjjcorrmat,list(data=d,dep=vars,grvar='group',typestatistics=method,partial=partial,naHandling=missing,padjustmethod=adjust,conflevel=.9))
  cohorts<-got$cohorts$asDF;tab<-got$correlations$asDF
  expect_equal(cohorts$group,c('B','A'));expect_equal(cohorts$input,c(19L,20L));expect_equal(cohorts$complete,c(18L,18L));expect_equal(cohorts$family,c(3L,3L))
  for(label in c('B','A')){
   group<-d[which(d$group==label),vars];selected<-tab[tab$group==label,];raw<-numeric(nrow(selected))
   for(i in seq_len(nrow(selected))){
    pair<-c(selected$first[i],selected$second[i]);sub<-if(missing=='listwise')na.omit(group)else na.omit(group[pair])
    n<-nrow(sub);k<-if(partial)1L else 0L;df<-n-k-2
    if(partial){
     if(method=='nonparametric')sub<-as.data.frame(lapply(sub,rank,ties.method='average'))
     design<-cbind(1,as.matrix(sub[setdiff(vars,pair)]));a<-lm.fit(design,sub[[pair[1]]])$residuals;b<-lm.fit(design,sub[[pair[2]]])$residuals
     r<-cor(a,b);p<-2*pt(-abs(r)*sqrt(df/(1-r*r)),df)
    }else{ref<-cor.test(sub[[pair[1]]],sub[[pair[2]]],method=if(method=='parametric')'pearson'else'spearman',exact=FALSE);r<-unname(ref$estimate);p<-ref$p.value}
    raw[i]<-p;expect_equal(selected$n[i],n);expect_equal(selected$excluded[i],nrow(group)-n)
    expect_equal(selected$controls[i],k);expect_equal(selected$df[i],df)
    expect_equal(selected$estimate[i],r,tolerance=1e-11);expect_equal(selected$p[i],p,tolerance=1e-11)
    if(method=='parametric')expect_equal(c(selected$lower[i],selected$upper[i]),tanh(atanh(r)+c(-1,1)*qnorm(.95)/sqrt(n-k-3)),tolerance=1e-11)
    else expect_true(is.na(selected$lower[i])&&is.na(selected$upper[i]))
   }
   expect_equal(selected$adjusted,p.adjust(raw,adjust,n=3),tolerance=1e-11)
  }
 }
 raster<-ClinicoPathPj:::.cpjRenderPlot(got$matrix$state,800L,650L,list(palette='jmv'))
 expect_equal(dim(raster)[1:2],c(650L,800L))
})
