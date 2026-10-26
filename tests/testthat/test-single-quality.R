test_that('single-variable screening agrees with base R and preserves original IDs', {
 d<-data.frame(x=c(rep(0,10),100,NA),row.names=as.character(seq(4,37,3)))
 a<-pycheckdata(data=d,var='x',showOutliers=TRUE,showDistribution=TRUE,showPatterns=TRUE,showInteractive=TRUE)
 expect_equal(a$overview$asDF$valid,11)
 expect_equal(a$overview$asDF$missing,1)
 expect_equal(a$overview$asDF$repeats,9)
 expect_equal(a$outliers$asDF$row,rownames(d)[11])
 expect_equal(a$outliers$asDF$votes,2)
 expect_equal(a$outliers$asDF$madFlag,'Unavailable')
 distribution<-a$distribution$asDF
 expect_equal(distribution$value[distribution$statistic=='sd'],sd(d$x,na.rm=TRUE))
 expect_equal(distribution$value[distribution$statistic=='q1'],unname(quantile(d$x,.25,na.rm=TRUE)))
 expect_match(a$explorer$content,'full-data results unchanged',fixed=TRUE)
 expect_equal(a$plot$state$kind,'points')
 options<-pycheckdataOptions$new(var='x')
 control<-options$option('screeningFlag');control$value<-list(value=TRUE,vars=list())
 analysis<-pycheckdataClass$new(options=options,data=d);analysis$init();analysis$run()
 jmvcore:::initProtoBuf()
 pb<-analysis$results$screeningFlag$asProtoBuf(incAsText=TRUE)$outputs
 expect_equal(as.integer(pb$rowNums),as.integer(rownames(d))-1L)
 expect_equal(as.integer(pb$outputs[[1]]$i[1:11]),c(rep(1L,10),2L))
 expect_true(is.na(pb$outputs[[1]]$i[12])||pb$outputs[[1]]$i[12]==-2147483648)
 expect_equal(vapply(pb$outputs[[1]]$levels,function(x)x$label,character(1)),c('Not selected','Selected'))
})

test_that('categorical levels and pending lifecycle remain consistent', {
 d<-data.frame(g=factor(c('NA','B',NA,'NA'),levels=c('B','NA','unused')))
 a<-pycheckdata(data=d,var='g',showDuplicates=TRUE)
 expect_equal(a$overview$asDF$valid,3)
 expect_equal(a$overview$asDF$distinct,2)
 expect_equal(a$frequencies$asDF$value,c('NA','B'))
 d<-data.frame(x=c(1:10,100))
 a<-pycheckdataClass$new(options=pycheckdataOptions$new(var='x',showInteractive=TRUE),data=d)
 a$init();a$run()
 expect_equal(a$results$overview$rowCount,1L)
 selected<-a$options$option('var');selected$value<-NULL
 a$.__enclos_env__$private$.run()
 expect_equal(a$results$overview$rowCount,0L)
 expect_equal(a$results$outliers$rowCount,0L)
 expect_equal(a$results$explorer$content,'<div></div>')
 expect_null(a$results$plot$state)
 selected$value<-'x';a$.__enclos_env__$private$.run()
 expect_equal(a$results$overview$rowCount,1L)
 expect_match(a$results$explorer$content,'Filtering does not recalculate',fixed=TRUE)
})

 test_that('pending saved flags are cleared and a valid rerun restores them', {
 d<-data.frame(x=c(rep(0,10),100,NA))
 options<-pycheckdataOptions$new(var='x')
 control<-options$option('screeningFlag');control$value<-list(value=TRUE,vars=list())
 a<-pycheckdataClass$new(options=options,data=d);a$init();a$run()
 jmvcore:::initProtoBuf()
 original<-a$results$screeningFlag$asProtoBuf(incAsText=TRUE)$outputs$outputs[[1]]
 expect_equal(as.integer(original$i[11]),2L)
 selected<-options$option('var');selected$value<-NULL;a$.__enclos_env__$private$.run()
 missing<-a$results$screeningFlag$asProtoBuf(incAsText=TRUE)$outputs$outputs[[1]]
 expect_true(all(as.integer(missing$i)==-2147483648|is.na(missing$i)))
 expect_equal(length(missing$i),nrow(d))
 selected$value<-'x';a$.__enclos_env__$private$.run()
 restored<-a$results$screeningFlag$asProtoBuf(incAsText=TRUE)$outputs$outputs[[1]]
 expect_equal(as.integer(restored$i),as.integer(original$i))
 })

test_that('pending existing saved categories clear and restore through the same bridge', {
 d<-data.frame(x=c(1,2,3,4,NA))
 options<-pycategorizeOptions$new(var='x',method='quantile',nbins=2L,showplot=FALSE)
 control<-options$option('addtodata');control$value<-list(value=TRUE,vars=list())
 a<-pycategorizeClass$new(options=options,data=d);a$init();a$run()
 jmvcore:::initProtoBuf()
 before<-a$results$addtodata$asProtoBuf(incAsText=TRUE)$outputs$outputs[[1]]
 selected<-options$option('var');selected$value<-NULL;a$.__enclos_env__$private$.run()
 pending<-a$results$addtodata$asProtoBuf(incAsText=TRUE)$outputs$outputs[[1]]
 expect_true(all(is.na(as.integer(pending$i))))
 selected$value<-'x';a$.__enclos_env__$private$.run()
 after<-a$results$addtodata$asProtoBuf(incAsText=TRUE)$outputs$outputs[[1]]
 expect_equal(as.integer(after$i),as.integer(before$i))
 expect_equal(vapply(after$levels,function(x)x$label,character(1)),vapply(before$levels,function(x)x$label,character(1)))
})
