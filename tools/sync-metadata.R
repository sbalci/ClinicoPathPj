# Regenerate top-level module version/date from DESCRIPTION before compiler preparation.
sync_module_metadata <- function(root = ".") {
    description <- read.dcf(file.path(root, "DESCRIPTION"))
    path <- file.path(root, "jamovi", "0000.yaml")
    metadata <- readLines(path, warn = FALSE)
    # The compiler terminates YAML with "..."; new generated fields belong before it.
    metadata <- metadata[!grepl("^\\.\\.\\.[[:space:]]*$", metadata)]
    fields <- c(version = "Version", date = "Date")
    for (key in names(fields)) {
        field <- fields[[key]]
        pattern <- paste0("^", key, ":")
        if (sum(grepl(pattern, metadata)) != 1)
            stop("Expected one top-level ", key, " in module metadata")
        metadata <- sub(paste0(pattern, ".*$"),
                        paste0(key, ": '", description[1, field], "'"), metadata)
    }
    if (file.exists(file.path(root, "data", "python_core_examples.omv")) &&
        !any(grepl("^datasets:", metadata))) {
        metadata <- c(metadata, "datasets:",
            "  - name: Python Core Examples",
            "    path: python_core_examples.omv",
            "    description: Six Python core analyses using 36 synthetic observations.",
            "    tags: [Python, Diagnostic accuracy, Decision curves, Data quality]")
    }
    document <- yaml::yaml.load(paste(metadata, collapse = "\n"))
    set_data <- "python_set_intersection_examples.csv"
    if (file.exists(file.path(root, "data", set_data)) &&
        !any(vapply(document$datasets, function(x) identical(x$path, set_data), logical(1)))) {
        document$datasets[[length(document$datasets) + 1L]] <- list(
            name = "Set Intersection Examples", path = set_data,
            description = "Four synthetic binary markers with all sixteen membership patterns and two missing-value examples.",
            tags = c("Python", "Set membership", "Marker panels"))
    }
    unequal_data <- "python_set_intersection_unequal_examples.csv"
    if (file.exists(file.path(root, "data", unequal_data)) &&
        !any(vapply(document$datasets, function(x) identical(x$path, unequal_data), logical(1)))) {
        document$datasets[[length(document$datasets) + 1L]] <- list(
            name = "Set Intersections: Unequal Frequencies", path = unequal_data,
            description = "Sixty synthetic complete marker panels with unequal pattern counts (0 to 12) and two missing-value examples.",
            tags = c("Python", "Set membership", "Unequal frequencies"))
    }
    outlier_data <- "python_outlier_screening_examples.csv"
    if (file.exists(file.path(root, "data", outlier_data)) &&
        !any(vapply(document$datasets, function(x) identical(x$path, outlier_data), logical(1)))) {
        document$datasets[[length(document$datasets) + 1L]] <- list(
            name = "Univariate Screening Examples", path = outlier_data,
            description = "Thirty-one synthetic complete measurement pairs including one extreme pair, plus two rows with missing measurements.",
            tags = c("Python", "Outliers", "Data quality"))
    }
    tree_data <- "python_variable_tree_examples.csv"
    if (file.exists(file.path(root, "data", tree_data))) {
        tree_entry <- list(
            name = "Categorical Tree Examples", path = tree_data,
            description = "Thirty-six synthetic complete tumor/grade/stage profiles across three tumor categories, plus two missing-category examples.",
            tags = c("Python", "Categorical tree", "Descriptives"))
        tree_index <- which(vapply(document$datasets,
            function(x) identical(x$path, tree_data), logical(1)))
        if (length(tree_index)) document$datasets[[tree_index[1L]]] <- tree_entry
        else document$datasets[[length(document$datasets) + 1L]] <- tree_entry
    }
    summary_data <- "python_tree_node_summary_examples.csv"
    if (file.exists(file.path(root, "data", summary_data)) &&
        !any(vapply(document$datasets, function(x) identical(x$path, summary_data), logical(1)))) {
        document$datasets[[length(document$datasets) + 1L]] <- list(
            name = "Tree Node Summary Examples", path = summary_data,
            description = "Eight synthetic profiles: seven categorical complete rows, four valid marker scores and node-local numeric missingness.",
            tags = c("Python", "Categorical tree", "Node summaries"))
    }
    reference_data <- "python_tree_reference_examples.csv"
    if (file.exists(file.path(root, "data", reference_data)) &&
        !any(vapply(document$datasets, function(x) identical(x$path, reference_data), logical(1)))) {
        document$datasets[[length(document$datasets) + 1L]] <- list(
            name = "Tree Reference Percentage Examples", path = reference_data,
            description = "Eight synthetic profiles with seven categorical complete rows, four valid reference classifications and both numeric/reference missingness.",
            tags = c("Python", "Categorical tree", "Reference percentages"))
    }
    alluvial_data <- "python_alluvial_examples.csv"
    if (file.exists(file.path(root, "data", alluvial_data)) &&
        !any(vapply(document$datasets, function(x) identical(x$path, alluvial_data), logical(1)))) {
        document$datasets[[length(document$datasets) + 1L]] <- list(
            name = "Categorical Flow Examples", path = alluvial_data,
            description = "Twenty complete synthetic profiles on four unequal paths (12, 5, 2, 1 rows), plus two missing-category profiles.",
            tags = c("Python", "Alluvial", "Categorical flows"))
    }
    cross_data <- "python_cross_table_examples.omv"
    if (file.exists(file.path(root, "data", cross_data))) {
        cross_entry <- list(
            name = "Grouped Cross Table Examples", path = cross_data,
            description = "Twenty-five synthetic profiles with explicit continuous Age/Code types and a preconfigured cross table (Holm adjustment); default retention is 24, complete-case retention is 21.",
            tags = c("Python", "Grouped summaries", "Cross tables"))
        cross_index <- which(vapply(document$datasets, function(x)
            x$path %in% c(cross_data, "python_cross_table_examples.csv"), logical(1)))
        if (length(cross_index)) document$datasets[[cross_index[1L]]] <- cross_entry
        else document$datasets[[length(document$datasets) + 1L]] <- cross_entry
    }
    tableone_data <- "python_table_one_examples.omv"
    if (file.exists(file.path(root, "data", tableone_data))) {
        tableone_entry <- list(
            name = "Overall Table One Examples", path = tableone_data,
            description = "Twenty-five synthetic profiles with explicit continuous Age/Code types, binary categories and an entirely uncollected variable; a preconfigured overall Table One retains 25 rows, or 21 with complete-case exclusion.",
            tags = c("Python", "Overall cohort", "Table One"))
        tableone_index <- which(vapply(document$datasets, function(x)
            x$path %in% c(tableone_data, "python_table_one_examples.csv"), logical(1)))
        if (length(tableone_index)) document$datasets[[tableone_index[1L]]] <- tableone_entry
        else document$datasets[[length(document$datasets) + 1L]] <- tableone_entry
    }
    registry_path <- file.path(root, "inst", "python", "registry.json")
    if (file.exists(registry_path)) {
        registry <- jsonlite::fromJSON(registry_path, simplifyVector = FALSE)
        installed_names <- unlist(lapply(registry$analyses, function(entry)
            if (!is.null(entry$source)) c(entry$id, unlist(entry$aliases, use.names = FALSE))), use.names = FALSE)
        document$analyses <- Filter(function(a) a$name %in% installed_names, document$analyses)
        # The compiler preserves metadata for existing entries. Seed hidden aliases here,
        # because its analysis schema rejects `hidden` although the module schema supports it.
        for (entry in registry$analyses) {
            if (is.null(entry$source)) next
            for (name in c(entry$id, unlist(entry$aliases, use.names = FALSE))) {
                index <- which(vapply(document$analyses, function(a) identical(a$name, name), logical(1)))
                hidden <- !identical(name, entry$id)
                if (!length(index)) {
                    document$analyses[[length(document$analyses) + 1L]] <- list(
                        name = name, ns = "ClinicoPathPj", hidden = hidden)
                } else {
                    document$analyses[[index]]$hidden <- hidden
                }
                index <- which(vapply(document$analyses, function(a) identical(a$name, name), logical(1)))
                document$analyses[[index]]$menuGroup <- entry$menu_group
                document$analyses[[index]]$menuSubgroup <- entry$menu
                document$analyses[[index]]$menuTitle <- if (is.null(entry$menu_title)) entry$title else entry$menu_title
            }
        }
    }
    # js-yaml uses YAML 1.2: R yaml's default yes/no would become strings.
    writeLines(yaml::as.yaml(document, handlers = list(logical = function(x)
        structure(tolower(as.character(x)), class = "verbatim"))), path)
    invisible(NULL)
}
