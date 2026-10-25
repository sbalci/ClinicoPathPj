test_that("factor transport preserves ordinal status and normalizes genuine missing levels", {
    x <- ordered(c("low", NA, "high"), levels = c("low", "high"), exclude = NULL)
    col <- ClinicoPathPj:::.cpjColumn(x, "grade")
    expect_true(col$ordered)
    expect_false(anyNA(col$levels))
    expect_true(is.na(col$codes[2]))
})

test_that("pyreportcat agrees with base R categorical tables including ordered levels", {
    d <- data.frame(nominal = factor(c("NA", "High", "NA", "High", NA), levels = c("High", "NA", "unused")),
                    ordinal = ordered(c("G2", "G2", "G1", NA, "G2"), levels = c("G1", "G2", "G3")))
    got <- pyreportcat(data = d, vars = names(d))
    freq <- got$frequencies$asDF
    for (name in names(d)) {
        counts <- table(d[[name]], useNA = "no")
        if (!is.ordered(d[[name]])) counts <- counts[order(-counts)]
        rows <- freq[freq$variable == name, ]
        expect_equal(rows$level, names(counts))
        expect_equal(rows$n, as.numeric(counts))
        expect_equal(rows$validPercent, as.numeric(counts) / sum(!is.na(d[[name]])))
        expect_equal(rows$totalPercent, as.numeric(counts) / nrow(d))
    }
    expect_match(got$reportSentences$content, "equally")
})
