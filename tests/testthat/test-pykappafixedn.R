# Oracle: kappaSize::FixedNBinary / FixedN4Cats. A calculator: data = data.frame(), as in test-pyruntime.R.

notesOf <- function(table) vapply(table$notes, function(note) note$note, character(1))
fixedn <- function(...) pykappafixedn(data = data.frame(), ...)

test_that("the lower limit matches kappaSize for a binary rating and every rater count", {
    skip_if_not_installed("kappaSize")
    for (r in 2:6) {
        got <- fixedn(raters = as.character(r))$bound$asDF
        expect_equal(got$kappaL, kappaSize::FixedNBinary(kappa0 = 0.6, n = 100, props = 0.2, raters = r,
                                                         alpha = 0.05)$kappaL, tolerance = 1e-10)
    }
})

test_that("four categories match kappaSize::FixedN4Cats", {
    skip_if_not_installed("kappaSize")
    got <- fixedn(outcome = "4", props = "0.1, 0.2, 0.3, 0.4", raters = "3", kappa0 = 0.7, n = 150,
                  alpha = 0.025)$bound$asDF
    expect_equal(got$kappaL, kappaSize::FixedN4Cats(kappa0 = 0.7, n = 150, props = c(0.1, 0.2, 0.3, 0.4),
                                                    raters = 3, alpha = 0.025)$kappaL, tolerance = 1e-10)
})

test_that("the notes explain the method and a limit that cannot rule out chance", {
    result <- fixedn()
    expect_true(any(startsWith(notesOf(result$bound), "kappaSize fixed-sample approach: kappa is stepped down")))
    expect_match(result$summary$content, "is **0.418** if the study observes the anticipated kappa", fixed = TRUE)
    low <- fixedn(props = "0.5", kappa0 = 0.1, n = 11)
    expect_lt(low$bound$asDF$kappaL, 0)
    expect_true(any(startsWith(notesOf(low$bound), "The expected lower limit is not above 0")))
})

test_that("a limit the 0.001 search cannot place inside the model is left empty", {
    # kappaSize::FixedNBinary(kappa0 = 0.01, n = 100, props = 0.02, raters = 3, alpha = 0.2) returns -0.841,
    # far below -0.0004, the lowest kappa this model allows for a 2% category and 3 raters.
    result <- fixedn(props = "0.02", raters = "3", kappa0 = 0.01, alpha = 0.2)
    expect_true(is.na(result$bound$asDF$kappaL))
    expect_true(any(startsWith(notesOf(result$bound), "Not available: the limit lies within about 0.001 of -0.0004")))
})

test_that("unusable proportions are rejected with a clear message", {
    expect_error(fixedn(outcome = "3"), "Enter 3 proportions")
    expect_error(fixedn(props = "0,20 0,80"), "decimal comma")
})
