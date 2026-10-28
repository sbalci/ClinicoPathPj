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
