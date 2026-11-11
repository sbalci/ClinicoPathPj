# Independent paired-percentile CCC oracle. No Python target or target expected values read.
# CCC = 2 * (sum(x*y) - sum(x)*sum(y)/n) /
#       (sum(x*x) + sum(y*y) - 2*sum(x)*sum(y)/n).
# This follows directly from the population-moment definition. Each row of the
# fixed index matrix draws complete PAIRS with replacement. Quantiles are R type 7.
suppressPackageStartupMessages(library(jsonlite))

args <- commandArgs(trailingOnly = TRUE)
out <- if (length(args)) args[[1L]] else "tests/fixtures/concordance-bootstrap.json"

ccc <- function(x, y) {
  n <- length(x)
  cross <- sum(x * y) - sum(x) * sum(y) / n
  denominator <- sum(x * x) + sum(y * y) - 2 * sum(x) * sum(y) / n
  if (!is.finite(denominator) || denominator <= 0) return(NA_real_)
  2 * cross / denominator
}

make_case <- function(id, x, y, seed, mode = "random", B = 199L) {
  retained <- which(!is.na(x) & !is.na(y))
  xx <- x[retained]
  yy <- y[retained]
  n <- length(xx)
  stopifnot(n >= 10L, all(is.finite(xx)), all(is.finite(yy)))
  set.seed(seed)
  indices <- matrix(sample.int(n, B * n, replace = TRUE) - 1L, nrow = B)
  # One deterministic non-resampled row guarantees cohort orientation is visible.
  indices[1L, ] <- seq_len(n) - 1L
  if (mode == "undefined_row") indices[2L, ] <- 0L
  if (mode == "collapsed") {
    indices <- matrix(rep(seq_len(n) - 1L, B), nrow = B, byrow = TRUE)
  }
  if (mode == "biased_indices") {
    # Permitted explicit samples can place a percentile interval away from the
    # original estimate. The contract does not require the CI to contain it.
    indices <- matrix(rep(rep(c(0L, 1L), length.out = n), B), nrow = B, byrow = TRUE)
    indices[seq(2L, B, 2L), ] <- rep(c(0L, 3L), length.out = n)
  }
  point <- ccc(xx, yy)
  distribution <- apply(indices, 1L, function(i) ccc(xx[i + 1L], yy[i + 1L]))
  bad <- which(!is.finite(distribution))
  finite <- length(bad) == 0L
  se <- if (finite) sd(distribution) else NA_real_
  intervals <- lapply(c(.8, .95, .99), function(confidence) {
    raw <- if (finite) {
      unname(quantile(distribution, c((1 - confidence) / 2, (1 + confidence) / 2),
                      type = 7, names = FALSE))
    } else c(NA_real_, NA_real_)
    reason <- if (!is.finite(point)) {
      "source CCC undefined"
    } else if (abs(point) >= 1) {
      "source CCC on parameter boundary"
    } else if (!finite) {
      "undefined bootstrap replicate"
    } else if (raw[[1L]] >= raw[[2L]]) {
      "zero-width percentile limits"
    } else ""
    list(confidence = confidence, raw_quantiles = raw,
         policy_status = if (reason == "") "ok" else "unavailable",
         policy_reason = reason,
         policy_lower = if (reason == "") raw[[1L]] else NA_real_,
         policy_upper = if (reason == "") raw[[2L]] else NA_real_)
  })
  list(id = id, x = x, y = y, resamples = B, indices = indices,
       expected = list(n_complete = n, retained_indices = retained - 1L,
                       n_missing = length(x) - n, point = point,
                       distribution = distribution, n_undefined = length(bad),
                       undefined_resample_indices = bad - 1L,
                       raw_bootstrap_se = se, intervals = intervals))
}

# Tiny fixture: n=12, with ties, denominator/orientation deliberately asymmetric.
x <- rep(c(-1, -1, 1, 1), 3)
y <- rep(c(-1, 1, 0, 2), 3)
set.seed(724901)
normal_x <- rnorm(30)
normal_y <- .6 * normal_x + .8 * rnorm(30) + .4
skew_x <- exp(rnorm(30))
skew_y <- .2 + .7 * skew_x + exp(rnorm(30))
negative_x <- seq(-2, 2, length.out = 30)
negative_y <- -.7 * negative_x + .15 * sin(seq_len(30))
high_x <- seq(-1, 1, length.out = 30)
high_y <- high_x + .001 * cos(seq_len(30))
fixtures <- list(
  make_case("hand_asymmetric_ties_n12", x, y, 3101L),
  make_case("missing_pairs_n12", c(x[1:5], NA, x[6:12], 99),
            c(y[1:5], 99, y[6:12], NA), 3102L),
  make_case("normal_n30", normal_x, normal_y, 3103L, B = 399L),
  make_case("skew_n30", skew_x, skew_y, 3104L, B = 399L),
  make_case("zero_covariance_n12", x, rep(c(-1, 1, -1, 1), 3), 3105L),
  make_case("negative_n30", negative_x, negative_y, 3106L),
  make_case("high_concordance_n30", high_x, high_y, 3107L),
  make_case("one_constant_n12", rep(2, 12), seq_len(12), 3108L),
  make_case("unequal_constants_n12", rep(2, 12), rep(3, 12), 3109L),
  make_case("equal_constants_n12", rep(2, 12), rep(2, 12), 3110L),
  make_case("perfect_positive_n12", x, x, 3111L),
  make_case("perfect_negative_n12", x, -x, 3112L),
  make_case("perfect_pearson_shifted_n12", x, x + 1, 3113L),
  # Row zero is (0,0), making the all-row-zero resample mathematically undefined.
  make_case("undefined_resample_n12", seq(0, 11), c(0, 1, 3, 2, 5, 4, 6, 8, 7, 10, 9, 12),
            3114L, mode = "undefined_row"),
  make_case("collapsed_distribution_n12", x, y, 3115L, mode = "collapsed"),
  make_case("percentiles_exclude_point_n12", seq(0, 11),
            c(0, 2, 1, 7, 3, 8, 4, 9, 5, 12, 6, 13),
            3116L, mode = "biased_indices"),
  make_case("minimum_n10", x[1:10], y[1:10], 3117L)
)
# Hand calculation independent of simulated samples and bootstrap code.
stopifnot(abs(ccc(x, y) - 2 / 5) < 1e-14)
# At perfect agreement or constants, raw bootstrap intervals may exist or
# collapse. Keep them as raw mathematics; policy still withholds source inference.
result <- list(
  scope = "Independent base-R paired percentile CCC bootstrap oracle; not coverage or native qualification",
  derivation = "CCC from raw sums, population divisor n; same indices for each pair; equal-tailed quantile(type=7); sd uses B-1",
  index_origin = "zero-based retained complete-pair cohort",
  missing_tokens = "NA strings represent genuine missing values",
  R_version = R.version.string,
  jsonlite_version = as.character(packageVersion("jsonlite")),
  RNGkind = RNGkind(),
  hand_point = 2 / 5,
  fixtures = fixtures
)
write_json(result, out, pretty = TRUE, digits = 17, auto_unbox = TRUE,
           na = "string", null = "null")
cat("Wrote", length(fixtures), "independent fixtures to", out, "\n")
