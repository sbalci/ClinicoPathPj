# Independent exact multinomial coverage using pinned upstream R interval functions.
# Enumerate all tables: no Monte Carlo seeds or target Python implementation.
stopifnot(requireNamespace("jsonlite",quietly=TRUE),requireNamespace("digest",quietly=TRUE))
folder <- "tests/reference/frozen/paired-intervals"
provenance <- jsonlite::fromJSON(file.path(folder,"provenance.json"),simplifyVector=FALSE)
for(name in names(provenance$independent$files))
  stopifnot(digest::digest(file=file.path(folder,name),algo="sha256")==provenance$independent$files[[name]])
env <- new.env(parent=globalenv())
env$validateArguments <- function(...) invisible(NULL)
env$contingencytables_result <- function(res,...) res
sys.source(file.path(folder,"Wilson_score_CI_1x2.R"),env)
sys.source(file.path(folder,"Newcombe_square_and_add_CI_paired_2x2.R"),env)
scenarios <- list(independent_balanced=c(.25,.25,.25,.25),positive_association=c(.45,.05,.05,.45),
  negative_association=c(.05,.45,.45,.05),asymmetric_difference=c(.35,.25,.05,.35),
  rare_successes=c(.005,.005,.005,.985),sparse_boundary=c(0,.001,.099,.9),
  first_always_succeeds=c(.6,.4,0,0),identical_fixed_failures=c(0,0,0,1),fixed_discordance=c(0,1,0,0))
rows <- list()
for(n in c(5,10,20,50)) {
  cells <- matrix(0,choose(n+3,3),4);i<-1L
  for(a in 0:n) for(b in 0:(n-a)) for(c in 0:(n-a-b)) {
    cells[i,] <- c(a,b,c,n-a-b-c);i<-i+1L
  }
  masses <- lapply(scenarios,function(p)apply(cells,1,dmultinom,size=n,prob=p))
  stopifnot(all(vapply(masses,function(m)abs(sum(m)-1)<1e-12,logical(1))))
  for(confidence in c(.8,.95,.99)) {
    limits <- t(apply(cells,1,function(x)unlist(env$Newcombe_square_and_add_CI_paired_2x2(
      matrix(as.numeric(x),2,byrow=TRUE),alpha=1-confidence)[c("lower","upper")])))
    limits[,1] <- pmax(-1,limits[,1]);limits[,2] <- pmin(1,limits[,2])
    for(name in names(scenarios)) {
      p<-scenarios[[name]];truth<-p[2]-p[3];m<-masses[[name]]
      covered <- limits[,1]<=truth+1e-12 & limits[,2]>=truth-1e-12
      coverage <- sum(m[covered])
      rows[[length(rows)+1L]] <- list(n=n,confidence=confidence,scenario=name,
        probabilities=p,true_difference=truth,table_count=nrow(cells),mass_sum=sum(m),
        coverage=coverage,mean_width=sum(m*(limits[,2]-limits[,1])),
        screen_pass=coverage>=confidence-.02-1e-12)
    }
  }
  cat("Enumerated independent R coverage for n=",n,"\n",sep="")
}
report <- list(schema_version=1L,source="Exact multinomial enumeration using unmodified pinned independent R intervals and stats::dmultinom",
  nominal_tolerance=.02,endpoint_tolerance=1e-12,rows=rows,
  reference_sha256=digest::digest(file="tests/reference/paired-difference-coverage.R",algo="sha256"),
  provenance=provenance,R_version=as.character(getRversion()))
jsonlite::write_json(report,"tests/fixtures/paired-difference-coverage.json",auto_unbox=TRUE,digits=17,pretty=TRUE)
cat(length(rows),"coverage profiles;",sum(!vapply(rows,function(r)r$screen_pass,logical(1))),"screen failures.\n")
