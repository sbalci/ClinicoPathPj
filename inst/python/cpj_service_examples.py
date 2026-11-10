"""One portable calculation shared by the direct and Pj teaching examples."""
import math
import statistics


def summarize_values(values):
    if len(values) > 100000:
        raise ValueError("This teaching example supports at most 100,000 rows.")
    kept = []
    for value in values:
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("Measurement must contain numeric values or missing cells.")
        if not math.isfinite(value):
            raise ValueError("Measurement must contain finite values.")
        kept.append(value)
    return dict(input=len(values), n=len(kept), missing=len(values) - len(kept),
                mean=statistics.mean(kept) if kept else None,
                sd=statistics.stdev(kept) if len(kept) > 1 else None,
                median=statistics.median(kept) if kept else None,
                minimum=min(kept) if kept else None,
                maximum=max(kept) if kept else None)


def run_summary_example(data, options, out, backend):
    from cpj_runtime import InputError
    try:
        # Runtime missing numeric cells are NumPy NaN; normalize at the boundary.
        values = data[options['measurement']].tolist()
        values = [None if isinstance(v, float) and math.isnan(v) else v for v in values]
        result = summarize_values(values)
    except (ValueError, OverflowError) as error:
        raise InputError(str(error)) from None
    out.row('summary', **result)
    route = ('ClinicoPathPj launches its own Python subprocess.' if backend == 'processx'
             else 'ClinicoPathPj calls the installed Pj public service using jamovi Python; no editor opens.')
    out.markdown('route', route + ' Both examples execute the same Python summary function. '
                 'Missing cells are excluded; SD uses N minus 1. These are descriptive summaries, '
                 'with no independence assumption or inferential test. Elapsed time includes the '
                 'complete backend route and does not isolate process-launch performance.')
