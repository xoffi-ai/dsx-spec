# Appendix A — Open questions

*Living document. Everything here is knowingly unresolved. It is published
rather than hidden, because a specification that pretends to certainty it does
not have is the more dangerous artefact.*

## Blocking `v0.1` completion

| # | Question | Needed from |
|---|---|---|
| A1 | Normative sampler test vectors do not yet exist (§4.4). Until they do, the interoperability guarantee is an intention. | this project |
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
| A26 | The seam rules (R10.21, R10.22) are checked at manifest level only: the validator confirms that a loop is *declared* and that the handover is masked, but nothing yet evaluates the trajectory files to prove position and velocity actually match at the seam. That check needs the sampler (§4.4), which has no test vectors — so loop continuity is currently a declaration, not a verified property. |

## Third-party format observation

| # | Question |
|---|---|
| A27 | The 4-byte field at offset 6 of a v2 SKYB header is unresolved (Appendix B.1.4). Eleven CRC-32 variants, four non-CRC checksums and three truncated hashes over five byte ranges were excluded. Until it is identified, DSX importers MUST NOT claim to verify SKYB integrity. |
| A28 | No public sample has been located for `.dac`, `.bin`, `.path`/`.path3` or Drotek JSON. Appendix B stays incomplete until one is contributed. |

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
| A31 | **The two central data structures are underspecified.** §4.2 does not state, per segment `type`, the exact field list, where the first segment's start point comes from, or the Bézier parameterisation; §4.3 does not state the element layout, tuple order or units of a sampled `data` array. **Until this is written, no conforming reader can be built — not even at L0.** This is the highest-priority item in the specification. | **blocking** |
| A32 | §4.4 is not yet bit-exact as written: the rounding mode for `t_k` is unstated while later steps name two different rounding rules; whether `fade` is interpolated in encoded sRGB or in linear light is undefined; `strobe` has no phase origin or on/off boundary rule; and the reduction of a 4-channel (RGBW) program to `R, G, B` is described as profile-governed but the profile has no such field. Each of these alone defeats the §1.4 guarantee. | **blocking for §1.4** |
| A33 | Container security rules are missing from §2.1: archive entry names are not constrained (path traversal, absolute paths), duplicate entry names are not forbidden — which is a signature-bypass vector against §2.3.1, since one entry can be hashed and another parsed — and no decompression limits are stated. A format intended to be opened by ground stations needs all three. | open |
| A34 | Profile applicability is scattered across §1.3, §2.3, §3, §7.1.1 and §10.9 with no single matrix, and §1.3 lists `yaw` as an L2 feature although yaw is specified nowhere in the document. A normative member × profile × REQUIRED/OPTIONAL/FORBIDDEN appendix is needed; `yaw` must be either specified or withdrawn from §1.3. | open |
| A35 | Several identifiers used in the §10 inequalities (`aircraft_per_wave`, `service_s`, `flight_s`, `turnaround_s`) are prose names, not field paths, so R10.17–R10.19 are not machine-checkable from the text alone — only from `conformance/check_rotation.py`, which is the wrong direction of authority. | open |
