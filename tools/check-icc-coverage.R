# Independent R spot-checks of the exact first simulated matrix in each scenario.
# No Python engine is invoked by this checker. Requires development-only oracles.
report <- jsonlite::read_json('docs/validation-exports/python-icc-coverage-2026-11-07.json',
                             simplifyVector=FALSE)
checked <- 0L
withheld <- 0L
for (scenario in report$results) {
    example <- scenario$oracle_example
    x <- do.call(rbind,lapply(example$ratings,unlist))
    py <- example$result
    a <- irr::icc(x,model='twoway',type='agreement',unit='average',
                 conf.level=report$confidence)
    b <- suppressWarnings(psych::ICC(x,lmer=FALSE,alpha=1-report$confidence))$results
    stopifnot(abs(py$unconstrained_estimate-a$value)<1e-10,
              abs(py$unconstrained_estimate-b$ICC[5])<1e-10,
              nrow(x)==scenario$n,ncol(x)==scenario$k)
    expected_truth <- scenario$subject_variance / (scenario$subject_variance+
                          (scenario$rater_variance+scenario$error_variance)/ncol(x))
    stopifnot(abs(expected_truth-scenario$true_average_icc)<1e-14)
    references <- list(frozen_irr=c(a$lbound,a$ubound),
                       transformed_single=as.numeric(b[5,c('lower bound','upper bound')]))
    for (name in names(references)) {
        actual <- unlist(py$candidate_intervals[[name]])
        expected <- references[[name]]
        if(length(actual)==2L) {
            stopifnot(max(abs(actual-expected))<1e-8)
            checked <- checked+1L
        } else {
            # Do not call withheld uncertainty numerical agreement. Preserve it
            # separately so the study cannot silently drop unsuccessful intervals.
            withheld <- withheld+1L
        }
    }
}
result <- list(status='pass',matrices=length(report$results),
               coefficient_comparisons=2L*length(report$results),
               interval_comparisons=checked,withheld_candidates=withheld,
               irr=as.character(packageVersion('irr')),psych=as.character(packageVersion('psych')))
cat(jsonlite::toJSON(result,auto_unbox=TRUE,pretty=TRUE),'\n')
