# Check the interpreter selected by Pj's public System Python route; install nothing.
# --empty-path checks discovery under the empty PATH used by the engine-like R tests.
# --clean-environment is a diagnostic control; --adapter-only tests CPJ's installed adapter.
main <- function() {
    args <- commandArgs(TRUE)
    if (any(!args %in% c("--empty-path", "--clean-environment", "--adapter-only"))) stop("Unknown System Python probe flag")
    empty_path <- "--empty-path" %in% args
    module_root <- path.expand("~/Library/Application Support/jamovi/modules")
    .libPaths(c(Sys.getenv("CPJ_LIBRARY", file.path(module_root, "ClinicoPathPj", "R")),
        file.path(module_root, "Pj", "R"),
        "/Applications/jamovi.app/Contents/Resources/modules/base/R", .libPaths()))
    Sys.setenv(PYTHONHOME = "/Applications/jamovi.app/Contents/Resources",
        PYTHONPATH = "/Applications/jamovi.app/Contents/Resources/jamovi/server")
    library(ClinicoPathPj)
    jmvcore:::initProtoBuf()
    if (empty_path) Sys.setenv(PATH = "") # This child R process only.
    service <- ClinicoPathPj:::.cpjPjService()
    clean_environment <- "--clean-environment" %in% args
    if (clean_environment) {
        original_run <- service$run
        service$run <- function(..., python = "jamovi", checkpoint = NULL) {
            if (identical(python, "system")) {
                keys <- c("PYTHONHOME", "PYTHONPATH")
                saved <- Sys.getenv(keys, unset = NA_character_)
                on.exit({
                    Sys.unsetenv(keys)
                    present <- saved[!is.na(saved)]
                    if (length(present)) do.call(Sys.setenv, as.list(present))
                }, add = TRUE)
                Sys.unsetenv(keys)
            }
            original_run(..., python = python, checkpoint = checkpoint)
        }
    }
    interpreter <- NULL
    before <- Sys.getenv(c("PYTHONHOME", "PYTHONPATH"), unset = NA_character_)
    outcome <- tryCatch({
        if (!"--adapter-only" %in% args) {
        probe <- service$run(python = "system", code = paste(c(
            "import json, platform, sys",
            "info = dict(executable=sys.executable, version=platform.python_version(), machine=platform.machine())",
            "for name in ('numpy', 'scipy'):",
            "    try:",
            "        module = __import__(name)",
            "        info[name] = module.__version__",
            "    except ImportError as e: info[name] = str(e)",
            "mzpjShowText(json.dumps(info), name='systemProbe')"), collapse = "\n"))
        item <- Filter(function(x) identical(x$name, "systemProbe") && identical(x$type, "Text"), probe$items)
        stopifnot(length(item) == 1L)
        interpreter <- jsonlite::fromJSON(item[[1]]$content)
        }
        request <- jsonlite::toJSON(list(schema_version = 1L, analysis = "pydecisioncalculator",
            options = list(tp = 14L, fp = 0L, fn = 41L, tn = 125L),
            columns = list(), row_ids = list()), auto_unbox = TRUE)
        calls <- 0L
        system <- ClinicoPathPj:::.cpjPjExecute(request, python = "system", service = service,
            checkpoint = function() calls <<- calls + 1L)
        bundled <- ClinicoPathPj:::.cpjPjExecute(request, python = "jamovi", service = service)
        stopifnot(identical(system$result$status, "ok"), calls > 0L,
            identical(system$service$python, "system"),
            isTRUE(system$service$checkpoint_enabled),
            isTRUE(all.equal(system$result$tables, bundled$result$tables, tolerance = 1e-10)))
        failed <- tryCatch(ClinicoPathPj:::.cpjPjExecute("not json", python = "system", service = service),
            error = identity)
        stopifnot(inherits(failed, "mzPjServiceError"), identical(failed$kind, "python"))
        recovered <- ClinicoPathPj:::.cpjPjExecute(request, python = "system", service = service)
        stopifnot(identical(recovered$result$status, "ok"))
        list(status = "pass", interpreter = interpreter, matching_accuracy_tables = TRUE,
            checkpoint_enabled = TRUE, python_error_recovery = TRUE)
    }, error = function(e) list(status = "unqualified", error = conditionMessage(e),
        kind = if (is.null(e$kind)) "probe" else e$kind, details = e$details))
    candidate <- unname(Sys.which("python3"))
    outcome$system_candidate <- if (nzchar(candidate)) normalizePath(candidate) else NULL
    outcome$empty_path <- empty_path
    outcome$clean_environment <- clean_environment
    outcome$adapter_only <- "--adapter-only" %in% args
    if (!is.null(interpreter)) outcome$interpreter <- interpreter
    outcome$pj_version <- service$info$module_version
    outcome$cpj_version <- as.character(packageVersion("ClinicoPathPj"))
    outcome$environment_restored <- identical(before,
        Sys.getenv(c("PYTHONHOME", "PYTHONPATH"), unset = NA_character_))
    if (!isTRUE(outcome$environment_restored)) outcome$status <- "unqualified"
    outcome$scope <- "macOS R API probe; not native GUI or other-platform qualification"
    cat(jsonlite::toJSON(outcome, auto_unbox = TRUE, pretty = TRUE), "\n")
    if (identical(outcome$status, "pass")) 0L else 2L
}
quit(status = main())
