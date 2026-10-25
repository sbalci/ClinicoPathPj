# Regenerate, build and install ClinicoPathPj into the local jamovi:
#
#     Rscript --vanilla tools/build.R
#
# Exits non-zero when any step fails. jmvtools::install() reports failure only through its
# return value (Rscript itself still exits 0), so the status and the installed file are checked.

script <- sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE))
setwd(dirname(dirname(normalizePath(script))))
Sys.unsetenv("ELECTRON_RUN_AS_NODE")  # set by VS Code; makes the jamovi binary answer as Node
started <- Sys.time()
source("tools/sync-metadata.R")
sync_module_metadata()

app <- "/Applications/jamovi.app/Contents"
status <- system2(file.path(app, "MacOS", "python"), c("-B", "tools/generate.py"),
                  env = paste0("PYTHONHOME=", shQuote(file.path(app, "Resources"))))
if (status != 0) quit(status = status)

if ("--build-only" %in% commandArgs(TRUE)) {
    # The GUI app probe can fail in a restricted shell. Use the installed app's real
    # plist version for compiler preparation, and leave installation to the GUI.
    version <- system2("/usr/libexec/PlistBuddy", c("-c", shQuote("Print :CFBundleShortVersionString"),
        shQuote(file.path(app, "Info.plist"))), stdout = TRUE)
    if (length(version) != 1 || !grepl("^[0-9]+(\\.[0-9]+){2,3}$", version))
        stop("Could not read the installed jamovi version")
    node <- Sys.which("node")
    if (!nzchar(node)) stop("Node is required by the jamovi compiler")
    compiler <- system.file("node_modules", "jamovi-compiler", "index.js", package = "jmvtools", mustWork = TRUE)
    status <- system2(node, c(shQuote(compiler), "--build", ".", "--assume-app-version", version,
                             "--skip-deps"))
    quit(status = status)
}

status <- jmvtools::install()
if (status != 0) quit(status = status)

installed <- path.expand("~/Library/Application Support/jamovi/modules/ClinicoPathPj/jamovi.yaml")
for (i in 1:60) {  # a running jamovi installs the .jmo asynchronously
    if (file.exists(installed) && file.mtime(installed) > started) {
        message("ClinicoPathPj installed: ", installed)
        quit(status = 0)
    }
    Sys.sleep(1)
}
message("jmvtools reported success, but ", installed, " was not updated.")
quit(status = 1)
