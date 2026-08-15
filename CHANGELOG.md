# Changelog

## Unreleased

### Changed (licensing and trademark round)

- **Trademark risk corrected downward (A15 resolved).** The previous round
  treated the crowded "DSX" register as an obstacle to publishing. It is not.
  Infringement requires use of a sign *in the course of trade as an indicator
  of commercial origin*; naming a format, defining an extension and publishing
  a specification is technical use, on the same footing as `.zip`, `.json` and
  `.csv`. The register findings are retained as background — they establish
  only that the project could never *own* the letters DSX, which it does not
  need to. No registration will be sought for "DSX"; the sole future
  registration is the separately coined certification mark, deferred until a
  conformance programme exists. `TRADEMARK.md` §0 states the distinction that
  the earlier analysis omitted.
- **Specification licence is now the Community Specification License 1.0**
  (SPDX `Community-Spec-1.0`), reproduced verbatim in
  `licenses/Community-Spec-1.0.md`. This is the *third* attempt and the first
  correct one. OWFa 1.0 had the right patent scope but is an executory
  agreement that binds nobody when merely listed in a repository. The
  replacement — CC BY 4.0 **or** Apache-2.0 — was worse in a subtler way:
  Apache-2.0 §3 licenses patents to "otherwise transfer **the Work**", and
  where the Work is a document, that arguably covers redistributing the
  document rather than implementing it. CSL §9.8 licenses "making, using,
  selling, offering for sale, importing or distributing any **implementation**
  of the Specification" and is accepted by shipping the licence or by a pull
  request to `NOTICES.md` — right scope, workable delivery. Code remains
  Apache-2.0 (CSL §4). CC BY is no longer offered for the specification: it
  grants no patent rights, so offering it let an implementer take the
  copyright and leave the patent peace behind.
- **`SCOPE.md` added** — operative under CSL §9.13. It bounds every
  contributor's and licensee's patent commitment: the data format, its
  semantics and its conformance criteria are in; flight control, deconfliction
  algorithms, radio protocols, authoring tools and hardware are out. Without
  this file each contributor's commitment would shrink to their own
  contributions.
- **`NOTICES.md` added** — licence acceptance (CSL §2.1.3.3), patent
  exclusions (§3) and withdrawals (§2.3).
- **`TRADEMARK.md` added, and the trademark claim withdrawn.** A knock-out
  search found EUTM 017940461 — a live *word mark* for "DSX" covering computer
  software, computer programs and electronic publications (classes 9, 35, 36,
  42) — plus incontestable US Reg. 2679754 in class 9, generic use of DSX-1/
  DSX-3 in telecoms, and four unrelated formats already using the `.dsx`
  extension. **China was not verifiable; deferred, since it blocks nothing.** Documents no
  longer assert rights in "the name DSX, the DSX logo, or the DSX conformance
  badge"; none of those rights exist. The proposed split follows the IEEE
  802.11 / Wi-Fi precedent: leave the format name unprotected, coin and
  register a separate **certification mark** for the badge.
- **"Clean room" renamed to what it actually is.** The provenance notice is
  now titled *Separation of Roles*: GPL source was read to establish
  observable facts, so the process is a one-way wall (spec yes, implementation
  no), not a clean room. The notice says so itself.
- **§10.9 conformance table completed.** The cyclic row previously left
  R10.2, R10.13 and R10.14 neither applied nor discharged; all three apply to
  cyclic operation and the table now says why.
- **Schema enforces R10.10 / R10.11.** Rotation shows must declare
  `ground_service.bays` and `throughput_per_min`; a `swap` turnaround policy
  must declare `battery_pool`. Negative tests prove both rejections, and a
  `charge_in_place` control proves the requirement is scoped, not blanket.
- **Appendix B records full SHA-256 digests** of the thirteen observed
  fixtures (previously truncated to 16 hex), plus the source repository URL —
  the stated purpose is reproducibility, and a truncated hash cannot pin exact
  bytes.

### Added
- **Section 10 — waves, sorties and rotation operation.** Three-level model
  (role / airframe / sortie) enabling shows longer than one battery charge.
  Rules R10.1–R10.14 and R10.25: role coverage, module exclusivity, turnaround closure,
  ground-service capacity, battery-pool closure, per-sortie energy closure,
  cross-wave separation, corridor intersection, no-silent-degradation.
- **Section 10.8 — unbounded rotation and continuous operation.** Wave groups
  and waves per group are explicitly unbounded (R10.15); an endless show is
  declared generatively via `wave_cycle` instead of enumerating infinitely many
  waves, with a normative derivation rule (R10.16). Because an indefinite
  timeline cannot be simulated, capacity validation becomes inductive:
  closed-form steady-state inequalities for airframes, batteries, bays and crew
  throughput (R10.17–R10.19), consumable closure for actuators that do not
  recirculate (R10.20), loop-seam continuity and declared handover masking
  (R10.21–R10.22), cyclic termination maps (R10.23) and a mandatory drain plan
  (R10.24) — because an endless show still has to end.
- `conformance/check_rotation.py` — semantic validator for the rules JSON
  Schema cannot express, for both enumerated and cyclic rotation. Negative tests
  in `run_schema_checks.py` and `check_rotation.py` prove the rules bite — the
  suites print their own counts, which is why none are quoted here; the
  normative wave derivation (R10.16) is pinned by a test so two implementations
  cannot diverge. 20 of the 25 rules of §10 have an executable check —
  R10.2, R10.7, R10.8, R10.13 and R10.25 do not yet, and are listed as such in
  `spec/A-open-questions.md`.
- `examples/rotation-l2/` — 42-minute show flown by 6 aircraft with a declared
  620 s energy budget and 450 s of use per sortie; demonstrates why two wave groups are
  insufficient at a 420 s turnaround and three are required.
- `examples/continuous-l2/` — an *indefinite* show: 18 aircraft in 3 groups
  sustaining 6 roles without interruption for as long as the permit allows.
  Nothing in the file grows with running time. Its battery pool is sized by
  R10.18 at a minimum of 46 (the file declares 48), not by the 6 aircraft in
  the air — the factor that a single-changeover plan gets wrong.
- **Appendix B — observed third-party formats.** SKYB container framing,
  block typing and event records verified against 13 published fixtures with
  recorded SHA-256. Written under the separation-of-roles rule of
  `NOTICE-PROVENANCE.md` §4.

### Fixed
- Schema `$ref` resolution went to the network and silently never resolved.
  Now resolved from a local registry: the toolchain validates **air-gapped**,
  as the operating rules DSX targets require. Fixing this immediately exposed
  an incomplete `termination` block that had been passing unchecked.
- Six schema tests for the continuous example were passing for the wrong
  reason (an invalid `time` block in the fixture masked the property under
  test). Each negative test now fails on the rule it names.


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
