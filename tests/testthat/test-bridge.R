test_that("displayed text keeps markup-like content visible", {
    safe <- ClinicoPathPj:::.cpjSafeText
    expect_equal(safe("<b>x</b> [abc]", brackets = TRUE), "< b>x< /b> (abc)")
    expect_equal(safe("<5 years"), "<5 years")
    expect_equal(safe("p < 0.05 [ref]"), "p < 0.05 [ref]")  # cells keep brackets
    # the notice renderer splits on U+0004 and decodes what follows as JSON
    expect_equal(safe("a\004{}\033b\tc\nd"), "a{}b\tc\nd")
})

test_that("factor columns keep level order, unused levels and missing values", {
    column <- ClinicoPathPj:::.cpjColumn(factor(c("b", NA, "a"), levels = c("a", "b", "z")), "g")
    expect_equal(column$kind, "factor")
    expect_equal(unclass(column$levels), c("a", "b", "z"))
    expect_equal(unclass(column$codes), c(1L, NA, 0L))
})

pythonChildren <- function() {  # live Python processes started by this R process
    Filter(function(h) isTRUE(tryCatch(grepl("python", ps::ps_name(h), ignore.case = TRUE), error = function(e) FALSE)),
           ps::ps_children(ps::ps_handle(), recursive = TRUE))
}

test_that("a checkpoint condition stops Python at once and leaves no process behind", {
    python <- ClinicoPathPj:::.cpjPython()
    started <- Sys.time()
    expect_error(ClinicoPathPj:::.cpjExecute(python, c("-B", "-s", "-c", "import time; time.sleep(30)"),
        checkpoint = function() if (difftime(Sys.time(), started, units = "secs") > 0.5) stop("restart requested")),
        "restart requested")
    expect_lt(as.numeric(difftime(Sys.time(), started, units = "secs")), 5)
    expect_length(pythonChildren(), 0)
})

test_that("a run over the time limit is stopped, even inside C code", {
    started <- Sys.time()
    expect_error(ClinicoPathPj:::.cpjExecute(ClinicoPathPj:::.cpjPython(),
        c("-B", "-s", "-c", "sum(range(10**11))"), checkpoint = NULL, timeout = 1), "did not finish within 1 seconds")
    expect_lt(as.numeric(difftime(Sys.time(), started, units = "secs")), 5)
    expect_length(pythonChildren(), 0)
})

test_that("jamovi's restart request (an option change) ends the analysis in 'restarting'", {
    d <- data.frame(y = c(1, 2, 3, 4, 6, 8, 7, 9), g = factor(rep(c("a", "b"), each = 4)))
    analysis <- pywelchClass$new(options = pywelchOptions$new(dep = "y", group = "g", refLevel = NULL), data = d)
    analysis$.setCheckpoint(function(results) "restart")  # what the engine answers after an option change
    expect_error({ analysis$init(); analysis$run() }, "restarting")
    expect_equal(analysis$status, "restarting")
    expect_length(pythonChildren(), 0)
})

test_that("a Python process that dies without answering is reported, with what it printed", {
    d <- data.frame(y = c(1, 2, 3, 4, 6, 8, 7, 9), g = factor(rep(c("a", "b"), each = 4)))
    analysis <- pywelchClass$new(options = pywelchOptions$new(dep = "y", group = "g", refLevel = NULL,
                                                              showConsole = TRUE), data = d)
    analysis$.setCheckpoint(function(...) {  # as if Python crashed: killed before it could answer
        for (child in pythonChildren()) ps::ps_send_signal(child, ps::signals()$SIGKILL)
        NULL
    })
    expect_error({ analysis$init(); analysis$run() }, "Python returned no result. Python was killed by signal 9.",
                 fixed = TRUE)
    expect_equal(analysis$results$console$content, paste("Python stopped before it answered.",
                 "What run() printed is passed on only with an answer, so it was lost."))
})

test_that("infinite values are rejected and the column name is shown as written", {
    expect_error(ClinicoPathPj:::.cpjColumn(c(1, Inf), "Ki {67}"), "'Ki {67}' contains infinite values",
                 fixed = TRUE)
})

test_that("stopping a run also kills what Python started", {
    marker <- tempfile()
    script <- "import subprocess, sys, time; p = subprocess.Popen(['/bin/sleep', '30']); open(sys.argv[1], 'w').write(str(p.pid)); time.sleep(30)"
    expect_error(ClinicoPathPj:::.cpjExecute(ClinicoPathPj:::.cpjPython(), c("-B", "-s", "-c", script, marker),
        checkpoint = function() if (file.exists(marker) && file.size(marker) > 0) stop("restart requested")),
        "restart requested")
    sleeper <- as.integer(readLines(marker, warn = FALSE))
    for (i in 1:20) if (sleeper %in% ps::ps_pids()) Sys.sleep(0.1) else break  # reaped once its parent is gone
    expect_false(sleeper %in% ps::ps_pids())  # /bin/sleep: kill_tree() alone cannot see Apple binaries
})

test_that("a closed pipe does not make the wait loop spin", {
    calls <- 0
    ClinicoPathPj:::.cpjExecute(ClinicoPathPj:::.cpjPython(),
        c("-B", "-s", "-c", "import os, time; os.dup2(os.open(os.devnull, os.O_WRONLY), 2); time.sleep(2)"),
        checkpoint = function() calls <<- calls + 1)
    expect_gt(calls, 3)
    expect_lt(calls, 40)  # one poll per 200 ms; a pipe at EOF polled as ready would call it thousands of times
})

test_that("processx comes from jamovi itself, so the module ships no compiled code", {
    expect_true(startsWith(find.package("processx"), "/Applications/jamovi.app/"))
})

test_that("a plot with no rows has no state", {
    expect_null(ClinicoPathPj:::.cpjPlotState(list(kind = "interval",
        columns = list(label = list(), estimate = list(), lower = list(), upper = list()))))
})
