test_that('first event agrees with independently grouped chronological records', {
    d <- expand.grid(ta=c(0,1,5),tb=c(0,1,5),sa=c('N','Y'),sb=c('N','Y'),stringsAsFactors=FALSE)
    d$sa <- factor(d$sa,levels=c('N','Y'));d$sb <- factor(d$sb,levels=c('N','Y'))
    reference <- t(vapply(seq_len(nrow(d)),function(i) {
        timeline <- data.frame(time=c(d$ta[i],d$tb[i]),event=c(d$sa[i]=='Y',d$sb[i]=='Y'))
        timeline <- timeline[order(timeline$time),]
        earliest <- timeline[timeline$time==timeline$time[1],]
        c(time=earliest$time[1],status=as.integer(any(earliest$event)))
    },c(time=0,status=0)))
    got <- pyfirstevent(data=d,timeA='ta',timeB='tb',statusA='sa',statusB='sb',eventA='Y',freeA='N',eventB='Y',freeB='N',preview_rows=100)
    expect_equal(got$preview$asDF$time,reference[,'time'])
    expect_equal(got$preview$asDF$status,reference[,'status'])
    expect_equal(got$cohort$asDF$retained,36)
    expect_equal(got$counts$asDF$n,as.numeric(table(factor(reference[,'status'],levels=0:1))))
})

test_that('literal rows, sparse IDs and stale-output recovery are preserved', {
    d <- data.frame(ta=c(2,8,NA,-1),tb=c(8,2,4,4),sa=factor(c('Y','Y','Y','Y'),levels=c('N','Y')),sb=factor(c('N','N','N','N'),levels=c('N','Y')),row.names=c('2','8','20','40'))
    opts <- pyfirsteventOptions$new(timeA='ta',timeB='tb',statusA='sa',statusB='sb',eventA='Y',freeA='N',eventB='Y',freeB='N',showReport=TRUE,showPlot=TRUE)
    for (name in c('timeOut','statusOut','sourceOut')) {opt<-opts$option(name);opt$value<-list(value=TRUE,vars=list())}
    a <- pyfirsteventClass$new(options=opts,data=d);a$init();a$run();jmvcore:::initProtoBuf()
    output <- function(name) a$results$get(name)$asProtoBuf(incAsText=TRUE)$outputs
    expect_equal(as.integer(output('timeOut')$rowNums),c(1,7,19,39))
    expect_equal(as.numeric(output('timeOut')$outputs[[1]]$d),c(2,2,NA,NA))
    expect_equal(a$results$preview$asDF$status,c(1,0,NA,NA))
    expect_equal(a$results$preview$asDF$sourceID,rownames(d))
    expect_equal(a$results$cohort$asDF$invalid,1)
    expect_equal(a$results$cohort$asDF$missing,1)
    expect_equal(a$results$cohort$asDF$late,1)
    expect_equal(a$results$distribution$state$data$value,c(1,1))
    expect_match(a$results$summary$content,'event wins')
    role <- opts$option('timeB');role$value<-NULL;a$init();a$run()
    expect_equal(a$results$cohort$rowCount,0)
    expect_equal(a$results$preview$rowCount,0)
    expect_true(all(is.na(output('timeOut')$outputs[[1]]$d)))
    expect_null(a$results$distribution$state)
    role$value<-'tb';a$init();a$run()
    expect_equal(a$results$preview$asDF$status,c(1,0,NA,NA))
    level <- opts$option('eventA');level$value<-NULL;a$init();a$run()
    expect_equal(a$results$counts$rowCount,0)
    expect_true(all(is.na(output('timeOut')$outputs[[1]]$d)))
    level$value<-'Y';a$init();a$run()
    expect_equal(a$results$cohort$asDF$retained,2)
    level$value<-'N';a$init();expect_error(a$run(),'distinct')
})

test_that('administrative cutoff agrees with a third observation-ending timepoint', {
    d <- expand.grid(ta=c(0,1,5),tb=c(0,1,5),sa=c('N','Y'),sb=c('N','Y'),stringsAsFactors=FALSE)
    d$sa <- factor(d$sa,levels=c('N','Y'));d$sb <- factor(d$sb,levels=c('N','Y'))
    for (cutoff in c(0,1,3,5,10)) {
        ref <- t(vapply(seq_len(nrow(d)),function(i) {
            timeline <- data.frame(time=c(d$ta[i],d$tb[i],cutoff),event=c(d$sa[i]=='Y',d$sb[i]=='Y',FALSE))
            timeline <- timeline[order(timeline$time),]
            earliest <- timeline[timeline$time==timeline$time[1],]
            c(time=earliest$time[1],status=as.integer(any(earliest$event)))
        },c(time=0,status=0)))
        got <- pyfirstevent(data=d,timeA='ta',timeB='tb',statusA='sa',statusB='sb',eventA='Y',freeA='N',eventB='Y',freeB='N',preview_rows=100,use_admin=TRUE,admin_cutoff=as.character(cutoff))
        expect_equal(got$preview$asDF$time,ref[,'time'])
        expect_equal(got$preview$asDF$status,ref[,'status'])
        expect_equal(got$cohort$asDF$retained,36)
    }
})

test_that('cutoff lifecycle clears and restores all outputs without changing defaults', {
    d <- data.frame(ta=c(1,5,NA),tb=c(5,8,3),sa=factor(c('Y','Y','Y'),levels=c('N','Y')),sb=factor(c('N','N','N'),levels=c('N','Y')),row.names=c('2','9','41'))
    opts <- pyfirsteventOptions$new(timeA='ta',timeB='tb',statusA='sa',statusB='sb',eventA='Y',freeA='N',eventB='Y',freeB='N',use_admin=TRUE,admin_cutoff='2',showPlot=TRUE)
    for (name in c('timeOut','statusOut','sourceOut')) {opt<-opts$option(name);opt$value<-list(value=TRUE,vars=list())}
    a <- pyfirsteventClass$new(options=opts,data=d);a$init();a$run();jmvcore:::initProtoBuf()
    output <- function(name) a$results$get(name)$asProtoBuf(incAsText=TRUE)$outputs
    expect_equal(as.integer(output('timeOut')$rowNums),c(1,8,40))
    expect_equal(as.numeric(output('timeOut')$outputs[[1]]$d),c(1,2,NA))
    expect_equal(a$results$preview$asDF$baseTime,c(1,5,NA))
    expect_equal(a$results$preview$asDF$status,c(1,0,NA))
    expect_equal(a$results$adminAudit$asDF$eventsRemoved,1)
    expect_equal(a$results$preview$asDF$adminApplied,c(0,1,NA))
    cutoff <- opts$option('admin_cutoff');cutoff$value<-'';a$init();a$run()
    expect_equal(a$results$adminAudit$rowCount,0)
    expect_equal(a$results$preview$rowCount,0)
    expect_null(a$results$distribution$state)
    expect_true(all(is.na(output('timeOut')$outputs[[1]]$d)))
    for (name in c('statusOut','sourceOut')) {
        v <- output(name)$outputs[[1]]$i
        expect_true(all(is.na(v)|v == -2147483648))
    }
    cutoff$value<-'0';a$init();a$run()
    expect_equal(a$results$preview$asDF$time,c(0,0,NA))
    expect_equal(a$results$preview$asDF$status,c(0,0,NA))
    enabled <- opts$option('use_admin');enabled$value<-FALSE;a$init();a$run()
    expect_equal(a$results$preview$asDF$time,c(1,5,NA))
    expect_equal(a$results$preview$asDF$status,c(1,1,NA))
    expect_equal(a$results$adminAudit$rowCount,0)
    enabled$value<-TRUE;cutoff$value<-'2';a$init();a$run()
    expect_equal(a$results$preview$asDF$time,c(1,2,NA))
    cutoff$value<-'Inf';a$init();expect_error(a$run(),'finite nonnegative')
})

test_that('subject identities agree with independent exact-label counts', {
    ids <- c('001','001','1','01','NA',NA,'','  ',' S','S','S ')
    d <- data.frame(ta=rep(1,length(ids)),tb=rep(2,length(ids)),sa=factor(rep('Y',length(ids)),levels=c('N','Y')),sb=factor(rep('N',length(ids)),levels=c('N','Y')),id=ids)
    got <- pyfirstevent(data=d,timeA='ta',timeB='tb',statusA='sa',statusB='sb',eventA='Y',freeA='N',eventB='Y',freeB='N',audit_subject=TRUE,subject='id')
    valid <- !is.na(ids) & nzchar(trimws(ids))
    freq <- table(ids[valid]);expected <- rep(NA_real_,length(ids));expected[valid] <- as.numeric(freq[ids[valid]])
    expect_equal(got$preview$asDF$subjectRecords,expected)
    expect_equal(got$identityAudit$asDF$known,sum(valid))
    expect_equal(got$identityAudit$asDF$subjects,length(freq))
    expect_equal(got$identityAudit$asDF$repeatedSubjects,sum(freq>1))
    expect_equal(got$identityAudit$asDF$repeatedRows,sum(freq[freq>1]))
    expect_equal(got$repeatedSubjects$asDF$subject,'001')
    expect_equal(got$preview$asDF$subject[c(3,4,5,9,10,11)],ids[c(3,4,5,9,10,11)])
    d$id <- factor(ids,levels=c('001','1','01','NA','','  ',' S','S','S ','unused'))
    fact <- pyfirstevent(data=d,timeA='ta',timeB='tb',statusA='sa',statusB='sb',eventA='Y',freeA='N',eventB='Y',freeB='N',audit_subject=TRUE,subject='id')
    expect_equal(fact$identityAudit$asDF,got$identityAudit$asDF)
    expect_equal(fact$preview$asDF$time,got$preview$asDF$time)
})

test_that('strict ID gate clears saved outputs and recovers with unique IDs', {
    d <- data.frame(ta=c(1,5,NA),tb=c(5,8,3),sa=factor(rep('Y',3),levels=c('N','Y')),sb=factor(rep('N',3),levels=c('N','Y')),id=c('001','001',NA),unique=c('a','b','c'),row.names=c('2','9','41'))
    opts <- pyfirsteventOptions$new(timeA='ta',timeB='tb',statusA='sa',statusB='sb',eventA='Y',freeA='N',eventB='Y',freeB='N',audit_subject=TRUE,subject='id',use_admin=TRUE,admin_cutoff='2')
    for (name in c('timeOut','statusOut','sourceOut','identityOut')) {opt<-opts$option(name);opt$value<-list(value=TRUE,vars=list())}
    a <- pyfirsteventClass$new(options=opts)
    a$.setReadDatasetSource(function(...) d)
    a$.setReadDatasetHeaderSource(function(...) d)
    a$init();a$run();jmvcore:::initProtoBuf()
    saved <- function() a$results$timeOut$asProtoBuf(incAsText=TRUE)$outputs$outputs[[1]]$d
    flags <- function() a$results$identityOut$asProtoBuf(incAsText=TRUE)$outputs$outputs[[1]]$i
    flags_missing <- function() {
        values <- as.numeric(flags())
        length(values) == 3 && all(is.na(values) | values == -2147483648)
    }
    expect_equal(as.numeric(saved()),c(1,2,NA))
    expect_equal(as.integer(flags()),c(3L,3L,1L))
    expect_equal(a$results$identityAudit$asDF$missing,1)
    strict <- opts$option('require_unique_id');strict$value<-TRUE;a$init();expect_error(a$run(),'One record')
    expect_true(all(is.na(saved())))
    expect_true(flags_missing())
    subject <- opts$option('subject');subject$value<-'unique';a$init();a$run()
    expect_equal(as.numeric(saved()),c(1,2,NA))
    expect_equal(a$results$identityAudit$asDF$repeatedRows,0)
    expect_equal(a$results$identityAudit$asDF$subjects,3)
    expect_equal(as.integer(flags()),rep(2L,3))
    subject$value<-NULL;a$init();a$run()
    expect_equal(a$results$identityAudit$rowCount,0)
    expect_true(all(is.na(saved())))
    expect_true(flags_missing())
    strict$value<-FALSE;enabled<-opts$option('audit_subject');enabled$value<-FALSE;a$init();a$run()
    expect_equal(as.numeric(saved()),c(1,2,NA))
    expect_equal(a$results$identityAudit$rowCount,0)
    expect_true(flags_missing())
})
