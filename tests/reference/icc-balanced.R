# Independent installed R references; no Python implementation is called.
stopifnot(requireNamespace('irr', quietly=TRUE), requireNamespace('psych', quietly=TRUE))
sets <- list(
  two_cases=cbind(c(1,4), c(2,3)),
  three_raters=cbind(c(1,2,4,7,9,12),c(0,3,2,4,7,10),c(2,2,5,6,8,14)),
  biased=cbind(1:12, (1:12)+5+sin(1:12), (1:12)-3+cos(1:12)),
  four_raters=sapply(1:4, function(j) (1:20)*.7+2*sin((1:20)*j)+j/4),
  weak=sapply(1:3, function(j) sin((1:20)*j)*10+(1:20)/10))
models <- c('icc11','icc21','icc31','icc1k','icc2k','icc3k')
fixtures <- list()
for (name in names(sets)) for (confidence in c(.8,.95,.99)) {
  x <- sets[[name]]
  other <- suppressWarnings(psych::ICC(x,lmer=FALSE,alpha=1-confidence))$results
  for (i in seq_along(models)) {
    code <- models[i]
    a <- irr::icc(x,model=if(substr(code,4,4)=='1') 'oneway' else 'twoway',
                 type=if(substr(code,4,4)=='2') 'agreement' else 'consistency',
                 unit=if(endsWith(code,'k')) 'average' else 'single',conf.level=confidence)
    fixtures[[length(fixtures)+1L]] <- list(name=name,x=unname(split(x,row(x))),
      model=code,confidence=confidence,estimate=a$value,
      irr_interval=c(a$lbound,a$ubound),psych_estimate=other$ICC[i],
      psych_interval=unname(as.numeric(other[i,c('lower bound','upper bound')])))
  }
}
jsonlite::write_json(list(reference_versions=list(irr=as.character(packageVersion('irr')),
                     psych=as.character(packageVersion('psych'))),cases=fixtures),
  'tests/fixtures/icc-balanced.json',auto_unbox=TRUE,digits=17,pretty=TRUE,na='null')
