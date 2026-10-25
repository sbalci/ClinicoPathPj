# Runs against the installed module (tools/check.sh), with jamovi's PYTHONHOME.

test_that("pyruntime reports jamovi's bundled Python and its libraries", {
    result <- pyruntime(data = data.frame())
    table <- result$runtime$asDF
    values <- stats::setNames(table$value, table$item)
    expect_true(endsWith(values[["Interpreter"]], "/Contents/MacOS/python"))
    expect_match(values[["Python"]], "^3\\.")
    expect_false(any(values[c("numpy", "scipy")] == "not available"))
})
