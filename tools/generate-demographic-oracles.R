# Developer-only frozen-source helper and independent base-R cut/table fixtures.
script <- sub('^--file=', '', grep('^--file=', commandArgs(FALSE), value=TRUE))
root <- dirname(dirname(normalizePath(script)))
.libPaths(c(path.expand('~/Library/Application Support/jamovi/modules/ClinicoPathDescriptives/R'),
 '/Applications/jamovi.app/Contents/Resources/modules/base/R', .libPaths()))
ns <- asNamespace('ClinicoPathDescriptives')
tmp <- tempfile('cpj-age-oracle-'); dir.create(tmp)
on.exit(unlink(tmp, recursive=TRUE))
utils::untar(file.path(root,'docs/baselines/released-2026-10-25.tar.gz'),
 files='ClinicoPathDescriptives/R/agepyramid.b.R', exdir=tmp)
env <- new.env(parent=ns)
sys.source(file.path(tmp,'ClinicoPathDescriptives/R/agepyramid.b.R'),envir=env)
obj <- env$agepyramidClass$new(options=get('agepyramidOptions',ns)$new(age='a',gender='g',female='Female',male='Male'),
 data=data.frame(a=1:5,g=factor(c('Female','Male','Female','Male','Female'))))
p <- obj$.__enclos_env__$private
presets <- list(who=c(seq(0,85,5),Inf),who_infant=c(0,1,seq(5,85,5),Inf),
 pediatric=c(0,1,2,5,10,15,18,Inf), reproductive=c(0,15,20,25,30,35,40,45,50,Inf),
 geriatric=c(0,65,70,75,80,85,90,95,Inf),lifecourse=c(0,5,15,25,45,65,75,85,Inf))
cases <- list()
add <- function(ages, preset='custom', width=5, custom='', right=FALSE, base='within_gender') {
 g <- rep(c('Female','Male'), length.out=length(ages))
 valid <- !is.na(ages) & ages>=0 & is.finite(ages)
 x <- ages[valid]; sex <- g[valid]
 opt <- obj$options$option('bin_width'); opt$value <- width
 b <- if (preset != 'custom') presets[[preset]] else if (nzchar(custom)) c(sort(unique(as.numeric(strsplit(custom,',')[[1]]))),Inf) else p$.bin_width_breaks(max(x))
 actual_right <- right && preset=='custom'
 lab <- p$.create_age_labels(b,right=actual_right,whole_ages=all(abs(x-round(x))<1e-8),
  last_width=if (preset=='custom' && !nzchar(custom)) width else NULL)
 band <- cut(x,b,labels=lab,right=actual_right,include.lowest=TRUE)
 counts <- table(factor(band,levels=lab),factor(sex,levels=c('Female','Male')))
 den <- if (base=='total') rep(sum(counts),2) else colSums(counts)
 percentages <- sweep(counts,2,den,'/')
 cases[[length(cases)+1]] <<- list(ages=I(ages),gender=I(g),preset=preset,width=width,custom=custom,
  interval=if(right)'right' else 'left',percentage=base,breaks=I(b[-length(b)]),labels=I(lab),
  female=I(as.integer(counts[,1])),male=I(as.integer(counts[,2])),
  fp=I(percentages[,1]),mp=I(percentages[,2]))
}
a <- c(0,.5,1,2,4.999,5,10,14.9,15,18,25,50,64.9,65,70,85,95,100,120,121,NA,-1)
for (preset in c('custom',names(presets))) for (right in c(FALSE,TRUE)) for (base in c('within_gender','total'))
 add(a,preset=preset,right=right,base=base)
for (a in list(0,c(0,1,4),c(5,10,15,20,25),c(0,.1,.25,.5,.75,1,1.01),c(1.1,5.5,10.3)))
 for (w in c(.25,1,5,10)) for (right in c(FALSE,TRUE)) add(a,width=w,right=right)
for (right in c(FALSE,TRUE)) for (bounds in c('0,18,65,100','18,65','0','-10,0,10'))
 add(c(0,5,18,50,65,100,120),custom=bounds,right=right)
output <- list(provenance=list(R=R.version.string,source='Frozen agepyramid helpers plus independent base::cut and table'),cases=cases)
jsonlite::write_json(output,file.path(root,'tests/fixtures/demographic-oracles.json'),auto_unbox=TRUE,null='null',na='null',digits=17,pretty=TRUE)
cat(length(cases),'demographic fixtures\n')
