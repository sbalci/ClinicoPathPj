# Source the hand-written adapter so these tests also work before rebuilding the JMO.
pjBridge <- function() {
    env <- new.env(parent = asNamespace("ClinicoPathPj"))
    sys.source(testthat::test_path("..", "..", "R", "utils-pj-service.R"), env)
    sys.source(testthat::test_path("..", "..", "R", "utils-python.R"), env)
    env
}

pjAnswer <- function() list(items = list(list(name = "cpjEnvelope", type = "Text",
    content = '{"schema_version":1,"status":"ok","tables":{},"plots":{},"texts":{}}')),
    service = list(module_version = "1.5.0", runner = "processx",
        checkpoint_enabled = TRUE, capabilities = list(timeout_scope = "call")))

test_that("System calls isolate and restore Python environment on every exit", {
    env <- pjBridge()
    keys <- c("PYTHONHOME", "PYTHONPATH")
    cases <- list(c(PYTHONHOME = "bundled-home", PYTHONPATH = "bundled-path"),
        c(PYTHONHOME = "", PYTHONPATH = ""),
        c(PYTHONHOME = NA_character_, PYTHONPATH = NA_character_))
    for (values in cases) withr::with_envvar(values, {
        original <- Sys.getenv(keys, unset = NA_character_)
        for (mode in c("ok", "error", "restart")) {
            problem <- structure(list(message = mode, call = NULL,
                code = if (mode == "restart") "restart" else NULL),
                class = c("simpleError", "error", "condition"))
            service <- list(run = function(...) {
                expect_true(all(is.na(Sys.getenv(keys, unset = NA_character_))))
                if (mode != "ok") stop(problem)
                pjAnswer()
            })
            result <- tryCatch(env$.cpjPjExecute("{}", python = "system", service = service),
                error = identity)
            expect_identical(Sys.getenv(keys, unset = NA_character_), original)
            if (mode == "ok") expect_identical(result$result$status, "ok")
            else expect_identical(result, problem)
        }
        service <- list(run = function(...) {
            expect_identical(Sys.getenv(keys, unset = NA_character_), original)
            pjAnswer()
        })
        expect_identical(env$.cpjPjExecute("{}", python = "jamovi", service = service)$result$status, "ok")
    })
})

test_that("a bundled executable on System PATH is rejected without changing the environment", {
    skip_if_not(identical(Sys.info()[["sysname"]], "Darwin"))
    binary <- "/Applications/jamovi.app/Contents/MacOS/python"
    skip_if_not(file.exists(binary))
    folder <- withr::local_tempdir()
    expect_true(file.symlink(binary, file.path(folder, "python3")))
    env <- pjBridge()
    called <- FALSE
    service <- list(run = function(...) { called <<- TRUE; pjAnswer() })
    withr::with_envvar(c(PATH = folder, PYTHONHOME = "/Applications/jamovi.app/Contents/Resources",
        PYTHONPATH = "bundled-server"), {
        before <- Sys.getenv(c("PYTHONHOME", "PYTHONPATH"))
        expect_error(env$.cpjPjExecute("{}", python = "system", service = service),
            "System Python currently resolves to jamovi's bundled interpreter", fixed = TRUE)
        expect_identical(Sys.getenv(c("PYTHONHOME", "PYTHONPATH")), before)
        expect_false(called)
    })
})

test_that("new services receive the caller checkpoint and old signatures do not", {
    env <- pjBridge()
    calls <- 0L
    callback <- function() calls <<- calls + 1L
    modern <- list(info = list(capabilities = list(checkpoint = TRUE)),
        run = function(..., checkpoint = NULL) {
            expect_identical(checkpoint, callback)
            checkpoint()
            pjAnswer()
        })
    env$.cpjPjExecute("{}", service = modern, checkpoint = callback)
    expect_identical(calls, 1L)
    # Older API v1 runners have no checkpoint formal (even if they accept ...).
    old <- list(run = function(...) {
        expect_false("checkpoint" %in% names(list(...)))
        pjAnswer()
    })
    env$.cpjPjExecute("{}", service = old, checkpoint = callback)
    expect_identical(calls, 1L)
    modern$info$capabilities$checkpoint <- FALSE
    modern$run <- function(..., checkpoint = NULL) {
        expect_null(checkpoint)
        pjAnswer()
    }
    env$.cpjPjExecute("{}", service = modern, checkpoint = callback)
})

test_that("host service cancellation preserves the exact restart condition", {
    env <- pjBridge()
    marker <- structure(list(message = "restart requested", call = NULL, code = "restart"),
        class = c("simpleError", "error", "condition"))
    env$.cpjPjService <- function() list(
        info = list(capabilities = list(checkpoint = TRUE)),
        run = function(..., checkpoint = NULL) {
            checkpoint()
            stop("cancel callback was lost")
        })
    ns <- asNamespace("ClinicoPathPj")
    analysis <- get("pybridgecompareClass", ns)$new(
        options = get("pybridgecompareOptions", ns)$new(
            marker = "x", reference = "g", positive = "P", execution = "pj"),
        data = data.frame(x = 1:4, g = factor(c("N", "N", "P", "P"))))
    analysis$init()
    calls <- 0L
    got <- tryCatch(env$.cpjRun(analysis, "pybridgecompare",
        options = c("marker", "reference", "positive"), backend = "pj",
        timing = "backendTiming", checkpoint = function() {
            calls <<- calls + 1L
            if (calls == 2L) stop(marker)
        }), error = identity)
    expect_identical(calls, 2L)
    expect_identical(got, marker)
    expect_false(grepl("restart requested", analysis$results$console$content, fixed = TRUE))
})

test_that("service timing describes actual capabilities rather than API version alone", {
    env <- pjBridge()
    modern <- env$.cpjPjExecutionNote(pjAnswer()$service)
    expect_match(modern, "1.5.0", fixed = TRUE)
    expect_match(modern, "checkpoint enabled", fixed = TRUE)
    expect_match(modern, "shared call timeout", fixed = TRUE)
    old <- env$.cpjPjExecutionNote(list(module_version = "1.3.0"))
    expect_match(old, "no running checkpoint", fixed = TRUE)
    expect_match(old, "per-subprocess timeout", fixed = TRUE)
    expect_false(grepl("shared call timeout", old, fixed = TRUE))
})

test_that("ordinary service failures keep diagnostics and do not become restart conditions", {
    env <- pjBridge()
    problem <- structure(list(message = "service deadline expired", call = NULL,
        kind = "timeout", details = "isolated service diagnostic"),
        class = c("mzPjServiceError", "error", "condition"))
    env$.cpjPjService <- function() list(run = function(...) stop(problem))
    ns <- asNamespace("ClinicoPathPj")
    analysis <- get("pybridgecompareClass", ns)$new(
        options = get("pybridgecompareOptions", ns)$new(
            marker = "x", reference = "g", positive = "P", execution = "pj"),
        data = data.frame(x = 1:4, g = factor(c("N", "N", "P", "P"))))
    analysis$init()
    got <- tryCatch(env$.cpjRun(analysis, "pybridgecompare",
        options = c("marker", "reference", "positive"), backend = "pj"), error = identity)
    expect_identical(conditionMessage(got), "service deadline expired")
    expect_null(got$code)
    expect_identical(analysis$results$console$content, "isolated service diagnostic")
})
