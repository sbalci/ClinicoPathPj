# Independent MPFR oracle for CCC high-precision transition cases.
# Run from repo root: LANG=en_US.UTF-8 Rscript --vanilla tests/reference/concordance-intervals-transition.R
# Existing concordance fixtures remain untouched, including discrepancies.
stopifnot(requireNamespace("Rmpfr", quietly = TRUE), requireNamespace("jsonlite", quietly = TRUE),
          requireNamespace("digest", quietly = TRUE))
suppressPackageStartupMessages(library(Rmpfr))
source_path <- "tests/fixtures/concordance-intervals.json"
source <- jsonlite::fromJSON(source_path, simplifyVector = FALSE)
precision <- 256L
mp <- function(x) mpfr(x, precBits = precision)
fmt <- function(x) unname(format(x, digits = 75, scientific = TRUE, trim = TRUE))
sha <- function(x) digest::digest(x, algo = "sha256", serialize = FALSE)
noise_levels <- c(.1, .008, .005, .004)
rows <- lapply(noise_levels, function(noise) {
  id <- paste0("transition_noise_", format(noise, scientific = FALSE, trim = TRUE))
  xd <- as.double(1:12)
  yd <- xd + noise * rep(c(-1, 2, -2, 1), 3)
  # Hexadecimal doubles specify exact binary inputs, independently of JSON decimals.
  input_hex <- list(x = sprintf("%a", xd), y = sprintf("%a", yd))
  input_hash <- sha(paste(c(input_hex$x, input_hex$y), collapse = "\n"))
  x <- mp(xd); y <- mp(yd); n <- length(x)
  dx <- x - mean(x); dy <- y - mean(y)
  vx <- sum(dx * dx) / n; vy <- sum(dy * dy) / n
  covariance <- sum(dx * dy) / n
  denominator <- vx + vy + (mean(y) - mean(x))^2
  rho <- 2 * covariance / denominator
  r <- covariance / sqrt(vx * vy)
  cb <- 2 * sqrt(vx * vy) / denominator
  u2 <- (mean(y) - mean(x))^2 / sqrt(vx * vy)
  variance <- (rho^2 * (1 - r^2) * (1 - rho^2) / r^2 +
    2 * rho^3 * (1 - rho) * u2 / r - rho^4 * u2^2 / (2 * r^2)) / (n - 2)
  se <- sqrt(variance); z <- atanh(rho); z_se <- se / (1 - rho^2)
  runs <- lapply(seq_along(source$confidence_levels), function(i) {
    confidence <- source$confidence_levels[[i]]
    # qnorm is evaluated in standard double precision then lifted exactly to MPFR.
    critical_double <- qnorm((1 + confidence) / 2)
    critical <- mp(critical_double)
    zl <- z + mp(c(-1, 1)) * critical * z_se
    wald <- rho + mp(c(-1, 1)) * critical * se
    # Independent double arithmetic is retained beside high precision for adjudication.
    ddx <- xd - mean(xd); ddy <- yd - mean(yd)
    dvx <- sum(ddx * ddx) / n; dvy <- sum(ddy * ddy) / n
    dcov <- sum(ddx * ddy) / n
    drho <- 2 * dcov / (dvx + dvy + (mean(yd) - mean(xd))^2)
    dr <- dcov / sqrt(dvx * dvy)
    du2 <- (mean(yd) - mean(xd))^2 / sqrt(dvx * dvy)
    dv <- (drho^2 * (1 - dr^2) * (1 - drho^2) / dr^2 +
      2 * drho^3 * (1 - drho) * du2 / dr -
      drho^4 * du2^2 / (2 * dr^2)) / (n - 2)
    base <- list(rho = drho, z_se = sqrt(dv) / (1 - drho^2))
    list(confidence = confidence, n = n, rho = fmt(rho), r = fmt(r), Cb = fmt(cb),
      u_squared = fmt(u2), variance = fmt(variance), se = fmt(se), z = fmt(z),
      z_se = fmt(z_se), critical_z_double = critical_double,
      critical_z_binary_hex = sprintf("%a", critical_double),
      z_limits = as.list(fmt(zl)), back_transformed_limits = as.list(fmt(tanh(zl))),
      wald_limits = as.list(fmt(wald)),
      base_double_z_se = base$z_se,
      base_double_z_se_minus_mpfr = fmt(mp(base$z_se) - z_se),
      base_double_rho_minus_mpfr = fmt(mp(base$rho) - rho),
      one_minus_rho_squared = fmt(1 - rho^2))
  })
  list(id = id, noise = noise, x = xd, y = yd, input_hex = input_hex, input_binary_hex_sha256 = input_hash, runs = runs)
})
result <- list(schema_version = 1L, precision_bits = precision,
  purpose = paste("Independent transition-case oracle for transformed SE sensitivity near |CCC|=1.",
    "Original fixtures retained unchanged. Double cross-product reference also recorded."),
  numerical_contract = paste("All moments and Lin corrected variance operations use MPFR256",
    "on exact binary input doubles, with divisor n for moments and n-2 for variance.",
    "atanh and tanh use MPFR256. Standard double qnorm critical values are treated as exact inputs.",
    "High precision outputs are decimal strings with 75 significant digits; no rounding to double."),
  source_fixture = source_path,
  source_fixture_sha256 = digest::digest(file = source_path, algo = "sha256"),
  source_reference_sha256 = digest::digest(file = "tests/reference/concordance-intervals.R", algo = "sha256"),
  source_seed = source$seed, confidence_levels = source$confidence_levels,
  versions = list(R = R.version.string, Rmpfr = as.character(packageVersion("Rmpfr")),
    gmp = as.character(packageVersion("gmp")), jsonlite = as.character(packageVersion("jsonlite")),
    digest = as.character(packageVersion("digest"))),
  session_info = capture.output(sessionInfo()), fixtures = rows)
jsonlite::write_json(result, "tests/fixtures/concordance-intervals-transition.json",
  pretty = TRUE, auto_unbox = TRUE, digits = NA)
cat("Transition MPFR256 cases:", length(rows), "; confidence runs:", length(rows) * 5L, "\n")
