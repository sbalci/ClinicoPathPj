# Frozen migration references

`released-2026-10-25.json` stores the R option, result and UI definitions for the 61-target
union. The matching tar archive stores their exact analysis YAML and backend bytes;
SHA-256 digests are recorded in `inst/python/registry.json` and checked by tests.

These references came from the sibling working trees identified by their manifests.
`timeinterval` came from the umbrella production route because the survival sibling
manifest did not yet contain it. `agepyramid` and `survivalcont` were retained from sibling
manifests despite their current test routing in the umbrella.

The recorded Git commit gives context; exact archived bytes and hashes identify the
baseline even when a working tree differs from its commit. These are local migration
references, not a claim that the frozen working-tree bytes match a published library JMO.

`clinicopathpj-pre-migration-source.tar.gz` preserves the tracked ClinicoPathPj source
before this implementation. `tests/fixtures/legacy-python-0.2.0.omv` preserves a GUI-saved
synthetic compatibility document from the previously installed module.

Normal builds never resnapshot mutable sibling sources. Replacing a baseline requires
explicit review of methods, defaults, provenance and validation fixtures.
