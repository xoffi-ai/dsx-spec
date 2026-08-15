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
| A15 | **Searched 2026-08-15; result is not encouraging.** "DSX" is a crowded acronym: EUTM 017940461 (DSX Holdings Ltd) is a live *word mark* covering computer software, electronic publications and computer programming; US Reg. 2679754 (DSX Access Systems) is incontestable in class 9; DSX-1/DSX-3 is generic in telecoms; `.dsx` is already used by four unrelated formats. Registering "DSX" is therefore **not** a viable plan. Full findings and the proposed split — unprotected format name, separately coined certification mark, per the IEEE 802.11 / Wi-Fi precedent — are in [`TRADEMARK.md`](../TRADEMARK.md). |
| A15a | **China is unverified and is the urgent gap.** CNIPA was not reachable from the search environment. China is first-to-file, examines relative grounds *ex officio*, and is where the manufacturers and the intended steward are. A local knock-out search in classes 9 and 42 is needed **before** any public announcement, and its result may still force a rename. |
| A15b | The certification-programme name has not been coined. It must be a distinctive invented word cleared in EU, US and CN, and registered as a **certification mark** — whose owner may not itself sell the certified goods and must apply the standard even-handedly. That constraint is a feature: it makes the neutrality claim in `GOVERNANCE.md` legally enforceable rather than merely promised. |

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
