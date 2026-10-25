test_that("continuous summaries, Shapiro and moments agree with independent R calculations", {
    x <- c(-5, -3, -1, 0, 1, 2, 3, 4, 7, 20, NA)
    d <- data.frame(x = x)
    got <- pysummarydata(data = d, vars = "x", distr = TRUE, outliers = TRUE, showplot = FALSE)
    clean <- na.omit(x)
    desc <- got$descriptives$asDF
    expect_equal(desc$n, length(clean))
    expect_equal(desc$missing, 1)
    expect_equal(c(desc$mean, desc$sd, desc$minimum, desc$q1, desc$median, desc$q3, desc$maximum),
                 c(mean(clean), sd(clean), min(clean), unname(quantile(clean,.25)), median(clean),
                   unname(quantile(clean,.75)), max(clean)), tolerance = 1e-10)
    sw <- shapiro.test(clean)
    diag <- got$diagnostics$asDF
    expect_equal(diag$w, unname(sw$statistic), tolerance = 2e-7)
    expect_equal(diag$p, sw$p.value, tolerance = 2e-7)
    expect_equal(diag$skewness, mean((clean-mean(clean))^3)/mean((clean-mean(clean))^2)^1.5)
    expect_equal(diag$kurtosis, mean((clean-mean(clean))^4)/mean((clean-mean(clean))^2)^2)
})

test_that("all closures and missingness denominators reproduce cut", {
    x <- c(-1,0,1,2,3,4,5,NA)
    d <- data.frame(x=x)
    for (right in c(TRUE,FALSE)) for (include in c(TRUE,FALSE)) {
        got <- pycategorize(data=d,var="x",method="manual",breaks="0,2,4",excludeoutofrange=TRUE,
             rightclosed=right,includelowest=include,labels="numbered",excl=FALSE,showplot=FALSE)
        expected <- cut(x,breaks=c(0,2,4),labels=c("1","2"),include.lowest=include,right=right)
        freq <- got$freqTable$asDF
        expect_equal(freq$n[1:2],as.numeric(table(expected)))
        expect_equal(freq$percent[1:2],as.numeric(table(expected))/length(x))
        expect_equal(got$summary$asDF$categorized,sum(!is.na(expected)))
        expect_equal(got$summary$asDF$uncategorized,sum(!is.na(x)&is.na(expected)))
    }
})

test_that("saved categories keep original row numbers names ordered status and levels", {
    d <- data.frame(x=c(0,1,2,NA,4),row.names=c("2","5","9","12","15"))
    options <- pycategorizeOptions$new(var="x",method="manual",breaks="0,2,4",labels="semantic",
                    newvarname="Grade / band",ordered=TRUE,showplot=FALSE)
    output_option <- options$option("addtodata")
    output_option$value <- list(value=TRUE,vars=list())
    analysis <- pycategorizeClass$new(options=options,data=d)
    analysis$init();analysis$run()
    jmvcore:::initProtoBuf()
    pb <- analysis$results$addtodata$asProtoBuf(incAsText=TRUE)$outputs
    expect_equal(as.integer(pb$rowNums),c(1L,4L,8L,11L,14L))
    saved <- pb$outputs[[1]]
    expect_equal(saved$title,"Grade / band")
    expect_equal(as.integer(saved$measureType),3L) # jamovi MeasureType ORDINAL
    expect_equal(vapply(saved$levels,function(x)x$label,character(1)),c("Low","High"))
    expect_equal(as.integer(saved$i[c(1,2,3,5)]),c(1L,1L,1L,2L))
    expect_true(is.na(saved$i[4]) || saved$i[4] == -2147483648)
    ordered_option <- analysis$options$option("ordered")
    ordered_option$value <- FALSE
    analysis$init();analysis$run()
    pb <- analysis$results$addtodata$asProtoBuf(incAsText=TRUE)$outputs
    expect_equal(as.integer(pb$outputs[[1]]$measureType),2L) # NOMINAL
})

test_that("exported R code preserves the exact displayed break points and unusual names", {
    name <- 'x [marker] "q"'
    target <- 'new "grade"'
    d <- data.frame(x=c(.1,.2,.3,.4,.5,NA));names(d)<-name
    got <- do.call(pycategorize,list(data=d,var=name,method="quantile",nbins=3L,newvarname=target,showplot=FALSE))
    env <- new.env(parent=baseenv());env$data<-d
    eval(parse(text=got$rcode$content),envir=env)
    b <- got$breakpointsTable$asDF$value
    expected <- cut(d[[name]],breaks=b,include.lowest=TRUE,ordered_result=TRUE)
    expect_equal(as.integer(env$data[[target]]),as.integer(expected))
    expect_equal(levels(env$data[[target]]),got$freqTable$asDF$category[1:3])
})


test_that("successful and pending bridge reruns replace all native state", {
    d <- data.frame(x=1:8,y=2:9)
    a <- pysummarydataClass$new(options=pysummarydataOptions$new(vars=c("x","y"),showplot=TRUE),data=d)
    a$init();a$run()
    expect_equal(nrow(a$results$descriptives$asDF),2L)
    selected <- a$options$option("vars")
    selected$value <- "x"
    a$.__enclos_env__$private$.run()
    expect_equal(nrow(a$results$descriptives$asDF),1L)
    selected$value <- character()
    a$.__enclos_env__$private$.run()
    expect_equal(a$results$descriptives$rowCount,0L)
    expect_null(a$results$distribution$state)
    selected$value <- "y"
    a$.__enclos_env__$private$.run()
    expect_equal(a$results$descriptives$asDF$variable,"y")
})

test_that("computed notices are reused and retired after a successful method change", {
    a <- pycategorizeClass$new(options=pycategorizeOptions$new(var="x",method="jenks",nbins=3L,showplot=FALSE),data=data.frame(x=1:20))
    a$init();a$run()
    initial <- length(a$results$items)
    a$.__enclos_env__$private$.run()
    expect_equal(length(a$results$items),initial)
    method <- a$options$option("method");method$value<-"equal"
    a$.__enclos_env__$private$.run()
    notices <- Filter(function(x)inherits(x,"Notice"),a$results$items)
    expect_false(any(vapply(notices,function(n)n$visible,logical(1))))
})
