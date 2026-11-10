# Deliberately unequal band counts and disjoint exclusions; no real patient data.
d <- read.csv("data/python_age_pyramid_service_examples.csv")
d$Gender <- factor(d$Gender, levels = c("Female", "Male", "Other"))
attr(d$Case, "jmv-id") <- TRUE
jmvReadWrite::write_omv(d, "data/python_age_pyramid_service_examples.omv", frcWrt = TRUE)
