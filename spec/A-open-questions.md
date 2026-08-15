# Appendix A — Open questions

*Living document. Everything here is knowingly unresolved. It is published
rather than hidden, because a specification that pretends to certainty it does
not have is the more dangerous artefact.*

## Blocking `v0.1` completion

| # | Question | Needed from |
|---|---|---|
| A1 | **Resolved 2026-08-15.** Six hand-computed (`analytic`) sampler test vectors exist in `conformance/sampling/` and pass against `tools/dsx_sample.py`, run in CI by `run_sampling_checks.py`. The §1.4 guarantee is now a demonstrated property for the cases covered — Bézier evaluation, `fade`/`strobe` rounding, `until_next`/`since_previous` displacement, and Catmull–Rom with endpoint duplication, and (since 2026-08-16) yaw. Coverage is not exhaustive; see A36 for what is not yet vectorised. | this project |
| A2 | `.dsb` binary encoding is specified only in outline. | this project |
| A3 | Conformance suite is an outline (§9). | this project |

## Field data required

| # | Question | Why it matters |
|---|---|---|
| A4 | **Show-clock holdover after GNSS loss is uncharacterised in all public sources.** No drift figure, no defined behaviour. | §3.2 — `max_drift_ms_per_min` is `null` by default; there is no state of the art to copy here |
| A5 | **RTK degradation behaviour during a running show** is undocumented industry-wide. | §7.4 — the degradation policy is currently a proposal, not a description |
| A6 | Failsafe and termination chains of the major manufacturers are not publicly documented. | §7 — vocabulary must match real behaviour, not assumed behaviour |
| A7 | LED channel count is contradictory in vendor documentation for at least one common show aircraft. | §5.1 — resolvable only by the manufacturer |
| A8 | Broadcast-termination latency at fleet sizes above one thousand aircraft: no public figures. | §7.1 — the one-action requirement needs a timing bound |

A4 and A5 are the most interesting entries in this table: **there is no
existing practice to align with.** Whatever DSX specifies there will be the
first written description.

## Regulatory sources not yet obtained

| # | Document | Status |
|---|---|---|
| A9 | Shenzhen local standard on formation-flight display safety (DB4403/T, draft for approval) | led by the authorising authority itself; adoption to be tracked |
| A10 | Shenzhen UAV Industry Association group standard T/SZUIA 002-2021 | paid, apparently not self-declared on the national platform; obtainable in person |
| A11 | EASA SORA 2.5 annex — does **any** PDRA apply to drone shows? | unresolved; if none applies, every show is a full SORA, which defines the automation opportunity |
| A12 | UK CAP 722E, CASA Annex B, Japanese examination guidance | PDFs identified, not yet parsed |
| A13 | UAE and Saudi Arabia | no primary source located despite record-scale shows |
| A14 | NFPA 1123 / 1126 wording on firing-circuit shunting and key switches | paywalled; to be purchased, not guessed, before L2 pyro is finalised |

Freely available and already usable: the Shanghai group standard on drone
formation display safety (T/SHUAV 1—2021), and the EASA Easy Access Rules in
XML form, which is directly embeddable.

## Naming and trademark

| # | Question |
|---|---|
| A15 | **Resolved: no trademark is needed, and none will be sought for "DSX".** Naming a format, defining an extension and publishing a specification is technical use, not use of a sign as an indicator of commercial origin — the same footing as `.zip`, `.json` and `.csv`, none of which is anyone's mark. A 2026-08-15 knock-out search did find a crowded field (EUTM 017940461, DSX Holdings Ltd, live word mark over software and electronic publications; US Reg. 2679754, DSX Access Systems, incontestable in class 9; DSX-1/DSX-3 generic in telecoms; `.dsx` used by four unrelated formats), which settles a *different* question: the project could never own the letters DSX. It does not need to. Background and reasoning in [`TRADEMARK.md`](../TRADEMARK.md). |
| A15a | **China: unverified, and deliberately deferred.** CNIPA was not reachable from the search environment. It is not a blocker on publication — see A15. It becomes relevant only for the certification-programme name (A15b), and secondarily as squatting intelligence: a Chinese class-9 holder of "DSX" could make a manufacturer hesitate to use the word in its own marketing, which is commercial friction rather than legal exposure for this project. |
| A15b | The certification-programme name has not been coined, and this is the **only** name the project should ever pay to clear and register. It must be a distinctive invented word, cleared in EU, US and CN, and registered as a **certification mark** — whose owner may not itself sell the certified goods and must apply the standard even-handedly. That constraint is a feature: it makes the neutrality claim in `GOVERNANCE.md` legally enforceable rather than merely promised. Deferred until a conformance programme actually exists; until then `conformance/` plus misrepresentation law is the enforcement basis. |

## Rotation operation (section 10)

| # | Question |
|---|---|
| A16 | `turnaround.min_s` is declared per show. Real turnaround differs by group, by cycle and by ambient temperature. A per-group or per-sortie override is likely needed; deferred until an operator has run the model against a real changeover. |
| A17 | R10.10 models ground service as a bay count and a throughput rate. Real service is a queue with crew skill, battery logistics and weather holds. The current check is a necessary condition, not a sufficient one, and is documented as such. |
| A18 | Corridor/flight-volume intersection (R10.8) is specified but not yet implemented in the conformance suite: it needs a geometry dependency the suite deliberately does not have yet. |
| A19 | Whether a sortie may change `wave` mid-flight (an aircraft diverted into another group's return) — currently forbidden by construction. No operator has been asked whether that matters. |
| A20 | The steady-state inequalities (R10.17–R10.19) are **necessary conditions on averages**. They do not model the transient at the start of a continuous show, where the pool is full and the first cycles are easier, nor the burst load when two groups need servicing within one period. A queueing model with variance would be stricter; the closed forms were chosen because they are checkable by hand on site. |
| A21 | Wear is not modelled. `open_ended.limited_by` can name `battery_cycles` and `airframe_hours`, but nothing counts them across cycles or carries them between shows. A continuous installation running nightly needs a maintenance ledger, which is arguably a fleet-management concern rather than a show-file concern. Undecided. |
| A22 | `role_binding: "explicit"` is declared in the schema but has no defined mapping syntax yet; only `by_slot_index` is specified. Explicit binding is what a show with mixed aircraft types per wave will need. |
| A23 | Under `by_slot_index`, R10.17 (airframe closure) is implied by R10.15 plus the slot-completeness rule and cannot fail independently. It is kept as a separate rule because it *can* fail under explicit binding, but the redundancy should be revisited once A22 is resolved. |
| A24 | Five rules of §10 are specified but have **no executable check** in `conformance/`: R10.2 (ingress/egress is not choreography), R10.7 (handover windows are termination-aware), R10.8 (corridor intersection, see A18), R10.13 (energy is per sortie, not per model) and R10.25 (no silent degradation, which constrains readers rather than files). They are normative regardless; the gap is in the suite, not in the specification, and is recorded here rather than left for a reader to discover. |
| A25 | §4.4 derives the normative sample count from `duration_ms`, but R10.24 requires `duration_ms: null` for an indefinite show. The interoperability guarantee of §1.4 therefore has **no defined meaning** for the shows §10.8 introduces. The likely resolution is to sample one loop period and declare it as repeating, but that is not specified yet, and until it is, an open-ended file cannot be reduced to `t,x,y,z,R,G,B` by the rule the specification gives. |
| A26 | **Resolved 2026-08-15.** `check_archive.py::eval_seam` now evaluates the actual trajectory files and proves position (and, where `continuity: c1` is declared, velocity) match at the loop seam, using the §4.2.4 endpoint-tangent formulas directly rather than by calling `tools/dsx_sample.py`. Both directions are tested: `continuous-l2` passes, and a mutated copy with a 1 m seam gap is proven to fail. **Residual limitation (A37):** the formula assumes the first and last segment of the loop are `bezier`; a loop closed with a `poly` or `linear` segment at either end raises `KeyError` in `eval_seam` instead of failing with a clear message, or possibly not at all. |

## Third-party format observation

| # | Question |
|---|---|
| A27 | The 4-byte field at offset 6 of a v2 SKYB header is unresolved (Appendix B.1.4). Eleven CRC-32 variants, four non-CRC checksums and three truncated hashes over five byte ranges were excluded. Until it is identified, DSX importers MUST NOT claim to verify SKYB integrity. |
| A28 | No public sample has been located for `.dac`, `.bin`, `.path`/`.path3` or the vendor JSON variants. Appendix B stays incomplete until one is contributed. |

## Specification completeness (external review, 2026-08-15)

*An external standards reviewer with no exposure to this project read `spec/`
and concluded that an engineer could not yet write an importer from the prose
alone. The verdict is accepted. The items below are the unresolved remainder;
they are recorded here rather than left for a reader to discover, and A31 is
the one that blocks first use.*

| # | Question | Status |
|---|---|---|
| A29 | The one-action-per-rung requirement (§7.1) is addressed to the ground station, which §1.1 places outside DSX's scope, and is therefore not checkable by `conformance/`. A file-level representation — declaring the operator action count per rung — would make it verifiable, at the cost of stating something the file cannot enforce. Undecided. | open |
| A30 | The fall model behind `disarmed_fall_containment` (§7.5) is unspecified: no drag model, no tumbling assumption, no mass/area inputs, no wind case. Two validators can reach different verdicts on the same geometry. `v0.1` therefore requires disclosure of model, tool and wind case rather than a geometric guarantee. | open |
| A31 | **Resolved 2026-08-15.** §4.2 now states the field list per segment `type` (`bezier`, `poly`, `linear`), the start-point rule (`start_point` for the first segment, the previous segment's `p` thereafter) and the Bézier parameterisation; §4.3 states the sampled `data` element layout, tuple order and units. `tools/dsx_sample.py` is a clean-room implementation from this text alone and passes the vectors of A1, which is the practical proof that a reader can now be built from the prose. | resolved |
| A32 | **Resolved 2026-08-15.** §4.4 now fixes `t_k` rounding (round-half-away-from-zero, ties away from zero — the case A1's `a1-bezier` vector exists specifically to distinguish from banker's rounding), states `fade` is interpolated in encoded sRGB, gives `strobe` a phase origin and a strict `<` on/off boundary, and requires `duty` on every `strobe` op with no default (this last point was implemented as a *default* rather than a *rejection* in the reference tool until the 2026-08-15 audit found the discrepancy against the now-complete text; both the schema and `tools/dsx_sample.py` reject its absence now, see CHANGELOG.md). RGBW reduction is specified directly in §4.4.5, not deferred to the device profile. | resolved |
| A33 | **Resolved 2026-08-16.** §2.1.1 constrains entry names (C1–C3 relative paths, no traversal, no control characters; C4/C5 no duplicate and no case-folding-colliding names; C6 regular files and directories only) and §2.1.2 states resource limits. §2.3.1 now names C4/C5 as a precondition of the digest rather than a separate concern. `tools/dsx_container.py` implements the rules and `conformance/check_container.py` demonstrates the bypass concretely: an archive carrying `show.json` twice is hashed at a 20 m separation minimum and parsed at 2 m by two readings of the same standard library. Writing the section produced two corrections of its own — a per-entry compression-ratio limit was specified and then **withdrawn**, because DEFLATE is bounded at ~1032:1 (measured 1028.6:1) so any cap below that rejects legitimate content (this repository's own near-silent audio track reaches 243:1) and any cap above it never fires; and the total-size limit was moved from the declared directory sizes to bytes actually produced during decompression, since the declared sizes are the writer's claim. | resolved |
| A34 | **Resolved 2026-08-16.** Both halves are closed. `yaw` is now specified in §4.2.5 — unwrapped degrees measured from +X toward +Y, linear in the segment parameter `u` for *every* segment type, clamped outside the track, all-or-nothing per track, rounded to millidegrees, and emitted as its own `t_ms,yaw_deg` reduction so that the canonical CSV of §4.4.5 stays exactly `t_ms,x_m,y_m,z_m,r,g,b` and adding yaw to a show cannot change what an L0 consumer receives. The hand-computed vector `a6-yaw` pins the three decisions a reader could otherwise get wrong: 180.000° exactly (where shortest-arc interpolation is undefined), 370.000° (which a reader normalising modulo 360 would emit as 10.000), and a half-millidegree tie that separates round-half-away-from-zero from banker's rounding. The matrix is `profiles/profile-matrix.json`, published as normative [Appendix C](C-profile-matrix.md) and generated from it; `conformance/check_profiles.py` mutates a real reference file for every REQUIRED and FORBIDDEN cell and asks the schema whether it notices. Writing it found five rules that existed only as prose — `roles` and segment trajectories at L0, `payloads` and `termination.fallback_channel` below L2, and `trajectory_sampled` being the one trajectory form an L0 file may carry — which are now schema-enforced; 73 of 73 manifest cells are enforced by the schema and the remaining four (yaw) are checked against the resource files directly. | resolved |
| A35 | Several identifiers used in the §10 inequalities (`aircraft_per_wave`, `service_s`, `flight_s`, `turnaround_s`) are prose names, not field paths, so R10.17–R10.19 are not machine-checkable from the text alone — only from `conformance/check_rotation.py`, which is the wrong direction of authority. | open |

## Profile matrix follow-ups (added 2026-08-16, while closing A34)

*Both were found by writing the matrix down: a member-by-member table forces a
decision on cases that scattered prose lets stay undecided.*

| # | Question | Status |
|---|---|---|
| A38 | **Resolved 2026-08-16.** `examples/show-l1/` is the L1 reference file: eight aircraft, one figure, 120 s, and exactly the constructs §1.3 names for L1 — `bezier` segment trajectories, light programs (including a `strobe` that declares its `duty`), device-profile binding with a `declared_envelope`, a show geofence, a staggered takeoff grid, and an RTH feasibility map whose infeasible windows are the climb and the descent. It carries nothing above L1: no yaw, no payloads, no waves, no sorties. Two things were made true rather than asserted. The track is **C¹ at every joint** — §4.2.2 forbids re-timing at playback, so a corner between two segments is a real velocity step, and the control points of the climb, transit and descent are placed to match the circle's tangent (measured residual at 45 joints: 0.012 m/s, which is the finite-difference artefact). And `declared_envelope` is **measured from the generated tracks** by `tools/build_examples.py`, which refuses to build the example if any axis exceeds the bound device profile or if the closest approach falls below `safety.min_separation_m` (measured: 4.99 m at t=80380 ms against a 2.5 m floor). Closing this also closed two holes it exposed: `check_archive.py` iterated a hand-maintained list of example names and would have shipped the new example unchecked, and `run_schema_checks.py::binding` compared only `peak_speed_xy_ms` against the device profile, leaving the other five limits and the `safety` floor looking enforced when they were not. | resolved |
| A39 | §1.3 advertises the *GNSS integrity policy* as an L2 ingredient, yet `position_integrity`, `interference_policy` and `time_source` are OPTIONAL at L2 in `v0.1` — and neither L2 reference file carries the first two. Appendix C states the fact rather than hiding it. The question for `v0.2` is whether an L2 file, which is the profile an operator files with an authority, may legitimately stay silent about how it detects a degraded or spoofed GNSS solution. Making them REQUIRED is a breaking change and needs the field data of A6–A8 first. | open |
| A40 | **Found while closing A38.** No example carries a `payloads` array and no bundled device profile declares a `payload_slot`, so §6 — actuators, `authority: show\|safety`, `prefire_latency_ms`, `hazard`, interlocks, and the arm/disarm state machine — is the only normative section with **no reference file** behind it. Every other section is exercised by a fixture that `conformance/` validates; §6 is exercised by prose alone. This matters more than the L1 gap it was found beside: §6 is where the two threat models of §7 diverge (a flight kill must be unforgeable against *prevention*, a pyro fire must be protected against *unauthorised triggering*), and an implementer currently has no worked example of either. A `pyro-l2/` example needs a device profile with a real `payload_slot` before it can exist. | open |

## Sampler and seam-check coverage (added 2026-08-15, after A1/A26/A31/A32 closed)

*These two are new, not carried over — they surfaced while writing the fixes
for A1, A26, A31 and A32 and are recorded immediately rather than left for the
next reader to rediscover.*

| # | Question | Status |
|---|---|---|
| A36 | The five vectors that close A1 cover Bézier evaluation, `fade`/`strobe` rounding, both `time_semantics` values, and Catmull–Rom with endpoint duplication — the cases that were hardest to get bit-exact. They do **not** cover: `poly` segments, `linear` segments, the `hold` interpolation mode on an interval track, before/after-track clamping (§4.2.1/§4.3.4), the grid-collision `w=0` rule (§4.3.1) at rate > 1000 Hz, or the RGBW-channel-drop reduction (§4.4.5, now covered only by a hand-run check in `run_sampling_checks.py`, not a byte-exact CSV vector). The §1.4 guarantee is demonstrated for the covered cases and still an intention for the rest. | open |
| A37 | `conformance/check_archive.py::eval_seam` proves loop-seam continuity (R10.21/R10.22, closing A26) but its tangent formula assumes both the first and the last segment of the loop are `bezier`. A loop closed with a `poly` or `linear` segment either raises an unhelpful `KeyError` or silently evaluates the wrong thing, depending on which field happens to collide. Needs either a segment-type-aware seam evaluator or an explicit restriction, stated in §10, that a declared loop's boundary segments MUST be `bezier`. | open |
