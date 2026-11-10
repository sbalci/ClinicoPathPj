# Execute both packaged host analyses, including the real installed Pj service.
# Usage: bundled R -f tools/check-service-examples.R --args <host-library> <Pj-library>
args <- commandArgs(TRUE)
stopifnot(length(args) == 2L)
.libPaths(c(normalizePath(args[1]), normalizePath(args[2]),
    "/Applications/jamovi.app/Contents/Resources/modules/base/R", .libPaths()))
Sys.setenv(PYTHONHOME = "/Applications/jamovi.app/Contents/Resources",
           PYTHONPATH = "/Applications/jamovi.app/Contents/Resources/jamovi/server")
setwd("/Applications/jamovi.app/Contents/MacOS")
suppressPackageStartupMessages(library(ClinicoPathPj))
jmvcore:::initProtoBuf()
cat("Host", as.character(packageVersion("ClinicoPathPj")),
    "Pj", ClinicoPathPj:::.cpjPjService()$info$module_version, "\n")
fixtures <- list(c(1, 2, 3, 4, NA, 10), c(7, NA), c(NA_real_, NA_real_),
                 c(-2, 0, 0, 4, 1e4))
for (x in fixtures) {
    d <- data.frame(x = x)
    own <- pyservicedirect(d, measurement = "x")$summary$asDF
    pj <- pyservicepj(d, measurement = "x")$summary$asDF
    stopifnot(identical(own, pj))
    kept <- x[!is.na(x)]
    expected <- c(input = length(x), n = length(kept), missing = sum(is.na(x)),
        mean = if(length(kept)) mean(kept) else NA_real_, sd = sd(kept),
        median = if(length(kept)) median(kept) else NA_real_,
        minimum = if(length(kept)) min(kept) else NA_real_,
        maximum = if(length(kept)) max(kept) else NA_real_)
    stopifnot(nrow(own) == 1L,
        isTRUE(all.equal(as.numeric(own[1, names(expected)]), unname(expected), tolerance = 1e-12)))
    cat("Matched routes and independent base R summary: input", length(x),
        "retained", length(kept), "PASSED\n")
}
# Input error followed by successful reuse of each route.
for (fun in list(pyservicedirect, pyservicepj)) {
    bad <- try(fun(data.frame(x = Inf), measurement = "x"), silent = TRUE)
    stopifnot(inherits(bad, "try-error"))
    good <- fun(data.frame(x = c(1, 3)), measurement = "x")$summary$asDF
    stopifnot(good$n == 2L, good$mean == 2)
}
cat("Error recovery on both routes PASSED\n")
