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
  (see `GOVERNANCE.md` §6).

## 8.2 Round-trip preservation

> A reader that re-exports a DSX file **MUST preserve fields and extensions it
> did not understand.**

Silently discarding unknown data is a conformance failure. This is the rule
that decides whether a format survives a real production chain, where a file
passes through four tools from three vendors and each one must not destroy the
metadata of the previous one.

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
