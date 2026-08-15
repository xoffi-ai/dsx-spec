# Termination is Data

**What a drone light show file must contain before anyone can check it —
and why the operating rules alone cannot get there.**

| | |
|---|---|
| Document | DSX Whitepaper 01 |
| Status | `draft` — for review and contradiction |
| Version | 0.1, 2026-08-16 |
| Editor | Thomas Fleissner, trading as FLEITEC |
| Normative counterpart | [`spec/07-safety-and-termination.md`](../spec/07-safety-and-termination.md) — **that** text governs; this one explains it |
| Licence | Community Specification License 1.0, as the specification |
| Audience | industry associations, civil-aviation and public-security authorities, show-system manufacturers, operators |

> **A note on how sources are used here.** Accidents are cited by their official
> investigation number and by what the published report says. **Operators,
> aircraft types and software products are not named**, here or anywhere else in
> this project (see [`NOTICE-PROVENANCE.md`](../NOTICE-PROVENANCE.md) §5). The
> purpose is to describe a class of failure that the industry shares, not to
> assign blame that an investigating authority has not assigned. Every company
> reading this has flown the same data through the same gaps.

---

## In one page

A drone light show is regulated as a **procedure** and exchanged as a
**choreography**. The safety envelope — separation minima, geofence geometry,
what happens on link loss, what the operator can still do at second 92 — lives
in neither. It lives in a PDF, in a ground-station configuration screen, and in
the experience of the pilot in command.

The consequence is that **nobody outside the operating company can check a show
before it flies.** An authority receives a flight application; a client receives
a preview video; a subcontracted crew receives a CSV of positions and colours.
None of these three can be tested against the others by a machine.

This document argues one point:

> **The safety envelope of a show is data, it can be carried in the show file,
> and once it is carried there it becomes checkable by a third party without
> access to the vendor's software.**

DSX is one attempt to write that data down. The seven requirements in §3 are
the part that matters; they would still matter if a different format carried
them.

---

## 1. Four findings, four data problems

On 21 December 2024 a show of roughly 500 aircraft over a public park resulted
in aircraft falling into a crowd and a child being injured. The investigating
authority's preliminary report [1] contains four findings. It is worth reading
them as a data engineer rather than as an operator:

| Finding, as reported | What it is, as data |
|---|---|
| "the launch parameter file that contained the final flight paths had not been sent" | a **transfer that completed while incomplete** — nothing compared what the aircraft held against what the show demanded |
| "the show position was rotated by 7°" | the **frame of reference** was wrong, and no artefact stated the frame well enough for a tool to notice |
| the geofence "was set to five metres rather than the company's standard of one metre" | a **safety scalar was editable without cross-check** against the geometry it was supposed to protect |
| the pilot let the show continue "due to the steps involved in pausing the show, recovering airborne aircraft and the designated flight paths" | the **abort path was too expensive to use** while aircraft were already falling |

Three of the four are file problems. The fourth is an interface problem created
by a file problem: aborting was expensive *because* the recovery paths and the
consequences of pausing were not available as pre-computed, inspectable data.

This is the whole argument of this document, and it comes from a public
accident report rather than from a design meeting:

- A file with a **content hash over its complete manifest** cannot be
  half-transferred without both ends noticing.
- A file that **declares its coordinate frame, origin and heading** as data
  turns a 7° rotation into a comparison, not an observation made at liftoff.
- A file that carries **fence geometry and audience geometry in the same
  document** lets a validator ask whether 5 m is still enough — before the
  countdown, on a laptop, with no aircraft present.
- A file that carries a **pre-computed return path and states when it is
  feasible** makes "pause the show" a decision with a known cost instead of an
  unknown one.

None of this would have been exotic engineering. It was simply not anybody's
job, because no format asked for it.

## 2. The failure that scales: interference

The second failure class is different in character. On 27 October 2018 a public
show lost dozens of aircraft in a single event, and the reported cause was
interference with satellite navigation; a criminal investigation followed [2].
Comparable mass-loss events at public shows have been publicly attributed to
interference or to "compromised positional accuracy" since. The technical
detail that matters is not the jamming. It is this:

> Every aircraft did the correct thing. The correct thing is to land when the
> position solution is lost. Under area-wide interference, *every* aircraft
> does the correct thing **at the same time, from wherever it happens to be.**

The individual failsafe is sound and the fleet behaviour is not, because the
failsafe was designed for one aircraft and there are five hundred. A file
format cannot fix a jammer. It can carry the one thing that is missing: a
**fleet-level declaration of what the fleet does**, distinct from what a single
aircraft does — hold rather than land where holding is safe, degrade separation
minima rather than descend, reject a suspicious solution rather than follow it.

The relevant telemetry already exists in mainstream autopilots: jamming state,
spoofing state, GNSS authentication status, automatic gain control, noise per
channel. **No regulation currently requires anyone to act on any of it.** The
minimum useful step is to make the policy declarable, so that an operator can
be asked what theirs is and a reviewer can read the answer.

A related case is subtler and is the reason DSX contains a field that looks
paranoid. A widely used autopilot resets its state estimate to the satellite
solution once a glitch has persisted for a period documented as roughly seven
seconds. An attacker who *pulls slowly* is therefore rewarded by the recovery
logic, and the conventional failsafes never fire, because every subsystem
agrees with every other subsystem. A geofence that compares the *estimated*
position against the commanded position stops protecting at exactly the moment
protection is needed. DSX therefore asks for a guard value below that window,
and for a declaration of whether an integrity check exists that does **not**
depend on the same estimate.

## 3. What the file must contain

Seven requirements. Each is stated as an obligation on the **file**, because an
obligation on the file is the only kind a third party can verify without
entering the operator's building.

### R1 — Termination is a ladder with named rungs

Four rungs, in this order, with reversibility stated: `hold`,
`coordinated_rth`, `land_in_place`, `disarm`. Independently developed systems
have converged on them; naming them in the file is what makes an emergency
procedure comparable between two operators and two authorities.

**Corollary, addressed to integrators rather than to files:** each rung MUST be
reachable by a **single operator action**. An abort path that costs more
decisions than continuing will lose to continuing, under time pressure, by
people who are not negligent. That is the documented mechanism of finding four
in §1.

### R2 — Naming a rung obliges the file to define it

An escalation ladder that lists `coordinated_rth` without a return path is a
ladder with a missing step. Declaring a capability and not carrying its data is
the specific failure that makes safety fields in existing formats worthless:
they exist in the schema, they are exported empty, and nothing rejects the file.

### R3 — Termination is independent of playback

Termination data MUST be evaluable **onboard**, without a connection to the
ground station, and MUST NOT be a function of the show frame rate. At current
fleet sizes, per-aircraft intervention is not physically possible; automatic
onboard mitigation is the only mechanism that scales. A safety channel that
lives in the player is a safety channel that is gone when the player is.

### R4 — Availability of a rung is a function of time, not a constant

This is the requirement that does not exist in any format we have found, and
the one we would most like to be contradicted on.

Pre-computing return branches at a fixed interval is established practice. But
**in a dense transition, a collision-free return may not exist at all** — and a
branch every 15 seconds does not help if six consecutive branches are
infeasible. DSX therefore carries a **feasibility map over the show timeline**:
for every instant, which rungs are actually available, and why not, where not.

Two consequences, both cheap:

- The operator interface can show *"RTH unavailable — hold or land"* instead of
  offering a button that would not work.
- The validator can report, **before** the show: *"between 92 s and 108 s there
  is no safe retreat for 16 seconds — do you want to change the choreography?"*

The default interval is specified at **15 000 ms**, not 30 000, because the
interval is the **maximum additional exposure time**: trigger at t = 47 s with
the next branch at t = 60 s and the show continues for 13 seconds while
something is going wrong. The storage cost is a few kilobytes per aircraft. The
real cost is deconfliction computation, and that is a pre-flight expense paid
on a workstation.

### R5 — Position integrity is a declared policy, not an implementation detail

Required solution quality (satellites, dilution of precision, error estimate,
RTK state) and — more importantly — the **degradation policy**: what the fleet
does when RTK drops from fixed to float, from float to single, and when the
solution is lost entirely. Plus the interference policy of §2 and the estimator
guard.

Loss of satellite navigation is usually modelled as a position problem. It is
also a **time** problem: the show clock and the position solution typically
come out of the same receiver. A format that specifies the position response
and says nothing about the clock has specified half of the failure.

### R6 — Fallout geometry is disclosed, even when it cannot yet be guaranteed

The safety area MUST contain the fall trajectory of a **disarmed** aircraft
from every position the show reaches. Where payloads are carried, their debris
distance enters the same computation.

DSX `v0.1` does **not** define the fall model — drag, tumbling, mass and area
assumptions, wind case. Two validators can therefore reach different verdicts
on the same geometry, and the specification says so in the open-questions
appendix (A30). Until a model exists, the checkable obligation is one of
**disclosure**: the file records the model, the tool and version that computed
it, the wind case, and the result — and a reader MUST NOT display the
containment as verified when the file says it is not.

A declared, attributable, falsifiable claim is worth more than a number whose
derivation nobody can reproduce. Publishing a geometric guarantee we cannot yet
define would be precisely the behaviour this project exists to replace.

### R7 — Two threat models, not one

Termination and payload firing are **opposite** security problems, and treating
them as one is how systems end up with the wrong protection on both:

| | Threat | Requirement |
|---|---|---|
| Flight termination (`disarm`) | someone **prevents** it | must not be blockable; availability outranks confidentiality |
| Payload firing (pyrotechnics) | someone **triggers** it | must not be actuable without authorisation; per-channel arm/disarm state |

Payload channels are therefore auto-disarmed on hard-fence breach, on link loss
and on any escalation at or above `land_in_place` — the payload interlock is
driven by the same ladder as the flight behaviour, not by a parallel system
with its own opinion.

## 4. What this document deliberately does **not** require

A specification that demands what the industry cannot deliver is a
specification with zero conformant implementations on day one, and it converts
its own safety requirements into a reason to ignore the standard. Four
deliberate omissions:

**Encrypted flight-control links are not required.** Encryption in the show
control channel is *not* the state of the art in this industry — one widely
deployed system was transmitting unencrypted until recently. Authentication
requirements therefore sit in the highest profile (L2), where they describe an
achievable target, rather than in the baseline, where they would describe a
world that does not exist.

**Recovery parachutes are not required, including at L2.** They are available
as an option on show aircraft in this class and are not standard equipment. The
documented mitigation strategy for swarms is coordinated return plus contained
fallout, not per-aircraft recovery. Where a recovery device *is* fitted, DSX
follows the structure of the applicable industry standard — an autonomous
trigger independent of the flight-critical system, an independent manual
trigger, and a termination function that stops the motors — and puts the tested
deployment altitude in the **device profile**, where a per-type tested value
belongs, not in the show file where an author could edit it.

**Ground-station design is not specified.** DSX describes what a show *is*, not
how a console behaves. The single-action requirement of R1 is stated as the one
explicit exception, and it is marked in the specification as not verifiable by
the conformance suite. Marking it is more honest than quietly implying that a
file check covers it.

**No numerical safety minima are invented.** Separation minima, wind limits and
audience distances are *carried* by the format and *set* by the regulator, the
association or the operator. A file format that legislates numbers competes
with the bodies whose job that is, and loses.

## 5. What is checkable today — and what is not

Stated as a table, because a whitepaper that only lists strengths is marketing.

| Claim | Status today |
|---|---|
| Container safety: entry names, traversal, duplicate entries, decompression limits | **tested** — `conformance/check_container.py`, including a demonstrated signature-bypass via duplicate entries |
| Profile rules (which member is required, optional or forbidden at L0/L1/L2) | **tested** — every cell mutated in a real file and put to the schema (`check_profiles.py`) |
| Reduction of any conforming file to `t,x,y,z,R,G,B` at any frame rate, bit-identically | **partially proven** — six hand-computed vectors pass against a clean-room reference sampler; coverage is not exhaustive (A36) |
| Rotation/wave semantics, loop-seam continuity | **tested**, with one known evaluator limitation (A37) |
| `.dsb` compiled onboard encoding | **not written** — outline only (A2) |
| Fall-containment geometry | **not computable** — disclosure only (A30, R6 above) |
| Single-action abort (R1) | **not file-checkable** — an obligation on the operating system, marked as such (A29) |
| A DSX file that has flown | **none** — no aircraft has flown a DSX file |

Anyone who wants to attack this project should start with that table. It is
where the weaknesses are, and it is published for exactly that reason.

## 6. How this fits the rules that already exist

DSX does not compete with any regulation. It is the **data layer underneath**
them: the same file satisfies different rule sets by carrying the fields each
of them asks about, with jurisdiction-specific limits supplied as overlay
profiles rather than baked into the format.

The Chinese framework is worth spelling out, because it already demands, in
prose, most of what §3 asks for in fields. Under the *Interim Regulations on
the Administration of Unmanned Aircraft Flight* (State Council and Central
Military Commission Order No. 761, in force 1 January 2024) [3]:

| Provision | What it requires | The corresponding DSX data |
|---|---|---|
| Art. 31 ¶2(5) | swarm flight (集群飞行) always requires a flight application under Art. 26 — the exemption for small aircraft in permitted airspace does **not** apply | every show file is, by definition, an application document |
| Art. 27(11) | the application MUST include the **emergency handling procedure** (应急处置程序) | `termination`: the ladder, the fences, link-loss behaviour, RTH feasibility |
| Art. 27(7)(9) | flight route, altitude, speed, airspace boundaries; communication, navigation and surveillance capability | trajectories, geofence geometry, `position_integrity` |
| Art. 32(2) | before flight, verify aircraft state and **keep geofence data up to date** (及时更新电子围栏) | fence geometry as a hashed resource inside the signed file, not a console setting |
| Art. 32(4) | maintain the necessary **safe separation** | `safety.min_separation_m`, one show-wide floor that a per-type profile may raise but never lower |
| Art. 39 ¶3 | **designers and manufacturers** must ensure the aircraft has emergency avoidance and landing functions to avoid or reduce harm | the device profile (`.dsxp`) is where a manufacturer declares exactly that, in a form a show file is checked against |

Article 39 is the interesting one. It places a duty on the *manufacturer*, and
it is currently discharged by assertion, because there is no artefact in which
the manufacturer's declaration and the operator's show can be compared. A
device profile bound by UUID to a show file is that artefact.

Two further observations, at different levels of confidence:

- **Association standards are the live layer.** Art. 6 explicitly assigns
  industry associations the role of strengthening self-regulation by developing
  group standards (团体标准). A group standard for the safety of drone
  formation-flight displays was published in Shenzhen in October 2021 [4]; we
  have not obtained the full text, so we make no claim about its contents. If
  such a standard needs a machine-checkable data annex, that is precisely what
  this project can supply, and it is offered.
- **Air-gapped operation is a design constraint, not a preference.** At least
  one Chinese municipal rule set is reported to require physical separation of
  show-control networks. [^airgap] DSX is therefore specified so that the entire
  toolchain — validation, sampling, sealing, conformance testing — runs offline
  on a local machine. A format whose validity depends on reaching a vendor's
  server cannot be used under such a rule.

The same mapping exists for other jurisdictions and is deliberately not written
here as a comparison table: we have primary sources for some of them and
secondary sources for others, and a table that mixes the two would be the kind
of document this project criticises.

## 7. What we are asking for

The specification is public, the tests run offline, and issue creation is open.
Four concrete asks, in ascending order of effort:

1. **Contradict the ladder.** If the four rungs are wrong, or ordered wrongly,
   or if your system has a fifth, say so — with the case that requires it.
2. **Publish one device profile.** A `.dsxp` file states what a given aircraft
   can do: envelope, separation minimum, light channels, failsafe behaviour,
   tested recovery-deployment altitude if fitted. Two templates and one worked
   example exist. A manufacturer that publishes one makes every show file
   checkable against its own hardware — and discharges Art. 39 with an artefact
   rather than an assertion.
3. **Tell us what the failure chain actually looks like.** Not the marketing
   version: what happens, in order, when the link drops at second 300 of a
   nine-minute show with 800 aircraft over water. Field reports have their own
   issue template.
4. **Run one show through the validator** — from your existing export, via the
   converters, without changing your production pipeline. If the validator is
   wrong about your show, that is a bug report we want more than a compliment.

## 8. The limits of this document

This is a `v0.1` draft written by a small group, published early on purpose.
Nothing in it has flown. Three of its central mechanisms — the compiled onboard
encoding, the fall model, and the question of whether GNSS-integrity policy
should be mandatory at the production profile rather than optional — are open
questions with numbers (A2, A30, A39) rather than solved problems.

The open-questions appendix is part of the specification, not an afterthought
appended to it, and it is deliberately **not translated**, because a stale list
of open problems misinforms worse than no list at all.

If this document is wrong, the useful response is a pull request or an issue,
not a private correction. Everything here is designed to be falsifiable.

---

## References

[1] United States National Transportation Safety Board, preliminary report,
accident **DCA25LA065**, 21 December 2024, Orlando, Florida. Quoted findings:
non-transferred launch parameter file; 7° rotation of show position; geofence
set to 5 m against a 1 m company standard; and the pilot's stated reason for
continuing — "due to the steps involved in pausing the show, recovering
airborne aircraft and the designated flight paths". Report published January
2025; investigation subsequently continued. Retrieved 2026-08-16 via
contemporaneous trade-press reproduction of the report text; the report itself
is public in the investigating authority's docket system.

[2] Public drone display, Hong Kong, 27 October 2018: dozens of aircraft lost
in a single event, attributed in contemporaneous reporting to interference with
satellite navigation, followed by a criminal investigation and a reported claim
of approximately HK$1 million in damage. Retrieved 2026-08-16 from
contemporaneous press and industry reporting. **Secondary sources only** — no
official investigation report was located.

[3] 《无人驾驶航空器飞行管理暂行条例》 (Interim Regulations on the
Administration of Unmanned Aircraft Flight), State Council and Central Military
Commission Order No. 761, promulgated 28 June 2023, in force 1 January 2024.
Articles 6, 26, 27, 31, 32 and 39 as cited. **Primary source**, full text
retrieved 2026-08-16 from the official State Council portal (`gov.cn`).
Translations of article text in this document are informal.

[4] 《无人机编队飞行表演安全规范》, a group standard (团体标准) on the safety of
drone formation-flight displays, published in Shenzhen, October 2021.
**Secondary sources only** — announcement reporting; full text not obtained, no
claim is made about its contents.

[^airgap]: Reported requirement for physically separated show-control networks
    in a Chinese municipal rule set. **Not re-verified for this draft** — cited
    as motivation for an offline-capable design, not as a statement of law.
    This footnote will carry the issuing body, document number and retrieval
    date, or the paragraph will be removed.
