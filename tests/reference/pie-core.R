# Independent aggregation and actual ggplot2 geometry. Written before Python core.
args <- commandArgs(TRUE)
suppressPackageStartupMessages(library(ggplot2))
make <- function(id,codes,levels,weights=NULL,ordered=FALSE) list(id=id,
    inputs=list(codes=I(codes),levels=as.list(levels),weights=if(is.null(weights))NULL else I(weights),ordered=ordered))
fixtures <- list(
    make('unequal',c(0L,1L,2L),c('A','B','C'),c(12,8,5)),
    make('reordered',c(2L,0L,1L,0L),c('third','first','second'),c(3,12,7,2)),
    make('unused_levels',c(0L,1L,0L),c('A','B','Unused'),c(2,3,0)),
    make('zero_first',c(1L,2L,0L),c('Zero','B','C'),c(3,7,0)),
    make('single_active',c(1L,1L,0L),c('Zero','Only','Unused'),c(2,3,0)),
    make('one_declared',c(0L,0L),c('Only')),
    make('missing_unweighted',c(0L,-1L,1L,0L),c('A','B')),
    make('overlapping_missing',c(0L,-1L,1L,0L,1L),c('A','B'),c(12,NA,8,0,NA)),
    make('actual_missing_level',c(0L,1L,2L,0L,-1L),c('NA',NA,'Other'),c(2,7,3,0,1)),
    make('ordinal_unicode',c(1L,0L,2L,1L),c('III','İkinci','<A & B>'),c(1,2,3,4),TRUE),
    make('large_exact',c(0L,1L,2L),c('A','B','C'),c(2^50,2^50-1,1)),
    make('twenty_levels',as.integer(0:19),paste0('L',1:20),1:20))
for(i in seq_along(fixtures)) {
    a <- fixtures[[i]]$inputs; codes <- as.integer(a$codes); labels <- unlist(a$levels)
    weights <- if(is.null(a$weights)) rep(1,length(codes)) else as.numeric(a$weights)
    missing_factor <- codes<0L
    missing_factor[!missing_factor] <- is.na(labels[codes[!missing_factor]+1L])
    complete <- !missing_factor & !is.na(weights); positive <- complete & weights>0
    valid <- which(!is.na(labels)); sums <- vapply(valid,function(k) sum(weights[positive & codes==k-1L]),numeric(1))
    total <- sum(sums)
    f <- factor(labels[codes[positive]+1L],levels=labels[valid],ordered=a$ordered)
    tbl <- tapply(weights[positive],f,sum,default=0)
    stopifnot(identical(as.numeric(tbl),sums))
    d <- data.frame(level=factor(labels[valid],levels=labels[valid],ordered=a$ordered),frequency=sums)
    plot <- ggplot(d,aes(x='',y=frequency,fill=level))+geom_col(position='fill',width=1)+coord_polar(theta='y')
    b <- ggplot_build(plot);g <- b$data[[1]]
    stopifnot(identical(as.integer(g$group),seq_along(valid)),b$layout$coord$start==0,b$layout$coord$direction==1)
    # Also execute the actual ggpiestats path where its bounded palette supports it.
    if(length(valid)<=4L) {
        p <- tryCatch(suppressWarnings(ggstatsplot::ggpiestats(data.frame(level=f,frequency=weights[positive]),
            x=level,counts=frequency,results.subtitle=FALSE,proportion.test=FALSE,bf.message=FALSE)),error=identity)
        if(inherits(p,'error')) {
            stopifnot(fixtures[[i]]$id=='large_exact',grepl('integer',conditionMessage(p)))
            fixtures[[i]]$baseline_limit <- conditionMessage(p)
        } else {
            actual <- ggplot_build(p)$data[[1]]
            stopifnot(isTRUE(all.equal(actual$ymin,g$ymin)),isTRUE(all.equal(actual$ymax,g$ymax)))
        }
    }
    cells <- lapply(seq_along(valid),function(j) {
        middle <- (g$ymin[j]+g$ymax[j])/2
        list(code=valid[j]-1L,label=labels[valid[j]],count=sums[j],proportion=sums[j]/total,
             lower=g$ymin[j],upper=g$ymax[j],theta_lower=2*pi*g$ymin[j],theta_upper=2*pi*g$ymax[j],
             theta_center=2*pi*middle,anchor_x=if(sums[j]>0)sin(2*pi*middle) else NULL,
             anchor_y=if(sums[j]>0)cos(2*pi*middle) else NULL)
    })
    fixtures[[i]]$expected <- list(n_source=length(codes),n_complete=sum(complete),
        excluded_missing=sum(!complete),missing_outcome=sum(missing_factor),missing_frequency=sum(is.na(weights)),
        zero_frequency=sum(complete & weights==0),n_contributing=sum(positive),n_total=total,
        retained_indices=I(which(positive)-1L),cells=cells)
}
registry <- jsonlite::fromJSON('inst/python/registry.json',simplifyVector=FALSE)
entry <- Filter(function(e)e$id=='pyjjpiestats',registry$analyses)[[1]]
result <- list(schema_version=1,baseline_hashes=entry$baseline$files,
    versions=list(R=as.character(getRversion()),ggplot2=as.character(packageVersion('ggplot2')),
                  ggstatsplot=as.character(packageVersion('ggstatsplot'))),fixtures=fixtures)
json <- jsonlite::toJSON(result,auto_unbox=TRUE,digits=17,na='null',null='null')
if(length(args))writeLines(json,args[[1]]) else cat(json,'\n')
