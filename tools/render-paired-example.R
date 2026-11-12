# Run with PYTHONHOME=/Applications/jamovi.app/Contents/Resources Rscript --vanilla ...
args <- commandArgs(TRUE)
lib <- if(length(args)) args[[1]] else 'build/R4.6.0-arm64-macos'
.libPaths(c(normalizePath(lib,mustWork=TRUE),
            '/Applications/jamovi.app/Contents/Resources/modules/base/R',.libPaths()))
suppressPackageStartupMessages(library(ClinicoPathPj))
jmvcore:::initProtoBuf()
d <- read.csv('data/python_paired_test_examples.csv',stringsAsFactors=TRUE,na.strings='')
opts <- get('pydecisioncompareOptions',asNamespace('ClinicoPathPj'))$new(
    gold='Reference',test1='Test_A',test2='Test_B',test3='Test_C',
    goldPositive='Positive',goldNegative='Negative',test1Positive='Positive',test1Negative='Negative',
    test2Positive='Positive',test2Negative='Negative',test3Positive='Positive',test3Negative='Negative',
    referenceType='disease',excludeIndeterminate=TRUE,statComp=TRUE,ci=TRUE,plot=TRUE,
    showCases=TRUE,showPairCounts=TRUE)
a <- get('pydecisioncompareClass',asNamespace('ClinicoPathPj'))$new(options=opts,data=d)
a$run()
stopifnot(a$results$cohort$asDF$retained==16,a$results$cohort$asDF$missing==3,
          a$results$cohort$asDF$outside==1,a$results$comparisons$rowCount==9)
out <- 'docs/validation-exports'
image <- file.path(out,'python-paired-native-example-20261111.png')
a$results$proportionPlot$saveAs(image)
jsonlite::write_json(list(scope='Independent synthetic fixture rendered through native source analysis',
    cohort=a$results$cohort$asDF,counts=a$results$counts$asDF,estimates=a$results$estimates$asDF,
    comparisons=a$results$comparisons$asDF,cases=a$results$cases$asDF,plot=image),
    file.path(out,'python-paired-native-example-20261111.json'),pretty=TRUE,auto_unbox=TRUE,
    dataframe='rows',na='null',digits=17)
cat(image,'\n')
