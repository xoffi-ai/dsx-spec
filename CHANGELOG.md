# Changelog

## Unreleased

### Added
- **Section 10 — waves, sorties and rotation operation.** Three-level model
  (role / airframe / sortie) enabling shows longer than one battery charge.
  Rules R10.1–R10.14: role coverage, module exclusivity, turnaround closure,
  ground-service capacity, battery-pool closure, per-sortie energy closure,
  cross-wave separation, corridor intersection, no-silent-degradation.
- `conformance/check_rotation.py` — semantic validator for the rules JSON
  Schema cannot express. Nine negative tests prove each rule bites.
- `examples/rotation-l2/` — 42-minute show flown by 6 aircraft with 7.5
  minutes of endurance each; demonstrates why two wave groups are
  insufficient at a 420 s turnaround and three are required.
- **Appendix B — observed third-party formats.** SKYB container framing,
  block typing and event records verified against 13 published fixtures with
  recorded SHA-256. Written under the clean-room boundary of
  `NOTICE-PROVENANCE.md` §4.

### Fixed
- Schema `$ref` resolution went to the network and silently never resolved.
  Now resolved from a local registry: the toolchain validates **air-gapped**,
  as the operating rules DSX targets require. Fixing this immediately exposed
  an incomplete `termination` block that had been passing unchecked.


## v0.1-draft — 2026-08-15

Initial public draft. Nothing is stable.

Established in this draft:

- Two-layer model: `.dsx` (interchange) / `.dsb` (compiled), with a
  deterministic compiler between them.
- Conformance profiles L0 / L1 / L2.
- The interoperability guarantee: normative reduction to `t,x,y,z,R,G,B` at any
  rate (§4.4) — *specified, not yet backed by test vectors.*
- Mandatory coordinate frame and time objects, including `alt_ref`,
  `handedness` and `bearing_deg` at every profile (§3).
- Dual trajectory representation (segment + sampled) with declared
  interpolation and time semantics (§4).
- Device profiles `.dsxp` with stable UUID identity, modes, firmware gating,
  and the capability/intent split (§5) — the field no existing format carries.
- Three-level error semantics REJECT / BLOCK-FLIGHT / WARN, with the rule that
  an uploader must be strict where a visualiser may be permissive (§5.6).
- Generic actuator model for payloads, with the authority rule separating show
  actuators from safety actuators (§6).
- Termination as an independent, playback-decoupled channel, with an RTH
  **feasibility map** rather than a fixed interval (§7.3).
- GNSS integrity policy covering time as well as position, estimator trust, and
  interference response (§7.4).
- Extension mechanism with must-understand/may-ignore semantics and mandatory
  round-trip preservation; regulatory requirements as overlay profiles (§8).
- Governance: DCO not CLA, open issues, named attribution, and a written
  stewardship pledge to hand the format to a neutral body once three
  independent implementers exist.

Known incomplete: `.dsb` encoding, sampler test vectors, conformance suite,
all regulatory profiles. See `spec/A-open-questions.md`.
