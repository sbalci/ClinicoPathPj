# Independent numerical references for the six Python cores; run against an installed package.
test_that("both diagnostic interfaces agree with base R and epiR", {
    tp <- 90L; fp <- 30L; fn <- 20L; tn <- 80L
    d <- data.frame(reference = factor(c(rep("P", tp + fn), rep("N", fp + tn))),
                    test = factor(c(rep("+", tp), rep("-", fn), rep("+", fp), rep("-", tn))))
    a <- pydecision(data = d, reference = "reference", test = "test",
                    referencePositive = "P", testPositive = "+", ciWidth = 90)
    b <- pydecisioncalculator(tp = tp, fp = fp, fn = fn, tn = tn, ciWidth = 90)
    expect_equal(a$counts$asDF, b$counts$asDF)
    expect_equal(a$accuracy$asDF, b$accuracy$asDF)
    expect_equal(a$ratios$asDF, b$ratios$asDF)
    got <- b$accuracy$asDF
    for (i in seq_len(5)) {
        x <- c(tp, tn, tp, tn, tp + tn)[i]
        n <- c(tp + fn, tn + fp, tp + fp, tn + fn, tp + fp + fn + tn)[i]
        ref <- stats::binom.test(x, n, conf.level = .90)
        expect_equal(got$estimate[i], x / n)
        expect_equal(c(got$lower[i], got$upper[i]), as.numeric(ref$conf.int), tolerance = 1e-10)
    }
    skip_if_not_installed("epiR")
    ref <- epiR::epi.tests(matrix(c(tp, fp, fn, tn), 2, byrow = TRUE), method = "exact", conf.level = .90)$detail
    select <- match(c("se", "sp", "pv.pos", "pv.neg", "diag.ac"), ref$statistic)
    expect_equal(got$estimate, ref$est[select], tolerance = 1e-10)
    expect_equal(got$lower, ref$lower[select], tolerance = 1e-10)
    expect_equal(got$upper, ref$upper[select], tolerance = 1e-10)
    select <- match(c("lr.pos", "lr.neg", "diag.or", "youden"), ref$statistic)
    expect_equal(b$ratios$asDF$estimate, ref$est[select], tolerance = 1e-10)
})

test_that("the bridge excludes genuine NA factor levels but preserves literal NA labels", {
    missing <- factor(c("N", "P", NA), exclude = NULL)
    encoded <- ClinicoPathPj:::.cpjColumn(missing, "reference")
    expect_true(is.na(encoded$codes[3]))
    literal <- factor(c("N", "NA", NA), levels = c("N", "NA"))
    encoded <- ClinicoPathPj:::.cpjColumn(literal, "test")
    expect_equal(encoded$codes[2], 1L)
    expect_equal(as.character(encoded$levels[2]), "NA")
    d <- data.frame(r = missing, t = factor(c("N", "P", "P")))
    a <- pydecision(data = d, reference = "r", test = "t", referencePositive = "P", testPositive = "P")
    expect_equal(a$counts$asDF$n, c(1, 0, 0, 1))
})

test_that("sequential strategies match independent outcome-pattern enumeration", {
    a <- pysequentialtests(sens1 = .73, spec1 = .91, sens2 = .84, spec2 = .88,
                           prevalence = .17, populationSize = 137L, cost1 = 3, cost2 = 11, showCosts = TRUE)
    patterns <- expand.grid(disease = c(FALSE, TRUE), first = c(FALSE, TRUE), second = c(FALSE, TRUE))
    patterns$conditional <- with(patterns,
        ifelse(first, ifelse(disease, .73, .09), ifelse(disease, .27, .91)) *
        ifelse(second, ifelse(disease, .84, .12), ifelse(disease, .16, .88)))
    for (i in 1:3) {
        positive <- if (i == 1) with(patterns, first & second) else with(patterns, first | second)
        se <- sum(patterns$conditional[patterns$disease & positive])
        sp <- sum(patterns$conditional[!patterns$disease & !positive])
        retested <- if (i == 1) patterns$first else if (i == 2) !patterns$first else rep(TRUE, 8)
        share <- sum(patterns$conditional * ifelse(patterns$disease, .17, .83) * retested)
        expect_equal(a$strategies$asDF$sensitivity[i], se)
        expect_equal(a$strategies$asDF$specificity[i], sp)
        expect_equal(a$workload$asDF$secondTests[i], 137 * share)
        expect_equal(a$costs$asDF$total[i], 137 * (3 + 11 * share))
    }
})

test_that("contingency counts residuals adjustments and pairwise tests match stats", {
    tab <- matrix(c(12, 20, 5, 7, 14, 18, 21, 3, 8), 3, byrow = TRUE)
    d <- expand.grid(r = factor(c("A", "B", "C")), c = factor(c("X", "Y", "Z")))
    d$w <- as.vector(tab)
    ref <- suppressWarnings(stats::chisq.test(tab, correct = FALSE))
    for (method in c("bonferroni", "holm", "bh")) {
        a <- pychisqposttest(data = d, rows = "r", cols = "c", counts = "w", adjustment = method)
        overall <- a$overall$asDF
        expect_equal(overall$statistic, as.numeric(ref$statistic))
        expect_equal(overall$p, ref$p.value)
        expect_equal(overall$cramersV, sqrt(as.numeric(ref$statistic) / (sum(tab) * 2)))
        expect_equal(a$cells$asDF$expected, as.vector(t(ref$expected)))
        expect_equal(a$cells$asDF$residual, as.vector(t(ref$stdres)))
        cell_p <- as.vector(t(2 * stats::pnorm(-abs(ref$stdres))))
        expect_equal(a$cells$asDF$adjusted, stats::p.adjust(cell_p, "bonferroni"))
        pairs <- a$pairs$asDF
        oracle <- c(apply(combn(3, 2), 2, function(k) {
            stats::chisq.test(tab[k, ], correct = FALSE)$p.value
        }), apply(combn(3, 2), 2, function(k) {
            stats::chisq.test(tab[, k], correct = FALSE)$p.value
        }))
        expect_equal(pairs$p, unname(oracle))
        expect_equal(pairs$adjusted, stats::p.adjust(oracle, if (method == "bh") "BH" else method))
    }
    tab <- matrix(c(1, 0, 0, 1, 0, 5), 3, byrow = TRUE)
    d <- expand.grid(r = factor(c("A", "B", "C")), c = factor(c("X", "Y")))
    d$w <- as.vector(tab)
    pairs <- pychisqposttest(data = d, rows = "r", cols = "c", counts = "w")$pairs$asDF
    expect_equal(pairs$p, c(stats::fisher.test(tab[1:2, ])$p.value,
                           stats::fisher.test(tab[c(1, 3), ])$p.value))
    expect_true(all(pairs$method == "Fisher exact (2x2)"))
})

test_that("Benford digits statistics and MAD match independent fixtures and the R package", {
    x <- c(.3, 1, 20, 333, 4444, 55555)
    for (digits in 1:3) {
        a <- pybenford(data = data.frame(x = x), measurement = "x", digits = digits)
        categories <- seq.int(10^(digits - 1), 10^digits - 1)
        leading <- c(3, 1, 2, 3, 4, 5) * 10^(digits - 1)
        if (digits == 2) leading <- c(30, 10, 20, 33, 44, 55)
        if (digits == 3) leading <- c(300, 100, 200, 333, 444, 555)
        observed <- tabulate(match(leading, categories), nbins = length(categories))
        p <- log10(1 + 1 / categories)
        ref <- suppressWarnings(stats::chisq.test(observed, p = p))
        expect_equal(a$frequencies$asDF$observed, as.integer(observed))
        expect_equal(a$test$asDF$statistic, as.numeric(ref$statistic), tolerance = 1e-10)
        expect_equal(a$test$asDF$mad, mean(abs(observed / length(x) - p)), tolerance = 1e-10)
        if (requireNamespace("benford.analysis", quietly = TRUE)) {
            oracle <- benford.analysis::benford(x, number.of.digits = digits)
            expect_equal(a$frequencies$asDF$observed, as.integer(oracle$bfd$data.dist.freq))
            expect_equal(a$test$asDF$mad, as.numeric(oracle$MAD), tolerance = 1e-10)
        }
    }
})

test_that("decision curves use common complete cases and match dcurves at exact ties", {
    d <- data.frame(y = factor(c("N", "N", "P", "N", "P", "P", "P")),
                    p = c(.05, .1, .15, .2, .5, .9, NA), q = c(.1, NA, .2, .3, .6, .8, .9))
    a <- pydecisioncurve(data = d, outcome = "y", positive = "P", models = c("p", "q"),
                         thresholdMin = .05, thresholdMax = .5, thresholdStep = .1)
    expect_equal(a$cohort$asDF$n, 5L)
    got <- a$curves$asDF
    complete <- d[stats::complete.cases(d), ]
    y <- complete$y == "P"
    for (m in c("p", "q")) {
        part <- got[got$model == paste0("Model: ", m), ]
        for (i in seq_len(nrow(part))) {
            t <- part$threshold[i]
            positive <- complete[[m]] >= t
            nb <- (sum(y & positive) - sum(!y & positive) * t / (1 - t)) / length(y)
            expect_equal(part$netBenefit[i], nb)
        }
    }
    skip_if_not_installed("dcurves")
    complete$event <- as.integer(y)
    thresholds <- sort(unique(got$threshold))
    ref <- dcurves::dca(event ~ p + q, data = complete, thresholds = thresholds)$dca
    for (m in c("p", "q", "all", "none")) {
        label <- if (m == "all") "Reference: treat all" else if (m == "none") "Reference: treat none" else paste0("Model: ", m)
        expect_equal(got$netBenefit[got$model == label], ref$net_benefit[ref$variable == m], tolerance = 1e-10)
    }
})

test_that("native plots render from saved state without access to source data", {
    analyses <- list(
        pybenfordClass$new(options = pybenfordOptions$new(measurement = "x", digits = 2L), data = data.frame(x = c(1, 20, 333))),
        pydecisioncurveClass$new(options = pydecisioncurveOptions$new(outcome = "y", positive = "P", models = c("p")),
            data = data.frame(y = factor(c("N", "P", "P")), p = c(.1, .5, .8))),
        pysequentialtestsClass$new(options = pysequentialtestsOptions$new(), data = data.frame()))
    names <- c("digitPlot", "netBenefitPlot", "accuracyPlot")
    for (i in seq_along(analyses)) {
        analysis <- analyses[[i]]
        analysis$init(); analysis$run()
        element <- analysis$results$get(names[i])
        state <- unserialize(serialize(element$state, NULL))
        expect_gt(nrow(state$data), 0)
        target <- tempfile(fileext = ".png")
        grDevices::png(target, width = 800, height = 500)
        expect_true(ClinicoPathPj:::.cpjPlot(list(state = state), ggplot2::theme_grey(), list(palette = "jmv")))
        grDevices::dev.off()
        expect_gt(file.info(target)$size, 1000)
    }
})
