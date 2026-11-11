# Independent ROC oracle: literal case/control pairwise kernels, not target code.
# E[K(X+,X-)] = P(oriented X+ > X-) + .5 P(tie).
# DeLong covariance = sampleCov(case placements)/m + sampleCov(control placements)/n.
# Paired difference variance also computed directly from differences of placements.
suppressPackageStartupMessages(library(pROC))
suppressPackageStartupMessages(library(jsonlite))
set.seed(20261114)
fixtures <- list()
add <- function(id, codes, markers, directions = NULL, levels = c("Negative", "Positive"), positive = "Positive") {
  if (is.null(directions)) directions <- setNames(rep("higher", length(markers)), names(markers))
  fixtures[[length(fixtures) + 1L]] <<- list(id = id, codes = as.integer(codes), levels = levels,
    positive = positive, markers = markers, directions = directions)
}
# Hand kernel for A: positives 2,3,3,5 vs controls 1,2,3,4 -> placements 3/8,5/8,5/8,1;
# AUC = 21/32 = .65625 (ties receive half credit).
add("hand_asymmetric_ties", c(rep(0,4), rep(1,4)),
    list(A = c(1,2,3,4,2,3,3,5), B = c(1,4,2,3,3,2,5,4), C = c(9,8,7,6,8,7,7,5)),
    c(A="higher",B="higher",C="lower"))
add("zero_inverted_and_perfect", c(rep(0,4),rep(1,4)),
    list(perfect=c(1,2,3,4,5,6,7,8), inverted=c(5,6,7,8,1,2,3,4)))
add("below_chance_fixed_direction", c(rep(0,4),rep(1,4)),
    list(A=c(4,5,6,7,1,3,5,6),B=c(3,5,6,7,1,2,4,6)))
add("constant_scores", c(rep(0,4),rep(1,4)), list(A=rep(2,8),B=c(1,2,3,4,2,3,3,5)))
add("identical_models", c(rep(0,4),rep(1,4)), list(A=c(1,2,3,4,2,3,3,5),B=c(1,2,3,4,2,3,3,5)))
add("affine_duplicate_models", c(rep(0,4),rep(1,4)), list(A=c(1,2,3,4,2,3,3,5),B=7+3*c(1,2,3,4,2,3,3,5)))
add("negative_covariance",c(rep(0,4),rep(1,4)),list(A=c(1,2,3,4,2,3,3,5),B=-c(1,2,3,4,2,3,3,5)))
add("distinct_model_missingness",c(0,0,0,0,0,1,1,1,1,1,-1),
    list(A=c(1,NA,3,4,5,2,3,NA,5,6,9),B=c(2,3,4,NA,6,3,4,5,6,7,NA)))
add("literal_NA_label",c(0,0,0,0,1,1,1,1),list(`測定 A`=c(1,2,3,4,2,3,3,5)),
    levels=c("Other","NA"),positive="NA")
add("one_each",c(0,1),list(A=c(0,1),B=c(1,0)))
add("two_each",c(0,0,1,1),list(A=c(1,3,2,4),B=c(1,2,3,2)))
add("one_case_four_controls",c(0,0,0,0,1),list(A=c(1,2,3,4,3),B=c(4,3,2,1,2)))
codes <- rep(c(0,1),each=30);z <- rnorm(60)
add("normal_n60",codes,list(A=z+.8*codes,B=.5*z+rnorm(60)+.6*codes,C=-z-rnorm(60)-codes),
    c(A="higher",B="higher",C="lower"))
codes <- rep(c(0,1),each=20);z <- rnorm(40)
add("skew_n40",codes,list(A=exp(z+.5*codes),B=exp(.4*z+rnorm(40)+.4*codes)))
data(aSAH,package="pROC")
add("pROC_aSAH",as.integer(aSAH$outcome=="Poor"),list(s100b=aSAH$s100b,ndka=aSAH$ndka))
add("reordered_factor_levels",c(1,1,1,1,0,0,0,0),list(A=c(1,2,3,4,2,3,3,5)),
    levels=c("Positive","Negative"),positive="Positive")
add("increasing_extreme_scores",c(rep(0,4),rep(1,4)),
    list(A=1e300*c(1,2,3,4,2,3,3,5),B=1e-300*c(1,2,3,4,2,3,3,5)))

capture <- function(expr) {
  warnings <- character()
  value <- tryCatch(withCallingHandlers(expr,warning=function(w){warnings <<- c(warnings,conditionMessage(w));invokeRestart("muffleWarning")}),
                    error=function(e)list(error=conditionMessage(e)))
  list(value=value,warnings=warnings)
}
finite_num <- function(x) if(length(x)==1L && is.finite(x)) as.numeric(x) else NULL
scalar <- function(x) if (length(x)) unname(as.numeric(x[1])) else NULL
rows <- function(x) lapply(seq_len(nrow(x)),function(i)unname(x[i,]))

compute <- function(f) {
  raw <- f$markers
  keep <- f$codes>=0 & Reduce(`&`,lapply(raw,is.finite))
  source <- which(keep)-1L;codes <- f$codes[keep]
  truth <- codes == match(f$positive,f$levels)-1L
  m <- sum(truth);n <- sum(!truth);names <- names(raw);k <- length(raw)
  scores <- lapply(raw,function(x)x[keep]);case <- control <- vector("list",k)
  names(case) <- names(control) <- names
  model <- vector("list",k);rocs <- vector("list",k)
  for(j in seq_len(k)) {
    s <- scores[[j]];higher <- f$directions[[j]]=="higher"
    kernel <- outer(s[truth],s[!truth],if(higher) `>` else `<`) + .5*outer(s[truth],s[!truth],`==`)
    case[[j]] <- rowMeans(kernel);control[[j]] <- colMeans(kernel);auc <- mean(kernel)
    thresholds <- sort(unique(s),decreasing=higher)
    points <- c(list(list(cutoff=NULL,tp=0L,fp=0L,fn=m,tn=n,tpr=0,fpr=0)),
      lapply(thresholds,function(cut){pred <- if(higher)s>=cut else s<=cut;tp<-sum(pred&truth);fp<-sum(pred&!truth)
        list(cutoff=cut,tp=tp,fp=fp,fn=m-tp,tn=n-fp,tpr=tp/m,fpr=fp/n)}))
    fpr <- vapply(points,`[[`,0.0,"fpr");tpr <- vapply(points,`[[`,0.0,"tpr")
    area <- sum(diff(fpr)*(head(tpr,-1)+tail(tpr,-1))/2)
    roc_result <- capture(pROC::roc(factor(ifelse(truth,"case","control"),levels=c("control","case")),
                                   s,levels=c("control","case"),direction=if(higher)"<" else ">",quiet=TRUE))
    rocs[[j]] <- roc_result$value
    proc_var <- capture(pROC::var(rocs[[j]],method="delong"))
    variance <- if(m>=2 && n>=2) var(case[[j]])/m + var(control[[j]])/n else NULL
    intervals <- lapply(c(.8,.95,.99),function(confidence){
      q <- qnorm((1+confidence)/2);available <- !is.null(variance) && is.finite(variance) && variance>0
      ci <- capture(pROC::ci.auc(rocs[[j]],conf.level=confidence,method="delong"))
      list(confidence=confidence,status=if(available)"ok" else "unavailable",
        se=if(available)sqrt(variance) else NULL,
        raw_lower=if(available)auc-q*sqrt(variance) else NULL,
        raw_upper=if(available)auc+q*sqrt(variance) else NULL,
        lower=if(available)max(0,auc-q*sqrt(variance)) else NULL,
        upper=if(available)min(1,auc+q*sqrt(variance)) else NULL,
        pROC_raw_ci=if(is.numeric(ci$value))unname(ci$value) else ci$value,pROC_warnings=ci$warnings)
    })
    stopifnot(abs(auc-area)<1e-14,abs(auc-as.numeric(pROC::auc(rocs[[j]])))<1e-14)
    if(!is.null(variance))stopifnot(abs(variance-as.numeric(proc_var$value))<1e-12)
    model[[j]] <- list(name=names[j],direction=f$directions[[j]],auc=auc,auc_trapezoid=area,
                      positive_placements=unname(case[[j]]),negative_placements=unname(control[[j]]),
                      variance=variance,points=points,intervals=intervals,pROC_variance=proc_var$value,
                      pROC_variance_warnings=proc_var$warnings,pROC_warnings=roc_result$warnings)
  }
  covariance <- if(m>=2&&n>=2) stats::cov(do.call(cbind,case))/m+stats::cov(do.call(cbind,control))/n else NULL
  if(!is.null(covariance)) for(a in seq_len(k)) for(b in seq_len(k)) {
    cv <- capture(pROC::cov(rocs[[a]],rocs[[b]],method="delong"));stopifnot(abs(covariance[a,b]-cv$value)<1e-12)
  }
  pairs <- list()
  if(k>=2)for(a in seq_len(k-1))for(b in seq.int(a+1,k)) {
    delta <- model[[a]]$auc-model[[b]]$auc
    variance <- if(m>=2&&n>=2)var(case[[a]]-case[[b]])/m+var(control[[a]]-control[[b]])/n else NULL
    intervals <- lapply(c(.8,.95,.99),function(confidence){
      available <- !is.null(variance)&&is.finite(variance)&&variance>0;q <- qnorm((1+confidence)/2)
      result <- capture(pROC::roc.test(rocs[[a]],rocs[[b]],method="delong",paired=TRUE,
                                       alternative="two.sided",conf.level=confidence))
      if(available) {
        stopifnot(abs(scalar(result$value$statistic)-delta/sqrt(variance))<1e-10)
        stopifnot(abs(result$value$p.value-2*pnorm(-abs(delta/sqrt(variance))))<1e-12)
      }
      list(confidence=confidence,status=if(available)"ok" else "unavailable",se=if(available)sqrt(variance) else NULL,
           z=if(available)delta/sqrt(variance) else NULL,p=if(available)2*pnorm(-abs(delta/sqrt(variance))) else NULL,
           lower=if(available)delta-q*sqrt(variance) else NULL,upper=if(available)delta+q*sqrt(variance) else NULL,
           pROC_raw_z=scalar(result$value$statistic),pROC_raw_p=scalar(result$value$p.value),
           pROC_raw_ci=if(is.numeric(result$value$conf.int))unname(result$value$conf.int) else NULL,
           pROC_warnings=result$warnings,pROC_error=result$value$error)
    })
    pairs[[length(pairs)+1L]] <- list(first=names[a],second=names[b],difference=delta,variance=variance,intervals=intervals)
  }
  list(n_source=length(keep),n_complete=sum(keep),n_positive=m,n_negative=n,
       retained_indices=unname(source),excluded_indices=unname(which(!keep)-1L),
       positive=f$positive,negative=setdiff(f$levels,f$positive),models=model,
       covariance=if(is.null(covariance))NULL else rows(covariance),comparisons=pairs)
}

output <- list(scope="Independent literal pairwise-kernel and pROC reference for source-only fixed-direction ROC/DeLong",
  formulas=list(auc="mean(K), K=I(oriented case score > control score)+.5*I(tie)",
    covariance="cov(rowMeans(K))/m + cov(colMeans(K))/n using sample covariance",
    paired_variance="var(case placements A-B)/m + var(control placements A-B)/n",
    intervals="normal qnorm((1+confidence)/2); AUC bounded, raw paired difference unbounded"),
  R_version=as.character(getRversion()),pROC_version=as.character(packageVersion("pROC")),
  jsonlite_version=as.character(packageVersion("jsonlite")),
  pROC_defaults=list(roc_direction=deparse(formals(pROC:::roc.default)$direction),
                    roc_test_method=deparse(formals(pROC:::roc.test.roc)$method),
                    ci_auc_method=deparse(formals(pROC:::ci.auc.roc)$method)),
  hand_AUC=list(numerator=21,denominator=32,value=21/32),
  fixtures=lapply(fixtures,function(f){f$expected<-compute(f);f}))
write_json(output,"tests/fixtures/roc-delong.json",auto_unbox=TRUE,pretty=TRUE,digits=17,na="string",null="null")
cat("Independent fixtures:",length(fixtures),"\n")
