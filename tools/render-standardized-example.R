args<-commandArgs(TRUE)
lib<-if(length(args))args[[1]] else '/private/tmp/cpj-standardized-native-library'
.libPaths(c(normalizePath(lib,mustWork=TRUE),
 '/Applications/jamovi.app/Contents/Resources/modules/base/R',.libPaths()))
suppressPackageStartupMessages(library(ClinicoPathPj))
jmvcore:::initProtoBuf()
d<-read.csv('data/python_estimation_examples.csv',colClasses=c(Subject='character'),check.names=FALSE)
d$IndependentGroup<-factor(d$IndependentGroup,levels=c('First','Second'))
a<-pyjjbetweenstats(data=d,dep='Outcome',group='IndependentGroup',firstLevel='First',secondLevel='Second',
 subject='Subject',showCases=TRUE,varequal=TRUE,showStandardized=TRUE)
b<-pyjjwithinstats(data=d,dep1='FirstMeasurement',dep2='SecondMeasurement',subject='Subject',
 showCases=TRUE,showStandardized=TRUE)
refs<-jsonlite::fromJSON('tests/fixtures/standardized-effects.json',simplifyVector=FALSE)$fixtures
report<-list(scope='Isolated-source native standardized renders; no new package or desktop qualification',
    independent_cohort=a$cohort$asDF,paired_cohort=b$cohort$asDF)
for(name in c('independent','paired')) {
 result<-if(name=='independent')a else b
 id<-if(name=='independent')'hand_unequal_variance' else 'paired_missing_alignment'
 fixture<-Filter(function(f)f$id==id,refs)[[1]]
 ref<-Filter(function(r)r$confidence==.95,fixture$runs)[[1]]
 stopifnot(abs(result$standardized$asDF$estimate-ref$cohens_d)<=1e-10,
   abs(result$standardized$asDF$lower-ref$delta_lower)<=2e-7,
   abs(result$standardized$asDF$upper-ref$delta_upper)<=2e-7,
   abs(result$hedges$asDF$estimate-ref$hedges_g)<=1e-10)
 file<-paste0('docs/validation-exports/python-standardized-',name,'-native-20261112.png')
 result$standardizedPlot$saveAs(file)
 stopifnot(file.exists(file),file.info(file)$size>1000)
 report[[name]]<-list(standardizer=result$standardizer$asDF,
                     cohen=result$standardized$asDF,hedges=result$hedges$asDF,plot=file)
}
stopifnot(a$cohort$asDF$retained==13,b$cohort$asDF$retained==5,
 identical(a$cases$asDF$subjectID[1:3],c('001','01','1')),
 identical(b$cases$asDF$sourceID,c('2','3','5','7','8')))
jsonlite::write_json(report,'docs/validation-exports/python-standardized-native-example-20261112.json',
 auto_unbox=TRUE,na='null',pretty=TRUE,digits=17)
cat('Rendered both native standardized examples; independent R point/interval checks passed.\n')
