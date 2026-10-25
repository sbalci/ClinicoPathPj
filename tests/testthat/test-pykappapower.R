# Oracle: kappaSize::PowerBinary / Power3Cats. A calculator: data = data.frame(), as in test-pyruntime.R.

notesOf <- function(table) vapply(table$notes, function(note) note$note, character(1))
kpower <- function(...) pykappapower(data = data.frame(), ...)

test_that("the sample size matches kappaSize for a binary rating and every rater count", {
    skip_if_not_installed("kappaSize")
    for (r in 2:6) {
        got <- kpower(props = "0.30", kappa0 = 0.4, kappa1 = 0.6, raters = as.character(r))$size$asDF
        expect_equal(got$n, ceiling(kappaSize::PowerBinary(kappa0 = 0.4, kappa1 = 0.6, props = 0.3, raters = r,
                                                           alpha = 0.05, power = 0.8)$N))
    }
})

test_that("three categories match kappaSize::Power3Cats", {
    skip_if_not_installed("kappaSize")
    got <- kpower(outcome = "3", props = "0.2, 0.3, 0.5", raters = "3", kappa0 = 0.4, kappa1 = 0.6)$size$asDF
    expect_equal(got$n, ceiling(kappaSize::Power3Cats(kappa0 = 0.4, kappa1 = 0.6, props = c(0.2, 0.3, 0.5),
                                                      raters = 3, alpha = 0.05, power = 0.8)$N))
})

test_that("the notes give the formula and flag an alternative below the null", {
    result <- kpower(props = "0.30", kappa0 = 0.4, kappa1 = 0.6)
    expect_equal(result$size$asDF$n, 191)
    expect_true(any(startsWith(notesOf(result$size), "kappaSize power approach: N = lambda / 0.0412111, rounded up to 191")))
    expect_match(result$summary$content, "**191 subjects**", fixed = TRUE)
    below <- kpower(props = "0.15", kappa0 = 0.6, kappa1 = 0.4, alpha = 0.01, power = 0.9)
    expect_true(any(startsWith(notesOf(below$size), "kappa1 is below kappa0")))
})

test_that("the Monte Carlo check reports its seed and draws and is reproducible", {
    result <- kpower(props = "0.30", kappa0 = 0.4, kappa1 = 0.6, simulate = TRUE, draws = 2000, seed = 20261018)
    check <- result$check$asDF
    expect_equal(check$planned, c(0.8, 0.05))
    # Exact power and type I error by enumerating every study of 191 subjects (tests/python/test_pykappapower.py)
    expect_lt(abs(check$simulated[1] - 0.81782417351593995), 4 * sqrt(0.818 * 0.182 / 2000))
    expect_lt(abs(check$simulated[2] - 0.051920497191875879), 4 * sqrt(0.052 * 0.948 / 2000))
    expect_true(any(startsWith(notesOf(result$check),
                               "2,000 simulated studies of 191 subjects for each row, random seed 20261018")))
    expect_equal(kpower(props = "0.30", kappa0 = 0.4, kappa1 = 0.6, simulate = TRUE, draws = 2000,
                        seed = 20261018)$check$asDF, check)
})

test_that("the Monte Carlo check is not offered for more than two raters", {
    # its plug-in test rejects a true kappa too often there (tests/python/test_pykappapower.py)
    result <- kpower(props = "0.30", kappa0 = 0.4, kappa1 = 0.6, raters = "3", simulate = TRUE)
    expect_equal(result$size$asDF$n, 106)
    expect_equal(result$check$rowCount, 0)
    expect_true(any(startsWith(notesOf(result$check), "Not available for more than two raters or for 3-5 categories")))
})

test_that("unusable input is rejected with a clear message", {
    expect_error(kpower(kappa0 = 0.5, kappa1 = 0.5), "must differ")
    expect_error(kpower(alpha = 0.2, power = 0.2), "The power must exceed alpha")
})
