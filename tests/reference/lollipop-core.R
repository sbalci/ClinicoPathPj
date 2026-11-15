# Independent R summary/order reference and actual ggplot2 stem geometry.
# Written before cpj_lollipop.py; do not import the target Python implementation.
args<-commandArgs(TRUE)
Sys.setlocale('LC_COLLATE','C')
suppressPackageStartupMessages(library(ggplot2))
make<-function(id,values,codes,levels,baseline=0)list(id=id,
    inputs=list(values=I(values),codes=I(as.integer(codes)),levels=as.list(levels),baseline=baseline))
fixtures<-list(
    make('unequal_groups',c(1,2,9,10,20,30),c(0,0,0,1,2,2),c('A','B','C')),
    make('factor_order',c(5,2,1,7),c(1,0,1,2),c('third','first','second','unused')),
    make('tied_extrema',c(1,5,1,5),c(0,0,1,1),c('A','B')),
    make('negative_baseline',c(-8,-2,0,5),c(0,0,1,1),c('Before','After'),-3),
    make('missing_pairs',c(NA,2,7,NA,8,9),c(0,0,-1,1,1,2),c('A','B','C','unused')),
    make('missing_level',c(1,99,3,5,7),c(0,1,2,0,-1),c('NA',NA,'Other')),
    make('unicode',c(3,1,8,4,7),c(2,0,1,2,0),c('İkinci','<A & B>','Üç')),
    make('constant',rep(4,5),c(0,0,1,1,2),c('A','B','C')),
    make('two_singletons',c(8,2),c(1,0),c('A','B')),
    make('large_offset',1e10+c(1,2,3,4,9),c(0,0,1,1,2),c('A','B','C')),
    make('small_scale',1e-100*c(1,2,9,5),c(0,0,1,1),c('A','B')),
    make('large_scale',1e100*c(1,2,9,5),c(0,0,1,1),c('A','B')))
summary_values<-function(x)list(n=length(x),mean=mean(x),median=median(x),
    sd=if(length(x)>1)sd(x) else NULL,minimum=min(x),maximum=max(x),range=diff(range(x)),
    q1=unname(quantile(x,.25,type=7)),q3=unname(quantile(x,.75,type=7)))
for(i in seq_along(fixtures)) {
    a<-fixtures[[i]]$inputs; labels<-unlist(a$levels); values<-as.numeric(a$values);codes<-as.integer(a$codes)
    group_missing<-codes<0L
    group_missing[!group_missing]<-is.na(labels[codes[!group_missing]+1L])
    keep<-!group_missing & !is.na(values); retained<-which(keep)-1L
    active<-sort(unique(codes[keep])); active_labels<-labels[active+1L]
    d<-data.frame(value=values[keep],group=factor(labels[codes[keep]+1L],levels=active_labels))
    runs<-list()
    for(aggregation in c('mean','median','sum','none')) {
        if(aggregation=='none') {
            points<-d; members<-lapply(retained,function(j)I(j))
        } else {
            points<-aggregate(d$value,list(group=d$group),get(aggregation))
            names(points)<-c('group','value')
            members<-lapply(as.character(points$group),function(label)I(retained[as.character(d$group)==label]))
        }
        for(sorting in c('original','value_asc','value_desc','group_alpha')) {
            order<-switch(sorting,original=seq_len(nrow(points)),value_asc=order(points$value),
                value_desc=order(-points$value),group_alpha=order(as.character(points$group)))
            p<-points[order,,drop=FALSE]; membership<-members[order]
            for(orientation in c('vertical','horizontal')) {
                axis<-if(sorting=='original')active_labels else unique(as.character(p$group))
                if(sorting!='original' && orientation=='horizontal')axis<-rev(axis)
                p$group<-factor(p$group,levels=axis)
                plot<-ggplot(p,aes(x=group,y=value))+geom_segment(aes(xend=group,yend=a$baseline))
                geometry<-ggplot_build(plot)$data[[1]]
                cells<-lapply(seq_len(nrow(p)),function(j)list(code=active[match(as.character(p$group[j]),active_labels)],
                    label=as.character(p$group[j]),value=p$value[j],source_indices=membership[[j]],
                    slot=as.numeric(geometry$x[j]),stem_start=geometry$y[j],stem_end=geometry$yend[j]))
                # geom_segment above draws value -> baseline; the contract stores baseline -> value.
                for(j in seq_along(cells)) {
                    cells[[j]]$stem_start<-geometry$yend[j]; cells[[j]]$stem_end<-geometry$y[j]
                }
                runs[[length(runs)+1L]]<-list(aggregation=aggregation,sorting=sorting,orientation=orientation,
                    expected=list(n_source=length(values),n_complete=sum(keep),excluded_missing=sum(!keep),
                        missing_values=sum(is.na(values)),missing_group=sum(group_missing),
                        retained_indices=I(retained),active_codes=I(active),
                        unused_codes=I(setdiff(which(!is.na(labels))-1L,active)),
                        axis_levels=I(axis),points=cells,raw_summary=summary_values(d$value),
                        plotted_summary=summary_values(p$value),reference_mean=mean(p$value),
                        overplotting=aggregation=='none' && any(table(d$group)>1),
                        highest_groups=I(unique(as.character(p$group[p$value==max(p$value)]))),
                        lowest_groups=I(unique(as.character(p$group[p$value==min(p$value)])))))
            }
        }
    }
    fixtures[[i]]$runs<-runs
}
r<-jsonlite::fromJSON('inst/python/registry.json',simplifyVector=FALSE)
entry<-Filter(function(e)e$id=='pylollipop',r$analyses)[[1]]
result<-list(schema_version=1,baseline_hashes=entry$baseline$files,
    versions=list(R=as.character(getRversion()),ggplot2=as.character(packageVersion('ggplot2'))),fixtures=fixtures)
output<-jsonlite::toJSON(result,auto_unbox=TRUE,digits=17,na='null',null='null')
if(length(args))writeLines(output,args[[1]]) else cat(output,'\n')
