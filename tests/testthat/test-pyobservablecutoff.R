test_that("Observable experiment uses saved options for native results", {
    d <- data.frame(x = c(1, 2, 2, 4, 5, 6, NA, 8),
                    g = factor(c("N", "N", "P", "N", "P", "P", "P", NA)))
    got <- pyobservablecutoff(data = d, marker = "x", reference = "g", positive = "P", cutoff = "2")
    expect_equal(got$counts$asDF$n, c(3, 2, 0, 1))
    for (i in seq_len(5)) {
        ci <- binom.test(c(3, 1, 3, 1, 4)[i], c(3, 3, 5, 1, 6)[i])$conf.int
        expect_equal(unname(unlist(got$metrics$asDF[i, c("lower", "upper")])),
                     as.numeric(ci), tolerance = 1e-10)
    }
    expect_match(got$explorer$content, "Apply to HTML tables", fixed = TRUE)
    expect_match(got$explorer$content, '"excluded": 2', fixed = TRUE)
    expect_false(grepl("setOption", got$explorer$content, fixed = TRUE))
    reversed <- pyobservablecutoff(data = d, marker = "x", reference = "g", positive = "P",
                          cutoff = "2", direction = "le", ciMethod = "wilson")
    expect_equal(reversed$counts$asDF$n, c(1, 2, 2, 1))
    expect_equal(c(reversed$metrics$asDF$lower[1], reversed$metrics$asDF$upper[1]),
                 as.numeric(suppressWarnings(prop.test(1, 3, correct = FALSE))$conf.int),
                 tolerance = 1e-10)
})

test_that("Observable lifecycle clears pending results and recovers after invalid input", {
    d <- data.frame(x = c(1, 2, 2, 4, 5, 6), g = factor(c("N", "N", "P", "N", "P", "P")))
    a <- pyobservablecutoffClass$new(options = pyobservablecutoffOptions$new(marker = "x", reference = "g",
                         positive = "P", cutoff = "2"), data = d)
    a$init(); a$run()
    expect_equal(a$results$counts$asDF$n, c(3, 2, 0, 1))
    expect_match(a$results$explorer$content, "Apply to HTML tables", fixed = TRUE)
    event <- a$options$option("positive")
    event$value <- NULL
    a$.__enclos_env__$private$.run()
    expect_equal(a$results$counts$rowCount, 0L)
    expect_equal(a$results$metrics$rowCount, 0L)
    expect_equal(a$results$rocSummary$rowCount, 0L)
    expect_equal(a$results$explorer$content, "<div></div>")
    expect_null(a$results$staticDotplot$state)
    expect_null(a$results$staticROC$state)
    event$value <- "P"
    a$.__enclos_env__$private$.run()
    expect_equal(a$results$counts$asDF$n, c(3, 2, 0, 1))
    expect_match(a$results$explorer$content, "Apply to HTML tables", fixed = TRUE)
    cutoff <- a$options$option("cutoff")
    cutoff$value <- "bad"
    expect_error(a$.__enclos_env__$private$.run(), "finite number")
    # Existing bridge contract: jamovi greys prior native results behind an error.
    expect_equal(a$results$counts$asDF$n, c(3, 2, 0, 1))
    expect_equal(a$results$explorer$content, "<div></div>")
    expect_equal(a$results$staticROC$state$kind, "line")
    cutoff$value <- "3"
    a$.__enclos_env__$private$.run()
    expect_equal(a$results$counts$asDF$n, c(2, 1, 1, 2))
    expect_equal(a$results$staticROC$state$kind, "line")
})
