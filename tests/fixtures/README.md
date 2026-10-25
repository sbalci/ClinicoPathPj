# Compatibility fixture

`legacy-python-0.2.0.omv` was saved through the jamovi GUI with the installed 0.2.0
module before installing the migration build. It contains synthetic observations,
the six core analyses, co-testing and all three legacy kappa identifiers.

Do not overwrite it with a document saved by the new module. Use a separate GUI
validation document for recalculation and save/reopen checks. This fixture verifies
existing `py…` identifiers; no unprefixed ClinicoPathPj identifiers were released.
