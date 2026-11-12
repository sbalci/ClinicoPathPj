# Freeze independent interval references before writing the Python interval engine.
stopifnot(requireNamespace("jsonlite",quietly=TRUE),requireNamespace("digest",quietly=TRUE),
          requireNamespace("Rmpfr",quietly=TRUE))
folder <- "tests/reference/frozen/paired-intervals"
provenance <- jsonlite::fromJSON(file.path(folder,"provenance.json"),simplifyVector=FALSE)
for(name in names(provenance$independent$files))
  stopifnot(digest::digest(file=file.path(folder,name),algo="sha256")==provenance$independent$files[[name]])
stopifnot(digest::digest(file=file.path(folder,"meddecide-paired-proportions.R"),algo="sha256")==provenance$baseline$sha256)
upstream <- new.env(parent=globalenv())
upstream$validateArguments <- function(...) invisible(NULL)
upstream$contingencytables_result <- function(res,...) res
sys.source(file.path(folder,"Wilson_score_CI_1x2.R"),upstream)
sys.source(file.path(folder,"Newcombe_square_and_add_CI_paired_2x2.R"),upstream)
baseline <- new.env(parent=globalenv())
sys.source(file.path(folder,"meddecide-paired-proportions.R"),baseline)

mp_reference <- function(cells, confidence) {
  mp <- function(x) Rmpfr::mpfr(x,precBits=256)
  a<-mp(cells[1]);b<-mp(cells[2]);c<-mp(cells[3]);d<-mp(cells[4]);n<-a+b+c+d
  z <- mp(qnorm((1+confidence)/2));z2<-z*z
  # Independently expressed count-scale Wilson formula, lifted to MPFR256.
  bounds <- function(k) {
    center<-(2*k+z2)/(2*(n+z2))
    half<-z*sqrt(z2+4*k*(n-k)/n)/(2*(n+z2))
    c(max(mp(0),center-half),min(mp(1),center+half))
  }
  p<-(a+b)/n;q<-(a+c)/n;delta<-(b-c)/n
  x<-bounds(a+b);y<-bounds(a+c)
  margins<-(a+b)*(c+d)*(a+c)*(b+d)
  numerator<-a*d-b*c
  if(numerator>0) numerator<-max(numerator-n/2,mp(0))
  phi<-if(margins==0) mp(0) else numerator/sqrt(margins)
  lower<-max(mp(-1),delta-sqrt(max(mp(0),(p-x[1])^2+(y[2]-q)^2-2*phi*(p-x[1])*(y[2]-q))))
  upper<-min(mp(1),delta+sqrt(max(mp(0),(x[2]-p)^2+(q-y[1])^2-2*phi*(x[2]-p)*(q-y[1]))))
  list(lower=as.numeric(lower),upper=as.numeric(upper),estimate=as.numeric(delta),
       phi=as.numeric(phi),critical_z_double=as.numeric(z),
       lower_mpfr=unname(Rmpfr::formatMpfr(lower,digits=75,scientific=TRUE,trim=TRUE)),
       upper_mpfr=unname(Rmpfr::formatMpfr(upper,digits=75,scientific=TRUE,trim=TRUE)))
}

grid <- expand.grid(a=0:4,b=0:4,c=0:4,d=0:4)
cases <- lapply(seq_len(nrow(grid)),function(i)list(id=paste0("grid_",paste(grid[i,],collapse="_")),cells=as.numeric(grid[i,])))
add <- function(id,cells) cases[[length(cases)+1L]] <<- list(id=id,cells=as.numeric(cells))
add("published_Bentur",c(1,1,7,12))
add("published_Cavo",c(59,6,16,80))
add("R_integer_product_overflow",c(200,100,0,200))
add("million_near_identity",c(499999,1,0,500000))
add("million_discordant",c(0,500000,500000,0))
add("million_margin_one",c(0,1000000,0,0))
add("million_rare_first",c(0,1,0,999999))
set.seed(20261112)
for(i in 1:24) add(paste0("random_",i),as.numeric(rmultinom(1,sample(20:10000,1),runif(4))))

# Every class-specific comparison in the earlier, independently frozen diagnostic fixture.
diagnostic <- jsonlite::fromJSON("tests/fixtures/paired-decision.json",simplifyVector=FALSE)
for(f in diagnostic$fixtures) for(pair in f$expected$runs[[1]]$pairs)
  for(metric in c("accuracy","sensitivity","specificity"))
    add(paste(f$id,pair$first_name,pair$second_name,metric,sep="/"),unlist(pair[[metric]]$counts))

for(i in seq_along(cases)) {
  cells<-cases[[i]]$cells;n<-sum(cells)
  runs<-list()
  for(confidence in c(.8,.95,.99)) {
    if(n==0) expected<-list(estimate=NULL,lower=NULL,upper=NULL,phi=NULL,n=0L,status="empty")
    else {
      independent<-upstream$Newcombe_square_and_add_CI_paired_2x2(matrix(cells,2,byrow=TRUE),alpha=1-confidence)
      high<-mp_reference(cells,confidence)
      stopifnot(max(abs(unlist(independent[c("lower","upper","estimate")])-unlist(high[c("lower","upper","estimate")])))<1e-12)
      if(confidence==.95) {
        x<-rep(c(1,1,0,0),cells);y<-rep(c(1,0,1,0),cells)
        original<-baseline$pairedProportionDifference(x,y)
        stopifnot(max(abs(c(original$diff,original$lower,original$upper)-unlist(high[c("estimate","lower","upper")])))<1e-12)
      }
      expected<-list(estimate=high$estimate,lower=high$lower,upper=high$upper,
                     phi=high$phi,n=as.integer(n),status="ok")
    }
    runs[[length(runs)+1L]]<-list(confidence=confidence,expected=expected,
      independent=if(n) independent else NULL,mpfr=if(n) high else NULL,
      baseline_95=if(n && confidence==.95) original else NULL)
  }
  cases[[i]]$runs<-runs
}
report<-list(schema_version=1L,source="Pinned original R helper, unmodified independent contingencytables functions and MPFR256 arithmetic; no Python target called",
             provenance=provenance,reference_code_sha256=digest::digest(file="tests/reference/paired-difference-intervals.R",algo="sha256"),
             precision_bits=256L,quantile_policy="R double qnorm lifted exactly to MPFR256",
             paired_fixture_sha256=digest::digest(file="tests/fixtures/paired-decision.json",algo="sha256"),
             versions=list(R=as.character(getRversion()),Rmpfr=as.character(packageVersion("Rmpfr"))),fixtures=cases)
jsonlite::write_json(report,"tests/fixtures/paired-difference-intervals.json",auto_unbox=TRUE,null="null",digits=17,pretty=TRUE)
cat(length(cases),"count tables;",length(cases)*3L,"confidence runs; R/independent/MPFR references frozen.\n")
