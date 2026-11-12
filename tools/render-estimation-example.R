args<-commandArgs(TRUE)
lib<-if(length(args))args[[1]] else '/private/tmp/cpj-estimation-native-library'
.libPaths(c(normalizePath(lib,mustWork=TRUE),
 '/Applications/jamovi.app/Contents/Resources/modules/base/R',.libPaths()))
suppressPackageStartupMessages(library(ClinicoPathPj))
jmvcore:::initProtoBuf()
d<-read.csv('data/python_estimation_examples.csv',colClasses=c(Subject='character'),check.names=FALSE)
d$IndependentGroup<-factor(d$IndependentGroup,levels=c('First','Second'))
a<-pyjjbetweenstats(data=d,dep='Outcome',group='IndependentGroup',firstLevel='First',secondLevel='Second',
 subject='Subject',showCases=TRUE)
b<-pyjjwithinstats(data=d,dep1='FirstMeasurement',dep2='SecondMeasurement',subject='Subject',showCases=TRUE)
stopifnot(a$cohort$asDF$retained==13,b$cohort$asDF$retained==5,
 identical(a$cases$asDF$subjectID[1:3],c('001','01','1')),
 identical(b$cases$asDF$sourceID,c('2','3','5','7','8')))
report<-list(scope='Isolated-source native renders, not desktop exports',independent=a$contrast$asDF,
 paired=b$contrast$asDF,independent_cohort=a$cohort$asDF,paired_cohort=b$cohort$asDF)
for(name in c('independent','paired')) {
 result<-if(name=='independent')a else b
 file<-paste0('docs/validation-exports/python-estimation-',name,'-native-20261112.png')
 result$differencePlot$saveAs(file)
 stopifnot(file.exists(file),file.info(file)$size>1000)
}
jsonlite::write_json(report,'docs/validation-exports/python-estimation-native-example-20261112.json',
 auto_unbox=TRUE,na='null',pretty=TRUE,digits=17)
cat('Rendered both native examples; 13 independent cases and five paired cases.\n')
