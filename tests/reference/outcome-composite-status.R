# Frozen rule from jsurvival 283a8275e3dd6704f6bba2164215442d3d293b8c
# R/outcomeorganizer.b.R: pmax components, then preserve a known event over an NA.
# TTP follows progression only; current R skips the unused outcome coder entirely.
composite_status_reference <- function(outcome, recurrence, mode) {
    if (identical(mode,'ttp')) return(recurrence)
    composite <- pmax(recurrence,outcome)
    known_event <- (!is.na(recurrence) & recurrence==1) |
                   (!is.na(outcome) & outcome==1)
    composite[known_event] <- 1
    composite
}
