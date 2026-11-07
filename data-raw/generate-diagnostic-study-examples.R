d <- read.csv("data/python_diagnostic_study_examples.csv", na.strings = "", check.names = FALSE)
attr(d$Study, "jmv-id") <- TRUE
for (name in c("TP", "FP", "FN", "TN")) d[[name]] <- as.numeric(d[[name]])
jmvReadWrite::write_omv(d, "data/python_diagnostic_study_examples.omv", frcWrt = TRUE)
