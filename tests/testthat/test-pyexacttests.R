# Oracles: stats::fisher.test (p-values; its estimate and interval come from the same code with uniroot's
# tolerance tightened, because the default tolerance leaves visible errors), binom.test (exact McNemar),
# prop.test (Wilson limits of Newcombe's interval) and Exact::exact.test for Barnard and Boschloo (values
# pasted with their R call in tests/python/test_pyexacttests.py). Level arguments are always passed: a
# Level option has no default, so the generated wrapper makes it required.

fisherExact <- stats::fisher.test  # stats::fisher.test with every uniroot() at tol = 1e-300
body(fisherExact) <- do.call(substitute, list(body(stats::fisher.test), list(
    uniroot = quote((function(...) stats::uniroot(..., tol = 1e-300, maxiter = 10000))))))
environment(fisherExact) <- environment(stats::fisher.test)

newcombe <- function(x1, n1, x2, n2) {  # Newcombe (1998) method 10, two-sided 95%
    w1 <- suppressWarnings(stats::prop.test(x1, n1, correct = FALSE))$conf.int
    w2 <- suppressWarnings(stats::prop.test(x2, n2, correct = FALSE))$conf.int
    p1 <- x1 / n1
    p2 <- x2 / n2
    c(p1 - p2, p1 - p2 - sqrt((p1 - w1[1])^2 + (w2[2] - p2)^2), p1 - p2 + sqrt((w1[2] - p1)^2 + (p2 - w2[1])^2))
}

notesOf <- function(table) vapply(table$notes, function(note) note$note, character(1))

# group A: 7 of 12 with the event, B: 2 of 13; one row without a group and one without an outcome
df <- data.frame(
    g = factor(c(rep("A", 12), rep("B", 13), NA, "A")),
    y = factor(c(rep("yes", 7), rep("no", 5), rep("yes", 2), rep("no", 11), "yes", NA)))
trial <- matrix(c(7, 2, 5, 11), 2)  # rows A, B; columns yes, no

test_that("independent groups match fisher.test, Exact and Newcombe's interval", {
    result <- pyexacttests(data = df, group = "g", outcome = "y", event = "yes", refLevel = "B")
    table <- result$crosstab$asDF
    expect_equal(table$label, c("A", "B", "Total"))
    expect_equal(table$event, c(7, 2, 9))
    expect_equal(table$nonevent, c(5, 11, 16))
    tests <- result$tests$asDF
    expect_equal(tests$test, c("Fisher's exact test", "Barnard's exact test", "Boschloo's exact test"))
    expect_equal(tests$p[1], stats::fisher.test(trial)$p.value, tolerance = 1e-10)
    expect_equal(tests$p[2:3], c(0.0297732837751, 0.0297732837751), tolerance = 1e-10)
    effects <- result$effects$asDF
    oracle <- fisherExact(trial)
    expect_equal(c(effects$estimate[1], effects$lower[1], effects$upper[1]),
                 unname(c(oracle$estimate, oracle$conf.int)), tolerance = 1e-10)
    expect_equal(c(effects$estimate[2], effects$lower[2], effects$upper[2]), newcombe(7, 12, 2, 13),
                 tolerance = 1e-10)
})

test_that("the notes and the interpretation state the direction and the exclusions", {
    result <- pyexacttests(data = df, group = "g", outcome = "y", event = "yes", refLevel = "B")
    expect_true("2 row(s) with a missing value were excluded." %in% notesOf(result$crosstab))
    expect_true("Two-sided p-values." %in% notesOf(result$tests))
    expect_true(paste("Odds ratio = odds of yes in A divided by the odds in B; risk difference = proportion",
                      "with yes in A minus that in B.") %in% notesOf(result$effects))
    expect_match(result$summary$content, "in **A**: 7 of 12 (58.3%); in **B**: 2 of 13 (15.4%)", fixed = TRUE)
    expect_match(result$summary$content, "Fisher's exact test p = .041, Barnard's p = .030", fixed = TRUE)
    # fisher.test(trial): p = 0.041 but the 95% interval 0.903 to 93.4 contains 1; both are explained
    expect_true(any(startsWith(notesOf(result$effects),
                               "Fisher's two-sided p-value and the 95% odds-ratio interval disagree about an odds ratio of 1.")))
    expect_match(result$summary$content, "the odds-ratio interval disagree about an odds ratio of 1", fixed = TRUE)
    expect_true(any(grepl("Boschloo's p-value is never larger than Fisher's, but Barnard's can be.",
                          notesOf(result$tests), fixed = TRUE)))
})

test_that("the reference group and a one-sided alternative set the direction", {
    result <- pyexacttests(data = df, group = "g", outcome = "y", event = "yes", refLevel = "A")
    expect_equal(result$crosstab$asDF$label, c("B", "A", "Total"))
    oracle <- fisherExact(matrix(c(2, 7, 11, 5), 2))
    effects <- result$effects$asDF
    expect_equal(c(effects$estimate[1], effects$lower[1], effects$upper[1]),
                 unname(c(oracle$estimate, oracle$conf.int)), tolerance = 1e-10)

    result <- pyexacttests(data = df, group = "g", outcome = "y", event = "yes", refLevel = "B",
                           alternative = "greater", ciWidth = 90)
    expect_equal(result$tests$asDF$p[1], stats::fisher.test(trial, alternative = "greater")$p.value,
                 tolerance = 1e-10)
    oracle <- fisherExact(trial, alternative = "greater", conf.level = 0.9)
    expect_equal(result$effects$asDF$lower[1], oracle$conf.int[1], tolerance = 1e-10)
    expect_true(is.na(result$effects$asDF$upper[1]))  # infinite
    expect_true("One-sided p-values; the alternative is that yes is more likely in A than in B." %in%
                notesOf(result$tests))
})

test_that("a counts variable gives the same result as one row per subject", {
    counts <- data.frame(g = factor(c("A", "A", "B", "B")), y = factor(c("yes", "no", "yes", "no")),
                         n = c(7, 5, 2, 11))
    weighted <- pyexacttests(data = counts, group = "g", outcome = "y", counts = "n", event = "yes", refLevel = "B")
    rows <- pyexacttests(data = df, group = "g", outcome = "y", event = "yes", refLevel = "B")
    expect_equal(weighted$tests$asDF, rows$tests$asDF)
    expect_equal(weighted$effects$asDF, rows$effects$asDF)
    counts$n[2] <- 4.5
    expect_error(pyexacttests(data = counts, group = "g", outcome = "y", counts = "n", event = "yes", refLevel = "B"),
                 "whole numbers")
})

test_that("the paired design gives the exact McNemar test", {
    pairs <- data.frame(first = factor(c(rep("pos", 31), rep("neg", 18))),
                        second = factor(c(rep("pos", 20), rep("neg", 11), rep("pos", 3), rep("neg", 15))))
    result <- pyexacttests(data = pairs, group = "first", outcome = "second", event = "pos", refLevel = NULL,
                           design = "paired")
    expect_equal(result$crosstab$asDF$event, c(20, 3, 23))
    expect_equal(result$crosstab$asDF$nonevent, c(11, 15, 26))
    oracle <- stats::binom.test(11, 14, 0.5)
    expect_equal(result$tests$asDF$p, oracle$p.value, tolerance = 1e-10)
    effects <- result$effects$asDF
    expect_equal(effects$estimate, 11 / 3, tolerance = 1e-10)
    expect_equal(c(effects$lower, effects$upper), as.numeric(oracle$conf.int / (1 - oracle$conf.int)),
                 tolerance = 1e-10)
    expect_true(any(startsWith(notesOf(result$effects),
                               "Odds ratio b/c = pairs with pos only at first divided by pairs with pos only at second")))
})

test_that("degenerate tables give empty cells and a note instead of a defaulted statistic", {
    none <- data.frame(g = factor(rep(c("A", "B"), c(4, 6))), y = factor(rep("no", 10), levels = c("no", "yes")))
    result <- pyexacttests(data = none, group = "g", outcome = "y", event = "yes", refLevel = "B")
    expect_equal(result$tests$asDF$p, c(1, 1, 1))
    expect_true(is.na(result$effects$asDF$estimate[1]))
    expect_true("The odds ratio is undefined because no subject has yes." %in% notesOf(result$effects))

    concordant <- data.frame(first = factor(c("pos", "neg")), second = factor(c("pos", "neg")))
    result <- pyexacttests(data = concordant, group = "first", outcome = "second", event = "pos", refLevel = NULL,
                           design = "paired")
    expect_true(is.na(result$tests$asDF$p))
    expect_true("There are no discordant pairs, so the test and the odds ratio are undefined." %in%
                notesOf(result$tests))
})

test_that("tables larger than 2x2 are refused with the reason", {
    three <- data.frame(g = factor(c("A", "A", "B", "B")), y = factor(c("yes", "no", "maybe", "no")))
    expect_error(pyexacttests(data = three, group = "g", outcome = "y", event = "yes", refLevel = "B"),
                 "needs a 2x2 table.*Contingency Tables, whose Fisher's exact test uses R's fisher\\.test")
})

test_that("an unchosen event level lists the levels instead of guessing one", {
    analysis <- pyexacttestsClass$new(options = pyexacttestsOptions$new(group = "g", outcome = "y"), data = df)
    analysis$init()
    analysis$run()
    expect_false(analysis$errored)
    expect_equal(analysis$results$get("cpjNotice1")$content,
                 "Choose which level of y is the event: no (16 rows), yes (10 rows).")
    expect_equal(analysis$results$tests$rowCount, 0)
    expect_equal(analysis$results$console$content, "Python was not started: choose which level of y is the event.")
})

test_that("the default reference is the first level, the orientation of fisher.test(table(group, outcome))", {
    got <- pyexacttests(data = df, group = "g", outcome = "y", event = "yes", refLevel = NULL)$effects$asDF
    oracle <- fisherExact(table(df$g, df$y))  # rows A, B; columns no, yes: odds of yes in B over A
    expect_equal(got$measure[1], "Odds ratio, B vs A (conditional MLE)")
    expect_equal(got$estimate[1], unname(oracle$estimate), tolerance = 1e-10)
    expect_equal(c(got$lower[1], got$upper[1]), as.numeric(oracle$conf.int), tolerance = 1e-10)
})
