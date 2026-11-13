#!/usr/bin/env Rscript
# Independent R oracle; frozen protocol: docs/python-welch-standardized-replication.md.
# This generator never imports or reads the statistical Python implementation.
stopifnot(requireNamespace("jsonlite", quietly = TRUE),
          requireNamespace("digest", quietly = TRUE))
args <- commandArgs(trailingOnly = TRUE)
root <- if (length(args)) normalizePath(args[[1]]) else normalizePath(".")
stopifnot(file.exists(file.path(root, "docs/python-welch-standardized-replication.md")))
out <- file.path(root, "tests/fixtures")
RNGkind("Mersenne-Twister", "Inversion", "Rejection")
set.seed(37112026)
options(digits = 17)

source_paths <- c("inst/python/cpj_welch_standardized.py",
  "inst/python/cpj_estimation.py", "inst/python/cpj_standardized.py",
  "tests/fixtures/welch-standardized-effects.json",
  "tests/fixtures/welch-standardized-coverage.json",
  "tests/fixtures/welch-standardized-coverage.csv")
source_hashes <- setNames(lapply(source_paths, function(path)
  digest::digest(file = file.path(root, path), algo = "sha256")), source_paths)

specs <- list()
add <- function(id, distribution, kind, n1, n2, delta, N) {
  specs[[length(specs) + 1L]] <<- list(id = id,
    label = sprintf("%s n=(%d,%d), delta=%g", distribution, n1, n2, delta),
    distribution = distribution, kind = kind, n1 = n1, n2 = n2,
    sigma1 = 1, sigma2 = 4, delta = delta, N = N)
}
add("replication-normal-20-5-d0", "normal", "replication", 20L, 5L, 0, 20000L)
for (pair in list(c(2L, 2L), c(2L, 5L), c(5L, 2L), c(3L, 3L))) {
  for (delta in c(0, 1.5)) add(sprintf("small-normal-%d-%d-d%s", pair[1], pair[2],
    if (delta == 0) "0" else "1p5"), "normal", "small_sample", pair[1], pair[2],
    delta, 4000L)
}
for (distribution in c("lognormal", "student_t5")) {
  for (pair in list(c(5L, 20L), c(20L, 5L))) {
    for (delta in c(0, 1.5)) add(sprintf("sensitivity-%s-%d-%d-d%s", distribution,
      pair[1], pair[2], if (delta == 0) "0" else "1p5"), distribution,
      "sensitivity", pair[1], pair[2], delta, 4000L)
  }
}
stopifnot(length(specs) == 17L)
draw <- function(n, distribution) {
  switch(distribution, normal = rnorm(n),
    lognormal = (exp(rnorm(n)) - exp(.5)) / sqrt((exp(1) - 1) * exp(1)),
    student_t5 = rt(n, 5) / sqrt(5 / 3))
}
warnings_seen <- character()
warning_context <- "initialization"
warning_contexts <- character()
quiet_pt <- function(q, df, ncp) withCallingHandlers(pt(q, df, ncp = ncp),
  warning = function(w) {
    warnings_seen <<- c(warnings_seen, conditionMessage(w))
    warning_contexts <<- c(warning_contexts, warning_context)
    invokeRestart("muffleWarning")
  })
invert <- function(t, df, probability) {
  f <- function(ncp) quiet_pt(t, df, ncp) - probability
  extent <- max(8, abs(t) + 8)
  while (f(-extent) < 0 || f(extent) > 0) extent <- extent * 2
  uniroot(f, c(-extent, extent), tol = 1e-12)$root
}
profiles <- observations <- csv_rows <- list()
boundaries <- list()
tail <- .05 / (2 * length(specs))
for (s in specs) {
  # Column order is replicate order; group one is drawn before group two.
  a <- matrix(draw(s$n1 * s$N, s$distribution), nrow = s$n1) * s$sigma1 +
    s$delta * sqrt((s$sigma1^2 + s$sigma2^2) / 2)
  b <- matrix(draw(s$n2 * s$N, s$distribution), nrow = s$n2) * s$sigma2
  mean1 <- colMeans(a)
  mean2 <- colMeans(b)
  var1 <- colSums((a - rep(mean1, each = s$n1))^2) / (s$n1 - 1)
  var2 <- colSums((b - rep(mean2, each = s$n2))^2) / (s$n2 - 1)
  difference <- mean1 - mean2
  se2 <- var1 / s$n1 + var2 / s$n2
  stderr <- sqrt(se2)
  df <- se2^2 / ((var1 / s$n1)^2 / (s$n1 - 1) +
    (var2 / s$n2)^2 / (s$n2 - 1))
  rms <- sqrt((var1 + var2) / 2)
  t <- difference / stderr
  degenerate <- stderr == 0 | stderr < 10 * .Machine$double.eps *
    pmax(abs(mean1), abs(mean2))
  available <- !degenerate & is.finite(df) & df >= 2 & df <= 100000 & abs(t) <= 40
  warning_context <- paste(s$id, "coverage")
  probability <- quiet_pt(t, df, s$delta * rms / stderr)
  success <- available & is.finite(probability) & probability >= .025 & probability <= .975
  successes <- sum(success)
  n_available <- sum(available)
  lower <- if (successes == 0) 0 else qbeta(tail, successes, s$N - successes + 1)
  upper <- if (successes == s$N) 1 else qbeta(1 - tail, successes + 1, s$N - successes)
  status <- if (lower >= .925) "pass" else if (upper < .925) "fail" else "inconclusive"
  profiles[[length(profiles) + 1L]] <- c(s, list(successes = successes,
    available = n_available, unsupported = s$N - n_available,
    coverage = successes / s$N,
    available_coverage = if (n_available) successes / n_available else NULL,
    lower = lower, upper = upper, status = status))
  near <- which(abs(df - 2) <= 16 * .Machine$double.eps)
  if (length(near)) boundaries[[s$id]] <- list(replicates = near,
    df = df[near], available = available[near])
  csv_rows[[length(csv_rows) + 1L]] <- data.frame(profile = s$id,
    replicate = seq_len(s$N), mean1, mean2, var1, var2, R_probability = probability)
  selected <- unique(c(1L, s$N, which.min(abs(probability - .025)),
    which.min(abs(probability - .975))))
  for (i in selected) {
    ncp_lower <- ncp_upper <- delta_lower <- delta_upper <- NULL
    state <- if (degenerate[i]) "degenerate" else if (available[i]) "ok" else
      "interval_unavailable"
    if (available[i]) {
      warning_context <- paste(s$id, "selected", i)
      ncp_lower <- invert(t[i], df[i], .975)
      ncp_upper <- invert(t[i], df[i], .025)
      delta_lower <- ncp_lower * stderr[i] / rms[i]
      delta_upper <- ncp_upper * stderr[i] / rms[i]
    }
    observations[[length(observations) + 1L]] <- list(profile = s$id, replicate = i,
      a = unname(a[, i]), b = unname(b[, i]), expected = list(
        difference = difference[i], stderr = stderr[i], df = df[i],
        standardizer_sd = if (degenerate[i]) NULL else rms[i],
        d_rms = if (degenerate[i]) NULL else difference[i] / rms[i],
        ncp_lower = ncp_lower, ncp_upper = ncp_upper,
        delta_lower = delta_lower, delta_upper = delta_upper, status = state))
  }
  cat(sprintf("%s: %d/%d covered; %d available; [%0.9f,%0.9f] %s\n",
    s$id, successes, s$N, n_available, lower, upper, status))
}
manifest <- list(schema_version = 1L,
  versions = list(R = R.version.string, jsonlite = as.character(packageVersion("jsonlite")),
    digest = as.character(packageVersion("digest")), RNG = RNGkind(), seed = 37112026L),
  source_hashes = source_hashes,
  domain = list(df_min = 2, df_max = 100000, abs_t_max = 40),
  profiles = profiles, selected = observations,
  numerical_warnings = as.list(sort(unique(warnings_seen))),
  numerical_warning_counts = as.list(table(warning_contexts)), boundary_cases = boundaries)
json_path <- file.path(out, "welch-standardized-replication.json")
jsonlite::write_json(manifest, json_path, auto_unbox = TRUE, pretty = TRUE,
  digits = NA, null = "null", na = "null")
csv_path <- tempfile("welch-standardized-replication-", fileext = ".csv")
csv_data <- do.call(rbind, csv_rows)
for (column in c("mean1", "mean2", "var1", "var2", "R_probability")) {
  csv_data[[column]] <- sprintf("%.17g", csv_data[[column]])
}
write.table(csv_data, csv_path, sep = ",", row.names = FALSE,
  col.names = TRUE, quote = TRUE, na = "")
gz_path <- file.path(out, "welch-standardized-replication.csv.gz")
# -n suppresses original filename and timestamp, making gzip bytes deterministic.
result <- system2("gzip", c("-n", "-c", shQuote(csv_path)), stdout = gz_path)
unlink(csv_path)
stopifnot(result == 0L)
for (path in c(json_path, gz_path)) cat(basename(path),
  digest::digest(file = path, algo = "sha256"), "\n")
cat("Selected datasets:", length(observations), "; numerical warning types:",
  length(unique(warnings_seen)), "; boundary profiles:", length(boundaries), "\n")
