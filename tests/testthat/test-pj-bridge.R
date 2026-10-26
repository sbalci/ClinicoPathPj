test_that("the optional Pj result envelope is validated before mapping", {
    original <- .libPaths()
    fake <- function(content, type="Text", duplicate=FALSE) list(run=function(...) {
        item<-list(name="cpjEnvelope",type=type,content=content)
        list(items=if(duplicate)list(item,item)else list(item),service=list(api_version=1L))
    })
    valid <- '{"schema_version":1,"status":"ok","tables":{},"plots":{},"texts":{}}'
    got<-ClinicoPathPj:::.cpjPjExecute("{}",service=fake(valid))
    expect_identical(got$result$status,"ok")
    expect_error(ClinicoPathPj:::.cpjPjExecute("{}",service=fake(valid,"Html")),"invalid or oversized")
    expect_error(ClinicoPathPj:::.cpjPjExecute("{}",service=fake(valid,duplicate=TRUE)),"invalid or oversized")
    expect_error(ClinicoPathPj:::.cpjPjExecute("{}",service=fake('{"schema_version":2,"status":"ok"}')),"unsupported")
    expect_error(ClinicoPathPj:::.cpjPjExecute("{}",service=fake("invalid json")))
    expect_identical(.libPaths(),original)
})

test_that("comparison has native processx results and clears incomplete selections", {
    d<-data.frame(x=c(1,2,2,4,5,6),g=factor(c("N","N","P","N","P","P")))
    a<-pybridgecompareClass$new(options=pybridgecompareOptions$new(marker="x",reference="g",positive="P",cutoff="2"),data=d)
    a$init();a$run()
    expect_identical(a$results$counts$asDF$n,c(3L,2L,0L,1L))
    expect_match(a$results$backendTiming$content,"Route: processx",fixed=TRUE)
    expect_match(a$results$explorer$content,'"hostApply": true',fixed=TRUE)
    ref<-a$options$option("reference");ref$value<-NULL
    a$.__enclos_env__$private$.run()
    expect_equal(a$results$counts$rowCount,0L)
    expect_identical(a$results$explorer$content,"<div></div>")
    expect_identical(a$results$backendTiming$content,"")
    ref$value<-"g";a$.__enclos_env__$private$.run()
    expect_identical(a$results$counts$asDF$n,c(3L,2L,0L,1L))
})
