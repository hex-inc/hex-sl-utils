# Schema generation

This directory contains scripts for generating JSON schemas and TypeScript
declarations for Hex Semantic Layer resources. The generated artifacts are
committed and distributed as package data by `hex-sl-utils`.

From the repository root, generate the artifacts with:

```text
just build-schema
```

This writes the JSON Schema and TypeScript declarations beneath
`packages/hex-sl-utils/src/hex_sl_utils/schema_files`.

Regenerate the artifacts and check that the checked-in copies are current
with:

```text
just verify-schema
```
