# 1. Overview and conformance model

## 1.1 Scope

DSX describes **what a drone light show is** — the aircraft, their trajectories,
their light output, their payloads, the safety envelope that constrains them,
and the provenance of the file itself.

DSX does **not** specify: how a show is authored, how transitions are solved,
what radio link is used, how a ground control station behaves, or how a
particular autopilot implements a command. Those are implementation and
operational matters.

## 1.2 The two-layer model

The defining mistake of existing formats is conflating the **authoring** artefact
with the **onboard** artefact. A compiled-only format cannot be reviewed,
diffed or submitted to an authority; a sampled-only format loses intent — after
sampling, a straight line and an arc are indistinguishable.

| Layer | Extension | Encoding | Purpose |
|---|---|---|---|
| Interchange | `.dsx` | ZIP + JSON (+ binary blobs) | exchange, review, archival, regulatory submission |
| Compiled | `.dsb` | binary TLV | upload to the aircraft |
| Device profile | `.dsxp` | JSON | capability declaration for an aircraft or payload |

The `.dsx` → `.dsb` compilation **MUST be deterministic**: the same input, with
the same declared compiler version and options, MUST produce a byte-identical
output. A show file that is submitted to an authority must be reproducible by
that authority.

## 1.3 Conformance profiles

| Profile | Contains | Intended for |
|---|---|---|
| **L0 — Sampled** | sampled position tracks + RGB, time base, coordinate frame | simple controllers, CSV-equivalent exchange |
| **L1 — Show** | L0 + segment trajectories, light programs, flight limits, geofence, takeoff grid, RTH, device profile binding | the normal case |
| **L2 — Production** | L1 + yaw, payloads and actuators, multi-fleet, audio sync, termination policy, GNSS integrity policy, provenance signature | pyrotechnics, mixed fleets, regulated operation |

A reader declares the highest profile it implements. A reader **MUST** be able
to load any file of its declared profile or lower, and **MUST** apply the error
semantics of §5.6 to anything above it — that is, it must fail safely rather
than silently ignore data it does not understand.

## 1.4 The interoperability guarantee

> Every conforming `.dsx` file with a non-null `show.duration_ms` **MUST** be
> reducible, by the normative sampling algorithm of §4.4, to `t, x, y, z, R, G, B`
> at any requested frame rate, producing bit-identical results in every
> conforming implementation.

**Known limits of this guarantee in `v0.1`, stated here rather than only in an
appendix:** reduction of an open-ended show (`duration_ms: null`, §10.8) is
**undefined** — §4.4 derives the sample count from the duration (A25). Five
hand-computed test vectors now exist and pass (`conformance/sampling/`,
`tools/dsx_sample.py`), which makes "bit-identical" a demonstrated property for
the cases they cover — but coverage is not exhaustive: `poly`/`linear`
segments, `hold` interpolation, before/after-track clamping and the RGBW
channel-drop path are not yet vectorised (A36). This section is a demonstrated
property with a known-partial proof, not the pure intention it was until
2026-08-15.

This is the property that makes DSX adoptable. A manufacturer whose hardware
consumes fixed-rate frame arrays does not need to implement polynomial
evaluation, spline mathematics or light bytecode in order to support DSX; it
needs to call the sampler. Interoperability is therefore a **property of the
format**, not a service provided by a server.

## 1.5 Design rules

These rules are binding on the specification itself, and on all future
proposals:

1. **Explicit beats implicit.** Coordinate frame, altitude reference, axis
   handedness, colour space and interpolation semantics are declared fields,
   never conventions. Every one of these has caused a documented failure when
   left implicit.
2. **`null` means unknown, and unknown is a legitimate state.** A specified
   default that happens to be wrong is more dangerous than an absent value.
3. **Capability is declared by the device, intent is declared by the show.**
   The two live in different files (§5) so that an author cannot widen a
   hardware limit by editing the show.
4. **Safety data is independent of playback.** Anything that must work when the
   show player is gone MUST be evaluable onboard (§7).
5. **Unknown data survives a round trip.** A reader that re-exports a file MUST
   preserve fields it did not understand (§8).
