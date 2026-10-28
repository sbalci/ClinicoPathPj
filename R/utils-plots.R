# R only displays a completed Python image. Both new and saved legacy states are supported.
.cpjPlotColumns <- list(
    setmatrix = c(pattern = "text", count = "integer", sets = "text"),
    dendrogram = c(xLeft = "number", xRight = "number", leftHeight = "number",
                   rightHeight = "number", height = "number", leftLabel = "text", rightLabel = "text"),
    interval = c(label = "text", estimate = "number", lower = "number", upper = "number"),
    line = c(x = "number", y = "number", group = "text"),
    box = c(group = "text", value = "number"),
    bar = c(label = "text", value = "number", group = "text"),
    points = c(x = "number", y = "number", group = "text"),
    scatter = c(x = "number", y = "number", group = "text"),
    ihcheatmap = c(variable = "text", row = "text", label = "text", value = "number"),
    qualitymap = c(variable = "text", row = "text", state = "text"),
    pyramid = c(label = "text", left = "number", right = "number", leftLabel = "text", rightLabel = "text", title = "text"),
    histogram = c(group = "text", lower = "number", upper = "number", count = "integer"))

.cpjRenderPlot <- function(state, width, height, theme, ggtheme = NULL) {
    columns <- if (!is.null(state$columns)) state$columns else lapply(state$data, as.list)
    plot <- list(kind = state$kind, columns = columns, xlab = state$xlab, ylab = state$ylab,
                 reference = state$reference, step = isTRUE(state$step),
                 boundaries = if (is.null(state$boundaries)) NULL else as.list(state$boundaries))
    directory <- tempfile("cpj-plot-")
    dir.create(directory)
    on.exit(unlink(directory, recursive = TRUE), add = TRUE)
    request <- file.path(directory, "request.json")
    response <- file.path(directory, "response.json")
    background <- ggtheme$plot.background$fill
    foreground <- ggtheme$text$colour
    if (is.null(background) || is.na(background) || identical(background, "transparent")) background <- "white"
    if (is.null(foreground) || is.na(foreground)) foreground <- "#222222"
    payload <- list(operation = "render_plot", plot = plot,
        settings = list(width = as.integer(width), height = as.integer(height),
            palette = as.list(jmvcore::colorPalette(10, theme$palette, type = "color")),
            background = background, foreground = foreground))
    writeLines(jsonlite::toJSON(payload, auto_unbox = TRUE, null = "null", na = "null", digits = I(17)), request)
    runtime <- system.file("python", "cpj_runtime.py", package = "ClinicoPathPj", mustWork = TRUE)
    process <- .cpjExecute(.cpjPython(), c("-B", "-s", runtime, request, response), checkpoint = NULL)
    if (!file.exists(response)) stop("Python plot renderer returned no image: ", process$output, call. = FALSE)
    result <- jsonlite::fromJSON(response, simplifyVector = FALSE)
    if (!identical(result$status, "ok")) stop(result$error$message, call. = FALSE)
    png::readPNG(jsonlite::base64_dec(result$asset$png))
}

.cpjPlot <- function(image, ggtheme, theme) {
    state <- image$state
    if (is.null(state)) return(FALSE)
    if (is.null(state$columns) && (is.null(state$data) || nrow(state$data) == 0)) return(FALSE)
    size <- pmax(200, pmin(2000, round(grDevices::dev.size("px"))))
    raster <- .cpjRenderPlot(state, size[1], size[2], theme, ggtheme)
    grid::grid.raster(raster, width = grid::unit(1, "npc"), height = grid::unit(1, "npc"))
    TRUE
}
