d <- read.csv('data/python_first_event_examples.csv',check.names=FALSE,na.strings='')
d[['Subject ID']] <- c('001','001','1','01','S04','S05','S06','S07',NA,'S08','S09','S09')
for (name in c('A time','B time','Expected time')) d[[name]] <- as.numeric(d[[name]])
for (name in c('A status','B status','Expected status')) d[[name]] <- factor(d[[name]],levels=c('Event-free','Event','Censored'))
attr(d$Record,'jmv-id') <- TRUE
attr(d[['Subject ID']],'jmv-id') <- TRUE
jmvReadWrite::write_omv(d,'data/python_first_event_identity.omv',frcWrt=TRUE)
