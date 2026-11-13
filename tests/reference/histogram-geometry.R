#!/usr/bin/env Rscript
# Blinded independent geometry oracle. Do not read the Python implementation.
args <- commandArgs(trailingOnly = TRUE)
output <- if (length(args)) args[[1]] else 'tests/fixtures/histogram-geometry.json'
stopifnot(requireNamespace('ggplot2'), requireNamespace('ggstatsplot'),
          requireNamespace('jsonlite'))
stopifnot(as.character(packageVersion('ggplot2')) == '4.0.3',
          as.character(packageVersion('ggstatsplot')) == '1.1.1')
registry_code <- paste0(
  "import json,tarfile,hashlib; r=json.load(open('inst/python/registry.json')); ",
  "walk=lambda x: ([x] if isinstance(x,dict) and x.get('id')=='pyjjhistostats' else ",
  "sum((walk(v) for v in x.values()),[]) if isinstance(x,dict) else ",
  "sum((walk(v) for v in x),[]) if isinstance(x,list) else []); ",
  "b=walk(r)[0]['baseline']['files']; t=tarfile.open('docs/baselines/released-2026-10-25.tar.gz'); ",
  "actual={p:hashlib.sha256(t.extractfile('jjstatsplot/'+p).read()).hexdigest() for p in b}; ",
  "assert actual==b,(actual,b); print(json.dumps(actual,sort_keys=True))")
hashes <- jsonlite::fromJSON(paste(system2('python3', c('-c', shQuote(registry_code)),
                                                     stdout = TRUE), collapse = '\n'))
stopifnot(length(hashes) == 4L)
fixtures <- list()
add <- function(id, values, widths = c(.5, 1.1)) {
  fixtures[[length(fixtures) + 1L]] <<- list(id = id, values = values, widths = widths)
}
add('ordinary', c(0,1,2,3,4,5))
add('negative_only', c(-9,-8,-7,-4,-2), c(1,2.5))
add('fractional', c(-.75,-.5,-.25,0,.25,.5,.75), c(.25,.1))
add('missing', c(NA,1,NA,2,4,NA,8), c(1,3))
add('constant_zero', rep(0,6), c(1,.1))
add('constant_nonzero', rep(3,5), c(1,1.1))
add('singleton', 1.25, c(1,.25))
add('missing_singleton', c(NA,NA,0,NA), 1)
add('raw_edge_neighbors', c(-2,-.5-2^-53,-.5,-.5+2^-54,
                           .5-2^-54,.5,.5+2^-53,1.5-2^-52,1.5,1.5+2^-52,2), 1)
f <- 1e-8
add('fuzzy_edge_neighbors', c(-2,-.5+f-2^-54,-.5+f,-.5+f+2^-54,
                             .5+f-2^-53,.5+f,.5+f+2^-53,2), 1)
# Extend original min/max to test both outside endpoints of a boundary-aligned range.
add('outer_raw_edges', c(-2.5,-2.5+2^-51,-.5,.5,2.5-2^-51,2.5), 1)
add('sparse_bins', c(-10,-10,0,10), c(.25,1))
add('shifted', c(8,9,10,11,13), c(.7,2))
add('large_offset', 1e12+c(-4,-2,-1,0,1,3,6), c(.7,2))
add('offset_rounding', 1e15+c(-2,-1,0,1,2), c(.7,1.1))
add('small_scale', c(-3,-1,0,1,2,7)*1e-100, c(.7,2)*1e-100)
add('large_scale', c(-3,-1,0,1,2,7)*1e100, c(.7,2)*1e100)
add('bin_limit', c(0,2000), c(1,.5))
add('collapsed_offset', 1e12+c(0,1), 1e-8)
add('overflow_width', c(-1e308,1e308), 1e308)
# Capture warnings exactly, including ggplot2's wrapped stat failures.
oracle_warnings <- list()
capture <- function(expr, id, label) {
  messages <- character()
  value <- tryCatch(withCallingHandlers(expr, warning = function(w) {
    messages <<- c(messages, conditionMessage(w)); invokeRestart('muffleWarning')
  }), error = function(e) e)
  for (message in messages) oracle_warnings[[length(oracle_warnings)+1L]] <<-
    list(id=id, run=label, message=message)
  list(value=value, warnings=messages,
       error=if(inherits(value,'error')) conditionMessage(value) else NULL)
}
close <- function(a,b) stopifnot(isTRUE(all.equal(a,b,tolerance=1e-12,
                                                  check.attributes=FALSE)))
make_run <- function(x, automatic, width, id) {
  label <- if(automatic) 'automatic' else sprintf('manual:%.17g',width)
  n <- length(x)
  run <- list(automatic=automatic,width=if(is.finite(width)) width else NULL,
              geometry_status='ok',raw_edges=numeric(),fuzzy_edges=numeric(),bins=list(),
              reference_error=NULL,warnings=character(),reference_status='ok')
  # Avoid asking ggplot2 to allocate an out-of-contract number of bins.
  if (is.finite(width) && width>0) {
    boundary <- width/2
    origin <- boundary+floor((min(x)-boundary)/width)*width
    upper <- max(x)+(1-1e-8)*width
    estimate <- (upper-origin)/width
    if (is.finite(estimate) && estimate>=2001) {
      run$geometry_status <- 'error'
      run$error_code <- 'too_many_bins'
      run$reason <- 'Geometry exceeds the frozen 2000-bin cap.'
      run$reference_status <- 'not_built_contract_cap'
      return(run)
    }
  }
  plot <- ggplot2::ggplot(data.frame(x=x),ggplot2::aes(x=x)) +
    ggplot2::geom_histogram(binwidth=width,closed='right',pad=FALSE)
  built <- capture(ggplot2::ggplot_build(plot)$data[[1]],id,label)
  run$warnings <- built$warnings
  if (automatic && width==0) {
    stopifnot(is.null(built$error),nrow(built$value)==0L,length(built$warnings)>0)
    run$geometry_status <- 'constant_auto'
    run$reason <- 'Automatic width is zero; select an explicit positive manual width.'
    run$reference_status <- 'empty_panel'
    return(run)
  }
  breaks <- capture(ggplot2:::bin_breaks_width(range(x),width,closed='right'),id,
                    paste0(label,':breaks'))
  if(!is.null(built$error) || !is.null(breaks$error) || nrow(built$value)==0L) {
    run$geometry_status <- 'error'
    run$error_code <- 'reference_numeric_error'
    run$reference_status <- 'error_or_empty_panel'
    run$reference_error <- built$error %||% breaks$error %||% paste(built$warnings,collapse='\n')
    return(run)
  }
  edges <- breaks$value
  run$raw_edges <- edges$breaks; run$fuzzy_edges <- edges$fuzzy
  # geom_histogram overwrites the `width` aesthetic with 0.9; stat_bin's actual
  # width is retained with geom='blank'. Use that actual built statistical layer.
  stat <- capture(ggplot2::ggplot_build(ggplot2::ggplot(data.frame(x=x),
      ggplot2::aes(x=x))+ggplot2::stat_bin(geom='blank',binwidth=width,
                                        closed='right',pad=FALSE))$data[[1]],id,
                  paste0(label,':stat'))
  stopifnot(is.null(stat$error))
  layer <- built$value; actual <- stat$value
  for (field in c('x','xmin','xmax','count','density')) close(layer[[field]],actual[[field]])
  stopifnot(nrow(layer)==length(edges$breaks)-1L)
  if(nrow(layer)>2000L || any(!is.finite(c(edges$breaks,edges$fuzzy,actual$width))) ||
     any(diff(edges$breaks)<=0) || any(actual$width<=0) || any(layer$xmax<=layer$xmin)) {
    run$geometry_status <- 'error'; run$error_code <- 'invalid_numeric_geometry'
    run$reason <- 'Reference edges or displayed bounds collapse, overflow, or exceed the cap.'
    return(run)
  }
  run$bins <- lapply(seq_len(nrow(layer)),function(i) list(center=layer$x[i],
    width=actual$width[i],lower=layer$xmin[i],upper=layer$xmax[i],
    count=layer$count[i],proportion=layer$count[i]/n,density=layer$density[i]))
  if(sum(layer$count)!=n) {
    run$geometry_status <- 'error'; run$error_code <- 'reference_lost_counts'
    run$reference_status <- 'lost_counts'
    run$reference_error <- sprintf('Actual ggplot2 counted %g of %d retained observations.',sum(layer$count),n)
    return(run)
  }
  close(sum(layer$count/n),1);close(sum(layer$density*actual$width),1)
  # Independent fuzzy interval membership also checks the actual stat counts.
  membership <- cut(x,edges$fuzzy,right=TRUE,include.lowest=TRUE,labels=FALSE)
  stopifnot(!anyNA(membership),identical(as.numeric(tabulate(membership,nrow(layer))),layer$count))
  run
}
`%||%` <- function(a,b) if(is.null(a)) b else a
make_fixture <- function(f) {
  source <- f$values; x <- source[!is.na(source)]; n <- length(x)
  width <- ggstatsplot:::.binwidth(x)
  # Verify actual gghistostats applies this helper's value, without inference.
  default_plot <- capture(ggstatsplot::gghistostats(data.frame(x=x),x,
    results.subtitle=FALSE,centrality.plotting=FALSE),f$id,'gghistostats_default')
  stopifnot(is.null(default_plot$error))
  close(default_plot$value$layers[[1]]$stat_params$binwidth,width)
  qs <- quantile(x,c(.25,.5,.75),type=7,names=FALSE)
  safe <- function(v) if(all(is.finite(v))) v else NULL
  list(id=f$id,values=source,n_source=length(source),n_complete=n,
    excluded_missing=sum(is.na(source)),retained_indices=which(!is.na(source))-1L,
    summary=list(n=n,mean=safe(mean(x)),sd=if(n>1)safe(sd(x)) else NULL,
      minimum=min(x),q1=safe(qs[1]),median=safe(qs[2]),q3=safe(qs[3]),maximum=max(x)),
    runs=c(list(make_run(x,TRUE,width,f$id)),
           lapply(f$widths,function(w)make_run(x,FALSE,w,f$id))))
}
result <- lapply(fixtures,make_fixture)
manifest <- list(schema_version=1L,
  versions=list(R=R.version.string,ggplot2=as.character(packageVersion('ggplot2')),
                ggstatsplot=as.character(packageVersion('ggstatsplot')),
                jsonlite=as.character(packageVersion('jsonlite'))),
  provenance=list(contract='docs/python-histogram-geometry.md',
    reference='Actual ggplot_build geom_histogram and stat_bin geom=blank layers.',
    breaks='ggplot2:::bin_breaks_width(range(retained), width, closed=right)',
    default_width='Verified actual gghistostats layer stat_params$binwidth against .binwidth.',
    maximum_bins=2000L),baseline_hashes_verified=hashes,
  discrepancies=list('geom_histogram built width aesthetic is 0.9; bins.width uses actual pre-geom statistical width, not that aesthetic.'),
  oracle_warnings=oracle_warnings,fixtures=result)
# Exact encoder taken from histogram-core.R, extended only for edge arrays.
encode <- function(x,force_array=FALSE) {
  if(is.null(x)) return('null')
  if(is.list(x)) {
    if(!is.null(names(x))) return(paste0('{',paste(vapply(names(x),function(k)
      paste0(jsonlite::toJSON(k,auto_unbox=TRUE),':',encode(x[[k]],force_array=k %in%
        c('values','raw_edges','fuzzy_edges','retained_indices','warnings'))),''),collapse=','),'}'))
    return(paste0('[',paste(vapply(x,encode,''),collapse=','),']'))
  }
  atom <- function(v) {
    if(is.na(v)) return('null')
    if(is.character(v)) return(as.character(jsonlite::toJSON(v,auto_unbox=TRUE)))
    if(is.logical(v)) return(if(v)'true' else 'false')
    stopifnot(is.finite(v)); sprintf('%.17g',v)
  }
  if(force_array || length(x)!=1L) paste0('[',paste(vapply(x,atom,''),collapse=','),']') else atom(x)
}
writeLines(encode(manifest),output,useBytes=TRUE)
parsed <- jsonlite::fromJSON(output,simplifyVector=FALSE)
# Check every numeric atom, not just input doubles, survives JSON round-trip.
roundtrip <- function(original,restored) {
  if(is.list(original)) for(i in seq_along(original)) roundtrip(original[[i]],restored[[i]])
  else if(is.numeric(original)) {
    recovered <- if(is.list(restored)) vapply(restored,function(v)if(is.null(v)) NA_real_ else v,0) else restored
    stopifnot(identical(as.double(original),as.double(recovered)))
  }
}
roundtrip(manifest,parsed)
runs <- unlist(lapply(result,function(f)lapply(f$runs,function(r)r$geometry_status)))
cat(sprintf('PASS: %d fixtures; %d runs (%s); %d warnings; exact numeric JSON round-trip.\n',
  length(result),length(runs),paste(names(table(runs)),table(runs),collapse=', '),length(oracle_warnings)))
cat(sprintf('Versions: R %s; ggplot2 %s; ggstatsplot %s.\n',getRversion(),
  packageVersion('ggplot2'),packageVersion('ggstatsplot')))
cat('Verified archive SHA-256 hashes:\n');print(hashes)
