d <- read.csv('data/python_icc_examples.csv', stringsAsFactors=FALSE)
attr(d$Case,'jmv-id') <- TRUE
jmvReadWrite::write_omv(d,'data/python_icc_examples.omv',frcWrt=TRUE)
