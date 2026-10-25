# The renderer reads only image$state, so it is tested on hand-made states. layer_data() runs while the
# png device is open; otherwise it would open the default device and write ./Rplots.pdf.

draw <- function(kind, data, ...) {
    grDevices::png(tempfile(fileext = ".png"))
    on.exit(grDevices::dev.off())
    state <- list(kind = kind, data = data, xlab = "x", ylab = "y", ...)
    expect_true(ClinicoPathPj:::.cpjPlot(list(state = state), ggplot2::theme_grey(), list(palette = "jmv")))
    plot <- ggplot2::last_plot()
    list(layers = lapply(seq_along(plot$layers), function(i) ggplot2::layer_data(plot, i)),
         ylabels = ggplot2::ggplot_build(plot)$layout$panel_params[[1]]$y$get_labels())
}

test_that("interval rows with the same label keep their own positions, first row on top", {
    drawn <- draw("interval", data.frame(label = c("A", "A", "B"), estimate = c(1, 2, 3),
                                         lower = c(0, NA, 2), upper = c(2, NA, 4)), reference = 0)
    expect_equal(drawn$layers[[1]]$xintercept, 0)
    points <- drawn$layers[[3]]
    expect_equal(points$x, c(1, 2, 3))
    expect_equal(as.numeric(points$y), c(3, 2, 1))
    expect_equal(as.character(drawn$ylabels), c("B", "A", "A"))  # bottom to top
})

test_that("a line group with one observation is drawn as a point", {
    drawn <- draw("line", data.frame(x = c(1, 2, 3, 1), y = c(1, 0.8, 0.5, 0.9), group = c("a", "a", "a", "b")),
                  reference = 0.5)
    expect_equal(drawn$layers[[1]]$yintercept, 0.5)
    expect_equal(nrow(drawn$layers[[2]]), 4)
    expect_equal(c(drawn$layers[[3]]$x, drawn$layers[[3]]$y), c(1, 0.9))  # only the lone 'b' observation
    missing <- draw("line", data.frame(x = c(1, 2, 1), y = c(1, 2, 3), group = c("a", "a", NA)))
    expect_equal(missing$layers[[2]]$y, 3)  # a row without a group is its own one-point group
    ungrouped <- draw("line", data.frame(x = 1, y = 2, group = NA_character_), step = TRUE)
    expect_equal(nrow(ungrouped$layers[[2]]), 1)
})

test_that("box plots draw the reference line and the same jitter every time", {
    data <- data.frame(group = rep(c("a", "b"), each = 5), value = c(1:5, 3:7))
    first <- draw("box", data, reference = 4)
    expect_equal(first$layers[[1]]$yintercept, 4)
    expect_equal(first$layers[[3]]$x, draw("box", data, reference = 4)$layers[[3]]$x)
})

test_that("no state, or no rows, renders nothing", {
    expect_false(ClinicoPathPj:::.cpjPlot(list(state = NULL), ggplot2::theme_grey(), list(palette = "jmv")))
    expect_false(ClinicoPathPj:::.cpjPlot(list(state = list(kind = "box", data = data.frame())),
                                          ggplot2::theme_grey(), list(palette = "jmv")))
})
