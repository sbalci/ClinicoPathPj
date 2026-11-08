# Isolated public-service check. Does not install/replace either jamovi module.
# Use jamovi's R home (system R cannot discover its bundled Python).
# Rscript tools/check-pj-service-lifecycle.R <Pj R library> [CPJ R library]
args <- commandArgs(TRUE)
if (!length(args)) stop("Supply the R library from an unpacked Pj >=1.5.0 package")
command <- commandArgs()
script <- sub("^--file=", "", grep("^--file=", command, value = TRUE))
if (!length(script) && "-f" %in% command) script <- command[match("-f", command) + 1L]
root <- dirname(dirname(normalizePath(script)))
cpj <- if (length(args) > 1L) args[[2]] else file.path(root, "build/R4.6.0-arm64-macos")
.libPaths(c(normalizePath(args[[1]]), normalizePath(cpj),
    "/Applications/jamovi.app/Contents/Resources/modules/base/R", .libPaths()))
Sys.setenv(PYTHONHOME = "/Applications/jamovi.app/Contents/Resources",
    PYTHONPATH = "/Applications/jamovi.app/Contents/Resources/jamovi/server")
setwd("/Applications/jamovi.app/Contents/MacOS")
library(ClinicoPathPj)
jmvcore:::initProtoBuf()
env <- new.env(parent = asNamespace("ClinicoPathPj"))
sys.source(file.path(root, "R/utils-pj-service.R"), env)
service <- env$.cpjPjService()
stopifnot(utils::compareVersion(service$info$module_version, "1.5.0") >= 0L,
    "checkpoint" %in% names(formals(service$run)),
    isTRUE(service$info$capabilities$checkpoint))
before <- .libPaths()
request <- jsonlite::toJSON(list(schema_version = 1L, analysis = "pydecisioncalculator",
    options = list(tp = 14L, fp = 0L, fn = 41L, tn = 125L),
    columns = list(), row_ids = list()), auto_unbox = TRUE)
calls <- 0L
got <- env$.cpjPjExecute(request, service = service,
    checkpoint = function() calls <<- calls + 1L)
stopifnot(identical(got$result$status, "ok"), calls > 0L,
    identical(vapply(got$result$tables$counts$rows, function(x) x$n, integer(1)),
        c(14L, 0L, 41L, 125L)),
    identical(got$service$runner, "processx"), isTRUE(got$service$checkpoint_enabled),
    identical(got$service$capabilities$timeout_scope, "call"))
cat("Packaged Pj", service$info$module_version,
    "CPJ envelope/counts/checkpoint/metadata PASS; callbacks:", calls, "\n")

marker <- structure(list(message = "service restart probe", call = NULL, code = "restart"),
    class = c("simpleError", "error", "condition"))
started <- proc.time()[["elapsed"]]
signal <- tempfile("cpj-main-started-")
cancelled <- tryCatch(service$run(code = paste0("import time\n",
    "with open(data['signal'][0], 'w') as f: f.write('started')\n",
    "time.sleep(30)"), data = data.frame(signal = signal), timeout = 20L,
    checkpoint = function() if (file.exists(signal)) stop(marker)), error = identity)
mainStarted <- file.exists(signal)
unlink(signal)
stopifnot(identical(cancelled, marker), proc.time()[["elapsed"]] - started < 10)
stopifnot(mainStarted)
cat("Real service cancellation during main Python preserves restart and returns promptly: PASS\n")

expired <- tryCatch(service$run(code = "import time; time.sleep(5)", timeout = 1L),
    error = identity)
stopifnot(inherits(expired, "mzPjServiceError"), identical(expired$kind, "timeout"))
cat("Real service timeout condition: PASS\n")
recovered <- env$.cpjPjExecute(request, service = service)
stopifnot(identical(recovered$result$status, "ok"),
    !isTRUE(recovered$service$checkpoint_enabled), identical(before, .libPaths()))
cat("Recovery after cancellation/timeout; unchanged library paths: PASS\n")
cat("Scope: bundled Python on macOS arm64, R service calls only. No desktop, System Python,",
    "descendant-process inspection or cross-platform qualification.\n")
