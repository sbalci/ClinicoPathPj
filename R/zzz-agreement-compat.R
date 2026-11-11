# Keep existing positional R calls stable when new method options are added.
# Saved jamovi options are name-bound; this additionally protects script callers.
pyagreement <- local({
    compiled <- pyagreement
    legacy <- c('data', 'vars', 'subject', 'baConfidenceLevel', 'confLevel',
                'showPairs', 'blandAltmanPlot', 'method', 'iccType', 'showICCCases', 'showConsole')
    defaults <- formals(compiled)
    formals(compiled) <- defaults[c(legacy, setdiff(names(defaults), legacy))]
    compiled
})
