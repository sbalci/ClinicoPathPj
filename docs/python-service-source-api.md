# Source/API interpreter comparisons

Verified **2026-11-10** with ClinicoPathPj 0.3.62 source and installed Pj 1.5.0 on
the current macOS arm64 setup. This developer probe compares calculation payloads
through our own subprocess and the real public Pj API. It changes no menu entry,
saved analysis option or fixed bundled-Python teaching route.

| Interpreter mode | Summary fixtures | Age-pyramid configurations | Result |
|---|---:|---:|---|
| jamovi Python 3.11.9 / NumPy 2.4.6 | 4 | 4 | All matched independent R calculations |
| Existing external Python 3.9.12 / NumPy 1.24.3 | 4 | 4 | All matched independent R calculations |

Each of the **16 pairs** verifies identical Python executable paths, Python versions,
NumPy versions and NumPy source locations between the own and Pj processes. Tables,
plot-ready data and notices must agree. Route explanations intentionally differ.
Pj reports processx execution with checkpoints enabled.

Summary fixtures cover ordinary missingness, singleton data, all-missing data and
signed/extreme values. Expected counts, mean, sample SD, median and range come from
base R. Age-pyramid configurations cross counts/percentages with within-gender/total
denominators; independent `cut()`/`table()` counts include explicit levels and exclusions.

See the [dated evidence](validation-exports/python-service-source-api-20261110.json)
and [shared harness](../tools/check-age-pyramid-source-api.R). The new `--summaries`
mode reuses the existing transport. Age-pyramid and `--service-smoke` modes remain
available; the refactored age-pyramid path was rerun with both interpreters.

## Developer reproduction

Run through jamovi's bundled R with the source checkout and installed Pj R library:

```sh
R_HOME=/Applications/jamovi.app/Contents/Frameworks/R.framework/Resources \
DYLD_LIBRARY_PATH=/Applications/jamovi.app/Contents/Frameworks/R.framework/Resources/lib \
/Applications/jamovi.app/Contents/Frameworks/R.framework/Resources/bin/exec/R \
  --vanilla --slave -f tools/check-age-pyramid-source-api.R --args \
  /path/to/ClinicoPathPj /path/to/modules/Pj/R --summaries --all
```

Omit `--summaries` for age-pyramid checks. For the external diagnostic add `--system`,
`--python=/existing/external/python3` and
`--site-packages=/existing/external/lib/pythonX.Y/site-packages`.
`--python` selects the **own** executable; Pj independently discovers System Python.
The probe fails if their executable or dependency locations differ.

The explicit site-packages path supports the probe's `-S` startup and is appended
only in its child scripts. It installs no dependencies and changes no production
setting. The System probe clears inherited jamovi Python home/path variables in
its R child only. Production adapter environment restoration has separate tests.
Unknown flags, a zero-second timeout and conflicting `--summaries --service-smoke`
are rejected before execution. Execution deadlines remain unchanged.

## Limits

These checks qualify source calculations and plot-ready data for the tested
versions. Native GUI System execution, System-computed `.omv` reopening, external
static rendering, clean machines and other platforms remain unqualified. The
previously observed Matplotlib 3.5.2 renderer incompatibility is not resolved by
successful numerical payloads. No packages were installed.

Installed `pyservicedirect`, `pyservicepj` and `pyagepyramidpj` teaching entries remain
fixed to bundled Python. A System-Python UI would be additional work with discovery,
dependency, rendering and persistence checks. The existing `pybridgecompare` System
option retains its documented GUI discovery limitations; see
[System isolation](python-system-bridge.md).
