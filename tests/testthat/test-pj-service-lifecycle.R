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
