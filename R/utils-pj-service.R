# Optional Pj API v1 transport. The host retains its own statistical/result contract.
.cpjPjService <- function() {
    if ("Pj" %in% loadedNamespaces()) {
        namespace <- getNamespace("Pj")
    } else {
        libraries <- .libPaths()
        roots <- strsplit(Sys.getenv("JAMOVI_MODULES_PATH"), .Platform$path.sep,
                          fixed = TRUE)[[1]]
        candidates <- unique(c(libraries,
            file.path(dirname(dirname(libraries)), "Pj", "R"),
            file.path(roots[nzchar(roots)], "Pj", "R")))
        candidates <- candidates[file.exists(file.path(candidates, "Pj", "DESCRIPTION"))]
        if (!length(candidates))
            stop("This optional route requires the Pj jamovi module 1.3.0 or newer. Install Pj and restart jamovi, or select the processx route.", call. = FALSE)
        namespace <- loadNamespace("Pj", lib.loc = candidates[1])
    }
    exports <- getNamespaceExports(namespace)
    if (!all(c("mzPjServiceInfo", "mzPjRunPython") %in% exports))
        stop("The loaded Pj has no public service API. Update Pj to 1.3.0 or newer and restart jamovi.", call. = FALSE)
    info <- getExportedValue("Pj", "mzPjServiceInfo")()
    if (!identical(info$api_version, 1L) ||
        utils::compareVersion(info$module_version, "1.3.0") < 0L)
        stop("This route requires Pj 1.3.0 or newer with service API version 1.", call. = FALSE)
    list(info = info, run = getExportedValue("Pj", "mzPjRunPython"))
}

.cpjPjExecutionNote <- function(service) {
    paste0("Pj ", service$module_version, "; runner: ",
        if (is.null(service$runner)) "not reported" else service$runner, "; ",
        if (isTRUE(service$checkpoint_enabled)) "checkpoint enabled" else "no running checkpoint",
        "; ", if (identical(service$capabilities$timeout_scope, "call"))
            "shared call timeout" else "per-subprocess timeout (legacy service)", ".")
}

.cpjPjExecute <- function(request, python = "jamovi", service = NULL, checkpoint = NULL) {
    if (is.null(service)) service <- .cpjPjService()
    if (identical(python, "system")) {
        # jamovi's Python paths cannot be reused by a different interpreter.
        keys <- c("PYTHONHOME", "PYTHONPATH")
        saved <- Sys.getenv(keys, unset = NA_character_)
        if (identical(Sys.info()[["sysname"]], "Darwin") &&
            !is.na(saved[["PYTHONHOME"]]) && nzchar(saved[["PYTHONHOME"]])) {
            bundled <- file.path(dirname(saved[["PYTHONHOME"]]), "MacOS", "python")
            candidates <- unname(Sys.which(c("python3", "python")))
            candidates <- candidates[nzchar(candidates)]
            if (file.exists(bundled) && length(candidates) &&
                identical(normalizePath(candidates[[1]]), normalizePath(bundled)))
                stop("System Python currently resolves to jamovi's bundled interpreter. Choose jamovi Python, or configure an external Python on PATH before starting jamovi.", call. = FALSE)
        }
        on.exit({
            Sys.unsetenv(keys)
            present <- saved[!is.na(saved)]
            if (length(present)) do.call(Sys.setenv, as.list(present))
        }, add = TRUE)
        Sys.unsetenv(keys)
    }
    root <- system.file("python", package = "ClinicoPathPj", mustWork = TRUE)
    # Only a trusted package path is embedded as a JSON literal. User values stay data.
    root <- as.character(jsonlite::toJSON(root, auto_unbox = TRUE))
    code <- paste0("import sys, json\nsys.path.insert(0, ", root, ")\n",
        "from cpj_runtime import execute\n",
        "request = json.loads(data['request'][0])\n",
        "response = execute(request)\n",
        "mzpjShowText(json.dumps(response, ensure_ascii=True, allow_nan=False), name='cpjEnvelope')\n")
    args <- list(code = code,
        data = data.frame(request = as.character(request), stringsAsFactors = FALSE),
        python = python, timeout = as.integer(.cpjTimeout), return_columns = FALSE)
    # API v1 predates checkpoint support. Do not send new arguments to old runners.
    # An explicit FALSE capability overrides the signature; ... alone is insufficient.
    if ("checkpoint" %in% names(formals(service$run)) &&
        !identical(service$info$capabilities$checkpoint, FALSE))
        args$checkpoint <- checkpoint
    response <- do.call(service$run, args)
    matches <- Filter(function(item) identical(item$name, "cpjEnvelope") &&
        identical(item$type, "Text"), response$items)
    if (length(matches) != 1L || !is.character(matches[[1]]$content) ||
        length(matches[[1]]$content) != 1L || nchar(matches[[1]]$content, type = "bytes") > 10000000L)
        stop("Pj returned an invalid or oversized ClinicoPathPj result envelope.", call. = FALSE)
    result <- jsonlite::fromJSON(matches[[1]]$content, simplifyVector = FALSE)
    if (!is.list(result) || !identical(result$schema_version, 1L) ||
        !is.character(result$status) || length(result$status) != 1L ||
        is.na(result$status) || !result$status %in% c("ok", "input_error", "exception"))
        stop("Pj returned an unsupported ClinicoPathPj result contract.", call. = FALSE)
    list(result = result, output = "", service = response$service)
}
