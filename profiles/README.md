# Regulatory profiles

A regulatory profile is an **overlay**: it may make existing core fields
required and narrow permitted value ranges. It **MUST NOT** add, rename or
redefine core fields (spec §8.3).

That constraint is the whole point. A new national rule produces a new file in
this directory — never a new format version, and never an invalidation of
archived shows.

## Requirements for a profile contribution

- an identifier: `CC-SCHEME` (e.g. `CN-WUHAN-2026`, `EASA-SORA`, `FAA-107`)
- a **citation of the source document**, with date and, where available, a
  link or document number
- a machine-readable constraint set
- a note on what is *not* encoded, and why

**Profiles whose source cannot be cited are not accepted.** An unsourced
regulatory constraint is a liability, not a feature.

## Drafted identifiers

`CN-761`, `CN-WUHAN-2026`, `KR-2025`, `CA-SFOC`, `SG-CAAS`, `AU-ONE-TO-MANY`,
`UK-CAP722E`, `EASA-SORA`, `FAA-107`

None of these is complete. Several depend on documents not yet obtained — see
`spec/A-open-questions.md`.
