#!/usr/bin/env Rscript
# Independent reference: derived only from the CCC estimand and iid moment CLT.
# No Python implementation, previous oracle, or target output was read.
# Run from repository root: Rscript --vanilla tests/reference/concordance-empirical.R
# For Z=(X,Y,X^2,Y^2,XY), m=E[Z]=(a,b,c,d,e):
# N=2(e-ab), D=c+d-2ab, rho=N/D.
# grad rho=(2b(N-D)/D^2,2a(N-D)/D^2,-N/D^2,-N/D^2,2/D).
# iid finite fourth moments: sqrt(n)(rho_hat-rho) -> N(0,g' Sigma g).
# Sigma_hat=mean((Zi-m_hat)(Zi-m_hat)'); Var_hat=rho IF second moment/n.
# No n-1 or n-2 adjustment, normality assumption, clipping, or fallback.
# Finite fourth moments and nonzero D are assumptions; zero first-order variance
# is possible and does not establish regular nondegenerate Gaussian inference.
stopifnot(requireNamespace("jsonlite", quietly = TRUE),
  requireNamespace("Rmpfr", quietly = TRUE))
seed <- 20261111L
set.seed(seed)
levels <- c(.8, .9, .95, .975, .99)
ccc_from_raw <- function(m) 2 * (m[5] - m[1] * m[2]) /
  (m[3] + m[4] - 2 * m[1] * m[2])
raw_status <- function(v) {
  ifelse(is.nan(v), "NaN", ifelse(is.na(v), "NA",
    ifelse(is.infinite(v), ifelse(v > 0, "+Infinity", "-Infinity"), "finite")))
}
# Preserve NA vs NaN vs +/-Inf, which JSON numbers alone cannot encode.
json_safe <- function(x) {
  if (is.list(x)) return(lapply(x, json_safe))
  if (is.numeric(x) && any(!is.finite(x))) {
    if (length(x) == 1L) return(unname(raw_status(x)))
    out <- lapply(seq_along(x), function(i) {
      if (is.finite(x[i])) unname(x[i]) else unname(raw_status(x[i]))
    })
    names(out) <- names(x)
    return(out)
  }
  x
}
reference <- function(x, y) {
  stopifnot(length(x) == length(y))
  # Only missing pairs removed; nonmissing infinite inputs rejected separately.
  keep <- !is.na(x) & !is.na(y)
  xx <- x[keep]; yy <- y[keep]; n <- length(xx)
  policy <- if (any(!is.finite(c(xx, yy)))) "nonfinite_input" else if (n < 10) {
    "below_minimum_n"
  } else if (n > 5000) "above_maximum_n" else "eligible"
  if (any(!is.finite(c(xx, yy))) || n == 0) {
    return(list(n = n, input_n = length(x), removed_indices = which(!keep),
      policy = policy, raw_calculation = "not_evaluated"))
  }
  z <- cbind(EX = xx, EY = yy, EX2 = xx^2, EY2 = yy^2, EXY = xx * yy)
  m <- colMeans(z); a <- m[1]; b <- m[2]
  N <- 2 * (m[5] - a * b); D <- m[3] + m[4] - 2 * a * b
  rho <- N / D
  g <- c(2 * b * (N - D) / D^2, 2 * a * (N - D) / D^2,
    -N / D^2, -N / D^2, 2 / D)
  names(g) <- colnames(z)
  centered <- sweep(z, 2, m)
  sigma <- crossprod(centered) / n
  influence <- as.vector(centered %*% g)
  variance <- mean(influence^2) / n
  quadratic_variance <- as.numeric(t(g) %*% sigma %*% g) / n
  se <- sqrt(variance)
  # Independent differential in central moments provides an algebraic check.
  dx <- xx - a; dy <- yy - b
  vx <- mean(dx^2); vy <- mean(dy^2); cv <- mean(dx * dy)
  central_influence <- (2 * (dx * dy - cv) - rho *
    (dx^2 - vx + dy^2 - vy + 2 * (a - b) * (dx - dy))) / D
  # Check all components at two steps; discrepancies are recorded, never replaced.
  fd_one <- function(multiplier) vapply(seq_along(m), function(j) {
    h <- multiplier * .Machine$double.eps^(1 / 3) * max(1, abs(m[j]))
    plus <- minus <- m
    plus[j] <- plus[j] + h; minus[j] <- minus[j] - h
    (ccc_from_raw(plus) - ccc_from_raw(minus)) / (2 * h)
  }, numeric(1))
  fd <- fd_one(1); fd_half <- fd_one(.5)
  intervals <- lapply(levels, function(confidence) {
    critical <- qnorm((1 + confidence) / 2)
    normal <- rho + c(-1, 1) * critical * se
    transformed_se <- se / (1 - rho^2)
    zrho <- atanh(rho)
    transformed <- tanh(zrho + c(-1, 1) * critical * transformed_se)
    list(confidence = confidence, critical_value = critical,
      normal = list(lower = normal[1], upper = normal[2], status = raw_status(normal)),
      atanh = list(transformed_point = zrho, transformed_se = transformed_se,
        lower = transformed[1], upper = transformed[2], status = raw_status(transformed)))
  })
  # 256-bit arithmetic is an independent numerical adjudicator, not a new method.
  # Inputs are the exact binary doubles already frozen in the input data arrays.
  mp <- function(v) Rmpfr::mpfr(v, precBits = 256)
  mx <- mp(xx); my <- mp(yy)
  ma <- Rmpfr::mean(mx); mb <- Rmpfr::mean(my)
  mdx <- mx - ma; mdy <- my - mb
  mvx <- Rmpfr::mean(mdx^2); mvy <- Rmpfr::mean(mdy^2); mcv <- Rmpfr::mean(mdx * mdy)
  mden <- mvx + mvy + (ma - mb)^2
  mrho <- 2 * mcv / mden
  mif <- (2 * (mdx * mdy - mcv) - mrho *
    (mdx^2 - mvx + mdy^2 - mvy + 2 * (ma - mb) * (mdx - mdy))) / mden
  mvar_unbalanced <- Rmpfr::mean(mif^2) / n
  # Algebraic reassociation avoids subtracting rounded centered squares twice.
  # It produces exact zero at exact agreement/antiagreement without a guard.
  mcontrast <- 2 * mdx * mdy - mrho *
    (mdx^2 + mdy^2 + 2 * (ma - mb) * (mdx - mdy))
  mif_balanced <- (mcontrast - Rmpfr::mean(mcontrast)) / mden
  mvar <- Rmpfr::mean(mif_balanced^2) / n
  mse <- sqrt(mvar)
  mz <- atanh(mrho)
  mzse <- mse / (1 - mrho^2)
  as_num <- function(v) unname(as.numeric(v))
  mp_intervals <- lapply(levels, function(confidence) {
    critical <- mp(qnorm((1 + confidence) / 2))
    mn <- mrho + c(-1, 1) * critical * mse
    mt <- tanh(mz + c(-1, 1) * critical * mzse)
    list(confidence = confidence, normal = as_num(mn), atanh = as_num(mt),
      normal_status = raw_status(as_num(mn)), atanh_status = raw_status(as_num(mt)))
  })
  mpfr <- list(precision_bits = 256L,
    unbalanced_variance = as_num(mvar_unbalanced),
    unbalanced_minus_balanced_variance = as_num(mvar_unbalanced - mvar), point = as_num(mrho), variance = as_num(mvar),
    se = as_num(mse), transformed_point = as_num(mz), transformed_se = as_num(mzse),
    variance_status = raw_status(as_num(mvar)), point_status = raw_status(as_num(mrho)),
    decimal_point = Rmpfr::format(mrho, digits = 75), decimal_variance = Rmpfr::format(mvar, digits = 75),
    decimal_se = Rmpfr::format(mse, digits = 75), intervals = mp_intervals,
    double_point_minus_mpfr = rho - as_num(mrho),
    double_variance_minus_mpfr = variance - as_num(mvar),
    quadratic_variance_minus_mpfr = quadratic_variance - as_num(mvar),
    double_se_minus_mpfr = se - as_num(mse))
  list(n = n, input_n = length(x), removed_indices = which(!keep), policy = policy,
    mpfr256 = mpfr, moment_order = colnames(z), raw_moments = unname(m), numerator = unname(N),
    denominator = unname(D), point = unname(rho), point_status = raw_status(rho),
    gradient = unname(g), covariance_of_contributions = unname(sigma),
    influence = influence, central_influence = unname(central_influence),
    variance = variance, se = se, variance_status = raw_status(variance),
    quadratic_variance = quadratic_variance,
    quadratic_minus_influence_variance = quadratic_variance - variance,
    influence_max_abs_discrepancy = max(abs(influence - central_influence)),
    gradient_finite_difference = fd, gradient_finite_difference_halfstep = fd_half,
    gradient_discrepancy = unname(g - fd),
    gradient_halfstep_discrepancy = unname(g - fd_half), intervals = intervals)
}
fixtures <- list()
add <- function(id, x, y, description) {
  fixtures[[length(fixtures) + 1L]] <<- list(id = id, description = description,
    x = x, y = y, expected = reference(x, y))
}
# Hand data sums: n=12; sum x=26, sum y=28, sum x^2=86,
# sum y^2=106, sum xy=91. Thus numerator=91/18,
# denominator=53/9, point=91/106. Ties in both variables.
hx <- c(0, 0, 1, 1, 1, 2, 2, 3, 3, 4, 4, 5)
hy <- c(0, 1, 0, 1, 2, 1, 3, 2, 4, 3, 5, 6)
add("hand_ties_n12", hx, hy, "Hand-checkable integer tied pairs")
# Freeze hand arithmetic from actual sums and expose disagreement with comment.
hand_sums <- c(sum(hx), sum(hy), sum(hx^2), sum(hy^2), sum(hx * hy))
add("hand_asymmetric_n12", rep(c(-1, -1, 1, 1), 3),
  rep(c(-1, 1, 0, 2), 3), "Parent-supplied candidate inputs, independently evaluated")
normal_x <- rnorm(80)
normal_y <- .7 * normal_x + rnorm(80, sd = .6)
add("normal_n80", normal_x, normal_y, "Correlated iid normal simulation")
skew_x <- exp(rnorm(60, sd = .8))
skew_y <- .8 * skew_x + exp(rnorm(60, sd = .6))
add("skewed_n60", skew_x, skew_y, "Positive skew with nonnormal fourth moments")
add("shifted_n80", normal_x + 3, normal_y + 5, "Location disagreement")
add("negative_n80", normal_x, -normal_y, "Negative concordance")
add("high_concordance_n80", normal_x, normal_x + rnorm(80, sd = .002),
  "Near-boundary concordance without exact equality")
add("missing_n12", c(hx, NA, 9, NA), c(hy, 3, NA, NA), "Twelve complete pairs")
add("nan_missing_n12", c(hx, NaN), c(hy, 2), "NaN treated as missing")
# Full factorial x,y in {-1,1}, repeated: exact covariance zero, positive IF variance.
add("zero_covariance_symmetric_n12", rep(c(-1, -1, 1, 1), 3),
  rep(c(-1, 1, -1, 1), 3), "Exact zero covariance with positive empirical variance")
# Orthogonal integer vectors with unequal empirical third/fourth moments.
zx <- rep(c(-2, -1, 0, 3), 3)
zy <- rep(c(1, -2, 1, 0), 3)
add("zero_covariance_asymmetric_n12", zx, zy,
  "Exact zero covariance; asymmetric x and y supports")
add("one_constant_n12", rep(0, 12), hx, "Zero first-order variance with constant x")
add("both_constants_different_n12", rep(2, 12), rep(3, 12), "CCC zero, variance zero")
add("both_constants_equal_n12", rep(2, 12), rep(2, 12), "Zero denominator: undefined CCC")
add("perfect_positive_n12", hx, hx, "Exact CCC one; atanh interval raw nonfinite")
add("perfect_negative_n12", rep(c(-3, -2, -1, 1, 2, 3), 2),
  -rep(c(-3, -2, -1, 1, 2, 3), 2), "Exact CCC minus one")
add("perfect_pearson_shifted_n12", hx, hx + 2,
  "Perfect Pearson does not imply perfect CCC or zero variance")
for (nn in c(0, 1, 2, 9, 10, 11)) {
  add(paste0("minimum_boundary_n", nn), seq_len(nn), seq_len(nn) +
    rep(c(0, 1, -1), length.out = nn), "Minimum sample policy boundary")
}
add("maximum_boundary_n5000", rep(hx, length.out = 5000),
  rep(hy, length.out = 5000), "Largest allowed number of pairs")
add("maximum_exceeded_n5001", rep(hx, length.out = 5001),
  rep(hy, length.out = 5001), "Raw calculation retained, policy excludes inference")
add("infinite_input_n12", c(hx[-1], Inf), hy, "Infinite nonmissing input is rejected")
add("all_missing_n12", rep(NA_real_, 12), rep(NA_real_, 12), "No complete pairs")
checks <- list(hand_sums = hand_sums, hand_expected_sums = c(26, 28, 86, 106, 91),
  hand_sum_discrepancy = hand_sums - c(26, 28, 86, 106, 91))
# Derivation/check errors fail visibly rather than revising expectations from target output.
stopifnot(identical(unname(hand_sums), c(26, 28, 86, 106, 91)))
for (f in fixtures) {
  r <- f$expected
  if (!is.null(r$gradient) && all(is.finite(r$gradient))) {
    stopifnot(max(abs(r$gradient_discrepancy)) < 1e-5,
      max(abs(r$gradient_halfstep_discrepancy)) < 1e-5,
      r$influence_max_abs_discrepancy < 1e-10)
  }
}
out <- list(schema_version = 1L,
  provenance = list(reference = "Independent R raw-moment delta derivation",
    R_version = R.version.string, jsonlite_version = as.character(packageVersion("jsonlite")),
    Rmpfr_version = as.character(packageVersion("Rmpfr")),
    seed = seed, session_info = capture.output(sessionInfo()),
    finite_fourth_moments_required = TRUE, minimum_n = 10L, maximum_n = 5000L,
    covariance_divisor = "n", variance_divisor = "n", confidence_levels = levels,
    missing_policy = "Pairwise NA/NaN removal; reject nonmissing infinities",
    raw_nonfinite_encoding = "NA, NaN, +Infinity, -Infinity strings; no clipping/fallback",
    policy_note = "Raw math retained below/above sample policy; not permitted inference"),
  hand_checks = checks, fixtures = fixtures)
args <- commandArgs(trailingOnly = TRUE)
path <- if (length(args)) args[1] else "tests/fixtures/concordance-empirical.json"
writeLines(jsonlite::toJSON(json_safe(out), auto_unbox = TRUE, digits = NA,
  pretty = TRUE, null = "null", na = "string"), path, useBytes = TRUE)
cat("Wrote", length(fixtures), "independent fixtures to", path, "\n")
