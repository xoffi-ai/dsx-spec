# DSX — Drone Show eXchange

**An open, vendor-neutral file format for drone light shows — designed to be
flight-capable and machine-validatable, not just viewable.**

> **Status: `v0.1-draft`.** Nothing here is stable. This is published early and
> in public *on purpose*: to be reviewed, contradicted and improved by the people
> who actually fly shows. See [GOVERNANCE.md](GOVERNANCE.md).

---

## Why

Every drone show format in use today is in one of two states:

| | Open & documented | Flight-capable | Validatable by a third party |
|---|---|---|---|
| **VVIZ** | yes | **no** — the published specification states it is not intended to output flight-ready path data [^vviz] | no |
| **.skyc / .skyb** | source-readable (GPL), no public spec | yes | no |
| **.dac, .bin, .path/.path3, .essp, Drotek .json, .packedshow, .ddsf** | no public specification located [^located] | yes | no |
| **CSV** | trivially open | partially | no |
| **DSX** | **yes** | designed for it — **not yet flown** | schema + §10 rules today; sampler vectors outstanding |

There is currently **no open format that is both flight-capable and
independently verifiable**. That is the gap DSX exists to close — and the last
row is deliberately not a row of green ticks. DSX is a v0.1 draft: the
specification and the JSON Schemas exist and are testable today, the `.dsb`
encoding and the sampler test vectors are not written yet, and no aircraft has
flown a DSX file. Claiming otherwise would reproduce the exact behaviour this
project was created to replace. See `conformance/README.md` for what the suite
actually covers and `spec/A-open-questions.md` for what is still open.

Consequences of that gap are documented, not hypothetical: shows are exchanged
as CSV and lose safety metadata; geofence fields exist in formats but are never
populated; altitude reference (AGL vs. AMSL vs. ellipsoid) is left implicit;
axis handedness differs silently between tools. Each of these has a known
failure mode.

## Design in one page

**Two layers, cleanly separated** — the mistake most formats make is mixing them:

| Layer | File | Purpose | Form |
|---|---|---|---|
| **Interchange** | `.dsx` | exchange, archive, review, regulatory submission | ZIP + JSON, diffable, human-readable |
| **Compiled** | `.dsb` | upload to the aircraft | binary TLV, MCU-parseable |
| **Device profile** | `.dsxp` | what a given aircraft or payload can do | JSON, shipped inside the `.dsx` |

The `.dsx` → `.dsb` compiler **is specified to be deterministic**: identical
input must produce byte-identical output, which is what makes a show file
auditable. The `.dsb` encoding is not yet written (A1), so this is a
requirement on implementations, not a property you can test today.

**Interoperability is a guarantee of the format, not a service of a server.**
Every conforming `.dsx` MUST be reducible, via a normative sampling algorithm,
to `t, x, y, z, R, G, B` at any frame rate — bit-identically in every
implementation. Any existing system therefore has an import path on day one,
without understanding polynomials.

**Conformance profiles** rather than a feature checklist:

- **L0 — Sampled**: positions + RGB only. CSV-equivalent. Any controller can do it.
- **L1 — Show**: segment trajectories, light programs, safety envelope, takeoff grid, RTH.
- **L2 — Production**: yaw, payloads (pyro, recovery, dispensers), multi-fleet, audio sync, signature.

**Hardware identity is explicit.** A show references a device profile
(`.dsxp`) by stable UUID and declares the mode it was authored for. Tools can
therefore refuse to upload a show whose declared flight envelope exceeds the
aircraft's published limits — instead of discovering it in the air.

**Safety is a first-class, playback-independent channel**, not a set of numbers
in a sidecar PDF. Termination escalation, geofences, link-loss behaviour,
GNSS-integrity policy and payload interlocks are data.

## Repository layout

```
spec/          the specification (Markdown, normative), chapters 1-10 + appendices A, B
schema/        JSON Schema for .dsx, .dsxp and termination
devices/       device profiles (.dsxp): two templates and one worked example
               (vendor-contributed profiles are invited, none exist yet)
profiles/      regulatory overlays — planned, currently a README stating the
               intended identifiers; no overlay is written
examples/      minimal-l0, rotation-l2, continuous-l2 (show-l1 and pyro-l2 are
               named in examples/README.md but not yet written)
conformance/   what exists: schema checks and the semantic rules of §10.
               The sampler, round-trip and determinism suites do not exist yet,
               so "DSX conformant" is not yet a claim anyone can earn
proposals/     change proposals (see proposals/TEMPLATE.md)
tools/         observe_skyb.py — byte-level inspection used to write Appendix B
```

## Licensing

| Part | License | Rationale |
|---|---|---|
| Specification, schemas, examples | **CC BY 4.0 OR Apache-2.0** | CC BY for documentation use; Apache-2.0 supplies the patent grant (§3) that vendor legal departments require |
| Code, schemas as used in software, reference tools | **Apache-2.0** | embeddable in proprietary firmware; includes a patent grant |
| The name "DSX" and the conformance badge | trademark, held by the steward | anyone may implement; only those who pass the conformance suite may *call* it DSX |

Explicitly **not GPL**: a reference implementation under GPLv3 cannot be
embedded in the proprietary firmware that has to read the format, and a
standard whose reference code its own audience cannot link is a standard with
an adoption ceiling. This is a statement about licence mechanics, not about any
particular vendor's decisions. Explicitly **not MIT**: no patent grant.

## Contributing — and a promise

Issue creation is **open**. Proposals are discussed, not closed as "not
planned". Contributors are **credited by name** in the specification.

This is stated explicitly because it is a commitment we can be held to, not a
comparison with anyone else. Where this document describes other formats it
does so from their published specifications and from bytes we inspected
ourselves (Appendix B); we make no claims about how other projects run their
issue trackers.

If you produce shows and the software is in your way: open an issue. That is
the whole point of this repository.

See [CONTRIBUTING.md](CONTRIBUTING.md) and [NOTICE-PROVENANCE.md](NOTICE-PROVENANCE.md).

[^vviz]: Cite the document, version and retrieval date here before publication.
    Until that footnote is filled in, treat the cell as unverified.

[^located]: "Located" is the accurate claim: absence of a public specification
    is not something this project can prove, only fail to find. Searched
    2026-08; see `spec/B-observed-formats.md` for the standard of evidence
    applied throughout.
