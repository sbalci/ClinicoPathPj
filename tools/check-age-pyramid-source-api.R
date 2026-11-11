# Compare source calculations through own/Pj execution without rebuilding the host.
# Usage: Rscript --vanilla this-file.R <source-root> <Pj-library> [--system] [--service-smoke]
# Optional: --python=/path/to/python --site-packages=/existing/path --all --timeout=60
# --summaries compares the matched summary utilities using the same source/API transport.
# Use an isolated source copy during local file-access problems; install nothing.
args <- commandArgs(TRUE)
if (length(args) < 2L) stop("Supply source root and installed Pj R library")
root <- normalizePath(args[1L], mustWork = TRUE)
pj_library <- normalizePath(args[2L], mustWork = TRUE)
flags <- args[-c(1L, 2L)]
if (any(!grepl("^(--system|--all|--summaries|--service-smoke|--timeout=[0-9]+|--python=.+|--site-packages=.+)$", flags))) stop("Unknown flag")
if (all(c("--summaries", "--service-smoke") %in% flags)) stop("Choose one probe type")
value <- function(prefix, default = "") {
    x <- flags[startsWith(flags, prefix)]
    if (length(x) > 1L) stop("Repeated flag: ", prefix)
    if (length(x)) substring(x, nchar(prefix) + 1L) else default
}
deadline <- as.integer(value("--timeout=", "60"))
if (is.na(deadline) || deadline < 1L || deadline > 300L) stop("Timeout must be 1 to 300 seconds")
mode <- if ("--system" %in% flags) "system" else "jamovi"
python <- value("--python=", if (mode == "system") unname(Sys.which("python3"))
                else "/Applications/jamovi.app/Contents/MacOS/python")
if (!nzchar(python) || !file.exists(python)) stop("Own-route interpreter is missing")
python <- normalizePath(python)
extra_site <- value("--site-packages=")
if (nzchar(extra_site)) extra_site <- normalizePath(extra_site, mustWork = TRUE)
.libPaths(c(pj_library, "/Applications/jamovi.app/Contents/Resources/modules/base/R", .libPaths()))
# Standalone R must initialize the result classes normally supplied by the engine.
jmvcore:::initProtoBuf()
ns <- loadNamespace("Pj", lib.loc = pj_library)
info <- getExportedValue("Pj", "mzPjServiceInfo")()
run_service <- getExportedValue("Pj", "mzPjRunPython")
stopifnot(identical(info$api_version, 1L),
          utils::compareVersion(info$module_version, "1.5.0") >= 0L)
if (mode == "system") {
    # This R child only; never pass jamovi's Python home into an external interpreter.
    Sys.unsetenv(c("PYTHONHOME", "PYTHONPATH"))
} else Sys.setenv(PYTHONHOME = "/Applications/jamovi.app/Contents/Resources",
                 PYTHONPATH = "/Applications/jamovi.app/Contents/Resources/jamovi/server")
Sys.setenv(OPENBLAS_NUM_THREADS = "1", OMP_NUM_THREADS = "1")
quote_json <- function(x) as.character(jsonlite::toJSON(x, auto_unbox = TRUE))
entry <- paste0("import sys, json\nsys.path.insert(0, ",
    quote_json(file.path(root, "inst", "python")), ")\n",
    if (nzchar(extra_site)) paste0("sys.path.append(", quote_json(extra_site), ")\n") else "",
    "from cpj_runtime import execute\n",
    "def calculate(request):\n",
    "    result = execute(request)\n",
    "    import numpy, platform\n",
    "    return {'result': result, 'python': sys.executable, 'version': platform.python_version(), 'numpy': numpy.__version__, 'numpy_file': numpy.__file__}\n")
if ("--service-smoke" %in% flags) {
    cat("Public Pj service smoke; version", info$module_version, "mode", mode,
        "timeout", deadline, "seconds\n"); flush.console()
    response <- tryCatch(run_service(
        code = "mzpjShowText(str(int(sum(data['x']))), name='smoke')",
        data = data.frame(x = 1:3), python = mode, timeout = deadline,
        checkpoint = function() invisible(NULL)), error = function(error) {
            if (identical(error$code, "restart")) stop(error)
            if (!is.null(error$kind)) cat("Pj error kind:", error$kind, "\n")
            if (!is.null(error$details)) cat("Pj error details:\n", error$details, "\n")
            stop(error)
        })
    items <- Filter(function(x) identical(x$type, "Text") && identical(x$name, "smoke"), response$items)
    stopifnot(length(items) == 1L, identical(items[[1L]]$content, "6"),
        identical(response$service$runner, "processx"), isTRUE(response$service$checkpoint_enabled))
    cat("Public service simple sum PASSED; no ClinicoPathPj calculation or NumPy required\n")
    quit(status = 0L)
}
run_pair <- function(request, service_name, folder) {
    path <- file.path(folder, "request.json")
    writeLines(jsonlite::toJSON(request, auto_unbox = TRUE, na = "null", null = "null"), path)
    own_code <- paste0(entry, "request = json.load(open(sys.argv[1]))\n",
                       "print(json.dumps(calculate(request), allow_nan=False))\n")
    script <- file.path(folder, "own.py"); writeLines(own_code, script)
    own <- processx::run(python, c("-S", "-B", script, path), timeout = deadline,
                         error_on_status = TRUE, cleanup_tree = TRUE)
    own <- jsonlite::fromJSON(own$stdout, simplifyVector = FALSE)
    stopifnot(identical(own$result$status, "ok"))
    cat("Own source calculation PASSED;", own$python, "Python", own$version,
        "NumPy", own$numpy, "\n"); flush.console()
    request$analysis <- service_name
    json <- as.character(jsonlite::toJSON(request, auto_unbox = TRUE, na = "null", null = "null"))
    response <- tryCatch(run_service(code = paste0(entry,
        "mzpjShowText(json.dumps(calculate(json.loads(data['request'][0])), allow_nan=False), name='sourceEnvelope')\n"),
        data = data.frame(request = json), python = mode, timeout = deadline,
        checkpoint = function() invisible(NULL)), error = function(error) {
            if (identical(error$code, "restart")) stop(error)
            if (!is.null(error$kind)) cat("Pj error kind:", error$kind, "\n")
            if (!is.null(error$details)) cat("Pj error details:\n", error$details, "\n")
            stop(error)
        })
    stopifnot(identical(response$service$runner, "processx"),
              isTRUE(response$service$checkpoint_enabled))
    items <- Filter(function(x) identical(x$type, "Text") && identical(x$name, "sourceEnvelope"), response$items)
    stopifnot(length(items) == 1L, is.character(items[[1]]$content), length(items[[1]]$content) == 1L)
    pj <- jsonlite::fromJSON(items[[1]]$content, simplifyVector = FALSE)
    stopifnot(identical(pj$result$status, "ok"),
        identical(normalizePath(own$python), normalizePath(pj$python)),
        identical(own$version, pj$version), identical(own$numpy, pj$numpy),
        identical(normalizePath(own$numpy_file), normalizePath(pj$numpy_file)))
    for (field in c("tables", "plots", "notices"))
        stopifnot(identical(own$result[[field]], pj$result[[field]]))
    cat("Matched interpreter/dependency provenance;", pj$python, "Python", pj$version,
        "NumPy", pj$numpy, "from", pj$numpy_file, "\n"); flush.console()
    pj$result
}

if ("--summaries" %in% flags) {
    fixtures <- list(c(1, 2, 3, 4, NA, 10), c(7, NA), c(NA_real_, NA_real_),
                     c(-2, 0, 0, 4, 1e4))
    if (!"--all" %in% flags) fixtures <- fixtures[1L]
    cat("Summary source API probe; Pj", info$module_version, "; requested", mode,
        "; own interpreter", python, "; timeout", deadline, "seconds\n"); flush.console()
    folder <- tempfile("cpj-summary-source-api-"); dir.create(folder)
    tryCatch({
        for (x in fixtures) {
            request <- list(schema_version = 1L, analysis = "pyservicedirect",
                options = list(measurement = "x"),
                columns = list(x = list(kind = "number", values = as.list(x))))
            result <- run_pair(request, "pyservicepj", folder)
            rows <- result$tables$summary$rows
            stopifnot(length(rows) == 1L)
            kept <- x[!is.na(x)]
            expected <- c(input = length(x), n = length(kept), missing = sum(is.na(x)),
                mean = if (length(kept)) mean(kept) else NA_real_, sd = sd(kept),
                median = if (length(kept)) median(kept) else NA_real_,
                minimum = if (length(kept)) min(kept) else NA_real_,
                maximum = if (length(kept)) max(kept) else NA_real_)
            actual <- vapply(names(expected), function(key)
                if (is.null(rows[[1L]][[key]])) NA_real_ else as.numeric(rows[[1L]][[key]]), numeric(1))
            stopifnot(isTRUE(all.equal(actual, expected, tolerance = 1e-12)))
            cat("Summary actual own/Pj payloads and independent base R oracle PASSED; input",
                length(x), "retained", length(kept), "\n"); flush.console()
        }
    }, finally = unlink(folder, recursive = TRUE))
    quit(status = 0L)
}
d <- read.csv(file.path(root, "data/python_age_pyramid_service_examples.csv"))
levels <- c("Male", "Other", "Female", "Unused")
columns <- list(Age = list(kind = "number", values = as.list(d$Age)),
    Gender = list(kind = "factor", levels = as.list(levels),
                  codes = as.list(match(d$Gender, levels) - 1L)))
keep <- !is.na(d$Age) & !is.na(d$Gender) & d$Age >= 0 & d$Gender %in% c("Female", "Male")
expected <- table(cut(d$Age[keep], c(seq(0, 85, 5), Inf), right = FALSE),
                  factor(d$Gender[keep], levels = c("Female", "Male")))
expected <- expected[rowSums(expected) > 0L, , drop = FALSE]
configurations <- if ("--all" %in% flags)
    expand.grid(base = c("within_gender", "total"), display = c("count", "percent"),
                stringsAsFactors = FALSE) else data.frame(base = "within_gender", display = "count")
cat("Source API probe; Pj", info$module_version, "; requested", mode,
    "; own interpreter", python, "; timeout", deadline, "seconds\n"); flush.console()
folder <- tempfile("cpj-source-api-"); dir.create(folder)
tryCatch({
    for (i in seq_len(nrow(configurations))) {
        option <- list(age = "Age", gender = "Gender", female = "Female", male = "Male",
            age_groups = "who", pct_base = configurations$base[i],
            plot_values = configurations$display[i], showInterpretation = TRUE)
        request <- list(schema_version = 1L, analysis = "pyagepyramid", options = option, columns = columns)
        result <- run_pair(request, "pyagepyramidpj", folder)
        rows <- result$tables$population$rows
        number <- function(key) vapply(rows[-length(rows)], function(x) as.numeric(x[[key]]), numeric(1))
        stopifnot(identical(number("female"), as.numeric(expected[, 1L])),
                  identical(number("male"), as.numeric(expected[, 2L])))
        pct <- if (configurations$base[i] == "total") expected / sum(expected)
               else sweep(expected, 2L, colSums(expected), "/")
        stopifnot(isTRUE(all.equal(number("femalePercent"), as.numeric(pct[, 1L]), tolerance = 1e-12)),
                  isTRUE(all.equal(number("malePercent"), as.numeric(pct[, 2L]), tolerance = 1e-12)))
        cat(configurations$base[i], configurations$display[i],
            "actual own/Pj payloads and independent base R oracle PASSED\n"); flush.console()
    }
}, finally = unlink(folder, recursive = TRUE))
