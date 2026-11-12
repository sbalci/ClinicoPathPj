# Pinned test-only interval references

`provenance.json` records exact commits and SHA-256 hashes. The baseline helper
comes from `meddecide`'s recorded migration commit, not its mutable working tree.
It fixes confidence at 95%. The two independent R functions and DESCRIPTION are
unmodified files from `ocbe-uio/contingencytables` at the pinned commit, version
3.1.1.9010, under GPL-3. Authors and license metadata are retained in DESCRIPTION.
These are development references; no R package or new Python dependency is
installed or bundled for module users.
The GPL-3 license text is included as `COPYING.GPL-3`; these independently
licensed test references do not change the license of the original project files.

The reference harness supplies `validateArguments` as a no-op for its own
prevalidated nonempty tables and `contingencytables_result` as a list-return
adapter. The actual statistical functions are sourced unchanged. Empty tables
are governed by our explicit undefined-result contract, not by these adapters.
