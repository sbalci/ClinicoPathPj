test_that('grouped summaries match independent base R denominators and moments', {
    d <- read.csv(file.path(Sys.getenv('CPJ_ROOT'),'data/python_cross_table_examples.csv'),
                  stringsAsFactors=TRUE,na.strings=c('','NA'))
    for (exclude in c(FALSE,TRUE)) {
        keep <- if (exclude) complete.cases(d) else !is.na(d$Group)
        cohort <- d[keep,,drop=FALSE]
        a <- pycrosstable(data=d,vars=c('Age','Marker','Code'),group='Group',excl=exclude,
                          showTyping=TRUE,showTestDetails=TRUE)
        expect_equal(a$cohort$asDF$n[1],nrow(cohort))
        expect_equal(a$typing$asDF$kind,c('continuous','categorical','categorical'))
        for (display in c('mean','median')) {
            a <- pycrosstable(data=d,vars=c('Age','Marker','Code'),group='Group',excl=exclude,
                              cont=display,showTyping=TRUE,showTestDetails=TRUE)
            tab <- a$continuous$asDF
            for (i in seq_len(nrow(tab))) {
                selected <- if (tab$scope[i]=='Overall') cohort else cohort[cohort$Group==tab$group[i],,drop=FALSE]
                observed <- selected$Age[!is.na(selected$Age)]
                expect_equal(tab$n[i],length(observed))
                expect_equal(tab$missing[i],sum(is.na(selected$Age)))
                if (display=='mean') {
                    expect_equal(tab$mean[i],mean(observed),tolerance=1e-12)
                    expect_equal(tab$sd[i],sd(observed),tolerance=1e-12)
                } else {
                    q <- quantile(observed,c(.25,.5,.75),type=7,names=FALSE)
                    expect_equal(c(tab$q1[i],tab$median[i],tab$q3[i]),q,tolerance=1e-12)
                }
            }
            cats <- a$categories$asDF
            for (i in seq_len(nrow(cats))) {
                selected <- if (cats$scope[i]=='Overall') cohort else cohort[cohort$Group==cats$group[i],,drop=FALSE]
                x <- selected[[cats$variable[i]]]
                valid <- sum(!is.na(x))
                expect_equal(cats$valid[i],valid)
                if (cats$level[i]=='(Missing)') {
                    expect_equal(cats$n[i],sum(is.na(x))); expect_true(is.na(cats$percent[i]))
                } else {
                    count <- sum(as.character(x)==cats$level[i],na.rm=TRUE)
                    expect_equal(cats$n[i],count)
                    expect_equal(cats$percent[i],count/valid)
                }
            }
        }
    }
})

test_that('continuous tests agree with base R exact, tied normal and multi-group ranks', {
    fixtures <- list(
        data.frame(g=factor(rep(c('A','B'),each=5)),x=1:10),
        data.frame(g=factor(rep(c('A','B'),each=6)),x=c(1,2,2,3,4,5,2,3,4,4,6,8)),
        data.frame(g=factor(rep(c('A','B','C'),each=5)),x=c(1:5,3:7,8:12)),
        data.frame(g=factor(rep(c('A','B'),each=49)),x=c(1:97,97)),
        data.frame(g=factor(rep(c('A','B'),each=60)),x=c(rep(1:20,3),rep(2:21,3))),
        data.frame(g=factor(rep(c('A','B'),each=3)),x=rep(2,6)))
    for (d in fixtures) {
        a <- pycrosstable(data=d,vars='x',group='g',numericMode='continuous',showTestDetails=TRUE)
        row <- a$tests$asDF[1,,drop=FALSE]
        if (nlevels(d$g)==2) {
            oracle <- suppressWarnings(wilcox.test(x~g,data=d))
            expect_equal(row$statistic,unname(oracle$statistic),tolerance=1e-12)
        } else {
            oracle <- kruskal.test(x~g,data=d)
            expect_equal(row$df,unname(oracle$parameter))
        }
        expect_equal(row$p,oracle$p.value,tolerance=1e-12)
        if (is.finite(oracle$p.value) && oracle$p.value>0)
            expect_equal(row$p/oracle$p.value,1,tolerance=1e-10)
    }
})

test_that('categorical selection and available-test multiplicity match R', {
    d <- data.frame(g=factor(c(rep('A',60),rep('B',42))),
                    cat=factor(c(rep('N',30),rep('P',30),rep('N',12),rep('P',30))),
                    x=seq_len(102),empty=NA_real_)
    raw <- c(suppressWarnings(chisq.test(table(d$cat,d$g),correct=FALSE))$p.value,
             wilcox.test(x~g,data=d)$p.value,NA_real_)
    for (method in c('none','bonferroni','holm','BH','BY')) {
        a <- pycrosstable(data=d,vars=c('cat','x','empty'),group='g',numericMode='continuous',
                          p_adjust=method,showTestDetails=TRUE)
        expect_equal(a$tests$asDF$p,raw,tolerance=1e-12)
        expect_equal(a$tests$asDF$adjusted,p.adjust(raw,method),tolerance=1e-12)
        expect_identical(a$tests$asDF$method[1],'Pearson χ²')
    }
    sparse <- data.frame(g=factor(c('A','A','B','B')),cat=factor(c('N','N','P','P')))
    a <- pycrosstable(data=sparse,vars='cat',group='g')
    expect_equal(a$tests$asDF$p,fisher.test(table(sparse$cat,sparse$g))$p.value)
    expect_identical(a$tests$asDF$method,'Fisher 2×2')
    larger <- data.frame(g=factor(rep(c('A','B'),each=3)),cat=factor(rep(c('X','Y','Z'),2)))
    a <- pycrosstable(data=larger,vars='cat',group='g')
    expect_true(is.na(a$tests$asDF$p));expect_match(a$tests$asDF$reason,'no Pearson substitution')
})

test_that('native lifecycle restores results and list-bound numeric columns', {
    d <- data.frame(g=factor(rep(c('A','B'),each=5)),x=1:10,cat=factor(rep(c('N','P'),5)))
    opts <- pycrosstableOptions$new(vars=c('x','cat'),group='g')
    a <- pycrosstableClass$new(options=opts,data=d);a$init();a$run()
    before <- a$results$continuous$asDF; p <- a$results$tests$asDF
    expect_true(all(c('mean','sd') %in% names(before)))
    expect_false(any(c('median','q1','q3') %in% names(before)))
    display <- a$options$option('cont');display$value <- 'median';a$init();a$run()
    median <- a$results$continuous$asDF
    expect_true(all(c('median','q1','q3') %in% names(median)))
    expect_false(any(c('mean','sd') %in% names(median)))
    expect_equal(a$results$tests$asDF,p)
    role <- a$options$option('group');role$value <- NULL;a$init();a$run()
    for (name in c('cohort','continuous','categories','tests','typing'))
        expect_equal(a$results[[name]]$rowCount,0)
    role$value <- 'g';display$value <- 'mean';a$init();a$run()
    expect_equal(a$results$continuous$asDF,before)
    expect_equal(a$results$tests$asDF,p)
    expect_equal(a$results$continuous$asDF,pycrosstable(data=d,vars=c('x','cat'),group='g')$continuous$asDF)
})

test_that('genuine missing factor level and recorded labels do not merge', {
    d <- data.frame(g=factor(c('Overall','Overall','B','B')),
                    cat=factor(c('NA',NA,'(Missing)',NA),exclude=NULL))
    a <- pycrosstable(data=d,vars='cat',group='g')
    tab <- a$categories$asDF
    overall <- tab[tab$scope=='Overall',,drop=FALSE]
    expect_equal(overall$n[overall$level=='NA'],1)
    expect_equal(overall$n[overall$level=='(Missing)'],1)
    expect_equal(overall$n[overall$level=='(Missing 2)'],2)
    expect_equal(a$cohort$asDF$n[1],4)
})

test_that('installed gtsummary default agrees on supported nondegenerate tests', {
    skip_if_not_installed('gtsummary')
    d <- data.frame(g=factor(c(rep('A',60),rep('B',42))),x=seq_len(102),
                    cat=factor(c(rep('N',30),rep('P',30),rep('N',12),rep('P',30))))
    reference <- gtsummary::add_p(gtsummary::tbl_summary(d,by=g,
                    type=list(x~'continuous',cat~'categorical')))$table_body
    expected <- reference$p.value[reference$row_type=='label']
    labels <- reference$variable[reference$row_type=='label']
    got <- pycrosstable(data=d,vars=c('x','cat'),group='g')$tests$asDF
    expect_equal(got$p,unname(expected[match(got$variable,labels)]),tolerance=1e-12)
})
