# DSX — Drone Show eXchange

**An open, vendor-neutral file format for drone light shows — designed to be
flight-capable and machine-validatable, not just viewable.**

> **Status: `v0.1-draft`.** Nothing here is stable. This is published early and
> in public *on purpose*: to be reviewed, contradicted and improved by the people
> who actually fly shows. See [GOVERNANCE.md](GOVERNANCE.md).
>
> **You can write an L0 reader from this draft now — that claim is backed by a
> test, not just prose.** An external review on 2026-08-15 found that §4.2/§4.3
> did not yet pin down the two central data structures; both are now fully
> specified, and `tools/dsx_sample.py` is a clean-room implementation from the
> text alone that passes five hand-computed test vectors
> (`conformance/sampling/`, run in CI). What remains open: vector coverage is
> not exhaustive ([A36](spec/A-open-questions.md)), the `.dsb` binary encoding
> is still an outline (A2), and open-ended shows (`duration_ms: null`) have no
> defined sampling behaviour yet (A25). See
> [`spec/A-open-questions.md`](spec/A-open-questions.md) for the current,
> honest list.

---

## Why

Every drone show format in use today is in one of two states:

| | Open & documented | Flight-capable | Validatable by a third party |
|---|---|---|---|
| **VVIZ** | yes | **no** — the published specification states it is not intended to output flight-ready path data [^vviz] | no |
| **.skyc / .skyb** | source-readable (GPL), no public spec | yes | no |
| **.dac, .bin, .path/.path3, .essp, vendor .json variants, .packedshow, .ddsf** | no public specification located [^located] | yes | no |
| **CSV** | trivially open | partially | no |
| **DSX** | **yes** | designed for it — **not yet flown** | container, schema, §10 rules and sampler vectors, all tested today |

There is currently **no open format that is both flight-capable and
independently verifiable**. That is the gap DSX exists to close — and the last
row is deliberately not a row of green ticks. DSX is a v0.1 draft: the
specification, JSON Schemas and normative sampler are tested today (five
hand-computed vectors, not exhaustive — A36), the `.dsb` encoding is still an
outline, and no aircraft has flown a DSX file. Claiming otherwise would
reproduce the exact behaviour this project was created to replace. See
`conformance/README.md` for what the suite actually covers and
`spec/A-open-questions.md` for what is still open.

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
auditable. The `.dsb` encoding is not yet written (A2), so *that* half is a
requirement on implementations, not a property you can test today.

**Interoperability is a guarantee of the format, not a service of a server.**
Every conforming `.dsx` MUST be reducible, via a normative sampling algorithm,
to `t, x, y, z, R, G, B` at any frame rate — bit-identically in every
implementation. Any existing system therefore has an import path on day one,
without understanding polynomials. This is now backed by a reference
implementation (`tools/dsx_sample.py`) and five hand-computed test vectors,
not only by prose — see `conformance/sampling/`.

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
examples/      minimal-l0, show-l1, rotation-l2, continuous-l2 (pyro-l2 is
               named in examples/README.md but not yet written)
conformance/   what exists: container safety (§2.1.1/§2.1.2), schema checks,
               the semantic rules of §10, archive integrity and the normative
               sampler (5 vectors). Round-trip and determinism suites do not
               exist yet, so "DSX conformant" is not yet a claim anyone can
               earn end to end
translations/  zh-Hans, ja, ko, de, es. English is the sole authoritative
               language; translations are informative and carry the hash of
               the English source they were made from, so drift is detected
               rather than discovered. See TRANSLATIONS.md
whitepaper/    01-termination-is-data.md — why the safety envelope belongs in
               the file, written for associations and authorities rather than
               implementers; spec/07 governs where the two differ
proposals/     change proposals (see proposals/TEMPLATE.md)
tools/         dsx_sample.py — reference sampler for §4.4, the normative
               reduction to t,x,y,z,R,G,B; dsx_seal.py — content hash and
               signature; observe_skyb.py — byte-level inspection used to
               write Appendix B
```

## Licensing

| Part | License | Rationale |
|---|---|---|
| Specification, schemas, examples, device profiles | **Community Specification License 1.0** (`Community-Spec-1.0`) | its patent grant covers *implementing* the specification (§9.8), which is the whole point and which a software licence does not reliably give |
| Code, reference tools, conformance suite | **Apache-2.0** | embeddable in proprietary firmware; patent grant whose scope genuinely fits code |
| The name "DSX" and the `.dsx` extension | **no trademark held, and none needed — see [`TRADEMARK.md`](TRADEMARK.md)** | a format name is a technical designation, like `.zip` or `.json`; anyone may implement, and conformance is defined by the public suite rather than by a mark |

Two related files are operative, not commentary: [`SCOPE.md`](SCOPE.md) bounds
the patent commitment, [`NOTICES.md`](NOTICES.md) is where implementers accept
the licence and contributors file exclusions.

Explicitly **not GPL**: a reference implementation under GPLv3 cannot be
embedded in the proprietary firmware that has to read the format, and a
standard whose reference code its own audience cannot link is a standard with
an adoption ceiling. This is a statement about licence mechanics, not about any
particular vendor's decisions. Explicitly **not MIT**: no patent grant.
Explicitly **not Apache-2.0 for the specification text**: its §3 licenses
patents to "otherwise transfer **the Work**" — the document — not to implement
what the document describes. [`LICENSE-SPEC.md`](LICENSE-SPEC.md) records that
this project got that wrong twice before getting it right.

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
