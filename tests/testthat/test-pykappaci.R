# Oracle: kappaSize::CIBinary / CI3Cats. A calculator: data = data.frame(), as in test-pyruntime.R.

notesOf <- function(table) vapply(table$notes, function(note) note$note, character(1))
ci <- function(...) pykappaci(data = data.frame(), ...)

test_that("the sample size matches kappaSize for a binary rating and every rater count", {
    skip_if_not_installed("kappaSize")
    for (r in 2:6) {
        got <- ci(raters = as.character(r))$size$asDF
        expect_equal(got$n, kappaSize::CIBinary(kappa0 = 0.6, kappaL = 0.4, kappaU = 0.8, props = 0.2,
                                                raters = r, alpha = 0.05)$n)
    }
    one <- ci(citype = "one_sided", props = "0.1", kappa0 = 0.7, kappaL = 0.5)$size$asDF
    expect_equal(one$n, kappaSize::CIBinary(kappa0 = 0.7, kappaL = 0.5, kappaU = NA, props = 0.1, raters = 2,
                                            alpha = 0.05)$n)
    expect_true(is.na(one$kappaU))
    expect_equal(one$interval, "95% one-sided")
})

test_that("three categories match kappaSize::CI3Cats", {
    skip_if_not_installed("kappaSize")
    got <- ci(outcome = "3", props = "0.2, 0.3, 0.5", raters = "4")$size$asDF
    expect_equal(got$n, kappaSize::CI3Cats(kappa0 = 0.6, kappaL = 0.4, kappaU = 0.8, props = c(0.2, 0.3, 0.5),
                                           raters = 4, alpha = 0.05)$n)
})

test_that("the notes and the interpretation say what the number promises", {
    result <- ci()
    expect_equal(result$size$asDF$n, 118)
    notes <- notesOf(result$size)
    expect_true(any(startsWith(notes, "kappaSize confidence-interval approach (Rotondi and Donner 2012)")))
    expect_true(any(startsWith(notes, "Agreement model: Donner and Eliasziw (1992).")))
    expect_match(result$summary$content, "These are expected limits, reached if the study observes kappa = 0.6",
                 fixed = TRUE)
    expect_equal(result$check$rowCount, 0)
})

test_that("the Monte Carlo check reports its seed and draws and is reproducible", {
    result <- ci(simulate = TRUE, draws = 2000, seed = 20261018)
    check <- result$check$asDF
    expect_equal(check$planned[1], 0.95)
    expect_true(is.na(check$planned[2]))
    # Exact coverage and P(within targets) by enumerating every possible study (tests/python/test_pykappaci.py)
    expect_lt(abs(check$simulated[1] - 0.94586653217667949), 4 * sqrt(0.946 * 0.054 / 2000))
    expect_lt(abs(check$simulated[2] - 0.26936920996023672), 4 * sqrt(0.269 * 0.731 / 2000))
    expect_true(any(startsWith(notesOf(result$check), "2,000 simulated studies of 118 subjects, random seed 20261018")))
    expect_match(result$summary$content, "In 2,000 simulated studies (seed 20261018)", fixed = TRUE)
    expect_equal(ci(simulate = TRUE, draws = 2000, seed = 20261018)$check$asDF, check)
})

test_that("the Monte Carlo check is not offered for more than two raters", {
    # its plug-in analysis rejects a true kappa too often there (tests/python/test_pykappaci.py)
    result <- ci(raters = "6", simulate = TRUE)
    expect_equal(result$size$asDF$n, 42)
    expect_equal(result$check$rowCount, 0)
    expect_true(any(startsWith(notesOf(result$check), "Not available for more than two raters or for 3-5 categories")))
})

test_that("unusable input is rejected with a clear message", {
    expect_error(ci(kappaL = 0.6), "must be below the anticipated kappa")
    expect_error(ci(outcome = "3"), "Enter 3 proportions")
    expect_error(ci(props = "20, 80"), "not percentages")
})
