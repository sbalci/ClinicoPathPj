d <- read.csv('data/python_first_event_examples.csv',check.names=FALSE,na.strings='')
for (name in c('A time','B time','Expected time')) d[[name]] <- as.numeric(d[[name]])
for (name in c('A status','B status','Expected status')) d[[name]] <- factor(d[[name]],levels=c('Event-free','Event','Censored'))
attr(d$Record,'jmv-id') <- TRUE
jmvReadWrite::write_omv(d,'data/python_first_event_examples.omv',frcWrt=TRUE)
