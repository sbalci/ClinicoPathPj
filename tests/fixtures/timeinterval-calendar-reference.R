# Frozen current R calendar method; commit 381df71e98e4fb460d44e5a6cc439a04289acfdd
# Full-source SHA256: 991bc0053ccbfb4a52132ffd27ae462969b34f783a3bb8c08ad8882f275c14e2
calendar_reference <- function(start_dates, end_dates, output_unit) {
    if (!inherits(start_dates, "Date") && !inherits(start_dates, "POSIXct")) {
        jmvcore::reject(.("Start dates are not valid date objects"))
    }
    if (!inherits(end_dates, "Date") && !inherits(end_dates, "POSIXct")) {
        jmvcore::reject(.("End dates are not valid date objects"))
    }
    intervals <- lubridate::interval(start_dates, end_dates)
    days <- lubridate::time_length(intervals, "days")
    if (output_unit == "days") 
        return(days)
    if (output_unit == "weeks") 
        return(days/7)
    whole_months <- intervals%/%lubridate::period(month = 1)
    remainder_start <- lubridate::add_with_rollback(start_dates, lubridate::period(month = whole_months))
    remainder_int <- lubridate::interval(remainder_start, end_dates)
    remainder_days <- lubridate::time_length(remainder_int, "days")
    step_dir <- ifelse(is.na(days) | days >= 0, 1L, -1L)
    next_anniv <- lubridate::add_with_rollback(start_dates, lubridate::period(month = whole_months + 
        step_dir))
    span_days <- abs(lubridate::time_length(lubridate::interval(remainder_start, next_anniv), "days"))
    span_days <- ifelse(is.na(span_days) | span_days == 0, NA_real_, span_days)
    fraction_months <- remainder_days/span_days
    total_months <- whole_months + fraction_months
    if (output_unit == "months") 
        return(total_months)
    if (output_unit == "years") 
        return(total_months/12)
    jmvcore::reject(.("Unsupported output unit for calendar-based calculation"))
}
