test_that('CCC native static renderer draws from serialized state without the dataset', {
    d <- data.frame(a=0:9, b=1:10)
    result <- pyagreement(d,vars=c('a','b'),method='ccc',cccPlot=TRUE)
    path <- tempfile(fileext='.rds')
    on.exit(unlink(path),add=TRUE)
    saveRDS(result$cccFigure$state,path)
    state <- readRDS(path)
    rm(d,result)
    raster <- ClinicoPathPj:::.cpjRenderPlot(state,800L,600L,
                    theme=list(palette='jmv'),ggtheme=ggplot2::theme_grey())
    expect_equal(dim(raster)[1:2],c(600L,800L))
    expect_true(all(is.finite(raster)))
    expect_gt(stats::sd(as.vector(raster)),.01)
})
