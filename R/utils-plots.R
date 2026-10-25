# Plots for ClinicoPathPj: Python computes the data (out.plot in inst/python/cpj_runtime.py), the
# bridge stores it as the image state, and these renderers draw it with ggplot2, so plots follow
# jamovi's theme and palette and export like any jamovi plot. Kinds and columns match PLOT_COLUMNS.

.cpjPlotColumns <- list(
    interval = c(label = "text", estimate = "number", lower = "number", upper = "number"),
    line = c(x = "number", y = "number", group = "text"),
    box = c(group = "text", value = "number"),
    bar = c(label = "text", value = "number", group = "text"))

.cpjPlot <- function(image, ggtheme, theme) {
    state <- image$state
    if (is.null(state) || is.null(state$data) || nrow(state$data) == 0)
        return(FALSE)
    d <- state$data
    # jamovi's global palette (Settings > Plot theme), so plots agree across modules
    colour <- function(n) jmvcore::colorPalette(n, theme$palette, type = "color")
    p <- switch(state$kind,
        interval = {
            # one axis position per row (first row at the top), so two entries with the same label stay apart
            d$row <- factor(seq_len(nrow(d)), levels = rev(seq_len(nrow(d))))
            q <- ggplot2::ggplot(d, ggplot2::aes(x = .data$estimate, y = .data$row)) +
                ggplot2::scale_y_discrete(labels = stats::setNames(d$label, d$row))
            if (!is.null(state$reference))
                q <- q + ggplot2::geom_vline(xintercept = state$reference, linetype = "dashed", colour = "grey55")
            q + ggplot2::geom_linerange(ggplot2::aes(xmin = .data$lower, xmax = .data$upper),
                                        colour = colour(1), linewidth = 0.9, na.rm = TRUE) +
                ggplot2::geom_point(colour = colour(1), size = 2.6)
        },
        line = {
            grouped <- any(!is.na(d$group))
            d$group <- factor(d$group, levels = unique(d$group))
            q <- if (grouped) ggplot2::ggplot(d, ggplot2::aes(x = .data$x, y = .data$y, colour = .data$group))
                 else ggplot2::ggplot(d, ggplot2::aes(x = .data$x, y = .data$y))
            if (!is.null(state$reference))
                q <- q + ggplot2::geom_hline(yintercept = state$reference, linetype = "dashed", colour = "grey55")
            geom <- if (isTRUE(state$step)) ggplot2::geom_step else ggplot2::geom_line
            q <- q + (if (grouped) geom(linewidth = 0.9) else geom(linewidth = 0.9, colour = colour(1)))
            # a group with one observation draws no line: show it as a point (ggtheme supplies the colours)
            key <- if (grouped) as.character(d$group) else rep("all", nrow(d))
            key[is.na(key)] <- "missing"  # never "": an empty name matches nothing when indexing
            single <- d[as.integer(table(key)[key]) == 1, , drop = FALSE]
            if (nrow(single))
                q <- q + if (grouped) ggplot2::geom_point(data = single, size = 2, na.rm = TRUE)
                         else ggplot2::geom_point(data = single, size = 2, colour = colour(1), na.rm = TRUE)
            q
        },
        bar = {
            labels <- unique(d$label)
            d$label <- factor(d$label, levels = labels)
            d$group <- factor(d$group, levels = unique(d$group))
            breaks <- labels[seq.int(1, length(labels), by = max(1, ceiling(length(labels) / 20)))]
            ggplot2::ggplot(d, ggplot2::aes(x = .data$label, y = .data$value, fill = .data$group)) +
                ggplot2::geom_col(position = "dodge", width = 0.8) +
                ggplot2::scale_x_discrete(breaks = breaks) +
                ggplot2::scale_fill_manual(values = jmvcore::colorPalette(
                    nlevels(d$group), theme$palette, type = "fill"))
        },
        box = {
            d$group <- factor(d$group, levels = unique(d$group))
            q <- ggplot2::ggplot(d, ggplot2::aes(x = .data$group, y = .data$value))
            if (!is.null(state$reference))
                q <- q + ggplot2::geom_hline(yintercept = state$reference, linetype = "dashed", colour = "grey55")
            q +
                ggplot2::geom_boxplot(outlier.shape = NA, width = 0.5, na.rm = TRUE,
                                      fill = jmvcore::colorPalette(1, theme$palette, type = "fill")) +
                ggplot2::geom_point(position = ggplot2::position_jitter(width = 0.15, height = 0, seed = 1),
                                    colour = colour(1), alpha = 0.6, na.rm = TRUE)  # seeded: same jitter every time
        },
        stop("Unknown plot kind '", state$kind, "'.", call. = FALSE))
    # ggtheme last: it is a complete theme and would reset any theme() set before it
    print(p + ggplot2::labs(x = state$xlab, y = state$ylab, colour = NULL, fill = NULL) + ggtheme)
    TRUE
}
