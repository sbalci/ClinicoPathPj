#!/usr/bin/env Rscript
# Blinded oracle: uses frozen contract, archived wrapper, base R and actual ggplot builds.
args <- commandArgs(trailingOnly=TRUE)
output <- if(length(args)) args[[1]] else 'tests/fixtures/barstats-core.json'
stopifnot(requireNamespace('ggplot2'),requireNamespace('ggstatsplot'),
          requireNamespace('effectsize'),requireNamespace('statsExpressions'),requireNamespace('jsonlite'))
registry_code <- paste0("import json,tarfile,hashlib; r=json.load(open('inst/python/registry.json')); ",
 "walk=lambda x: ([x] if isinstance(x,dict) and x.get('id')=='pyjjbarstats' else ",
 "sum((walk(v) for v in x.values()),[]) if isinstance(x,dict) else ",
 "sum((walk(v) for v in x),[]) if isinstance(x,list) else []); ",
 "b=walk(r)[0]['baseline']['files']; t=tarfile.open('docs/baselines/released-2026-10-25.tar.gz'); ",
 "actual={p:hashlib.sha256(t.extractfile('jjstatsplot/'+p).read()).hexdigest() for p in b}; ",
 "assert actual==b,(actual,b); print(json.dumps(actual,sort_keys=True))")
hashes <- jsonlite::fromJSON(paste(system2('python3',c('-c',shQuote(registry_code)),stdout=TRUE),collapse='\n'))
stopifnot(length(hashes)==4L)
warnings <- list()
capture <- function(expr,id) withCallingHandlers(expr,warning=function(w){
 warnings[[length(warnings)+1L]] <<- list(id=id,message=conditionMessage(w));invokeRestart('muffleWarning')})
close <- function(x,y) stopifnot(isTRUE(all.equal(as.numeric(x),as.numeric(y),tolerance=1e-12)))
fixtures <- list()
add <- function(id,o,g,ol=c('No','Yes'),gl=c('Control','Treatment'),w=NULL) {
 fixtures[[length(fixtures)+1L]] <<- list(id=id,inputs=list(outcome_codes=o,group_codes=g,
 outcome_levels=ol,group_levels=gl,weights=w))
}
add_table <- function(id,m,ol=paste0('O',seq_len(nrow(m))),gl=paste0('G',seq_len(ncol(m)))) {
 grid <- expand.grid(o=seq_len(nrow(m))-1L,g=seq_len(ncol(m))-1L)
 add(id,grid$o,grid$g,ol,gl,as.numeric(m))
}
add_table('dense_2x2',matrix(c(12,8,3,17),2))
add_table('sparse_2x2',matrix(c(1,0,0,5),2))
add_table('balanced_independent',matrix(c(20,20,20,20),2))
add_table('dense_3x3',matrix(c(20,11,9,12,18,15,30,14,21),3))
add_table('sparse_3x3',matrix(c(1,0,0,0,2,0,1,0,3),3))
add_table('unequal_2x3',matrix(c(1,9,20,10,100,50),2))
add_table('reversed_order',matrix(c(17,3,8,12),2),c('Yes','No'),c('Treatment','Control'))
add_table('ordinal_numeric_labels',matrix(c(5,10,7,8,9,12),3),c('10','2','1'),c('B','A'))
add_table('unicode',matrix(c(10,7,4,11),2),c('陰性','阳性'),c('İlaç','Kontrol'))
add_table('literal_NA',matrix(c(12,8,3,17),2),c('NA','observed'))
add_table('unused_zero_margins',matrix(c(12,8,0,3,17,0,0,0,0),3))
add('actual_NA_level',c(0,1,2,0,1,2),c(0,0,0,1,1,1),c('NA','yes',NA_character_),w=c(10,8,100,4,15,100))
add('missing_roles_frequencies',c(0,1,-1,0,1,0,1,0),c(0,0,0,1,1,-1,1,1),w=c(10,8,20,4,15,10,NA,0))
add('unweighted',c(0,1,0,1,0,1,1,0,1,1),c(0,0,0,0,1,1,1,1,1,1))
add('unweighted_missing',c(0,1,-1,0,1,1,0,1),c(0,0,0,1,1,-1,1,1))
add_table('huge_aggregated',matrix(c(100000000003,200000000007,300000000011,400000000019),2))
add_table('corrected_unavailable_n2',matrix(c(1,0,0,1),2))
add_table('zero_cells_dense_margins',matrix(c(0,40,30,0),2))
add_table('dense_4x2',matrix(c(10,20,30,40,15,25,35,45),4))
add_table('all_zero',matrix(0,2,2))
add_table('single_active_outcome',matrix(c(10,0,15,0),2))
add('all_missing',c(-1,-1),c(0,1))
add('negative_weight_on_missing',c(-1,0,1),c(0,0,1),w=c(-2,10,10))
add('fractional_weight',c(0,1),c(0,1),w=c(1.5,2))
add('infinite_weight',c(0,1),c(0,1),w=c(Inf,2))
add('invalid_code',c(0,2),c(0,1))
add('over_total_cap',c(0,1),c(0,1),w=c(2^53-1,1))
add('too_many_active',rep(0:20,2),rep(0:1,each=21),paste0('O',0:20))
make <- function(f) {
 z<-f$inputs;o<-z$outcome_codes;g<-z$group_codes;n<-length(o);w<-z$weights
 fail<-function(code) list(id=f$id,inputs=z,expected=list(status='error',error_code=code))
 if(is.null(w)) w<-rep(1,n)
 if(any(!is.na(w)&(!is.finite(w)|w<0|w!=floor(w)))) return(fail('invalid_weights'))
 if(any(o< -1|o>=length(z$outcome_levels))||any(g< -1|g>=length(z$group_levels))) return(fail('invalid_codes'))
 om<-o<0;gm<-g<0
 om[!om]<-is.na(z$outcome_levels[o[!om]+1]);gm[!gm]<-is.na(z$group_levels[g[!gm]+1])
 complete<-!om&!gm&!is.na(w);keep<-complete&w>0;keep[is.na(keep)]<-FALSE
 if(!any(keep)) return(fail('empty_cohort'))
 if(sum(w[keep])>2^53-1) return(fail('total_out_of_range'))
 # xtabs retains declared code order and never expands weighted records.
 d<-data.frame(o=factor(o[keep],levels=seq_along(z$outcome_levels)-1L),
 g=factor(g[keep],levels=seq_along(z$group_levels)-1L),w=w[keep])
 full<-xtabs(w~o+g,d,drop.unused.levels=FALSE)
 ao<-which(rowSums(full)>0);ag<-which(colSums(full)>0);m<-full[ao,ag,drop=FALSE]
 if(length(ao)<2||length(ag)<2) return(fail('insufficient_levels'))
 if(length(ao)>20||length(ag)>20) return(fail('too_many_levels'))
 N<-sum(m);r<-nrow(m);c<-ncol(m);E<-outer(rowSums(m),colSums(m))/N
 chi<-capture(chisq.test(m,correct=FALSE),f$id);close(chi$expected,E)
 X<-sum((m-E)^2/E);close(X,chi$statistic)
 denom<-min(r-(r-1)^2/(N-1)-1,c-(c-1)^2/(N-1)-1)
 vc<-if(denom>0)sqrt(max(0,X/N-(r-1)*(c-1)/(N-1))/denom) else NULL
 raw<-sqrt(X/N/min(r-1,c-1))
 if(!is.null(vc))close(effectsize::cramers_v(chi,adjust=TRUE,ci=NULL)[[1]],vc)
 fisher<-r==2&&c==2&&any(E<5)
 p<-if(fisher)capture(fisher.test(m)$p.value,f$id) else chi$p.value
 cells<-list();geo<-list(percentage=list(),count=list())
 for(j in seq_len(c))for(i in seq_len(r)) {
  count<-m[i,j];gt<-sum(m[,j]);ot<-sum(m[i,]);lo<-if(i<r)sum(m[(i+1):r,j]) else 0;hi<-lo+count
  base<-list(outcome=ao[i]-1L,group=ag[j]-1L,count=unname(count),expected=unname(E[i,j]),
   group_total=unname(gt),outcome_total=unname(ot),group_proportion=unname(count/gt),overall_proportion=unname(count/N))
  cells[[length(cells)+1L]]<-base
  for(scale in c('percentage','count')) {
   divisor<-if(scale=='percentage')gt else 1
   geo[[scale]][[length(geo[[scale]])+1L]]<-c(base,list(x=j,xmin=j-.45,xmax=j+.45,
    lower=unname(lo/divisor),upper=unname(hi/divisor),center=unname((lo+hi)/2/divisor)))
  }
 }
 grid<-expand.grid(o=factor(seq_len(r),levels=seq_len(r)),g=factor(seq_len(c),levels=seq_len(c)))
 grid$w<-as.numeric(m)
 for(scale in c('percentage','count')) {
  built<-ggplot2::ggplot_build(ggplot2::ggplot(grid,ggplot2::aes(x=g,y=w,fill=o))+
   ggplot2::geom_col(position=if(scale=='percentage')'fill' else 'stack',width=.9))$data[[1]]
  close(built$ymin,vapply(geo[[scale]],function(x)x$lower,0));close(built$ymax,vapply(geo[[scale]],function(x)x$upper,0))
  close(built$xmin,vapply(geo[[scale]],function(x)x$xmin,0));close(built$xmax,vapply(geo[[scale]],function(x)x$xmax,0))
 }
 assoc<-list(enabled=TRUE,pearson_statistic=unname(X),df=(r-1)*(c-1),pearson_p=unname(chi$p.value),
 primary_method=if(fisher)'fisher_exact' else 'pearson_chi_square',primary_p=unname(p),
 cramers_v_raw=raw,cramers_v_corrected=vc,corrected_unavailable_reason=if(is.null(vc))'nonpositive_corrected_denominator' else NULL,
 sparse_warning=any(E<5)&&!fisher,minimum_expected=min(E),expected_below5=sum(E<5))
 list(id=f$id,inputs=z,expected=list(status='ok',n_source=n,n_complete=sum(complete),excluded_missing=sum(!complete),
 missing_outcome=sum(om),missing_group=sum(gm),missing_frequency=sum(is.na(w)),zero_frequency=sum(complete&w==0,na.rm=TRUE),
 n_contributing=sum(keep),n_total=N,retained_indices=which(keep)-1L,outcome_codes=ao-1L,group_codes=ag-1L,
 dropped_outcome_codes=setdiff(seq_along(z$outcome_levels),ao)-1L,
 dropped_group_codes=setdiff(seq_along(z$group_levels),ag)-1L,cells=cells,association=assoc,
 association_off=list(enabled=FALSE,primary_method='disabled',primary_p=NULL,pearson_statistic=NULL,df=NULL,pearson_p=NULL,cramers_v_raw=NULL,cramers_v_corrected=NULL),geometry=geo))
}
result<-lapply(fixtures,make)
# Real ggstatsplot shape reference on modest weighted data only; no huge-N expansion.
m<-matrix(c(12,8,3,17),2);d<-expand.grid(o=factor(c('No','Yes'),levels=c('No','Yes')),
 g=factor(c('Control','Treatment'),levels=c('Control','Treatment')));d$w<-as.numeric(m)
p<-capture(ggstatsplot::ggbarstats(d,o,g,counts=w,results.subtitle=FALSE,
 proportion.test=FALSE,bf.message=FALSE),'ggbarstats_shape')
b<-ggplot2::ggplot_build(p)$data[[1]]
close(b$ymin,vapply(result[[1]]$expected$geometry$percentage,function(x)x$lower,0))
close(b$ymax,vapply(result[[1]]$expected$geometry$percentage,function(x)x$upper,0))
# Inspect raw-table and htest conventions empirically: effectsize recomputes the
# uncorrected statistic from observed/expected even when its internal htest used Yates.
u<-chisq.test(m,correct=FALSE);y<-chisq.test(m,correct=TRUE)
es_u<-effectsize::cramers_v(u,adjust=TRUE,ci=NULL)[[1]]
es_y<-effectsize::cramers_v(y,adjust=TRUE,ci=NULL)[[1]]
es_matrix<-effectsize::cramers_v(m,correct=FALSE,ci=NULL)[[1]]
close(es_y,es_matrix);close(es_u,es_matrix)
se<-capture(statsExpressions::contingency_table(d,o,g,counts=w),'statsExpressions_continuity')
stopifnot('effectsize'%in%names(se));close(se$estimate,es_matrix)
manifest<-list(schema_version=1,versions=lapply(c('ggplot2','ggstatsplot','effectsize','statsExpressions','jsonlite'),
 function(x)as.character(packageVersion(x))),R_version=R.version.string,
 provenance=list(contract='docs/python-barstats-core.md',oracle='base xtabs, chisq.test(correct=FALSE), fisher.test and explicit Bergsma equations',
 geometry='Actual ggplot_build geom_col(position=fill/stack) for every successful fixture; actual ggbarstats first layer for dense_2x2',
 inference_modes='Every success has association enabled and association_off; no inference required when disabled'),
 baseline_hashes_verified=hashes,discrepancies=list(list(id='2x2_continuity',
 explanation='No point discrepancy: statsExpressions 2.1.1 passes correct=FALSE to both test and raw-table effectsize call. effectsize 1.0.3 internally builds a default Yates htest but .effectsize_chisq.test_dep recomputes uncorrected .chisq(Obs,Exp). Raw table, Yates htest and uncorrected htest therefore give the same Bergsma point.',
 uncorrected_chisq=unname(u$statistic),yates_chisq=unname(y$statistic),corrected_v_uncorrected_htest=es_u,
 corrected_v_raw_table=es_matrix,statsExpressions_effectsize=unname(se$estimate))),oracle_warnings=warnings,fixtures=result)
names(manifest$versions)<-c('ggplot2','ggstatsplot','effectsize','statsExpressions','jsonlite')
# Exact binary64 encoder; input arrays and code arrays remain arrays, even singletons.
array_keys<-c('outcome_codes','group_codes','outcome_levels','group_levels','weights','retained_indices',
 'dropped_outcome_codes','dropped_group_codes')
encode<-function(x,force_array=FALSE){
 if(is.null(x))return('null')
 if(is.list(x)) {
  if(!is.null(names(x)))return(paste0('{',paste(vapply(names(x),function(k)paste0(
   jsonlite::toJSON(k,auto_unbox=TRUE),':',encode(x[[k]],k%in%array_keys)),''),collapse=','),'}'))
  return(paste0('[',paste(vapply(x,encode,''),collapse=','),']'))
 }
 atom<-function(v){if(is.na(v))return('null');if(is.character(v))return(as.character(jsonlite::toJSON(v,auto_unbox=TRUE)))
  if(is.logical(v))return(if(v)'true' else 'false');if(is.infinite(v))return(if(v>0)'"Infinity"' else '"-Infinity"');sprintf('%.17g',v)}
 if(force_array||length(x)!=1L)paste0('[',paste(vapply(x,atom,''),collapse=','),']') else atom(x)
}
writeLines(encode(manifest),output,useBytes=TRUE)
parsed<-jsonlite::fromJSON(output,simplifyVector=FALSE)
roundtrip<-function(a,b){
 if(is.list(a))for(i in seq_along(a))roundtrip(a[[i]],b[[i]])
 else if(is.numeric(a)) {
  recovered<-if(is.list(b))vapply(b,function(v)if(is.null(v))NA_real_ else as.double(v),0) else as.double(b)
  stopifnot(identical(as.double(a),recovered))
 }
}
roundtrip(manifest,parsed)
cat(sprintf('PASS: %d fixtures (%d successful); all geometry builds; four baseline hashes; exact numeric JSON round-trip.\n',
 length(result),sum(vapply(result,function(f)f$expected$status=='ok',FALSE))))
