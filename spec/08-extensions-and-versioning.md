# 8. Extensions, regulatory profiles and versioning

A format that must be broken every time a new regulation appears is dead on
arrival. Three separate mechanisms handle three separate kinds of change.

## 8.1 Extensions — must-understand vs. may-ignore

```jsonc
"extensions_used":     ["XOFFI_transition_solver", "VENDOR_telemetry"],
"extensions_required": ["XYZ_regulatory_field_set"]
```

- A reader that does not understand an entry in **`extensions_required`** MUST
  **reject** the file. Half-processing a file with unknown mandatory semantics
  is the failure mode this prevents.
- Entries in **`extensions_used`** MAY be ignored.
- Extensions **MUST NOT** change the meaning of core fields. They may only add.
- Names are vendor-prefixed. A vendor prefix requires no permission; promotion
  to multi-vendor or ratified status requires an independent implementation
  (see `GOVERNANCE.md` §6). A name MUST match
  `^[A-Z][A-Z0-9]+_[A-Za-z0-9_]+$` — prefix, underscore, identifier.

## 8.1.1 Where extension data lives

Declaring which extensions a file uses is only half the mechanism; the data has
to go somewhere. **Every object in a DSX document MAY carry an `extensions`
member**, keyed by the prefixed extension name:

```jsonc
"roles": [
  { "id": "r0001",
    "trajectory": "traj/r0001.json",
    "extensions": {
      "XOFFI_transition_solver": { "solver": "hungarian", "cost": "time" }
    } } ]
```

Everything outside `extensions` is core, and core objects are **closed**: an
unrecognised member is an error, not an extension. This is the deliberate part.
Leaving objects open looks friendlier, but it means a misspelt
`min_seperation_m` silently removes the show's separation floor and the file
still validates — a safety-critical value that vanishes on a typo, with nothing
anywhere reporting it. A format used to justify flying over people cannot
afford that trade, so the cost of a closed core is accepted: vendors get one
clearly marked place to write instead of anywhere they like.

Reference: `conformance/run_schema_checks.py` asserts both halves — that a
misspelt safety field is rejected, and that a correctly prefixed extension is
accepted.

## 8.2 Round-trip preservation

> A reader that re-exports a DSX file **MUST preserve `extensions` entries it
> did not understand, and MUST preserve core members it did not understand
> from a compatible minor version.**

Silently discarding unknown data is a conformance failure. This is the rule
that decides whether a format survives a real production chain, where a file
passes through four tools from three vendors and each one must not destroy the
metadata of the previous one.

The two halves are not the same case, and §8.1.1 is why:

- **`extensions` entries** are opaque to a reader that does not know them. It
  keeps them byte-for-byte and writes them back.
- **Core members** from a *newer minor version* are unknown to an older reader
  but are not extensions. Since a minor version may only add optional fields
  (§8.4), an older reader validating against its own schema will see them as
  unrecognised. It MUST NOT drop them on re-export, and it MUST NOT treat their
  presence as a reason to reject the file when the major version matches.

A reader therefore rejects an unrecognised core member only when the document's
`dsx` version is one it claims to implement fully. This keeps the typo defence
of §8.1.1 for the version a tool actually knows, without making every minor
addition a breaking change downstream.

## 8.3 Regulatory profiles

```jsonc
"regulatory_profiles": ["CN-761", "CN-WUHAN-2026", "EASA-SORA", "FAA-107"]
```

A regulatory profile is an **overlay** in `profiles/`. It may:

- make optional core fields **required**,
- **narrow** permitted value ranges (e.g. a lower wind limit, a larger audience
  distance),
- require the presence of specific evidence in `provenance`.

It **MUST NOT** add, rename or redefine core fields. Consequences:

- A new national rule produces a **new profile**, not a new format version.
- Previously archived files remain valid.
- A validator can report per jurisdiction: *conformant for A; not conformant
  for B, because field X is missing.*

Registered identifiers currently drafted: `CN-761`, `CN-WUHAN-2026`, `KR-2025`,
`CA-SFOC`, `SG-CAAS`, `AU-ONE-TO-MANY`, `UK-CAP722E`, `EASA-SORA`, `FAA-107`.
Each profile in `profiles/` MUST cite the source document it encodes, with a
date. Profiles whose source cannot be cited are not accepted.

## 8.4 Versioning

Semantic versioning, per `GOVERNANCE.md` §5: minor versions add only optional
fields; making a field required is a major version; readers MUST reject major
versions they do not implement.
