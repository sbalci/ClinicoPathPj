# Independent CCC interval oracle; never imports the Python implementation or tests.
# Run from repository root: LANG=en_US.UTF-8 Rscript --vanilla tests/reference/concordance-intervals.R
# Lin (1989), Biometrics 45:255-268; correction Lin (2000), Biometrics 56:324-325.
# Computational reference: installed DescTools::CCC 0.99.60, both documented CI options.
# Population moments use divisor n. The corrected variance uses divisor n-2.
# Base-R cross-products and tanh back-transform are independent of DescTools' cor/var
# calculation and exponential back-transform. Raw undefined cases are retained.
stopifnot(requireNamespace("DescTools", quietly = TRUE),
          requireNamespace("jsonlite", quietly = TRUE),
          as.character(packageVersion("DescTools")) == "0.99.60")
seed <- 20261111L
RNGkind("Mersenne-Twister", "Inversion", "Rejection")
set.seed(seed)
levels <- c(.8, .9, .95, .975, .99)
capture <- function(expr) {
  warnings <- character()
  value <- withCallingHandlers(tryCatch(force(expr), error = function(e) {
    list(error = conditionMessage(e))
  }), warning = function(w) {
    warnings <<- c(warnings, conditionMessage(w))
    invokeRestart("muffleWarning")
  })
  list(value = value, warnings = warnings)
}
base_reference <- function(x, y, confidence) {
  keep <- complete.cases(x, y)
  x <- x[keep]; y <- y[keep]; n <- length(x)
  dx <- x - mean(x); dy <- y - mean(y)
  vx <- sum(dx * dx) / n; vy <- sum(dy * dy) / n
  covariance <- sum(dx * dy) / n
  denominator <- vx + vy + (mean(y) - mean(x))^2
  rho <- 2 * covariance / denominator
  r <- covariance / sqrt(vx * vy)
  cb <- 2 * sqrt(vx * vy) / denominator
  u2 <- (mean(y) - mean(x))^2 / sqrt(vx * vy)
  # Lin's expression retained literally for its undefined r=0 domain.
  a <- rho^2 * (1 - r^2) * (1 - rho^2) / r^2
  b <- 2 * rho^3 * (1 - rho) * u2 / r
  c <- -rho^4 * u2^2 / (2 * r^2)
  variance <- (a + b + c) / (n - 2)
  se <- sqrt(variance)
  z <- atanh(rho); z_se <- se / (1 - rho^2)
  q <- qnorm((1 + confidence) / 2)
  z_limits <- z + c(-1, 1) * q * z_se
  reason <- if (vx == 0 || vy == 0) "constant_measurement" else if (r == 0) {
    "zero_pearson_reference_undefined"
  } else if (abs(rho) == 1) "perfect_concordance_boundary" else if (
    !is.finite(variance) || variance <= 0) "nonpositive_or_unresolved_variance" else "available"
  list(n = n, excluded_pairs = length(keep) - n, mean_x = mean(x), mean_y = mean(y),
       variance_x_population = vx, variance_y_population = vy,
       covariance_population = covariance, rho = rho, r = r, Cb = cb,
       u_squared = u2, variance_term_correlation = a, variance_term_location = b,
       variance_term_location_fourth = c, variance = variance, se = se,
       z = z, z_se = z_se, critical_z = q, z_limits = z_limits,
       back_transformed_limits = tanh(z_limits),
       wald_limits = rho + c(-1, 1) * q * se, inference_status = reason)
}
package_reference <- function(x, y, confidence, method) {
  z <- DescTools::CCC(x, y, ci = method, conf.level = confidence, na.rm = TRUE)
  list(rho = unname(z$rho.c$est), limits = unname(as.numeric(z$rho.c[1, 2:3])),
       Cb = unname(z$C.b), location_shift = unname(z$l.shift), scale_shift = unname(z$s.shift))
}
cases <- list()
add <- function(id, x, y, description) {
  stopifnot(length(x) == length(y), sum(complete.cases(x, y)) >= 10)
  cases[[length(cases) + 1L]] <<- list(id = id, description = description, x = x, y = y)
}
x <- rep(0:4, each = 2)
y <- c(0, 1, 1, 1, 2, 3, 2, 4, 4, 3)
# Hand check: n=10, mean(x)=2, mean(y)=2.1, sum(dx²)=20,
# sum(dy²)=16.9, sum(dx*dy)=16; rho=32/(20+16.9+10*.1²)=32/37.
add("ties_hand_check", x, y, "Integer ties; hand CCC 32/37 with population moments")
# Second hand fixture: means 0/.5, vx=1, vy=1.25, covariance=.5.
# rho=.4, r²=.2, Cb²=.8, u²=.25/sqrt(1.25); corrected variance=179/3125.
add("ties_hand_variance", rep(c(-1, -1, 1, 1), 3), rep(c(-1, 1, 0, 2), 3),
    "Hand-checkable shifted ties with exact CCC .4 and variance 179/3125")
add("ties_negative", x, -y, "Negative correlation with tied readings")
add("location_shift", x, y + 4, "Positive association with substantial location shift")
add("scale_shift", x, y * 2.5, "Positive association with scale and location shift")
add("negative_location_scale", x, -2 * y + 7, "Negative association plus both shifts")
add("pefr_desctools_help", c(494,395,516,434,476,557,413,442,650,433,417,656,267,
    478,178,423,427), c(512,430,520,428,500,600,364,380,658,445,432,626,260,
    477,259,350,451), "Public Bland-Altman PEFR pairs transcribed from DescTools CCC help")
x <- rep(c(-1, 1), 6)
e <- rep(c(-1, -1, 1, 1), 3)
add("pearson_exact_zero", x, e, "Exactly zero centered cross-product; package intervals undefined")
add("pearson_small_positive", x, e + .001 * x, "Small positive Pearson correlation")
add("pearson_small_negative", x, e - .001 * x, "Small negative Pearson correlation")
x <- as.double(1:12)
add("perfect_identity", x, x, "CCC=1 boundary")
add("perfect_reversal", x, 13 - x, "CCC=-1 boundary, same mean and spread")
add("perfect_linear_offset", x, x + 2, "Pearson=1 but CCC<1, location term yields variance")
add("perfect_negative_offset", x, -x + 17, "Pearson=-1 but CCC>-1 with location shift")
add("perfect_linear_scale", x, 2 * x, "Pearson=1 with scale/location mismatch")
add("constant_x", rep(3, 12), x, "First measurement constant")
add("constant_y", x, rep(3, 12), "Second measurement constant")
add("both_constant_equal", rep(3, 12), rep(3, 12), "Both constant, equal")
add("both_constant_different", rep(3, 12), rep(4, 12), "Both constant, different")
add("missing_pairs", c(NA, x, 7, NA), c(5, x + rep(c(-1, 1), 6), NA, NA),
    "Pair deletion retains 12 complete observations from 15")
add("near_identity", x, x + rep(c(-1, 1), 6) * 1e-4,
    "Near CCC=1; tests stable tanh back-transform")
add("near_reversal", x, 13 - x + rep(c(-1, 1), 6) * 1e-4,
    "Near CCC=-1; tests stable tanh back-transform")
for (n in c(10L, 30L, 100L)) {
  x <- rnorm(n); e <- rnorm(n)
  add(paste0("normal_positive_n", n), x, .7 * x + .7 * e + .3,
      "Seeded moderate positive bivariate normal draw")
  add(paste0("normal_negative_n", n), x, -.6 * x + .8 * e - .2,
      "Seeded moderate negative bivariate normal draw")
  x <- exp(rnorm(n, .3, .6)); e <- exp(rnorm(n, 0, .5))
  add(paste0("skewed_positive_n", n), x, .8 * x + .4 * e,
      "Seeded skewed correlated positive readings")
}
# Freeze the complete input matrix before computing either oracle.
stopifnot(length(cases) == 31L)
stopifnot(abs(base_reference(cases[[1]]$x, cases[[1]]$y, .95)$rho - 32 / 37) < 1e-15)
stopifnot(abs(base_reference(cases[[2]]$x, cases[[2]]$y, .95)$variance -
                179 / 3125) < 1e-15)
comparisons <- list()
close_number <- function(a, b, tolerance = 1e-8) {
  if (is.nan(a) || is.nan(b)) return(is.nan(a) && is.nan(b))
  if (is.na(a) || is.na(b)) return(is.na(a) && is.na(b))
  if (!is.finite(a) || !is.finite(b)) return(identical(a, b))
  abs(a - b) <= tolerance * if (b == 0) 1 else abs(b)
}
fixtures <- lapply(cases, function(case) {
  runs <- lapply(levels, function(confidence) {
    base <- capture(base_reference(case$x, case$y, confidence))
    z <- capture(package_reference(case$x, case$y, confidence, "z-transform"))
    w <- capture(package_reference(case$x, case$y, confidence, "asymptotic"))
    for (method in c("z_transform", "wald")) {
      package <- if (method == "z_transform") z$value else w$value
      reference <- if (method == "z_transform") base$value$back_transformed_limits else {
        base$value$wald_limits
      }
      fields <- c("rho", "lower", "upper", "Cb")
      observed <- c(package$rho, package$limits, package$Cb)
      expected <- c(base$value$rho, reference, base$value$Cb)
      for (j in seq_along(fields)) {
        finite <- is.finite(observed[j]) && is.finite(expected[j])
        # Constants have independent finite CCC/Cb algebra but package uses p/r.
        status <- if (close_number(observed[j], expected[j])) "agreement" else {
          if (!finite) "nonfinite_disagreement" else "finite_disagreement"
        }
        comparisons[[length(comparisons) + 1L]] <<- list(
          case = case$id, confidence = confidence, method = method, field = fields[j],
          package_value = observed[j], base_value = expected[j],
          difference = observed[j] - expected[j], status = status,
          inference_status = base$value$inference_status)
      }
    }
    list(confidence = confidence, base_r = base, desctools_z_transform = z,
         desctools_asymptotic = w)
  })
  c(case, list(runs = runs))
})
# JSON numbers retain full double precision; special strings explicitly preserve nonfinite kind.
encode_nonfinite <- function(x) {
  if (is.list(x)) return(lapply(x, encode_nonfinite))
  if (!is.numeric(x) || all(is.finite(x))) return(x)
  encoded <- lapply(x, function(v) {
    if (is.nan(v)) "NaN" else if (is.na(v)) "NA" else if (v == Inf) "+Inf" else {
      if (v == -Inf) "-Inf" else v
    }
  })
  if (length(x) == 1L) encoded[[1]] else encoded
}
statuses <- table(vapply(comparisons, `[[`, "", "status"))
ordinary <- Filter(function(v) v$inference_status == "available", comparisons)
ordinary_mismatch <- Filter(function(v) v$status != "agreement", ordinary)
result <- list(
  schema_version = 1L, seed = seed, rng_kind = RNGkind(), confidence_levels = levels,
  nonfinite_encoding = "Special numeric values are strings: NA, NaN, +Inf, -Inf; no clipping",
  provenance = list(primary_reference = "DescTools::CCC", version = "0.99.60",
    source = "Installed function body and help(CCC, package=DescTools), including PEFR example",
    base_reference = "Centered population cross-products; corrected Lin variance; atanh/tanh CI",
    source_function = paste(deparse(DescTools::CCC), collapse = "\n"),
    policy = paste("Withhold inference for constants, exact r=0, abs(CCC)=1 or unresolved",
                   "nonpositive variance. Finite raw oracle intervals remain recorded.",
                   "Pearson abs(r)=1 alone is not grounds for withholding.")),
  versions = list(R = R.version.string, DescTools = as.character(packageVersion("DescTools")),
                  jsonlite = as.character(packageVersion("jsonlite"))),
  session_info = capture.output(sessionInfo()), fixtures = fixtures, comparisons = comparisons,
  summary = list(cases = length(cases), confidence_runs = length(cases) * length(levels),
                 comparisons = length(comparisons), comparison_status_counts = as.list(statuses),
                 ordinary_comparisons = length(ordinary), ordinary_mismatches = length(ordinary_mismatch)))
output <- "tests/fixtures/concordance-intervals.json"
json <- jsonlite::toJSON(encode_nonfinite(result), auto_unbox = TRUE, pretty = TRUE,
                         digits = NA, null = "null")
writeLines(json, output, useBytes = TRUE)
cat("Cases:", length(cases), "runs:", length(cases) * length(levels), "\n")
print(statuses)
cat("Ordinary mismatches:", length(ordinary_mismatch), "\n")
if (length(ordinary_mismatch)) {
  print(ordinary_mismatch)
  quit(status = 1)
}
