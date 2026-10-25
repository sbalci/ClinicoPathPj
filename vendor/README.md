# Offline Python plotting dependencies

`python-lock.json` pins official PyPI wheels, SHA-256 digests, dependency metadata,
license descriptions and license-file locations. The wheels in `wheels/macos-arm64-cp311`
are the build inputs, not runtime installers. No network or pip command runs in jamovi.

`tools/build.R` invokes `tools/vendor-python.py` to verify every wheel and extract it into
`inst/python/_vendor/`. That generated directory is ignored by git and included in the
built R package. NumPy/SciPy remain supplied by jamovi; the lock records the verified versions.

All wheel license files, including bundled font/library notices, are retained in the module.
Matplotlib uses its PSF-style license; supporting libraries carry BSD, MIT, Apache, or Pillow
license notices as recorded in their metadata. Consult those complete texts for redistribution.

The renderer uses Agg without a GUI backend, TeX subprocesses, or a web server. Its temporary
font cache contains only relative paths to the bundled Matplotlib fonts and is removed when
the isolated rendering process exits. The checked-in cache is tied to Matplotlib 3.10.8.

These binary wheels support CPython 3.11/macOS arm64 only. Other platforms require separately
locked wheels and native acceptance before support can be claimed.
