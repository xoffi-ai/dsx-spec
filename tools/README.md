# Tools

The specification is normative; tools are not. Reference implementations are
published separately under **Apache-2.0** so they can be embedded in
proprietary firmware and products.

Planned:

| Tool | Purpose |
|---|---|
| `dsx-validate` | schema + semantic validation, regulatory profile checking, human-readable and PDF report |
| `dsx-sample` | the normative sampler (§4.4) — the piece every third-party importer needs |
| `dsx-convert` | conversion to and from existing formats, each with a published **loss matrix** (§9) |

**Clean-room boundary applies** (`NOTICE-PROVENANCE.md` §4): contributors who
have read the source of a GPL-licensed drone show implementation may work on
the specification but not on the corresponding reference implementation.
