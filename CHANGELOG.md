# Changelog

## Unreleased

### Added (multilingual publication, 2026-08-16)

- **`TRANSLATIONS.md` and `translations/`.** DSX will be published in
  zh-Hans, ja, ko, de and es. English is declared the **sole authoritative
  language** in `spec/README.md`; translations are informative and the English
  text governs any difference. This is stated as a safety rule rather than a
  legal formality: a `MUST` rendered as a recommendation produces an
  implementer who omits a required check and believes himself conformant.
- **Drift is detected mechanically.** Every translated file carries the
  SHA-256 of the English source it was made from, so the translation is marked
  **stale** the moment that source changes -- the failure mode where two
  languages quietly describe different formats is not available here.
- **`conformance/check_translations.py`**, in CI. Errors on a missing or
  malformed header, an undeclared language, a vanished source, a dropped
  governing-language notice, a translation of Appendix A (which changes too
  often to stay true), and an unreviewed machine translation of section 7.
  Stale is a WARN, deliberately: making it an error would block every English
  correction until six translations catch up, and a check that blocks ordinary
  work gets switched off.
- **The checker is self-tested** (`--selftest`, 7 synthetic cases, also in CI).
  A checker whose failure path is never exercised cannot be distinguished from
  one that returns success unconditionally.
- First translation: `translations/zh-Hans/spec/README.md`, marked
  `machine, unreviewed` in its own header rather than presented as finished.

### Added (container security, 2026-08-16)

- **A33 resolved — §2.1.1 "Entry names" and §2.1.2 "Resource limits" added.**
  Rules C1–C3 (relative paths only, no `.`/`..` component, no control
  characters, valid UTF-8), C4/C5 (no duplicate and no NFC-casefold-colliding
  entry names), C6 (regular files and directories only). All are REJECT: a
  violating archive must not be parsed, and must not be repaired, because every
  repair is a guess about which reading the author meant.
- **C4/C5 close a signature bypass against §2.3.1, and the bypass is now
  demonstrated rather than described.** `check_container.py` builds an archive
  carrying `show.json` twice; the same Python standard library hashes the first
  occurrence and parses the last, so the signature covers a 20 m minimum
  separation while the parsed manifest declares 2 m. §2.3.1 step 3 now states
  that C4/C5 are a precondition of the digest.
- New `tools/dsx_container.py` (reference implementation) and
  `conformance/check_container.py` (20 checks), wired into CI **first**, since
  every later suite assumes a vetted container.

### Changed (two corrections found while writing the above)

- **The per-entry compression-ratio limit was specified and then withdrawn.**
  DEFLATE cannot exceed roughly 1032:1 on any input (measured 1028.6:1 on
  50 MB), so a cap below that bound rejects legitimate content — the
  `continuous-l2` example's near-silent audio track reaches 243:1 and was
  rejected by the first draft's 200:1 rule — and a cap above it never fires.
  §2.1.2 now says so explicitly, because a ratio cap is the conventional
  advice and its absence would otherwise look like an oversight.
- **The total-size limit counts bytes actually produced during decompression**,
  not the sizes declared in the ZIP central directory, which are the writer's
  claim rather than a measurement. A declared size that does not match the
  stream is reported as a stated reason for rejection instead of surfacing as a
  `BadZipFile` at the caller.
- `check_container.py`'s negative checks assert *which entry* tripped a rule.
  Without that, the first C6 check passed while the implementation was in fact
  rejecting every ordinary archive: Python's own writer stores permission bits
  with the file-type bits clear, and testing `S_ISREG()` directly treated that
  as "not a regular file". C6 now judges only when `S_IFMT` is present.

### Changed (sampler audit and appendix-B anonymisation round, 2026-08-15)

- **A1, A31, A32 resolved — §4.2/§4.3/§4.4 are now specified completely, and
  it is proven rather than asserted.** `tools/dsx_sample.py` is a clean-room
  reference sampler written from the spec text alone; five hand-computed
  (`analytic`) test vectors in `conformance/sampling/` pin down cubic Bézier
  evaluation, `t_k` rounding (round-half-away-from-zero vs. banker's
  rounding), `fade`/`strobe` colour rounding, both `time_semantics` values and
  Catmull–Rom with endpoint duplication. `run_sampling_checks.py` runs in CI.
  The §1.4 interoperability guarantee is now a demonstrated property for the
  cases covered — README.md, `spec/01-overview.md` §1.4 and
  `spec/09-conformance.md` updated accordingly. Coverage is not exhaustive;
  the gap is recorded as new item **A36**, not hidden.
- **A26 resolved.** `check_archive.py::eval_seam` now evaluates trajectory
  files directly to prove loop-seam position/velocity continuity (R10.21,
  R10.22), using the §4.2.4 tangent formulas; proven both ways (passes on
  `continuous-l2`, fails on a mutated 1 m gap). Residual limitation recorded
  as new item **A37**: the formula assumes `bezier` boundary segments.
- **A real bug found auditing the AMBIGUITIES list against the completed
  §4.2–§4.5, not a hypothetical one.** Five of the six long-standing
  "ambiguity" notes in `tools/dsx_sample.py` turned out to be stale — the
  final spec text already resolved each of them and the code already matched
  it. The sixth was a genuine discrepancy: §4.5.2 makes `duty` REQUIRED on a
  `strobe` op with **no default** ("any default would be a house style
  silently imposed on every file that omits it"), but the reference tool
  silently substituted `0.5`, and `schema/resource.schema.json` did not
  require it either. Both are fixed: the schema now requires `duty` on
  `strobe`, and `_validate_light` rejects its absence before evaluation. A
  second, smaller gap surfaced in the same pass: §4.4.5 requires a producer to
  report dropped RGBW channels as a WARN-class finding; `sample_to_csv` did
  this silently and now prints the warning. Both are covered by new negative
  fixtures (`reject-strobe-no-duty.light.json`,
  `reject-rgbw-drop-warns.light.json`) and asserted at the end of
  `run_sampling_checks.py`, at both the tool level and the schema level, so
  the two cannot silently drift apart again. `AMBIGUITIES` in
  `tools/dsx_sample.py` is now empty, with the audit trail kept in a comment.
- **Appendix B provenance citation anonymised.** `spec/B-observed-formats.md`
  previously named the specific open-source repository and GitHub URL the
  thirteen `.skyb` fixtures were retrieved from. Per an explicit decision that
  the specification itself must name no third party anywhere, that citation
  is now generic ("a publicly readable GPL-licensed open-source project"), matching
  the wording already used throughout `NOTICE-PROVENANCE.md`. The SHA-256 of
  each fixture is kept, and remains sufficient to prove which exact bytes were
  examined to anyone who already has or independently obtains them —
  reproducibility does not require naming the source, only fixing the bytes.
  `NOTICE-PROVENANCE.md` §2 and §5 updated to match (removed "cited by URL",
  now "cited by SHA-256").

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
