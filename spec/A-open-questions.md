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
| A15 | The three-letter name "DSX" collides with existing marks in adjacent classes. Registrable subject matter is expected to be the compound wordmark and the conformance badge rather than the bare letters. Fallback candidates: `ODSX`, `OpenDSX`. To be resolved **before** external implementers depend on the name. |

## Rotation operation (section 10)

| # | Question |
|---|---|
| A16 | `turnaround.min_s` is declared per show. Real turnaround differs by group, by cycle and by ambient temperature. A per-group or per-sortie override is likely needed; deferred until an operator has run the model against a real changeover. |
| A17 | R10.10 models ground service as a bay count and a throughput rate. Real service is a queue with crew skill, battery logistics and weather holds. The current check is a necessary condition, not a sufficient one, and is documented as such. |
| A18 | Corridor/flight-volume intersection (R10.8) is specified but not yet implemented in the conformance suite: it needs a geometry dependency the suite deliberately does not have yet. |
| A19 | Whether a sortie may change `wave` mid-flight (an aircraft diverted into another group's return) — currently forbidden by construction. No operator has been asked whether that matters. |

## Third-party format observation

| # | Question |
|---|---|
| A20 | The 4-byte field at offset 6 of a v2 SKYB header is unresolved (Appendix B.1.4). Eleven CRC-32 variants, four non-CRC checksums and three truncated hashes over five byte ranges were excluded. Until it is identified, DSX importers MUST NOT claim to verify SKYB integrity. |
| A21 | No public sample has been located for `.dac`, `.bin`, `.path`/`.path3` or Drotek JSON. Appendix B stays incomplete until one is contributed. |
