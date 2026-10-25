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
    yaml::yaml.load(paste(metadata, collapse = "\n"))  # reject an invalid generated document
    writeLines(metadata, path)
    invisible(NULL)
}
