# Packaged own/Pj routes with an independent base R age-band oracle.
# Usage: bundled R -f tools/check-age-pyramid-service.R --args <host-library> <Pj-library>
args <- commandArgs(TRUE)
stopifnot(length(args) == 2L)
command <- commandArgs()
script <- sub("^--file=", "", grep("^--file=", command, value = TRUE))
if (!length(script) && "-f" %in% command) script <- command[match("-f", command) + 1L]
root <- dirname(dirname(normalizePath(script)))
.libPaths(c(normalizePath(args[1]), normalizePath(args[2]),
    "/Applications/jamovi.app/Contents/Resources/modules/base/R", .libPaths()))
Sys.setenv(PYTHONHOME = "/Applications/jamovi.app/Contents/Resources",
    PYTHONPATH = "/Applications/jamovi.app/Contents/Resources/jamovi/server")
setwd("/Applications/jamovi.app/Contents/MacOS")
suppressPackageStartupMessages(library(ClinicoPathPj))
jmvcore:::initProtoBuf()
cat("Host", as.character(packageVersion("ClinicoPathPj")),
    "Pj", ClinicoPathPj:::.cpjPjService()$info$module_version, "\n")
d <- read.csv(file.path(root, "data/python_age_pyramid_service_examples.csv"))
d$Gender <- factor(d$Gender, levels = c("Male", "Other", "Female", "Unused"))
keep <- !is.na(d$Age) & !is.na(d$Gender) & d$Age >= 0 & d$Gender %in% c("Female", "Male")
bins <- cut(d$Age[keep], breaks = c(seq(0, 85, 5), Inf), right = FALSE)
counts <- table(bins, factor(d$Gender[keep], levels = c("Female", "Male")))
counts <- counts[rowSums(counts) > 0, , drop = FALSE]
count_state <- NULL
for (denominator in c("within_gender", "total")) for (display in c("count", "percent")) {
    options <- list(data = d, age = "Age", gender = "Gender", female = "Female", male = "Male",
        age_groups = "who", pct_base = denominator, plot_values = display,
        showInterpretation = TRUE)
    own <- do.call(pyagepyramid, options)
    pj <- do.call(pyagepyramidpj, options)
    stopifnot(identical(own$population$asDF, pj$population$asDF),
        identical(own$dataSummary$asDF, pj$dataSummary$asDF),
        identical(own$assignment$content, pj$assignment$content),
        identical(own$pyramid$state, pj$pyramid$state))
    if (denominator == "within_gender" && display == "count") count_state <- pj$pyramid$state
    rows <- pj$population$asDF
    stopifnot(identical(rows$female, c(as.integer(counts[, 1]), 8L)),
        identical(rows$male, c(as.integer(counts[, 2]), 10L)),
        identical(pj$dataSummary$asDF$n, c(22L, 2L, 1L, 1L, 0L, 18L)))
    proportions <- if (denominator == "total") counts / sum(counts)
                   else sweep(counts, 2L, colSums(counts), "/")
    stopifnot(isTRUE(all.equal(rows$femalePercent[-nrow(rows)],
        unname(proportions[, 1]), tolerance = 1e-12)),
        isTRUE(all.equal(rows$malePercent[-nrow(rows)],
        unname(proportions[, 2]), tolerance = 1e-12)))
    cat(denominator, display, "native tables, plot state and independent cut/table oracle PASSED\n")
}
# Both routes reject the same invalid mapping and recover on the next call.
for (fun in list(pyagepyramid, pyagepyramidpj)) {
    bad <- try(fun(d, "Age", "Gender", "Female", "Female"), silent = TRUE)
    stopifnot(inherits(bad, "try-error"))
    good <- fun(d, "Age", "Gender", "Female", "Male", age_groups = "who", showplot = FALSE)
    stopifnot(tail(good$population$asDF$total, 1L) == 18L)
}
cat("Both routes recovered after an invalid mapping PASSED\n")

# The standalone app R omits the system R library used by this desktop setup.
# Load the already-installed PNG dependency explicitly; install no packages.
if (!requireNamespace("png", quietly = TRUE)) {
    png_namespace <- loadNamespace("png", lib.loc = "/Library/Frameworks/R.framework/Resources/library")
    cat("CLI renderer PNG dependency:", getNamespaceInfo(png_namespace, "path"), "\n")
}
image <- ClinicoPathPj:::.cpjRenderPlot(count_state, 650L, 550L, list(palette = "jmv"))
stopifnot(identical(as.integer(dim(image)[1:2]), c(550L, 650L)))
asset <- file.path(root, "docs", "validation-exports", "pyagepyramidpj-0.3.62-native-counts.png")
png::writePNG(image, asset)
cat("Native Python-rendered count image PASSED:", asset, "\n")
