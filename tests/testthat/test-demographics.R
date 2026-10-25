test_that("age bands, boundaries and percentage denominators agree with base R", {
  d <- data.frame(a=c(0,5,10,18,65,85,100,NA,-1),g=factor(c('F','M','F','M','F','M','F','F','M')))
  for (right in c(FALSE,TRUE)) for (base in c('within_gender','total')) {
    got <- pyagepyramid(data=d,age='a',gender='g',female='F',male='M',custom_breaks='0,18,65,85',
      age_interval=if(right)'right' else 'left',pct_base=base,showplot=FALSE)
    clean <- d[!is.na(d$a)&d$a>=0,]
    b <- cut(clean$a,c(0,18,65,85,Inf),right=right,include.lowest=TRUE)
    expected <- table(b,clean$g)
    rows <- got$population$asDF
    expect_equal(rows$female[-nrow(rows)],as.numeric(expected[,'F']))
    expect_equal(rows$male[-nrow(rows)],as.numeric(expected[,'M']))
    denominator <- if(base=='total') sum(expected) else sum(expected[,'F'])
    expect_equal(rows$femalePercent[-nrow(rows)],as.numeric(expected[,'F'])/denominator)
    expect_equal(got$dataSummary$asDF$n,c(9,1,1,0,0,7))
  }
})

test_that("numeric factor ages use value labels and explicit missing factor levels stay missing", {
  age <- factor(c('0','5','65',NA),levels=c('65','5','0'),exclude=NULL)
  g <- factor(c('M','F','M','F'))
  got <- pyagepyramid(data=data.frame(age=age,g=g),age='age',gender='g',female='F',male='M',age_groups='who',showplot=FALSE)
  expect_equal(got$population$asDF$band,c('0-4','5-9','65-69','Total'))
  expect_equal(got$population$asDF$total,c(1,1,1,3))
  expect_equal(got$dataSummary$asDF$n[2],1)
})

test_that("age pyramid lifecycle replaces counts and pending state clears the figure", {
  d <- data.frame(a=c(0,5,10,65),g=factor(c('F','M','F','M')))
  a <- pyagepyramidClass$new(options=pyagepyramidOptions$new(age='a',gender='g',female='F',male='M'),data=d)
  a$init();a$run()
  expect_equal(sum(a$results$population$asDF$total[-a$results$population$rowCount]),4)
  width <- a$options$option('bin_width');width$value<-20
  a$.__enclos_env__$private$.run()
  expect_equal(a$results$population$rowCount,3L)
  expect_equal(a$results$population$asDF$total,c(3,1,4))
  selected <- a$options$option('age');selected$value<-NULL
  a$.__enclos_env__$private$.run()
  expect_equal(a$results$population$rowCount,0L)
  expect_null(a$results$pyramid$state)
  selected$value<-'a'
  a$.__enclos_env__$private$.run()
  expect_equal(a$results$population$asDF$total,c(3,1,4))
})

test_that("single gender percentages are unavailable on an empty side", {
  d <- data.frame(a=c(0,10,20),g=factor(rep('Male',3)))
  got <- pyagepyramid(data=d,age='a',gender='g',female=NULL,male=NULL,showplot=FALSE)
  expect_true(all(is.na(got$population$asDF$femalePercent)))
  expect_equal(tail(got$population$asDF$malePercent,1),1)
  expect_error(pyagepyramid(data=d,age='a',gender='g',female='Male',male='Male'), 'must be different')
})
