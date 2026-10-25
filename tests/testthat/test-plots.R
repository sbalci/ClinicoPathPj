# Python constructs figures; R only displays their completed raster.
test_that("Python plots render native images from saved legacy state", {
    states <- list(
        list(kind = "interval", data = data.frame(label = c("A", "A"), estimate = c(1, 2), lower = c(0, NA), upper = c(2, NA))),
        list(kind = "line", data = data.frame(x = c(1, 2, 3), y = c(1, .8, .5), group = c("a", "a", "b"))),
        list(kind = "box", data = data.frame(group = rep(c("a", "b"), each = 4), value = 1:8)),
        list(kind = "bar", data = data.frame(label = c("A", "A"), value = c(2, 3), group = c("Observed", "Expected"))))
    for (state in states) {
        state$xlab <- "x"; state$ylab <- "y"
        raster <- ClinicoPathPj:::.cpjRenderPlot(state, 500L, 300L, list(palette = "jmv"))
        expect_equal(dim(raster)[1:2], c(300L, 500L))
        expect_gt(length(unique(as.vector(raster))), 10)
    }
})

test_that("no state, or no rows, renders nothing", {
    expect_false(ClinicoPathPj:::.cpjPlot(list(state = NULL), NULL, list(palette = "jmv")))
    expect_false(ClinicoPathPj:::.cpjPlot(list(state = list(kind = "box", data = data.frame())), NULL, list(palette = "jmv")))
})
