# Verify macOS Python descendants in the installed public Pj service.
# Optional flag: --new-session. System-route checks are separate.
# Run with jamovi's R home, as documented in docs/pj-service-review.md.
main <- function() {
    args <- commandArgs(TRUE)
    if (any(!args %in% "--new-session")) stop("Unknown cleanup probe flag")
    detached <- "--new-session" %in% args
    interpreter <- "jamovi"
    module_root <- path.expand("~/Library/Application Support/jamovi/modules")
    .libPaths(c(file.path(module_root, "ClinicoPathPj", "R"),
        file.path(module_root, "Pj", "R"),
        "/Applications/jamovi.app/Contents/Resources/modules/base/R", .libPaths()))
    Sys.setenv(PYTHONHOME = "/Applications/jamovi.app/Contents/Resources",
        PYTHONPATH = "/Applications/jamovi.app/Contents/Resources/jamovi/server")
    library(ClinicoPathPj)
    jmvcore:::initProtoBuf()
    service <- ClinicoPathPj:::.cpjPjService()
    stopifnot(utils::compareVersion(service$info$module_version, "1.5.0") >= 0L)
    folder <- tempfile("cpj-service-cleanup-")
    dir.create(folder)
    markers <- file.path(folder, paste0(c("success", "cancel", "timeout"), ".json"))
    # Only terminate a surviving probe child whose command line contains its unique marker.
    # This cleanup is a fallback on test failure, never evidence that Pj cleaned it up.
    on.exit({
        for (path in markers[file.exists(markers)]) {
            try({
                pids <- jsonlite::fromJSON(path)
                if (pids$child %in% ps::ps_pids()) {
                    handle <- ps::ps_handle(pids$child)
                    if (path %in% ps::ps_cmdline(handle)) ps::ps_kill(handle)
                }
            }, silent = TRUE)
        }
        unlink(folder, recursive = TRUE)
    }, add = TRUE)
    code <- paste(c(
        "import json, os, subprocess, sys, time",
        "path = data['marker'][0]",
        "child = subprocess.Popen([sys.executable, '-B', '-s', '-c',",
        "    \"import pathlib, sys, time; pathlib.Path(sys.argv[1] + '.ready').write_text('ready'); time.sleep(30)\", path],",
        "    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,",
        "    start_new_session=bool(data['new_session'][0]))",
        "deadline = time.monotonic() + 5",
        "while not os.path.exists(path + '.ready') and time.monotonic() < deadline:",
        "    if child.poll() is not None: raise RuntimeError('Probe child exited before readiness')",
        "    time.sleep(0.02)",
        "if not os.path.exists(path + '.ready') or child.poll() is not None:",
        "    raise RuntimeError('Probe child did not reach its sleeping state')",
        "with open(path, 'w') as f:",
        "    json.dump({'parent': os.getpid(), 'child': child.pid, 'child_ready': True,",
        "        'parent_sid': os.getsid(0), 'child_sid': os.getsid(child.pid)}, f)",
        "if data['mode'][0] != 'success': time.sleep(30)",
        "mzpjShowText('probe completed', name='cleanupProbe')"), collapse = "\n")
    restart <- structure(list(message = "cleanup probe restart", call = NULL, code = "restart"),
        class = c("simpleError", "error", "condition"))
    records <- list()
    for (i in seq_along(markers)) {
        mode <- c("success", "cancel", "timeout")[[i]]
        path <- markers[[i]]
        started <- proc.time()[["elapsed"]]
        answer <- tryCatch(service$run(code = code,
            python = interpreter,
            data = data.frame(marker = path, mode = mode, new_session = detached),
            timeout = if (mode == "timeout") 10L else 25L,
            checkpoint = if (mode == "cancel") function() {
                if (file.exists(path) && file.size(path) > 0) stop(restart)
            } else NULL), error = identity)
        if (mode == "cancel") stopifnot(identical(answer, restart))
        else if (mode == "timeout") stopifnot(inherits(answer, "mzPjServiceError"),
            identical(answer$kind, "timeout"))
        else stopifnot(inherits(answer, "mzPjServiceResult"),
            identical(answer$service$runner, "processx"))
        stopifnot(file.exists(path)) # Proves main Python ran; a bootstrap-only timeout cannot pass.
        recorded <- jsonlite::fromJSON(path)
        stopifnot(isTRUE(recorded$child_ready))
        stopifnot(identical(recorded$parent_sid != recorded$child_sid, detached))
        ids <- c(recorded$parent, recorded$child)
        exists <- function() ids %in% ps::ps_pids()
        for (attempt in 1:30) {
            if (!any(exists())) break
            Sys.sleep(0.1)
        }
        stopifnot(!any(exists()))
        records[[mode]] <- list(parent_pid = ids[[1]], child_pid = ids[[2]],
            child_ready = TRUE, both_absent = TRUE,
            child_new_session = detached, session_relationship_verified = TRUE,
            elapsed_seconds = proc.time()[["elapsed"]] - started)
        cat(mode, ": parent and child absent after Pj returned\n")
    }
    recovery <- service$run(code = "mzpjShowText('recovered', name='recovery')", python = interpreter)
    stopifnot(inherits(recovery, "mzPjServiceResult"))
    cat(jsonlite::toJSON(list(status = "pass", pj_version = service$info$module_version,
        python = interpreter, child_new_session = detached, cases = records, recovery = TRUE,
        scope = paste(if (detached) "New-session" else "Direct", "child on macOS arm64;",
            interpreter, "Python. No double-fork, Flatpak, desktop or other-platform qualification.")),
        auto_unbox = TRUE, pretty = TRUE), "\n")
}
main()
