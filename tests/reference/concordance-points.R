#!/usr/bin/env Rscript
# Independent point-estimate oracle. No Python implementation or Python tests
# are imported or read. Run from any working directory with Rscript --vanilla.
# Only finite measurements and NA (JSON null) are represented here.
stopifnot(requireNamespace("DescTools", quietly = TRUE))
stopifnot(requireNamespace("jsonlite", quietly = TRUE))

RNGkind("Mersenne-Twister", "Inversion", "Rejection")
set.seed(20261110)
seed <- 20261110L
tolerance <- 1e-12

cases <- list()
add <- function(id, x, y, note = "") {
  stopifnot(length(x) == length(y))
  cases[[length(cases) + 1L]] <<- list(id = id, x = x, y = y, note = note)
}

# Tiny arithmetic check: x=(-1,0,1), y=(-1,1,0); means=0,
# variances=2/3, covariance=1/3, hence CCC=r=1/2 and Cb=1.
add("tiny_hand_calculation", c(-1, 0, 1), c(-1, 1, 0))
add("identity", c(-3, -1, 0, 2, 5), c(-3, -1, 0, 2, 5))
add("offset_positive", 1:8, 1:8 + 2)
add("offset_negative", 1:8, 1:8 - 4)
add("scale_positive", -4:4, 2 * (-4:4))
add("scale_and_offset", -4:4, 1.7 * (-4:4) + 3)
add("reversed_centered", -4:4, -(-4:4))
add("reversed_shifted", 1:8, rev(1:8) + 3)
add("ties_both", c(0, 0, 1, 1, 2, 2), c(0, 1, 1, 1, 2, 3))
add("ties_asymmetric", c(1, 1, 1, 2, 4, 4, 7), c(2, 1, 3, 3, 4, 6, 6))
add("mixed_signs", c(-8, -3, -1, 0, 2, 6), c(-7, -5, 1, 2, 3, 5))
add("fractional", c(.1, .25, .5, .8, 1.3), c(.2, .3, .45, .9, 1.1))
add("two_pairs_positive", c(2, 7), c(3, 9))
add("two_pairs_negative", c(2, 7), c(9, 3))
add("zero_pearson_equal_scale", c(-1, -1, 1, 1), c(-1, 1, -1, 1),
    "Both marginal variances are positive. DescTools C.b is NaN because it divides CCC by r.")
add("zero_pearson_shifted_scaled", c(-1, -1, 1, 1), c(1, 5, 1, 5),
    "Both marginal variances are positive. Direct Cb remains defined when r=0.")
add("missing_alternating", c(1, NA, 3, 4, NA, 6, 7), c(2, 3, NA, 5, NA, 5, 9))
add("missing_x_only", c(NA, 2, 4, NA, 8, 10), c(0, 3, 3, 6, 9, 8))
add("missing_y_only", c(1, 2, 4, 6, 8, 10), c(NA, 3, 3, NA, 9, 8))
add("missing_both", c(1, NA, 4, 6, NA, 10), c(2, NA, 3, 7, NA, 8))

# Canonical public PEFR example copied from installed DescTools::CCC help,
# section Examples, labelled Figure 2 from Bland and Altman (1986).
add("desctools_public_pefr",
    c(494, 395, 516, 434, 476, 557, 413, 442, 650, 433, 417, 656, 267, 478, 178, 423, 427),
    c(512, 430, 520, 428, 500, 600, 364, 380, 658, 445, 432, 626, 260, 477, 259, 350, 451),
    "Installed DescTools help('CCC'), Examples: Bland and Altman Figure 2 PEFR pairs.")

for (i in seq_len(20L)) {
  n <- 5L + 3L * i
  x <- round(rnorm(n, mean = (i %% 5) - 2, sd = .5 + i / 8), 6)
  slope <- c(.3, .75, 1, 1.4, -.6)[(i - 1L) %% 5L + 1L]
  y <- round((i %% 4) - 1.5 + slope * x + rnorm(n, sd = .2 + i / 20), 6)
  if (i %% 4L == 0L) {
    x[c(2, n - 1L)] <- NA_real_
    y[c(3, n - 1L)] <- NA_real_
  }
  add(sprintf("seeded_moderate_%02d", i), x, y)
}

degenerate <- list(
  list(id = "empty", x = numeric(), y = numeric()),
  list(id = "single_equal", x = 3, y = 3),
  list(id = "single_unequal", x = 3, y = 5),
  list(id = "constant_equal", x = rep(3, 4), y = rep(3, 4)),
  list(id = "constant_unequal", x = rep(3, 4), y = rep(5, 4)),
  list(id = "constant_x", x = rep(3, 4), y = c(1, 2, 4, 7)),
  list(id = "constant_y", x = c(1, 2, 4, 7), y = rep(3, 4)),
  list(id = "all_pairs_missing", x = c(NA, 1, NA), y = c(1, NA, NA))
)

nonfinite <- function(z) {
  if (is.nan(z)) "NaN" else if (is.na(z)) "NA" else if (is.infinite(z)) {
    if (z > 0) "Inf" else "-Inf"
  } else NULL
}

base_reference <- function(x, y) {
  n <- length(x)
  mean_x <- mean(x)
  mean_y <- mean(y)
  variance_x <- sum((x - mean_x)^2) / n
  variance_y <- sum((y - mean_y)^2) / n
  covariance <- sum((x - mean_x) * (y - mean_y)) / n
  denominator <- variance_x + variance_y + (mean_x - mean_y)^2
  list(ccc = 2 * covariance / denominator,
       precision = covariance / sqrt(variance_x * variance_y),
       bias_correction = 2 * sqrt(variance_x * variance_y) / denominator,
       mean_x = mean_x, mean_y = mean_y,
       variance_x = variance_x, variance_y = variance_y,
       covariance = covariance, denominator = denominator)
}

prepare <- function(item, is_degenerate = FALSE) {
  # Enumerated from raw vector positions, independently of DescTools na.rm.
  keep <- which(!is.na(item$x) & !is.na(item$y))
  x <- item$x[keep]
  y <- item$y[keep]
  expected <- base_reference(x, y)
  out <- list(
    id = item$id, note = if (is.null(item$note)) "" else item$note,
    x = I(as.numeric(item$x)), y = I(as.numeric(item$y)),
    n_input = length(item$x), n_complete = length(keep),
    missing_x = sum(is.na(item$x)), missing_y = sum(is.na(item$y)),
    missing_either = sum(is.na(item$x) | is.na(item$y)),
    missing_both = sum(is.na(item$x) & is.na(item$y)),
    retained_indices = I(as.integer(keep - 1L)), expected = expected)
  if (is_degenerate) {
    out$formula_nonfinite <- lapply(expected, nonfinite)
    out$note <- paste("Base-R formula outcomes only; JSON null plus formula_nonfinite labels",
                      "represent undefined values. No estimate or acceptance policy is invented.",
                      "DescTools parity is not asserted for degenerate inputs.")
    return(out)
  }
  warnings <- character()
  ref <- withCallingHandlers(DescTools::CCC(item$x, item$y, na.rm = TRUE),
    warning = function(w) {
      warnings <<- c(warnings, conditionMessage(w))
      invokeRestart("muffleWarning")
    })
  package_values <- list(ccc = unname(ref$rho.c[1, "est"]),
                         precision = unname(stats::cor(x, y)),
                         bias_correction = unname(ref$C.b))
  compared <- vapply(names(package_values), function(key) {
    is.finite(package_values[[key]]) &&
      abs(package_values[[key]] - expected[[key]]) <= tolerance
  }, logical(1))
  # DescTools computes Cb as CCC/r; its 0/0 NaN at exactly zero r is
  # documented as an oracle limitation, never substituted for direct Cb.
  limitation <- expected$precision == 0 && is.nan(package_values$bias_correction)
  stopifnot(compared[["ccc"]], compared[["precision"]],
            compared[["bias_correction"]] || limitation)
  out$desctools <- package_values
  out$desctools_nonfinite <- lapply(package_values, nonfinite)
  out$desctools_cb_zero_r_limitation <- limitation
  out$desctools_warnings <- I(unique(warnings))
  out$absolute_difference <- lapply(names(package_values), function(key) {
    abs(package_values[[key]] - expected[[key]])
  })
  names(out$absolute_difference) <- names(package_values)
  out
}

result <- list(
  schema_version = 1L,
  metadata = list(seed = seed, normalization = "population (divide by n complete pairs)",
    missing_policy = "pairwise complete observations; input null is missing",
    retained_index_base = 0L, tolerance = tolerance,
    r_version = R.version.string,
    desctools_version = as.character(utils::packageVersion("DescTools")),
    jsonlite_version = as.character(utils::packageVersion("jsonlite")),
    package_call = "DescTools::CCC(x, y, na.rm = TRUE); point estimates only",
    public_data_source = "Installed DescTools help('CCC'), Examples, PEFR Figure 2",
    independence = "Base R arithmetic and DescTools; no target implementation read or executed",
    session_info = I(capture.output(utils::sessionInfo()))),
  cases = lapply(cases, prepare),
  degenerate_cases = lapply(degenerate, prepare, is_degenerate = TRUE))
result$metadata$case_count <- length(result$cases)
result$metadata$degenerate_case_count <- length(result$degenerate_cases)
result$metadata$desctools_unexpected_mismatches <- 0L
result$metadata$desctools_zero_r_cb_limitations <- sum(vapply(
  result$cases, function(x) x$desctools_cb_zero_r_limitation, logical(1)))

file_arg <- grep("^--file=", commandArgs(FALSE), value = TRUE)
stopifnot(length(file_arg) == 1L)
script_path <- normalizePath(sub("^--file=", "", file_arg))
output <- file.path(dirname(dirname(script_path)), "fixtures", "concordance-points.json")
dir.create(dirname(output), recursive = TRUE, showWarnings = FALSE)
jsonlite::write_json(result, output, auto_unbox = TRUE, pretty = TRUE,
                     digits = NA, null = "null", na = "null")
cat(sprintf("Wrote %d regular and %d degenerate cases; DescTools %s; unexpected mismatches 0; zero-r Cb limitations %d.\n",
            length(result$cases), length(result$degenerate_cases),
            result$metadata$desctools_version,
            result$metadata$desctools_zero_r_cb_limitations))
