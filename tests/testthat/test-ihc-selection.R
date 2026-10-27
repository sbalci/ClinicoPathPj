test_that('applied IHC selection flags keep original rows, missingness and full-data statistics', {
  d<-data.frame(a=c(0,10,1,11,NA,NA),b=c(0,20,2,22,3,NA),
                id=c('same','same','other','other','partial','all'),row.names=c('2','4','7','9','12','15'))
  options<-pyihcheatmapOptions$new(markers=c('a','b'),subject='id',enableSelection=TRUE)
  output<-options$option('selectionFlag');output$value<-list(value=TRUE,vars=list())
  a<-pyihcheatmapClass$new(options=options,data=d);a$init();a$run()
  signature<-regmatches(a$results$explorer$content,
    regexec('"snapshot": "([0-9a-f]{64})"',a$results$explorer$content))[[1]][2]
  expect_match(signature,'^[0-9a-f]{64}$')
  definition<-jsonlite::toJSON(list(version=1L,rows=as.list(c('4','12')),snapshot=signature),auto_unbox=TRUE)
  selected<-options$option('selectionDefinition');selected$value<-as.character(definition)
  a$.__enclos_env__$private$.run()
  expect_equal(a$results$selectionRows$asDF$sourceRow,c('4','12'))
  expect_equal(a$results$selectionRows$asDF$subject,c('same','partial'))
  expect_equal(a$results$markerSummary$asDF$mean,c(5.5,9.4))
  jmvcore:::initProtoBuf()
  saved<-function(x)x$results$selectionFlag$asProtoBuf(incAsText=TRUE)$outputs
  pb<-saved(a)
  expect_equal(as.integer(pb$rowNums),as.integer(rownames(d))-1L)
  expect_equal(as.integer(pb$outputs[[1]]$i[1:5]),c(1L,2L,1L,1L,2L))
  expect_true(is.na(pb$outputs[[1]]$i[6])||pb$outputs[[1]]$i[6]==-2147483648)
  expect_equal(as.integer(pb$outputs[[1]]$measureType),2L)
  expect_equal(vapply(pb$outputs[[1]]$levels,function(x)x$label,character(1)),c('Not selected','Selected'))
  missing<-options$option('missing');missing$value<-'complete';a$.__enclos_env__$private$.run()
  expect_equal(a$results$selectionSummary$asDF$selected,1)
  expect_equal(a$results$selectionSummary$asDF$unavailable,1)
  expect_true(is.na(saved(a)$outputs[[1]]$i[5]))
  enabled<-options$option('enableSelection');enabled$value<-FALSE;a$.__enclos_env__$private$.run()
  expect_true(all(is.na(as.integer(saved(a)$outputs[[1]]$i))))
  enabled$value<-TRUE;markers<-options$option('markers');markers$value<-character()
  a$.__enclos_env__$private$.run()
  expect_true(all(is.na(as.integer(saved(a)$outputs[[1]]$i))))
  expect_equal(a$results$selectionSummary$rowCount,0L)
  markers$value<-c('a','b');a$.__enclos_env__$private$.run()
  expect_equal(a$results$selectionRows$asDF$sourceRow,'4')
  expect_equal(as.integer(saved(a)$outputs[[1]]$i[2]),2L)
  edited<-d;edited$a[1]<-99
  opts<-pyihcheatmapOptions$new(markers=c('a','b'),subject='id',enableSelection=TRUE,
                               selectionDefinition=as.character(definition))
  control<-opts$option('selectionFlag');control$value<-list(value=TRUE,vars=list())
  changed<-pyihcheatmapClass$new(options=opts,data=edited);changed$init();changed$run()
  expect_equal(changed$results$selectionSummary$asDF$status,'Needs review')
  expect_equal(changed$results$selectionRows$rowCount,0L)
  expect_true(all(is.na(as.integer(saved(changed)$outputs[[1]]$i))))
})

test_that('selected marker data use retained-cohort scaling and clear across native lifecycle', {
  d <- data.frame(a=c(0,10,1,11,NA,NA), b=c(0,20,2,22,3,NA),
                  id=c('same','same','other','other','partial','all'),
                  row.names=c('2','4','7','9','12','15'))
  opts <- pyihcheatmapOptions$new(markers=c('a','b'), subject='id',
    enableSelection=TRUE, showSelectionValues=TRUE, scaling='zscore')
  a <- pyihcheatmapClass$new(options=opts, data=d); a$init(); a$run()
  table <- a$results$selectionValues
  expect_true(table$visible)
  expect_equal(table$rowCount,0L)
  signature <- regmatches(a$results$explorer$content,
    regexec('"snapshot": "([0-9a-f]{64})"',a$results$explorer$content))[[1]][2]
  definition <- jsonlite::toJSON(list(version=1L,rows=as.list(c('4','12')),
                                      snapshot=signature),auto_unbox=TRUE)
  saved <- opts$option('selectionDefinition');saved$value <- as.character(definition)
  a$.__enclos_env__$private$.run()
  values <- table$asDF
  expect_equal(values$sourceRow,c('4','4','12','12'))
  expect_equal(values$subject,c('same','same','partial','partial'))
  expect_equal(values$marker,c('a','b','a','b'))
  expect_equal(values$raw,c(10,20,NA,3))
  expect_equal(values$displayed,c(as.numeric(scale(d$a))[2],as.numeric(scale(d$b))[2],
                                 NA,as.numeric(scale(d$b))[5]))
  expect_equal(values$status,c('Observed','Observed','Missing','Observed'))
  expect_equal(values$position,c(2L,2L,5L,5L))
  jmvcore:::initProtoBuf()
  expect_silent(table$asProtoBuf(incAsText=TRUE))
  missing <- opts$option('missing');missing$value <- 'complete'
  a$.__enclos_env__$private$.run()
  expect_equal(table$asDF$sourceRow,c('4','4'))
  expect_equal(table$asDF$displayed,c(as.numeric(scale(d$a[1:4]))[2],
                                    as.numeric(scale(d$b[1:4]))[2]))
  saved$value <- gsub(signature,paste(rep('0',64),collapse=''),as.character(definition),fixed=TRUE)
  a$.__enclos_env__$private$.run();expect_equal(table$rowCount,0L)
  saved$value <- as.character(definition)
  a$.__enclos_env__$private$.run();expect_equal(table$rowCount,2L)
  shown <- opts$option('showSelectionValues');shown$value <- FALSE
  a$.__enclos_env__$private$.run();expect_equal(table$rowCount,0L)
  shown$value <- TRUE
  enabled <- opts$option('enableSelection');enabled$value <- FALSE
  a$.__enclos_env__$private$.run();expect_equal(table$rowCount,0L)
  enabled$value <- TRUE
  markers <- opts$option('markers');markers$value <- character()
  a$.__enclos_env__$private$.run();expect_equal(table$rowCount,0L)
  markers$value <- c('a','b')
  a$.__enclos_env__$private$.run();expect_equal(table$rowCount,2L)
  saved$value <- '';a$.__enclos_env__$private$.run();expect_equal(table$rowCount,0L)
  for (flags in list(c(FALSE,TRUE),c(TRUE,FALSE))) {
    control <- pyihcheatmapOptions$new(markers=c('a','b'),enableSelection=flags[1],
                                       showSelectionValues=flags[2])
    other <- pyihcheatmapClass$new(options=control,data=d);other$init();other$run()
    expect_false(other$results$selectionValues$visible)
    expect_equal(other$results$selectionValues$rowCount,0L)
  }
})
