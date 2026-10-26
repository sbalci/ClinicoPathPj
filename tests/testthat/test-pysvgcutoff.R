test_that("Native Svg preserves cutoff calculations and script serialization", {
    d <- data.frame(x = c(1, 2, 2, 4, 5, 6, NA, 8),
                    g = factor(c("N", "N", "P", "N", "P", "P", "P", NA)))
    got <- pysvgcutoff(data = d, marker = "x", reference = "g", positive = "P", cutoff = "2")
    expect_s3_class(got$explorer, "Svg")
    expect_equal(got$counts$asDF$n, c(3, 2, 0, 1))
    for (i in seq_len(5)) {
        ci <- binom.test(c(3, 1, 3, 1, 4)[i], c(3, 3, 5, 1, 6)[i])$conf.int
        expect_equal(unname(unlist(got$metrics$asDF[i, c("lower", "upper")])),
                     as.numeric(ci), tolerance = 1e-10)
    }
    expect_match(got$explorer$content, "Native SVG cutoff lab", fixed = TRUE)
    expect_match(got$explorer$content, "Local snapshot cutoff", fixed = TRUE)
    jmvcore:::initProtoBuf()
    expect_true(length(serialize(got$explorer$asProtoBuf(), NULL)) > 100)
})

test_that("Native Svg clears incomplete input and restores changed rules", {
    d <- data.frame(x = c(1, 2, 2, 4, 5, 6), g = factor(c("N", "N", "P", "N", "P", "P")))
    a <- pysvgcutoffClass$new(options = pysvgcutoffOptions$new(marker = "x", reference = "g",
                         positive = "P", cutoff = "2"), data = d)
    a$init()
    expect_equal(a$results$explorer$scripts, "js/pysvgcutoff.js")
    a$run()
    expect_equal(a$results$counts$asDF$n, c(3, 2, 0, 1))
    event <- a$options$option("positive"); event$value <- NULL
    a$.__enclos_env__$private$.run()
    expect_equal(a$results$counts$rowCount, 0L)
    expect_equal(a$results$explorer$content, "<div></div>")
    expect_null(a$results$staticROC$state)
    event$value <- "P"; cutoff <- a$options$option("cutoff"); cutoff$value <- "3"
    a$.__enclos_env__$private$.run()
    expect_equal(a$results$counts$asDF$n, c(2, 1, 1, 2))
    expect_match(a$results$explorer$content, "Local snapshot cutoff 3.0", fixed = TRUE)
    cutoff$value <- "bad"
    expect_error(a$.__enclos_env__$private$.run(), "finite number")
    expect_equal(a$results$explorer$content, "<div></div>")
    cutoff$value <- "2"
    a$.__enclos_env__$private$.run()
    expect_equal(a$results$counts$asDF$n, c(3, 2, 0, 1))
})
