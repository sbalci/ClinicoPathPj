# Independent base-R/moments/classInt fixtures. This developer tool never runs in jamovi.
script <- sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE))
root <- dirname(dirname(normalizePath(script)))
.libPaths(c(path.expand("~/Library/Application Support/jamovi/modules/ClinicoPathDescriptives/R"),
  "/Applications/jamovi.app/Contents/Resources/modules/base/R", .libPaths()))
ns <- asNamespace("ClinicoPathDescriptives")
temporary <- tempfile("cpj-descriptive-oracle-"); dir.create(temporary)
archive <- file.path(root, "docs", "baselines", "released-2026-10-25.tar.gz")
utils::untar(archive, files = "ClinicoPathDescriptives/R/categorize.b.R", exdir = temporary)
env <- new.env(parent = ns)
sys.source(file.path(temporary, "ClinicoPathDescriptives/R/categorize.b.R"), envir = env)
obj <- env$categorizeClass$new(options = get("categorizeOptions", ns)$new(var = "x"), data = data.frame(x = 1:10))
private <- obj$.__enclos_env__$private
numeric_cases <- list(
  simple = c(1, 2, 3, 4, 9, 20, NA),
  negative = c(-11, -7, -5, -2, 0, 3, 4, 9),
  constant = rep(5, 10), singleton = 4, two = c(1, 4),
  ties = c(0, 0, 0, 1, 1, 2, 10, NA, NA),
  tiny = c(.0001, .0002, .0003, .0004, .0009),
  large_n = sin(seq_len(5001) / 37) + seq_len(5001) / 10000)
summary <- lapply(names(numeric_cases), function(name) {
  raw <- numeric_cases[[name]]; x <- raw[!is.na(raw)]; n <- length(x)
  sw <- if (n >= 3 && n <= 5000 && length(unique(x)) > 1) shapiro.test(x) else NULL
  q <- unname(quantile(x, c(.25,.5,.75), type = 7))
  list(name = name, x = I(raw), expected = list(n = n, missing = sum(is.na(raw)),
    mean = mean(x), sd = sd(x), minimum = min(x), q1 = q[1], median = q[2], q3 = q[3], maximum = max(x),
    w = if (is.null(sw)) NULL else unname(sw$statistic), p = if (is.null(sw)) NULL else sw$p.value,
    skewness = if (n >= 3 && length(unique(x)) > 1) moments::skewness(x) else NULL,
    kurtosis = if (n >= 3 && length(unique(x)) > 1) moments::kurtosis(x) else NULL,
    lower = if (n >= 4) q[1] - 1.5 * (q[3]-q[1]) else NULL,
    upper = if (n >= 4) q[3] + 1.5 * (q[3]-q[1]) else NULL))
})
cases <- list()
add <- function(x, method = "quantile", nbins = 4L, manual = "", multiplier = 1,
                exclude = FALSE, include = TRUE, right = TRUE, label_style = "auto", custom = "") {
  clean <- x[!is.na(x)]
  b <- private$.calculateBreaks(clean, method, nbins, manual, multiplier, extend_to_data = !exclude)
  b <- sort(unique(b))
  if (!isTRUE(private$.validateBreaks(b)$valid)) return(invisible(NULL))
  labels <- private$.generateLabels(b, label_style, custom, include, right)
  assigned <- cut(x, breaks = b, labels = labels, include.lowest = include, right = right, ordered_result = TRUE)
  cases[[length(cases)+1L]] <<- list(x = I(x), method = method, nbins = nbins,
    manual = manual, multiplier = multiplier, exclude = exclude, include = include, right = right,
    label_style = label_style, custom = custom, breaks = I(b), labels = I(labels),
    codes = I(as.integer(assigned) - 1L), counts = I(as.integer(table(assigned))))
}
x <- c(-5, -3, -1, 0, 1, 2, 3, 4, 7, 20, NA)
for (method in c("equal", "quantile", "meansd", "median", "jenks")) {
  for (right in c(TRUE,FALSE)) for (include in c(TRUE,FALSE))
    add(x, method = method, nbins = 3L, right = right, include = include)
}
for (right in c(TRUE,FALSE)) for (include in c(TRUE,FALSE)) for (exclude in c(TRUE,FALSE))
  add(c(-1,0,1,2,3,4,5,6,NA), "manual", manual = "0,2,4", right = right, include = include, exclude = exclude)
for (style in c("auto","semantic","numbered","lettered","custom"))
  add(x, label_style = style, custom = "first, second, third, fourth")
add(x, label_style = "custom", custom = "duplicate, duplicate")
add(c(0,0,0,0,1,1,1,2), nbins = 4L)
add(c(.001,.0012,.0013,.0018,.002,.0021), nbins = 3L)
add(x, "manual", manual = "2")
add(x, "manual", manual = "4,2,2,0", exclude = TRUE)
add(c(1,2,8,9), "jenks", nbins = 4L)
add(c(1,2,20), "jenks", nbins = 4L)
set.seed(376)
for (i in seq_len(100)) {
  x <- sample(1:20, 5 + i %% 15, replace = TRUE)
  if (length(unique(x)) > 2) add(x, "jenks", nbins = 2L + i %% 3)
}
result <- list(provenance = list(date = "2026-10-25", R = R.version.string,
  moments = as.character(packageVersion("moments")), classInt = as.character(packageVersion("classInt")),
  baseline = "docs/baselines/released-2026-10-25.tar.gz"), summaries = summary, categories = cases)
jsonlite::write_json(result, file.path(root,"tests/fixtures/descriptive-oracles.json"),
                     auto_unbox=TRUE, na="null", null="null", digits=NA, pretty=TRUE)
unlink(temporary, recursive=TRUE)
cat(length(summary), "summary fixtures and", length(cases), "categorization fixtures written\n")
