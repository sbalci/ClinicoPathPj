# R side of the ClinicoPathPj bridge. Each generated .b.R calls .cpjRun(); one Python process
# per run reads a request file and writes a response file (inst/python/cpj_runtime.py). While it
# runs, R polls it and calls jamovi's checkpoint, so an option change cancels a stale run at once.

.cpjTimeout <- 60
.cpjMaxConsole <- 100000

# jamovi renders table cells, notes and notices as HTML, so a "<" before a letter would start a
# tag and swallow the text; notes and notices also lose a trailing " [word]" to translation, and
# the notice renderer treats U+0004 as a translation delimiter, so control characters are dropped.
.cpjSafeText <- function(x, brackets = FALSE) {
    x <- gsub("[\001-\010\013\014\016-\037\177]", "", as.character(x), perl = TRUE)
    x <- gsub("<(?=[A-Za-z/!?])", "< ", x, perl = TRUE)
    if (brackets) chartr("[]", "()", x) else x
}

# jamovi's engine runs with PYTHONHOME set to its bundled Python and an empty PATH,
# so the interpreter is found from PYTHONHOME, never through PATH.
.cpjPython <- function() {
    home <- Sys.getenv("PYTHONHOME")
    path <- if (identical(Sys.info()[["sysname"]], "Darwin") && nzchar(home))
        file.path(dirname(home), "MacOS", "python") else ""
    if (!nzchar(path) || !file.exists(path))
        jmvcore::reject("jamovi's bundled Python was not found. ClinicoPathPj has so far only been verified with jamovi for macOS.")
    list(path = path, env = c(PYTHONHOME = home, PYTHONPATH = ""))
}

.cpjColumn <- function(x, name) {
    if (is.factor(x)) {  # preserve labels/unused levels, including a literal "NA" label
        if (anyNA(levels(x))) levels(x) <- levels(x)
        codes <- as.integer(x) - 1L
        # A genuine NA factor level is not is.na(x); encode its observations as missing.
        codes[codes %in% (which(is.na(levels(x))) - 1L)] <- NA_integer_
        return(list(kind = "factor", levels = I(levels(x)), codes = I(codes), ordered = is.ordered(x)))
    }
    if (is.numeric(x)) {
        if (any(is.infinite(x)))
            jmvcore::reject("{}", msg = paste0("'", name, "' contains infinite values; recode them as missing first."))
        return(list(kind = "number", values = I(as.double(x))))
    }
    list(kind = "text", values = I(as.character(x)))
}

.cpjNotice <- function(self, type, text, index) {
    name <- paste0("cpjNotice", index)
    severity <- if (identical(type, "INFO")) jmvcore::NoticeType$INFO else jmvcore::NoticeType$WARNING
    notice <- self$results$get(name)
    if (is.null(notice)) {
        notice <- jmvcore::Notice$new(self$options, name = name, type = severity)
        self$results$insert(1, notice)  # the results group always holds the declared items
    }
    notice$set(severity, .cpjSafeText(gsub("\\s+", " ", text), brackets = TRUE))
    notice$setVisible(TRUE)
}

# Replace computed native state only on successful or pending runs. On failure,
# jamovi keeps the previous results greyed behind its error, as usual.
.cpjClearNative <- function(self, clearOutputs = FALSE) {
    for (item in self$results$items) {
        if (inherits(item, "Table")) {
            item$deleteRows()
            for (key in names(item$notes)) item$setNote(key, NULL)
        } else if (inherits(item, "Output") && clearOutputs && isTRUE(item$enabled) && item$isFilled()) {
            # Pending selections cannot safely materialize self$data. The successful
            # run stores only its row identities in the output element state.
            previous <- item$state
            if (!is.null(previous$cpjRowIds)) {
                item$setRowNums(unlist(previous$cpjRowIds, use.names = FALSE))
                item$setValues(rep(NA_integer_, length(previous$cpjRowIds)))
            }
        } else if (inherits(item, "Image")) {
            item$setState(NULL)
        } else if (inherits(item, "Notice") && startsWith(item$name, "cpjNotice")) {
            # A prior computed advisory no longer applies; this never signals failure.
            item$setVisible(FALSE)
        }
    }
}

.cpjTail <- function(text) {
    if (nchar(text) > .cpjMaxConsole) substr(text, nchar(text) - .cpjMaxConsole + 1, nchar(text)) else text
}

# Runs Python and waits for it. Cancellation wins over completion: the checkpoint is called after
# every poll, including the one that sees the process end. The process is killed whenever this
# function exits early (jamovi's restart condition, timeout, error), before the caller deletes
# the request directory; a cleanup failure never replaces the original condition.
.cpjExecute <- function(python, args, checkpoint, timeout = .cpjTimeout) {
    process <- NULL
    finished <- FALSE
    on.exit(if (!finished && !is.null(process)) {
        try(process$kill(), silent = TRUE)       # SIGKILL to -pid: Python's whole process group
        try(process$kill_tree(), silent = TRUE)  # descendants that left the group but kept processx's marker
    }, add = TRUE)
    process <- tryCatch(
        processx::process$new(python$path, args, env = c("current", python$env),
                              stdout = "|", stderr = "|", cleanup_tree = TRUE, supervise = TRUE),
        error = function(e) stop("Could not start Python at ", python$path, ": ", conditionMessage(e), call. = FALSE))
    started <- Sys.time()
    output <- ""
    collect <- function() {  # drain both pipes so output written straight to the fds cannot block Python
        new <- paste0(process$read_output(), process$read_error())
        if (nzchar(new)) output <<- .cpjTail(paste0(output, new))
    }
    repeat {
        # poll_io() reports a pipe at EOF as ready forever, which would spin while Python still runs
        open <- Filter(Negate(is.null), list(
            if (process$is_incomplete_output()) process$get_output_connection(),
            if (process$is_incomplete_error()) process$get_error_connection()))
        if (length(open)) processx::poll(open, 200) else process$wait(200)
        collect()
        if (!is.null(checkpoint)) checkpoint()  # throws jamovi's restart condition after an option change
        if (!process$is_alive()) break
        if (as.numeric(difftime(Sys.time(), started, units = "secs")) > timeout)
            stop("The Python analysis did not finish within ", timeout, " seconds and was stopped.", call. = FALSE)
    }
    for (i in 1:20) {  # whatever is still in the pipes; a stray child holding them must not block us
        open <- Filter(Negate(is.null), list(
            if (process$is_incomplete_output()) process$get_output_connection(),
            if (process$is_incomplete_error()) process$get_error_connection()))
        if (!length(open)) break
        processx::poll(open, 50)
        collect()
    }
    finished <- TRUE
    list(status = process$get_exit_status(), output = output)
}

.cpjPlotState <- function(plot) {
    if (length(plot$columns[[1]]) == 0)
        return(NULL)  # no rows: no state, so jamovi shows the empty placeholder, not a spinner
    types <- .cpjPlotColumns[[plot$kind]]
    data <- lapply(stats::setNames(names(types), names(types)), function(column) {
        values <- plot$columns[[column]]
        if (types[[column]] == "text")
            vapply(values, function(v) if (is.null(v)) NA_character_ else as.character(v), character(1))
        else
            vapply(values, function(v) if (is.null(v)) NA_real_ else as.numeric(v), numeric(1))
    })
    list(kind = plot$kind, data = as.data.frame(data, stringsAsFactors = FALSE),
         xlab = plot$xlab, ylab = plot$ylab, step = isTRUE(plot$step),
         reference = if (is.null(plot$reference)) NULL else as.numeric(plot$reference))
}

.cpjRun <- function(self, name, options, arrays = character(0), numeric = character(0),
                    required = character(0), events = character(0), terms = character(0), checkpoint = NULL) {
    # jmvcore restores Preformatted and Text content from the saved state, so clear it first:
    # otherwise an earlier run's traceback or interpretation would still show under this run's results.
    for (item in self$results$items)
        if (inherits(item, "Preformatted") || inherits(item, "Text")) item$setContent("")
    for (item in self$results$items)
        if (inherits(item, "Html") || inherits(item, "Svg")) item$setContent("<div></div>")
    # Every path that reaches Python's answer, or decides not to start it, replaces this.
    self$results$console$setContent("No report from Python: the run stopped with the error shown above.")
    notStarted <- function(why) {  # the console says why, instead of showing nothing
        self$results$console$setContent(paste("Python was not started:", why))
        invisible(NULL)
    }

    values <- lapply(stats::setNames(options, options), function(option) self$options$get(option))

    # Unconfigured is not an error: nothing chosen -> stay quiet; partly chosen -> say what is missing.
    unset <- vapply(names(required), function(option) length(values[[option]]) == 0, logical(1))
    if (any(unset)) {
        .cpjClearNative(self, clearOutputs = TRUE)
        if (!all(unset))
            .cpjNotice(self, "INFO", paste0("To run this analysis, also choose: ",
                                            paste(required[unset], collapse = ", "), "."), 1)
        return(notStarted(paste0("choose ", paste(required[unset], collapse = ", "), ".")))
    }
    # An event level is never guessed: until it is chosen, list the levels and wait.
    for (level in names(events)) {
        variable <- values[[events[[level]]]]
        if (length(variable) == 1 && is.null(values[[level]])) {
            .cpjClearNative(self, clearOutputs = TRUE)
            counts <- table(self$data[[variable]])  # data rows, not weighted counts
            .cpjNotice(self, "INFO", paste0("Choose which level of ", variable, " is the event: ",
                paste0(names(counts), " (", as.integer(counts), " rows)", collapse = ", "), "."), 1)
            return(notStarted(paste0("choose which level of ", variable, " is the event.")))
        }
    }
    for (option in arrays)  # a single chosen variable must still reach Python as a list
        values[[option]] <- as.list(as.character(values[[option]]))
    for (option in terms)
        values[[option]] <- lapply(values[[option]], function(term) as.list(as.character(term)))

    # Integer Nominal/Ordinal columns reach numeric-only boxes as factors carrying their values.
    numericColumns <- unlist(values[numeric], use.names = FALSE)
    columns <- lapply(stats::setNames(names(self$data), names(self$data)), function(column) {
        x <- self$data[[column]]
        if (column %in% numericColumns) x <- jmvcore::toNumeric(x)
        .cpjColumn(x, column)
    })
    python <- .cpjPython()
    runtime <- system.file("python", "cpj_runtime.py", package = "ClinicoPathPj", mustWork = TRUE)
    dir <- tempfile("cpj")
    dir.create(dir)
    on.exit(unlink(dir, recursive = TRUE), add = TRUE)
    request <- file.path(dir, "request.json")
    response <- file.path(dir, "response.json")
    json <- jsonlite::toJSON(list(schema_version = 1, analysis = name, options = values,
                             row_ids = as.list(rownames(self$data)), columns = columns),
                             auto_unbox = TRUE, na = "null", null = "null", digits = I(17))
    writeBin(charToRaw(enc2utf8(as.character(json))), request)

    run <- .cpjExecute(python, c("-B", "-s", runtime, request, response), checkpoint)
    if (!file.exists(response)) {
        self$results$console$setContent(paste(c(
            "Python stopped before it answered. What run() printed is passed on only with an answer, so it was lost.",
            if (nzchar(run$output)) c("Python's own error output:", run$output)), collapse = "\n"))
        why <- if (run$status < 0) paste0("Python was killed by signal ", -run$status, ".")
               else paste0("Python exited with status ", run$status, ".")
        stop(paste(c(paste("Python returned no result.", why), utils::tail(strsplit(run$output, "\n")[[1]], 15)),
                   collapse = "\n"), call. = FALSE)
    }
    result <- tryCatch(jsonlite::fromJSON(response, simplifyVector = FALSE),
        error = function(e) stop("Python returned an unreadable result: ", conditionMessage(e), call. = FALSE))
    if (!is.null(checkpoint)) checkpoint()  # an option change while reading still wins

    # Show the runtime's report and what Python printed and warned, before raising anything.
    output <- .cpjTail(paste(c(if (isTRUE(nzchar(result$console))) result$console,
                               if (nzchar(run$output)) run$output), collapse = "\n"))
    self$results$console$setContent(paste(c(if (is.character(result$report)) result$report,
        "----- Python output -----", if (nzchar(output)) output else "(the analysis printed nothing)"),
        collapse = "\n"))
    if (identical(result$status, "ok")) .cpjClearNative(self)
    for (i in rev(seq_along(result$notices)))
        .cpjNotice(self, result$notices[[i]]$type, result$notices[[i]]$text, i)

    if (identical(result$status, "input_error"))
        jmvcore::reject("{}", msg = result$error$message)
    if (!identical(result$status, "ok"))
        stop(if (is.null(result$error$message)) "Python returned an unknown status." else result$error$message,
             " (tick 'Python console output' for details)", call. = FALSE)

    for (table in names(result$tables)) {
        element <- self$results$get(table)
        if (!inherits(element, "Table"))
            stop("Python returned rows for '", table, "', which is not a table of this analysis.", call. = FALSE)
        rows <- result$tables[[table]]$rows
        for (i in seq_along(rows)) {
            cells <- lapply(rows[[i]], function(value) {
                if (is.null(value)) NA else if (is.character(value)) .cpjSafeText(value) else value
            })
            element$addRow(rowKey = i, values = cells)
        }
        notes <- result$tables[[table]]$notes
        for (j in seq_along(notes))
            element$setNote(paste0("cpjNote", j), .cpjSafeText(notes[[j]], brackets = TRUE))
    }
    for (text in names(result$texts))  # Preformatted (plain text) and Text (Markdown) results
        self$results$get(text)$setContent(gsub("[\001-\010\013\014\016-\037\177]", "", result$texts[[text]],
                                               perl = TRUE))
    for (name in names(result$htmls)) {
        element <- self$results$get(name)
        if (!inherits(element, "Html"))
            stop("Python returned HTML for a non-HTML result.", call. = FALSE)
        element$setContent(result$htmls[[name]])
    }
    for (name in names(result$svgs)) {
        element <- self$results$get(name)
        if (!inherits(element, "Svg"))
            stop("Python returned SVG for a non-SVG result.", call. = FALSE)
        element$setContent(result$svgs[[name]])
    }
    for (plot in names(result$plots)) {
        element <- self$results$get(plot)
        if (!inherits(element, "Image"))
            stop("Python returned a plot for '", plot, "', which is not an image of this analysis.", call. = FALSE)
        element$setState(.cpjPlotState(result$plots[[plot]]))
    }
    for (name in names(result$outputs)) {
        element <- self$results$get(name)
        if (!inherits(element, "Output")) stop("Python returned an undeclared saved column.", call. = FALSE)
        column <- result$outputs[[name]]
        if (!is.null(column$title) || !is.null(column$measure_type)) {
            element$set(keys = 1L, titles = column$title,
                descriptions = column$description, measureTypes = column$measure_type)
        }
        ids <- unlist(column$row_ids, use.names = FALSE)
        if (!identical(ids, rownames(self$data)) || length(column$values) != nrow(self$data))
            stop("Saved column row alignment does not match the input data.", call. = FALSE)
        values <- vapply(column$values, function(x) if (is.null(x)) NA_real_ else as.numeric(x), numeric(1))
        if (!is.null(column$levels)) values <- factor(values,
            levels = seq_along(column$levels) - 1L, labels = unlist(column$levels, use.names = FALSE),
            ordered = identical(column$measure_type, "ordinal"))
        element$setRowNums(ids)
        element$setValues(values)
        element$setState(list(cpjRowIds = as.list(ids)))
    }
    invisible(NULL)
}
