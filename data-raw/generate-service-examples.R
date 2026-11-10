# Synthetic, deliberately incomplete measurements for both execution examples.
d <- read.csv("data/python_service_examples.csv")
jmvReadWrite::write_omv(d, "data/python_service_examples.omv", frcWrt = TRUE)
