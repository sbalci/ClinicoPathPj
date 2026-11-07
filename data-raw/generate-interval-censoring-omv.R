# Preserve continuous endpoint types for the Data Library example; no analyses preconfigured.
d <- read.csv('data/python_interval_censoring_examples.csv',check.names=FALSE)
d[['Left endpoint']] <- as.numeric(d[['Left endpoint']])
d[['Right endpoint']] <- as.numeric(d[['Right endpoint']])
attr(d$Record,'jmv-id') <- TRUE
jmvReadWrite::write_omv(d,'data/python_interval_censoring_examples.omv',frcWrt=TRUE)
