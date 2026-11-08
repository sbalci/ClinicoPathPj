d <- read.csv('data/python_agreement_examples.csv',na.strings='',check.names=FALSE)
attr(d$Case,'jmv-id') <- TRUE
jmvReadWrite::write_omv(d,'data/python_agreement_examples.omv',frcWrt=TRUE)
