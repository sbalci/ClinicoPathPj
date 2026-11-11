# Third-source adjudication for ill-conditioned near-boundary transformed CCC SE.
# Run from repo root: LANG=en_US.UTF-8 Rscript --vanilla tests/reference/concordance-intervals-mpfr.R
# Original concordance-intervals fixtures remain untouched, including discrepancies.
stopifnot(requireNamespace("Rmpfr", quietly = TRUE), requireNamespace("jsonlite", quietly = TRUE),
          requireNamespace("digest", quietly = TRUE))
suppressPackageStartupMessages(library(Rmpfr))
source_path <- "tests/fixtures/concordance-intervals.json"
source <- jsonlite::fromJSON(source_path, simplifyVector = FALSE)
precision <- 256L
mp <- function(x) mpfr(x, precBits = precision)
fmt <- function(x) unname(format(x, digits = 75, scientific = TRUE, trim = TRUE))
sha <- function(x) digest::digest(x, algo = "sha256", serialize = FALSE)
rows <- lapply(c("near_identity", "near_reversal"), function(id) {
  case <- Filter(function(x) identical(x$id, id), source$fixtures)[[1]]
  xd <- unlist(case$x); yd <- unlist(case$y)
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
    base <- case$runs[[i]]$base_r$value
    list(confidence = confidence, n = n, rho = fmt(rho), r = fmt(r), Cb = fmt(cb),
      u_squared = fmt(u2), variance = fmt(variance), se = fmt(se), z = fmt(z),
      z_se = fmt(z_se), critical_z_double = critical_double,
      critical_z_binary_hex = sprintf("%a", critical_double),
      z_limits = as.list(fmt(zl)), back_transformed_limits = as.list(fmt(tanh(zl))),
      wald_limits = as.list(fmt(wald)),
      base_fixture_z_se = base$z_se,
      base_fixture_z_se_minus_mpfr = fmt(mp(base$z_se) - z_se),
      base_fixture_rho_minus_mpfr = fmt(mp(base$rho) - rho),
      one_minus_rho_squared = fmt(1 - rho^2))
  })
  list(id = id, input_hex = input_hex, input_binary_hex_sha256 = input_hash, runs = runs)
})
result <- list(schema_version = 1L, precision_bits = precision,
  purpose = paste("Third-source adjudication of double cancellation in transformed SE near |CCC|=1.",
    "Original double oracle and mismatches retained unchanged; this supplements its precision."),
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
jsonlite::write_json(result, "tests/fixtures/concordance-intervals-mpfr.json",
  pretty = TRUE, auto_unbox = TRUE, digits = NA)
cat("MPFR256 cases:", length(rows), "; confidence runs:", length(rows) * 5L, "\n")
