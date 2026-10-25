# Oracle: base R. numpy's default percentile is R's quantile(type = 7).

set.seed(20261018)
df <- data.frame(
    a = c(stats::rnorm(30, 50, 10), NA, NA),
    `Ki-67 (%)` = c(stats::runif(31, 0, 100), NA),
    const = rep(7, 32),
    check.names = FALSE)

test_that("statistics match base R for each variable", {
    table <- pydescriptives(data = df, vars = names(df))$desc$asDF
    expect_equal(table$variable, names(df))
    for (name in names(df)) {
        row <- table[table$variable == name, ]
        x <- df[[name]]
        observed <- x[!is.na(x)]
        expect_equal(row$n, length(observed))
        expect_equal(row$missing, sum(is.na(x)))
        expect_equal(row$mean, mean(observed), tolerance = 1e-10)
        expect_equal(row$sd, stats::sd(observed), tolerance = 1e-10)
        expect_equal(c(row$min, row$q1, row$median, row$q3, row$max),
                     unname(stats::quantile(observed, c(0, 0.25, 0.5, 0.75, 1), type = 7)),
                     tolerance = 1e-10)
    }
})

test_that("a single selected variable still reaches Python as a list", {
    table <- pydescriptives(data = df, vars = "a")$desc$asDF
    expect_equal(table$variable, "a")  # a bare string would be iterated letter by letter
})

test_that("variables without enough values give empty cells and a note", {
    sparse <- data.frame(none = c(NA_real_, NA_real_), one = c(3, NA))
    result <- pydescriptives(data = sparse, vars = c("none", "one"))
    table <- result$desc$asDF
    expect_equal(table$n, c(0, 1))
    expect_true(is.na(table$mean[1]))
    expect_equal(table$mean[2], 3)
    expect_true(is.na(table$sd[2]))
    text <- result$desc$asString()
    expect_match(text, "without observed values")
    expect_match(text, "at least two observed values")
})

test_that("integer Nominal/Ordinal columns are analysed as numbers, not as factor codes", {
    # jamovi passes such columns as factors carrying their values; values differ from the codes here
    values <- c(10, 30, 20, NA, 30, 10)
    for (ordered in c(FALSE, TRUE)) {
        f <- factor(values, ordered = ordered)
        attr(f, "values") <- c(10L, 20L, 30L)
        row <- pydescriptives(data = data.frame(score = I(f)), vars = "score")$desc$asDF
        observed <- values[!is.na(values)]
        expect_equal(row$n, length(observed))
        expect_equal(row$mean, mean(observed), tolerance = 1e-10)
        expect_equal(row$sd, stats::sd(observed), tolerance = 1e-10)
        expect_equal(row$median, stats::median(observed), tolerance = 1e-10)
    }
})

test_that("nothing selected means no Python run and no error", {
    # Not through the wrapper: given data = df and no variables, jmvcore::select() fails on a frame
    # with rows but no columns ("invalid 'row.names' length") before .run(). jamovi's engine reads
    # its data with readDataset() instead and never calls select(), so the GUI does not hit that.
    analysis <- pydescriptivesClass$new(options = pydescriptivesOptions$new(vars = NULL), data = data.frame())
    analysis$init()
    analysis$run()
    expect_false(analysis$errored)
    expect_equal(analysis$results$desc$rowCount, 0)
})
