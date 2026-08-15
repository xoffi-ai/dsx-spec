# 9. Conformance

*Outline. The suite itself lives in `conformance/` and is the normative
artefact; this chapter describes what it must contain.*

An implementation declares:

- the **profile** it implements (L0 / L1 / L2), and
- its **role**: `reader`, `writer`, `validator`, `uploader`, `visualiser`.

Roles matter because the required strictness differs. A visualiser MAY be
permissive about a BLOCK-FLIGHT condition (§5.6); an **uploader MUST NOT be**.

## Required test groups

| Group | Verifies |
|---|---|
| `sampling/` | bit-exact agreement with the normative sampler (§4.4), across rates, segment types and boundaries |
| `roundtrip/` | unknown fields and extensions survive read → write (§8.2) |
| `identity/` | device-profile binding, mode existence, envelope comparison, firmware gating (§5) |
| `errors/` | each REJECT / BLOCK-FLIGHT / WARN condition produces exactly the required level |
| `safety/` | termination object completeness, RTH feasibility windows, fall containment, payload authority rule (§6.2, §7) |
| `coordinates/` | altitude reference, handedness, bearing, and correct refusal when absent (§3) |
| `determinism/` | `.dsx` → `.dsb` is byte-identical across runs and platforms (§1.2) |

## Conversion loss reporting

Any converter to or from a non-DSX format **MUST** publish a **loss matrix**:
for each DSX construct, whether it is preserved, approximated or dropped by
that conversion.

This is a deliberate borrowing from a mature interchange format in another
industry, and it is the central credibility instrument of this project. A
format that competes with "risky conversions" must be honest about its own.

## Badge

Passing implementations may describe themselves as DSX conformant for the
declared profile and role, and use the badge. Results are published.
