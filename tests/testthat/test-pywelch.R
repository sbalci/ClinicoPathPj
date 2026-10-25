# Oracle: stats::t.test(var.equal = FALSE). The Level argument is always passed: a Level option
# has no default, so the generated wrapper makes it required.

set.seed(42)
df <- data.frame(
    y = c(stats::rnorm(15, 10, 2), stats::rnorm(11, 12, 4), NA, 3),
    g = factor(c(rep("ctrl", 15), rep("trt", 11), "trt", NA), levels = c("ctrl", "trt", "unused")))

test_that("results match t.test for either reference group and a 90% interval", {
    for (reference in c("ctrl", "trt")) {
        comparison <- setdiff(c("ctrl", "trt"), reference)
        result <- pywelch(data = df, dep = "y", group = "g", refLevel = reference, ciWidth = 90)
        got <- result$test$asDF
        oracle <- stats::t.test(df$y[which(df$g == comparison)], df$y[which(df$g == reference)],
                                var.equal = FALSE, conf.level = 0.90)
        expect_equal(got$diff, unname(oracle$estimate[1] - oracle$estimate[2]), tolerance = 1e-10)
        expect_equal(c(got$lower, got$upper), as.numeric(oracle$conf.int), tolerance = 1e-10)
        expect_equal(got$t, unname(oracle$statistic), tolerance = 1e-10)
        expect_equal(got$df, unname(oracle$parameter), tolerance = 1e-10)
        expect_equal(got$p, oracle$p.value, tolerance = 1e-10)
        expect_equal(result$groups$asDF$group, c("ctrl", "trt"))  # level order, whatever the reference
    }
})

test_that("the default reference is the second level, so the sign matches jamovi's T-Test", {
    # jmv::ttestIS reports level 1 minus level 2; stats::t.test(x = level 1, y = level 2) is the same
    got <- pywelch(data = df, dep = "y", group = "g", refLevel = NULL)$test$asDF
    oracle <- stats::t.test(df$y[which(df$g == "ctrl")], df$y[which(df$g == "trt")], var.equal = FALSE)
    expect_equal(got$t, unname(oracle$statistic), tolerance = 1e-10)
    expect_equal(got$diff, unname(oracle$estimate[1] - oracle$estimate[2]), tolerance = 1e-10)
})

test_that("the interpretation states direction, size, interval and test", {
    result <- pywelch(data = df, dep = "y", group = "g", refLevel = NULL)
    oracle <- stats::t.test(df$y[which(df$g == "ctrl")], df$y[which(df$g == "trt")], var.equal = FALSE)
    text <- result$summary$content
    direction <- if (oracle$estimate[1] > oracle$estimate[2]) "higher" else "lower"
    expect_match(text, paste0("^Mean y was [0-9.]+ ", direction, " in ctrl than in trt"))
    expect_match(text, sprintf("Welch t\\(%.1f\\) = %.2f", oracle$parameter, oracle$statistic))
})

test_that("the group-means plot holds each mean with its t interval and renders", {
    analysis <- pywelchClass$new(options = pywelchOptions$new(dep = "y", group = "g", refLevel = NULL), data = df)
    analysis$init()
    analysis$run()
    state <- analysis$results$means$state
    expect_equal(state$kind, "interval")
    expect_equal(state$data$label, c("ctrl", "trt"))
    ctrl <- stats::t.test(df$y[which(df$g == "ctrl")])
    expect_equal(c(state$data$lower[1], state$data$upper[1]), as.numeric(ctrl$conf.int), tolerance = 1e-10)
    grDevices::png(tempfile(fileext = ".png"))
    on.exit(grDevices::dev.off(), add = TRUE)
    expect_true(analysis$.__enclos_env__$private$.plot(analysis$results$means,
        ggtheme = ggplot2::theme_grey(), theme = list(palette = "jmv")))
})

test_that("group descriptives drop rows with a missing outcome or group", {
    groups <- pywelch(data = df, dep = "y", group = "g", refLevel = "ctrl")$groups$asDF
    expect_equal(groups$n, c(15, 11))
    expect_equal(groups$mean, c(mean(df$y[1:15]), mean(df$y[16:26])), tolerance = 1e-10)
    expect_equal(groups$sd[2], stats::sd(df$y[16:26]), tolerance = 1e-10)
})

notesOf <- function(table) vapply(table$notes, function(note) note$note, character(1))

test_that("the notes state the direction, the interval level and the exclusions", {
    notes <- notesOf(pywelch(data = df, dep = "y", group = "g", refLevel = "trt", ciWidth = 90)$test)
    expect_true(any(startsWith(notes, "Mean difference = ctrl minus trt; 90% confidence interval; two-sided p")))
    expect_true("2 row(s) with a missing outcome or group were excluded." %in% notes)
})

test_that("constant groups give no defaulted df, p or interval", {
    # scipy reports df = 1 (p '< .001', zero-width CI) where stats::t.test refuses the data
    for (y in list(c(0, 0, 0, 100, 100, 100), rep(0, 6), (1:6) * 1e-300)) {
        d <- data.frame(y = y, g = factor(rep(c("a", "b"), each = 3)))
        result <- pywelch(data = d, dep = "y", group = "g", refLevel = "a")
        got <- result$test$asDF
        expect_equal(got$diff, mean(y[4:6]) - mean(y[1:3]))
        expect_true(all(is.na(unlist(got[c("lower", "upper", "t", "df", "p")]))))
        expect_true(any(startsWith(notesOf(result$test), "t, df, p and the confidence interval are undefined")))
    }
})

test_that("one constant group is a valid test without a precision warning", {
    d <- data.frame(y = c(0.5, 0.5, 0.5, 0.5, 1.2, 3.4, 2.2, 5.1), g = factor(rep(c("ctrl", "case"), each = 4)))
    analysis <- pywelchClass$new(options = pywelchOptions$new(dep = "y", group = "g", refLevel = "ctrl"), data = d)
    analysis$init()
    analysis$run()
    oracle <- stats::t.test(d$y[5:8], d$y[1:4], var.equal = FALSE)
    expect_equal(analysis$results$test$asDF$p, oracle$p.value, tolerance = 1e-10)
    expect_null(analysis$results$get("cpjNotice1"))
})

test_that("an integer Nominal outcome is analysed by its values", {
    d <- data.frame(y = c(1, 4, 2, 5, 3, 8, 6, 9), g = factor(rep(c("a", "b"), each = 4)))
    f <- factor(d$y)
    attr(f, "values") <- as.integer(levels(f))
    d$y <- I(f)
    got <- pywelch(data = d, dep = "y", group = "g", refLevel = "a")$test$asDF
    oracle <- stats::t.test(c(3, 8, 6, 9), c(1, 4, 2, 5), var.equal = FALSE)
    expect_equal(got$t, unname(oracle$statistic), tolerance = 1e-10)
})

test_that("a later run does not keep an earlier run's console text or interpretation", {
    # jamovi's engine calls init -> .load (restore saved state) -> postInit -> run. .load() restores
    # Preformatted and Text content even after an option change; it only marks it stale.
    state <- tempfile(fileext = ".pb")
    engineRun <- function(..., checkpoint = NULL) {
        options <- utils::modifyList(list(dep = "y", group = "g", refLevel = "ctrl", showConsole = TRUE), list(...))
        analysis <- pywelchClass$new(options = do.call(pywelchOptions$new, options),
            datasetId = "test", analysisId = 1L, revision = 1L)
        analysis$.setReadDatasetSource(function(columns, ...) df[unlist(columns)])
        analysis$.setReadDatasetHeaderSource(function(columns, ...) df[0, unlist(columns), drop = FALSE])
        analysis$.setStatePathSource(function() state)
        if (!is.null(checkpoint)) analysis$.setCheckpoint(checkpoint)
        analysis$init(noThrow = TRUE)
        analysis$.load()
        analysis$postInit(noThrow = TRUE)
        analysis$run(noThrow = TRUE)
        analysis$.save()
        analysis
    }
    first <- engineRun()
    expect_match(first$results$console$content, "Status: ok.", fixed = TRUE)
    expect_true(nzchar(first$results$summary$content))
    # a run that ends before Python answers (an error, as at the time limit) shows no earlier report
    stopped <- engineRun(checkpoint = function(...) stop("stopped early"))
    expect_true(stopped$errored)
    expect_equal(stopped$results$console$content, "No report from Python: the run stopped with the error shown above.")
    second <- engineRun()
    expect_false(second$errored)
    expect_true(nzchar(second$results$summary$content))
    third <- engineRun(group = NULL, refLevel = NULL)  # Group emptied: the bridge returns before Python
    expect_false(third$errored)
    expect_equal(third$results$summary$content, "")
    expect_equal(third$results$console$content, "Python was not started: choose Group.")
})

test_that("the console reports every run, also when the analysis prints nothing", {
    small <- data.frame(y = c(1, 2, 3, 4, 6, 8, 7, 9), g = factor(rep(c("a", "b"), each = 4)))
    analysis <- pywelchClass$new(options = pywelchOptions$new(dep = "y", group = "g", refLevel = NULL,
                                                              showConsole = TRUE), data = small)
    analysis$init()
    analysis$run()
    lines <- strsplit(analysis$results$console$content, "\n")[[1]]
    expect_match(lines[1], "^pywelch [0-9.]+: Python 3\\.[0-9]+\\.[0-9]+, numpy [0-9.]+, scipy [0-9.]+$")
    expect_equal(lines[2], "Interpreter: /Applications/jamovi.app/Contents/MacOS/python")
    expect_equal(lines[3], 'Data received: 8 rows; "y" (number); "g" (factor, 2 levels: ["a", "b"])')
    expect_match(lines[4], '^Options received: \\{"dep": "y", "group": "g", "refLevel": null, ')
    expect_match(lines[5], "^Status: ok\\. run\\(\\) took [0-9.]+ s, including its scipy import; ")
    expect_equal(lines[6:7], c("----- Python output -----", "(the analysis printed nothing)"))

    tiny <- pywelchClass$new(options = pywelchOptions$new(dep = "y", group = "g", refLevel = NULL,
                                                          showConsole = TRUE), data = small[1:5, ])
    tiny$init()
    tiny$run(noThrow = TRUE)
    expect_true(tiny$errored)
    expect_match(tiny$results$console$content, "Status: input error.", fixed = TRUE)

    infinite <- small
    infinite$y[2] <- Inf  # refused in R, before Python starts
    refused <- pywelchClass$new(options = pywelchOptions$new(dep = "y", group = "g", refLevel = NULL,
                                                             showConsole = TRUE), data = infinite)
    refused$init()
    refused$run(noThrow = TRUE)
    expect_true(refused$errored)
    expect_equal(refused$results$console$content, "No report from Python: the run stopped with the error shown above.")

    # nothing chosen; an empty frame, because jmvcore::select() fails on data with no chosen variable
    none <- pywelchClass$new(options = pywelchOptions$new(showConsole = TRUE), data = data.frame())
    none$init()
    none$run()
    expect_equal(none$results$console$content, "Python was not started: choose Outcome, Group.")
})

test_that("an unset reference ignores unused levels when choosing the second level", {
    notes <- notesOf(pywelch(data = df, dep = "y", group = "g", refLevel = NULL)$test)
    expect_true(any(startsWith(notes, "Mean difference = ctrl minus trt;")))  # 'unused' is never chosen
})

test_that("unusable input is rejected with a clear message", {
    expect_error(pywelch(data = df, dep = "y", group = "g", refLevel = "unused"), "has no observations")
    three <- df
    three$g[1:3] <- "unused"
    expect_error(pywelch(data = three, dep = "y", group = "g", refLevel = NULL), "exactly two groups")
    tiny <- data.frame(y = c(1, 2, 3), g = factor(c("a", "b", "b")))
    expect_error(pywelch(data = tiny, dep = "y", group = "g", refLevel = NULL), "at least two observations")
})

test_that("a partly configured analysis says what is missing instead of failing", {
    analysis <- pywelchClass$new(options = pywelchOptions$new(dep = "y"), data = df)
    analysis$init()
    analysis$run()
    expect_false(analysis$errored)
    expect_match(analysis$results$get("cpjNotice1")$content, "also choose: Group")
    expect_equal(analysis$results$test$rowCount, 0)
})
