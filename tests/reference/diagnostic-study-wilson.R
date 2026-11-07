# Independent score-test inversion provided by base R, without Yates correction.
fixture <- list()
for (n in c(1, 2, 5, 10, 100, 10000)) {
    for (x in unique(c(0, 1, floor(n / 2), n - 1, n))) {
        for (level in c(0.50, 0.80, 0.95, 0.99)) {
            ci <- suppressWarnings(stats::prop.test(x, n, conf.level = level,
                                                  correct = FALSE)$conf.int)
            fixture[[length(fixture) + 1L]] <- list(x = x, n = n, level = level,
                                                  lower = ci[1], upper = ci[2])
        }
    }
}
writeLines(jsonlite::toJSON(fixture, auto_unbox = TRUE, digits = 16, pretty = TRUE),
           "tests/fixtures/diagnostic-study-wilson.json")
