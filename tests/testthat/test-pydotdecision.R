test_that("applied cutoff counts and exact intervals match base R", {
    d <- data.frame(x = c(1, 2, 2, 4, 5, 6, NA, 9),
                    g = factor(c("N", "N", "P", "N", "P", "P", "P", NA)))
    got <- pydotdecision(data = d, marker = "x", reference = "g", positive = "P", cutoff = "2")
    expect_equal(got$counts$asDF$n, c(3, 2, 0, 1))
    m <- got$metrics$asDF
    for (i in seq_len(5)) {
        numerator <- c(3, 1, 3, 1, 4)[i]
        denominator <- c(3, 3, 5, 1, 6)[i]
        oracle <- stats::binom.test(numerator, denominator)
        expect_equal(m$estimate[i], numerator / denominator)
        expect_equal(c(m$lower[i], m$upper[i]), as.numeric(oracle$conf.int), tolerance = 1e-10)
    }
    expect_match(got$explorer$content, "Apply cutoff", fixed = TRUE)
})
