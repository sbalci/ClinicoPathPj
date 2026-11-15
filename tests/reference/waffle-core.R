# Independent integer apportionment and actual installed waffle geometry.
# Freeze this oracle before implementing the Python engine.
suppressPackageStartupMessages(library(ggplot2))
make <- function(id, codes, levels, weights=NULL, facets=NULL, facet_levels=NULL) {
  list(id=id, inputs=list(codes=I(codes), levels=as.list(levels),
    weights=if(is.null(weights)) NULL else I(weights),
    facets=if(is.null(facets)) NULL else I(facets), facet_levels=as.list(facet_levels)))
}
fixtures <- list(
  make('unequal', 0:2, c('A','B','C'), c(12,8,5)),
  make('thirds_tie_later_wins', 0:2, c('A','B','C'), c(1,1,1)),
  make('halves_remainders', 0:2, c('A','B','C'), c(1,3,196)),
  make('legacy_29_truncation', 0:1, c('A','B'), c(29,71)),
  make('legacy_57_58_truncation', 0:2, c('A','B','C'), c(57,1,42)),
  make('rare_category', 0:2, c('Rare','Common','Unused'), c(1,999,0)),
  make('zero_first_unused', c(1,2,0), c('Zero','B','C','Unused'), c(3,7,0)),
  make('unweighted', c(0,1,0,2,1,0), c('III','İkinci','<A & B>')),
  make('missing_roles', c(0,-1,1,0,1,2), c('NA',NA,'Other'),
    c(2,NA,7,0,NA,3)),
  make('facet_denominators', c(0,1,0,1,2), c('A','B','Unused'),
    c(1,3,90,10,0), c(0,0,1,1,2), c('Small','Large','Zero','Unused')),
  make('facet_missing', c(0,1,0,1,0,1,0), c('A','B'),
    c(2,1,3,NA,4,0,1), c(0,0,1,1,-1,1,2), c('NA','Other',NA)),
  make('single_panel_category', c(0,1), c('A','B'), c(2,3), c(0,1), c('One','Two')),
  make('large_exact', 0:2, c('A','B','C'), c(2^40,2^40-1,1)),
  make('twenty_categories', 0:19, paste0('L',1:20), 1:20))
configurations <- list()
for (fixture in fixtures) {
  a <- fixture$inputs
  codes <- as.integer(a$codes); labels <- unlist(a$levels)
  f <- if(is.null(a$facets)) rep(0L,length(codes)) else as.integer(a$facets)
  fl <- if(is.null(a$facets)) 'All observations' else unlist(a$facet_levels)
  w <- if(is.null(a$weights)) rep(1,length(codes)) else as.numeric(a$weights)
  missing_group <- codes < 0L
  missing_group[!missing_group] <- is.na(labels[codes[!missing_group]+1L])
  missing_facet <- f < 0L
  missing_facet[!missing_facet] <- is.na(fl[f[!missing_facet]+1L])
  complete <- !missing_group & !missing_facet & !is.na(w)
  positive <- complete & w>0
  valid <- which(!is.na(labels)); fv <- which(!is.na(fl))
  # Independent base-R grouped counts; no observations are expanded.
  counts <- matrix(0, nrow=length(valid), ncol=length(fv))
  for(j in seq_along(fv)) for(k in seq_along(valid))
    counts[k,j] <- sum(w[positive & f==fv[j]-1L & codes==valid[k]-1L])
  for(rows in c(1L,5L,7L,10L,100L)) for(flip in c(FALSE,TRUE)) {
    panels <- list(); legacy <- list()
    for(j in which(colSums(counts)>0)) {
      count <- counts[,j]; total <- sum(count)
      quota <- 100*count/total; tiles <- floor(quota)
      # Use integer numerators for remainder ordering (all fixture products exact).
      remainder <- 100*count-tiles*total
      additions <- 100-sum(tiles)
      if(additions>0) {
        winners <- tail(order(remainder,seq_along(remainder)),additions)
        tiles[winners] <- tiles[winners]+1
      }
      stopifnot(sum(tiles)==100)
      grid <- expand.grid(y=seq_len(rows),x=seq_len(ceiling(100/rows)))[1:100,]
      if(flip) { old <- grid$x; grid$x <- grid$y; grid$y <- old }
      tile_codes <- rep(valid-1L,tiles)
      cells <- lapply(seq_along(valid),function(k) list(code=valid[k]-1L,
        label=labels[valid[k]],count=count[k],proportion=count[k]/total,
        tiles=tiles[k],represented_proportion=tiles[k]/100,
        allocation_error=tiles[k]/100-count[k]/total,
        omitted_positive=count[k]>0 && tiles[k]==0))
      geometry <- lapply(1:100,function(k) list(code=tile_codes[k],x=grid$x[k],y=grid$y[k],
        xmin=grid$x[k]-.5,xmax=grid$x[k]+.5,ymin=grid$y[k]-.5,ymax=grid$y[k]+.5))
      panels[[length(panels)+1L]] <- list(code=fv[j]-1L,label=fl[fv[j]],n_total=total,
        retained_indices=I(which(positive & f==fv[j]-1L)-1L),cells=cells,geometry=geometry)
      # Execute the real waffle layer. Keep its truncation differences as evidence.
      d <- data.frame(category=factor(labels[valid],levels=labels[valid]),count=count)
      palette <- setNames(sprintf('#%06x',seq_along(valid)),labels[valid])
      p <- ggplot(d,aes(fill=category,values=count))+
        waffle::geom_waffle(n_rows=rows,make_proportional=TRUE,flip=flip)+
        scale_fill_manual(values=palette,drop=FALSE)
      g <- suppressWarnings(ggplot_build(p))$data[[1]]
      actual <- match(g$fill,unname(palette))
      legacy_tiles <- tabulate(actual,nbins=length(valid))
      # Surviving baseline tiles must occupy precisely the same column-major grid.
      stopifnot(identical(as.numeric(g$x),as.numeric(grid$x[seq_len(nrow(g))])),
                identical(as.numeric(g$y),as.numeric(grid$y[seq_len(nrow(g))])),
                identical(g$xmin,as.numeric(grid$x[seq_len(nrow(g))])-.5),
                identical(g$xmax,as.numeric(grid$x[seq_len(nrow(g))])+.5),
                identical(g$ymin,as.numeric(grid$y[seq_len(nrow(g))])-.5),
                identical(g$ymax,as.numeric(grid$y[seq_len(nrow(g))])+.5))
      legacy[[length(legacy)+1L]] <- list(code=fv[j]-1L,tiles=I(legacy_tiles),
        n_tiles=nrow(g),differs=!identical(as.numeric(tiles),as.numeric(legacy_tiles)))
    }
    fixture$rows <- rows; fixture$flip <- flip
    fixture$expected <- list(schema_version=1,status='ok',rows=rows,flip=flip,
      n_source=length(codes),n_complete=sum(complete),excluded_missing=sum(!complete),
      missing_group=sum(missing_group),missing_facet=sum(missing_facet),
      missing_frequency=sum(is.na(w)),zero_frequency=sum(complete & w==0),
      n_contributing=sum(positive),n_total=sum(w[positive]),retained_indices=I(which(positive)-1L),
      inactive_facet_codes=I(fv[colSums(counts)==0]-1L),panels=panels)
    fixture$legacy <- legacy
    configurations[[length(configurations)+1L]] <- fixture
  }
}
registry <- jsonlite::fromJSON('inst/python/registry.json',simplifyVector=FALSE)
entry <- Filter(function(e)e$id=='pyjwaffle',registry$analyses)[[1]]
result <- list(schema_version=1,baseline_hashes=entry$baseline$files,
  versions=list(R=as.character(getRversion()),ggplot2=as.character(packageVersion('ggplot2')),
    waffle=as.character(packageVersion('waffle'))),fixtures=configurations)
args <- commandArgs(TRUE)
json <- jsonlite::toJSON(result,auto_unbox=TRUE,digits=17,na='null',null='null')
if(length(args)) writeLines(json,args[[1]]) else cat(json,'\n')
