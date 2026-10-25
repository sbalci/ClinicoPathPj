# TODO — ClinicoPathPj experiment (started 2026-10-18)

## Increment 2 (2026-10-18): faster and cancellable runs, plots, narrative text, first ports

Acceptance criteria:
- An option change while Python runs cancels that run. Proven by a test with an injected engine
  checkpoint that returns "restart": the worker is killed, the restart error propagates, and the next
  run succeeds.
- ~~With a warm worker, repeat runs skip the roughly 1 s numpy/scipy start-up~~. **Changed (Codex design
  review):** ship a one-shot processx run with checkpoint polling instead, so every run gets a fresh
  process. A warm worker would bring cross-analysis state leakage, stale or misattributed responses,
  partial-write framing, hung or idle-racing workers and four resident interpreters, to save about
  0.8 s. Deferred until measured latency justifies it; Codex's 8-risk test list is kept in CHANGELOG.
  Run time is measured instead.
- Python-computed plots are drawn by R/ggplot2, follow jamovi's theme and palette, and export like
  any jamovi plot.
- Every port matches its R oracle (or closed form) in tests; Monte Carlo results show their seed.

- [x] A1 Generator: List/Integer/String options; Level `role: "event"` (allowNone and a pending notice);
      Image results (plot kinds `interval`, `line`, `box`) and Text results; `.plot` renderFun and a
      checkpoint closure in the generated `.b.R`; tests.
- [x] A2 Runtime: `out.plot`, `out.markdown` and `md_escape`; bounded console capture. (`--serve` was
      dropped together with the warm worker.)
- [x] A3 Bridge: processx with checkpoint polling and cancellation, a fresh process per run; plot state
      with the `.cpjPlot` ggplot renderer; Text; the event-level pending notice; tests (injected restart,
      timeout inside C code, no surviving processes).
- [x] A4 pywelch: reference level `allowNone` (unset = second level, so the sign matches jamovi's
      T-Test); interval plot of group means with CIs; narrative Text; tests.
- [x] Verify A: generator check, build, `tools/check.sh`. Timing: pywelch takes about 1 s on an idle
      machine (scipy import); measured 1.9–3.7 s at load average 27.
- [x] B Ports, in parallel, each followed by an independent verifier who fixed findings in the port's
      own files: pycotest (18 Python tests), pyexacttests (22), pykappaci/fixedn/power plus
      `cpj_kappasize.py` (37). All mutants killed.
- [x] C Integrate: shared-file snapshot unchanged; build; `tools/check.sh` gives 118 Python tests OK
      and 257 R expectations PASS.
- [x] D Adversarial review of the bridge, plots, generator and cross-port consistency. Each confirmed
      finding was fixed with a regression test, and six mutants (one per bridge or plot fix) were all
      killed. Fixes:
      - stale interpretation: Text cleared like Preformatted;
      - `kill()` before `kill_tree()`;
      - polling only open pipes;
      - plots: rows with the same label keep their own positions, one-point line groups are drawn,
        the box plot gets its reference line, per-kind row caps, no state without rows;
      - `md_escape` collapses newlines; the shared `fmt_num()`;
      - pyexacttests: first-level reference and labels naming both groups;
      - pycotest: text display columns over hidden exact ones, specificity up to 0.999.
- [x] Verify D: build; `tools/check.sh` gives 124 Python tests OK and 288 R expectations PASS
      (0 fail, 0 warn, 0 skip).
- [ ] Verify (GUI, user): the increment-2 checklist given to the user on 2026-10-19.
- [x] Bug (user, GUI, 2026-10-19): "Python console output does not show anything". The console now
      opens with a run report and says why when there is none. Reproduced first; regression tests;
      adversarial review (7 agents), whose confirmed findings are fixed; 25 mutants killed. See
      CHANGELOG "Console report".
- [ ] Follow-up (found by the console review, R API only): a factor with an explicit NA level
      (`addNA()`, `factor(x, exclude = NULL)`) reaches Python as a level `null`. pywelch then fails in
      its plot ("missing ['label']"), and a two-level outcome would count NA as a category. jamovi
      never sends NA levels. Decide whether `.cpjColumn()` maps an NA level to missing, as jamovi
      does. Repro: `d$g <- addNA(d$g)` with some rows in the NA level, then
      `pywelch(data = d, dep = "y", group = "g", refLevel = NULL)`.
- [ ] Decide (user): minApp. It is 28.3.0, but processx and ps in jamovi's own R library were
      verified on 28.13 only.
- [ ] Next (not started): the generator owns the `.u.yaml` panel (`enable:` bindings, CollapseBox,
      default levels); the warm worker stays deferred.

Goal: install Pj in the local jamovi for testing (baseline, then macOS-patched), and build a
module whose jamovi analyses are generated from Python specs and run in jamovi's bundled Python.

Acceptance criteria:
- Pj builds and installs from scratch copies, and `../Pj` is unchanged.
- The baseline macOS failures are reproduced, and the patch fixes both interpreter modes.
- `Rscript --vanilla tools/build.R` regenerates, builds and installs ClinicoPathPj, failing loudly.
- `tools/check.sh` passes: Python unit tests and R oracle tests against the installed module.
- In the jamovi GUI, each analysis runs, and Welch matches jamovi's built-in t-test.

## Checklist
- [x] Re-verify the environment on jamovi 28.13 (R 4.6.0-arm64, bundled Python 3.11.9, numpy 2.1.1, scipy 1.17.1)
- [x] Install jmvtools 28.4; `jmvtools::check()` finds jamovi 28.13.0
- [x] Pj baseline: build and install the unmodified scratch copy; engine-faithful probe (`docs/pj-probe-baseline.txt`)
- [x] Pj patch: 3 edits in 2 files; build, install and probe (`docs/pj-probe-macos.txt`); `docs/pj-macos-fix.patch`
- [x] `../Pj` HEAD and status identical before and after
- [x] Skeleton: DESCRIPTION, NAMESPACE, COPYING, 0000.yaml (`analyses: []`), .gitignore, .Rbuildignore
- [x] Generator `tools/generate.py` (ast-only SPEC read, validation, JSON-as-YAML, `--check`)
- [x] Runtime `inst/python/cpj_runtime.py` and bridge `R/utils-python.R`
- [x] Analyses: pyruntime, pydescriptives, pywelch
- [x] `tools/build.R`, `tools/check.sh`
- [x] Verify: `tools/check.sh` gives 27 Python tests OK and 56 R expectations PASS
- [x] Verify (advisory): umbrella `tools/release_gate.py --root ../ClinicoPathPj`. Only the accepted
      items remain: version 0.x, no `00refs.yaml`, and `compilerMode` aggressive (intended).
- [x] Adversarial code review (3 lenses plus refutation). Fixed all 3 confirmed majors and the cheap
      minors; regression tests added. Mutation check: each bridge fix is caught by its own test.
- [x] Verify again after the fixes: `tools/check.sh` gives 33 Python tests OK and 82 R expectations PASS
- [ ] Verify (GUI, user): Pj Editor in both interpreter modes (patched build installed)
- [ ] Verify (GUI, user): each ClinicoPathPj analysis; Welch vs jamovi's T-Test (Welch), choosing the
      *second* level as reference so the signs match; save, reopen, rerun
- [ ] Follow-up (not started): umbrella `vignettes/jamovi_notices_guide.md` says Notice content is
      plain text, but the client renders it as HTML. Report to the user; don't edit the umbrella here.

## Working notes
- jamovi's engine environment: HOME plus `env.conf`, `PATH=''`, cwd `/Applications/jamovi.app/Contents/MacOS`,
  no TMPDIR. `Sys.which("python")` then returns `./python`, which is jamovi's own Python.
- The bundled Python needs `PYTHONHOME`, and dies under `-I`/`-E`. Its stdlib is a trimmed `.pyc`-only
  `python311.zip` (no `unittest/__main__`).
- `jmvtools::install()` returns the build status (Rscript exits 0 regardless). A running jamovi installs
  the `.jmo` asynchronously, about 10 s later, so poll the installed `jamovi.yaml`.
- A hand-written `0000.yaml` must contain `analyses: []`, or the compiler crashes (exit 1, silent).
- The R wrapper with `data=` and no selected variable fails inside `jmvcore::select()`
  (`invalid 'row.names' length`). The engine never calls `select()`, so the GUI is unaffected.

## Results
- Pj, engine-faithful probe:
  - baseline "jamovi Python": `sh: - : invalid option`, "exit status 2";
  - baseline "System Python": jamovi's own Python 3.11.9;
  - patched: `Contents/MacOS/python` 3.11.9 and Homebrew Python 3.15.0.
- ClinicoPathPj: pywelch matches `t.test` to 1e-10 for both reference choices and a 90% CI;
  pydescriptives matches base R, including `quantile(type = 7)`.
- How verified: `tools/check.sh` (exit 0; after the review fixes, 33 Python tests and 82 R expectations),
  the release gate (advisory), and both probes in an `env -i` engine-like environment.
