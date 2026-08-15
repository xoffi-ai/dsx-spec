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
| **VVIZ** | yes | **no** — spec says "not intended to output flight-ready path data" | no |
| **.skyc / .skyb** | source-readable (GPL), no public spec | yes | no |
| **.dac, .bin, .path/.path3, .essp, Drotek .json, .packedshow, .ddsf** | **no public specification** | yes | no |
| **CSV** | trivially open | partially | no |
| **DSX** | **yes** | **yes** | **yes** |

There is currently **no open format that is both flight-capable and
independently verifiable**. That is the gap DSX exists to close.

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

The `.dsx` → `.dsb` compiler is **deterministic**: identical input produces
byte-identical output. That is what makes a show file auditable.

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
spec/          the specification (Markdown, normative)
schema/        JSON Schema for .dsx and .dsxp
devices/       device profiles (.dsxp) contributed by vendors and operators
profiles/      regulatory overlays (CN-761, CN-WUHAN-2026, EASA-SORA, FAA-107, ...)
examples/      minimal L0, full L1, L2 with payloads
conformance/   test suite — passing it is what "DSX conformant" means
proposals/     change proposals (see proposals/TEMPLATE.md)
tools/         pointers to reference implementations
```

## Licensing

| Part | License | Rationale |
|---|---|---|
| Specification, schemas, examples | **CC BY 4.0** + **OWFa 1.0** patent grant | vendor legal departments need the patent grant before they will implement |
| Code, schemas as used in software, reference tools | **Apache-2.0** | embeddable in proprietary firmware; includes a patent grant |
| The name "DSX" and the conformance badge | trademark, held by the steward | anyone may implement; only those who pass the conformance suite may *call* it DSX |

Explicitly **not GPL**. `libskybrush` is GPLv3, which is precisely why no major
manufacturer embeds it — a technically good format that cannot become a
standard because its license excludes its own audience. Explicitly **not MIT**:
no patent grant.

## Contributing — and a promise

Issue creation is **open**. Proposals are discussed, not closed as "not
planned". Contributors are **credited by name** in the specification.

This is stated explicitly because the current state of the art is the opposite:
in the dominant open-source toolchain, issue creation is restricted on the main
repositories, and a detailed multi-vendor feature proposal from a working show
producer has sat unmerged for over a year.

If you produce shows and the software is in your way: open an issue. That is
the whole point of this repository.

See [CONTRIBUTING.md](CONTRIBUTING.md) and [NOTICE-PROVENANCE.md](NOTICE-PROVENANCE.md).
