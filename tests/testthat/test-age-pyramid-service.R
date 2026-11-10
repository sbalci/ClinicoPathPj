test_that("the Pj age pyramid replaces results and clears incomplete state", {
    d <- data.frame(Age = c(0, 5, 10, 65), Gender = factor(c("F", "M", "F", "M")))
    analysis <- pyagepyramidpjClass$new(options = pyagepyramidpjOptions$new(
        age = "Age", gender = "Gender", female = "F", male = "M"), data = d)
    analysis$init()
    analysis$run()
    expect_equal(tail(analysis$results$population$asDF$total, 1), 4)

    width <- analysis$options$option("bin_width")
    width$value <- 20
    analysis$.__enclos_env__$private$.run()
    fresh <- pyagepyramidpj(d, age = "Age", gender = "Gender", female = "F", male = "M",
                           bin_width = 20)
    expect_equal(analysis$results$population$asDF$total, c(3, 1, 4))
    expect_equal(analysis$results$population$asDF, fresh$population$asDF)
    expect_equal(analysis$results$pyramid$state, fresh$pyramid$state)

    selected <- analysis$options$option("age")
    selected$value <- NULL
    analysis$.__enclos_env__$private$.run()
    expect_equal(analysis$results$population$rowCount, 0L)
    expect_equal(analysis$results$dataSummary$rowCount, 0L)
    expect_null(analysis$results$pyramid$state)
    expect_true(is.null(analysis$results$assignment$content) ||
                identical(analysis$results$assignment$content, ""))

    selected$value <- "Age"
    analysis$.__enclos_env__$private$.run()
    expect_equal(analysis$results$population$asDF, fresh$population$asDF)
    expect_equal(analysis$results$pyramid$state, fresh$pyramid$state)
    expect_match(analysis$results$executionRoute$content, "Pj")
})
