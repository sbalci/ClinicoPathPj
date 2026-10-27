# Independent base-R average-linkage / Euclidean tree references, with source identities.
library(jsonlite)
cases <- list(
  separated = data.frame(a=c(0,2,9,13,20),b=c(1,4,6,19,22),c=c(5,7,11,12,30)),
  tied = data.frame(a=c(0,0,1,1),b=c(2,2,7,7),constant=rep(1,4)),
  missing = data.frame(a=c(1,NA,3,10,NA),b=c(2,5,8,20,NA),c=c(4,6,7,30,NA)))
references <- list()
pairs <- function(tree) {
  matrix <- as.matrix(cophenetic(tree))
  indices <- which(upper.tri(matrix), arr.ind=TRUE)
  lapply(seq_len(nrow(indices)),function(i) list(
    a=rownames(matrix)[indices[i,1]],b=colnames(matrix)[indices[i,2]],
    distance=unname(matrix[indices[i,1],indices[i,2]])))
}
for (name in names(cases)) for (mode in c('raw','zscore')) {
  data <- cases[[name]]
  rownames(data) <- as.character(seq(2,by=3,length.out=nrow(data)))
  x <- as.matrix(data[complete.cases(data),,drop=FALSE])
  if (mode=='zscore') for (j in seq_len(ncol(x))) {
    deviation <- sd(x[,j])
    x[,j] <- if (is.na(deviation)||deviation==0) 0 else (x[,j]-mean(x[,j]))/deviation
  }
  row_tree <- hclust(dist(x),method='average')
  marker_tree <- hclust(dist(t(x)),method='average')
  references[[length(references)+1L]] <- list(name=name,scaling=mode,
    columns=as.list(data),row_ids=rownames(data),
    row_heights=unname(row_tree$height),marker_heights=unname(marker_tree$height),
    row_pairs=pairs(row_tree),marker_pairs=pairs(marker_tree))
}
write_json(references,'tests/fixtures/ihc-tree-oracles.json',auto_unbox=TRUE,
           pretty=TRUE,na='null',digits=NA)
