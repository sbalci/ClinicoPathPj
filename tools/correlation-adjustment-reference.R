# Independent base-R oracle; no ClinicoPathPj code is loaded.
# Rscript --vanilla tools/correlation-adjustment-reference.R /private/tmp/cpj-adjust-reference.json
args <- commandArgs(TRUE)
stopifnot(length(args) == 1L)
set.seed(20261027)
methods <- c('none', 'holm', 'bonferroni', 'BH', 'BY', 'hochberg', 'hommel')
inputs <- list(numeric(), NA_real_, c(NA_real_, NA_real_), 0, 1,
               c(0, 1, NA), c(.01, .04, NA), c(.01, .01, .01, 1),
               c(1e-300, 1e-100, 1e-15, .999999999999, NA))
for (n in c(1, 2, 3, 5, 10, 30, 190)) {
  for (i in seq_len(30)) {
    p <- if (i %% 2) runif(n) else sample(c(0, .001, .01, .05, .5, 1), n, TRUE)
    if (i %% 3 == 0) p[sample.int(n, max(1, floor(n / 3)))] <- NA_real_
    inputs[[length(inputs) + 1L]] <- p
  }
}
fixtures <- list()
for (p in inputs) for (method in methods) {
  fixtures[[length(fixtures) + 1L]] <- list(
    method = jsonlite::unbox(method), p = p,
    expected = p.adjust(p, method = method, n = length(p)))
}
jsonlite::write_json(list(oracle = jsonlite::unbox('base R stats::p.adjust'),
                         R = jsonlite::unbox(R.version.string), fixtures = fixtures),
                     args[[1]], digits = NA, na = 'null')
cat(length(fixtures), 'independent R fixtures written\n')
