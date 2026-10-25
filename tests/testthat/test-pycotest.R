# Oracle: the textbook formulas, written here independently of the Python code. Gardner et al.'s
# conditional covariances (Prev Vet Med 2000;45:107-122), truncated to their Frechet bounds, and
# Bayes' theorem on the joint 2x2 tables. pycotest is a calculator: it reads no data and has no
# Level option, so no Level argument is passed.

gardner <- function(se1, sp1, se2, sp2, prev, phiD = 0, phiN = 0) {
    vD <- sqrt(se1 * (1 - se1) * se2 * (1 - se2))
    vN <- sqrt(sp1 * (1 - sp1) * sp2 * (1 - sp2))
    bD <- c(max(-se1 * se2, -(1 - se1) * (1 - se2)), min(se1 * (1 - se2), se2 * (1 - se1)))
    bN <- c(max(-(1 - sp1) * (1 - sp2), -sp1 * sp2), min((1 - sp1) * sp2, sp1 * (1 - sp2)))
    covD <- min(max(phiD * vD, bD[1]), bD[2])
    covN <- min(max(phiN * vN, bN[1]), bN[2])
    D <- c(se1 * se2 + covD, se1 * (1 - se2) - covD, (1 - se1) * se2 - covD, (1 - se1) * (1 - se2) + covD)
    N <- c((1 - sp1) * (1 - sp2) + covN, (1 - sp1) * sp2 - covN, sp1 * (1 - sp2) - covN, sp1 * sp2 + covN)
    pD <- c(1 - D[4], D[2], D[3], D[1], D[4])  # either positive, test 1 only, test 2 only, both, neither
    pN <- c(1 - N[4], N[2], N[3], N[1], N[4])
    post <- prev * pD / (prev * pD + (1 - prev) * pN)
    list(lr = pD / pN, odds = prev / (1 - prev) * pD / pN, post = post, phi = c(covD / vD, covN / vN))
}

notesOf <- function(table) vapply(table$notes, function(note) note$note, character(1))
noticesOf <- function(results) {
    names <- Filter(function(name) startsWith(name, "cpjNotice"), results$itemNames)
    vapply(names, function(name) results$get(name)$content, character(1), USE.NAMES = FALSE)
}
# asDF leaves out hidden columns, and the exact probabilities behind the formatted text columns are hidden
allColumns <- function(table) as.data.frame(lapply(table$columns, function(column) unlist(as.list(column), use.names = FALSE)))
plainText <- function(markdown) gsub("\\", "", markdown, fixed = TRUE)  # the summary escapes all punctuation

test_that("post-test probabilities match the closed form, independent or dependent", {
    cases <- list(
        list(args = list(indep = TRUE), oracle = gardner(.80, .90, .75, .95, .10)),
        list(args = list(), oracle = gardner(.80, .90, .75, .95, .10, .05, .05)),
        list(args = list(sens1 = .95, spec1 = .85, sens2 = .70, spec2 = .95, prevalence = .05,
                         depPos = .15, depNeg = .10),
             oracle = gardner(.95, .85, .70, .95, .05, .15, .10)),
        list(args = list(sens2 = .70, prevalence = .20, depPos = -.50, depNeg = .10),
             oracle = gardner(.80, .90, .70, .95, .20, -.50, .10)))
    for (case in cases) {
        result <- do.call(pycotest, c(list(data = data.frame()), case$args))
        got <- allColumns(result$posttest)
        expect_equal(got$prob, case$oracle$post, tolerance = 1e-10)
        expect_equal(got$lr, case$oracle$lr, tolerance = 1e-10)
        expect_equal(got$odds, case$oracle$odds, tolerance = 1e-10)
        expect_equal(result$dependence$asDF$fitted, case$oracle$phi, tolerance = 1e-10)
    }
    # the umbrella's exact fractions under independence
    expect_equal(allColumns(pycotest(data = data.frame(), indep = TRUE)$posttest)$prob,
                 c(190 / 451, 40 / 211, 10 / 37, 120 / 129, 10 / 1549), tolerance = 1e-10)
    params <- pycotest(data = data.frame())$params$asDF
    expect_equal(params$plr, c(8, 15), tolerance = 1e-10)
    expect_equal(params$nlr, c(2 / 9, 5 / 19), tolerance = 1e-10)
})

test_that("an unattainable correlation is truncated, reported and explained", {
    result <- pycotest(data = data.frame(), spec1 = .99, spec2 = .90, depNeg = .40)
    oracle <- gardner(.80, .99, .75, .90, .10, .05, .40)
    got <- allColumns(result$posttest)
    expect_equal(got$prob, oracle$post, tolerance = 1e-10)  # test 1 only: probability 1 by construction
    expect_true(is.na(got$lr[2]) && is.na(got$odds[2]))  # infinite, so not shown as a number
    expect_equal(result$dependence$asDF$fitted, oracle$phi, tolerance = 1e-10)
    expect_true(any(startsWith(noticesOf(result),
        "The correlation (phi) entered for subjects without disease, 0.4, is not attainable with these specificities")))
    expect_true(any(startsWith(notesOf(result$posttest),
        "Test 1 Positive Only: under the dependence entered this combination of results cannot occur in subjects without disease, so its probability is 1 by construction, not an estimate")))
    # just beyond the limit (raw 0.7507 against 0.75) is still a truncation
    near <- pycotest(data = data.frame(), depPos = .87)
    expect_equal(allColumns(near$posttest)$prob, gardner(.80, .90, .75, .95, .10, .87, .05)$post, tolerance = 1e-10)
    expect_true(any(startsWith(noticesOf(near),
        "The correlation (phi) entered for subjects with disease, 0.87, is not attainable with these sensitivities (attainable range -0.289 to 0.866)")))
})

test_that("a combination impossible in both groups has no post-test probability", {
    result <- pycotest(data = data.frame(), depPos = .90, depNeg = .90)
    got <- allColumns(result$posttest)
    expect_true(all(is.na(unlist(got[3, c("prob", "relative", "odds", "lr")]))))
    expect_equal(got$prob[c(1, 2, 4)], c(8 / 17, 0.10, 0.625), tolerance = 1e-10)
    expect_true(any(startsWith(notesOf(result$posttest),
        "Test 2 Positive Only: under the dependence entered this combination of results cannot occur in either group")))
})

test_that("intervals state their seed and draws and match the Jeffreys closed form", {
    # only the prevalence is uncertain: each limit is the post-test probability at a Beta quantile
    result <- pycotest(data = data.frame(), indep = TRUE, ci = TRUE, nPrev = 200)
    got <- allColumns(result$intervals)
    lr <- gardner(.80, .90, .75, .95, .10)$lr
    a <- .10 * 200 + .5
    b <- .90 * 200 + .5
    q <- qbeta(c(.025, .975), a, b)
    f <- function(p) p * lr / (p * lr + 1 - p)
    se <- function(p) sqrt(.025 * .975 / 20000) * lr / (p * lr + 1 - p)^2 / dbeta(p, a, b)  # Monte Carlo error
    expect_length(got$lower, 5)  # all() over an absent column would pass
    expect_true(all(abs(got$lower - f(q[1])) <= 4 * se(q[1])))
    expect_true(all(abs(got$upper - f(q[2])) <= 4 * se(q[2])))
    notes <- notesOf(result$intervals)
    expect_true(startsWith(notes[1], "95% percentile intervals over 20000 Monte Carlo draws (seed 1; numpy "))
    expect_match(notes[2], "Jeffreys posterior Beta(x + 0.5, n - x + 0.5)", fixed = TRUE)
    expect_match(notes[2], "Held at the entered value (n = 0): Test 1 sensitivity", fixed = TRUE)
    again <- allColumns(pycotest(data = data.frame(), indep = TRUE, ci = TRUE, nPrev = 200)$intervals)
    expect_identical(again$lower, got$lower)  # the seed reproduces the draws
})

test_that("draws at which the fixed correlations are not attainable are discarded and counted", {
    result <- pycotest(data = data.frame(), ci = TRUE, nSens1 = 40, nSpec1 = 60, nSens2 = 40, nSpec2 = 80,
                       nPrev = 200, depPos = .60, depNeg = .50)
    notes <- notesOf(result$intervals)
    discard <- notes[grepl("were discarded", notes, fixed = TRUE)]
    expect_length(discard, 1)
    count <- as.integer(sub(" of .*", "", discard))
    # an R Monte Carlo of the same model with 4e6 draws discarded 24.40455%
    expect_lte(abs(count / 20000 - 0.2440455), 4 * sqrt(0.2440455 * (1 - 0.2440455) / 20000))
    expect_true(any(endsWith(notes, "The correlations (phi) were held fixed at the entered values.")))
    expect_false(anyNA(allColumns(result$intervals)$lower))
    # accepted and requested draws, so the seed and the draws option reproduce the result
    expect_true(startsWith(notes[1], paste0("95% percentile intervals over ", 20000 - count,
                                            " of 20000 Monte Carlo draws (seed 1; numpy ")))
    expect_match(plainText(result$summary$content),
                 "the correlations were held fixed, and draws at which they are not attainable were discarded.", fixed = TRUE)
})

test_that("intervals are withheld, with the reason, when there is nothing to propagate", {
    result <- pycotest(data = data.frame(), ci = TRUE)
    expect_true(all(is.na(allColumns(result$intervals)$lower)))
    expect_true(startsWith(notesOf(result$intervals)[1], "No interval was computed: every sample size is 0"))
})

test_that("the plot holds each probability with its interval and the prevalence, and renders", {
    analysis <- pycotestClass$new(
        options = pycotestOptions$new(indep = TRUE, ci = TRUE, nPrev = 200, showPlot = TRUE), data = data.frame())
    analysis$init()
    analysis$run()
    state <- analysis$results$probPlot$state
    expect_equal(state$kind, "interval")
    expect_equal(state$reference, 10, tolerance = 1e-10)
    expect_equal(state$data$estimate, 100 * gardner(.80, .90, .75, .95, .10)$post, tolerance = 1e-10)
    expect_equal(state$data$lower, 100 * allColumns(analysis$results$intervals)$lower, tolerance = 1e-10)
    grDevices::png(tempfile(fileext = ".png"))
    on.exit(grDevices::dev.off(), add = TRUE)
    expect_true(analysis$.__enclos_env__$private$.plot(analysis$results$probPlot,
        ggtheme = ggplot2::theme_grey(), theme = list(palette = "jmv")))
})

test_that("names label the tables and the interpretation states the numbers and the model", {
    result <- pycotest(data = data.frame(), name1 = "HPV", name2 = "Pap")
    expect_equal(result$params$asDF$test, c("HPV", "Pap"))
    expect_equal(result$posttest$asDF$scenario[2:3], c("HPV Positive Only", "Pap Positive Only"))
    text <- plainText(result$summary$content)
    expect_match(text, paste("Co-testing with HPV (sensitivity 80%, specificity 90%) and Pap (sensitivity 75%,",
                             "specificity 95%) at a pre-test probability of 10.0% gave calculated post-test",
                             "probabilities of disease of 42.5% after a positive result on either test"), fixed = TRUE)
    expect_match(text, "These dependence values are the analysis defaults, not estimates from data.", fixed = TRUE)
    expect_true(any(startsWith(notesOf(result$posttest),
        "Sensitivity, specificity and prevalence are treated as exact, so these post-test probabilities carry no uncertainty interval.")))
})

test_that("checks on the entered values are shown as notices", {
    expect_true(any(startsWith(noticesOf(pycotest(data = data.frame(), sens1 = .20, spec1 = .30, indep = TRUE)),
                               "Test 1 is below the chance diagonal")))
    expect_true(any(startsWith(noticesOf(pycotest(data = data.frame(), prevalence = .02)), "Low prevalence (below 5%)")))
    expect_length(noticesOf(pycotest(data = data.frame())), 0)
    expect_true(any(grepl("not the figure from the study that validated the test",
                          notesOf(pycotest(data = data.frame())$params), fixed = TRUE)))
})
