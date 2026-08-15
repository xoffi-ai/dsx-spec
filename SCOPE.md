# Scope

This file has the meaning given to *Scope* in Community Specification License
1.0 §9.13. It bounds the Necessary Claims that each Contributor licenses and
each Licensee receives. **Changes to Scope are not retroactive.**

Read it as a boundary, not as a mission statement. Everything inside is covered
by the patent commitment; everything outside is not.

## In scope

The DSX Working Group develops an open, vendor-neutral **data interchange
format for drone light shows**, together with the schemas, conformance criteria
and reference tooling needed to exchange such data between systems. Specifically:

1. **The container and its structure** — the `.dsx` archive, its manifest, the
   ordering and naming of entries, and the resource files it carries.

2. **Representation of a show over time** — trajectories, colour and intensity
   over time, the coordinate and altitude reference frames in which they are
   expressed, and the timing model that relates them to a show clock.

3. **The normative sampling algorithm** — the deterministic procedure by which
   any conforming file is reduced to per-aircraft samples of time, position and
   colour, and which guarantees that two conforming implementations produce
   identical output from identical input.

4. **Fleet, role, aircraft and sortie modelling** — including waves, rotation
   between sorties, cyclic and open-ended shows, ground service and battery
   logistics as expressed *in the file*.

5. **Declaration of safety-relevant parameters** — separation minima,
   termination behaviour, escalation ladders, return-to-home availability,
   geofences, position-integrity requirements, environmental envelopes and
   ground zones, **as data fields and their semantics**.

6. **Device profiles** (`.dsxp`) — the description of an aircraft's or
   actuator's capabilities, limits, modes and firmware gating.

7. **Provenance and integrity of the file** — content hashing, signing and the
   validation record carried in the archive.

8. **Conformance profiles and the criteria** by which a file or an
   implementation is judged conformant, including the conformance suite in
   `conformance/`.

9. **The extension mechanism** — the `extensions` carrier, vendor prefixes, and
   the rules for must-understand extensions and round-trip preservation.

10. **Media type, file extension and version identifiers** for the above.

## Out of scope

The following are outside Scope. No patent commitment is made for them, and
contributions concerning them are not licensed under this Working Group's
patent terms:

- **Flight control, guidance, navigation and state estimation.** DSX states what
  a show *is* and what limits apply to it. How an aircraft flies, holds
  position, estimates its state or executes a landing is the manufacturer's.
- **Collision avoidance and trajectory deconfliction algorithms.** DSX carries
  the separation minimum as a declared value; computing or enforcing it is not
  in scope.
- **Radio protocols, telemetry links, command-and-control, encryption of the
  flight channel, and time synchronisation on the wire.** DSX describes what the
  show clock *means*, not how it is distributed.
- **Choreography authoring, transition solving, formation generation, path
  planning and any creative or optimisation tooling** that produces show content.
- **Ground infrastructure**: charging hardware, battery chemistry and management,
  launch pads, cases and handling equipment.
- **Aircraft, actuator, pyrotechnic, parachute and payload hardware**, and their
  internal control.
- **Operational procedures, crew roles, training, licensing and regulatory
  compliance workflows.** Regulatory profiles referenced by DSX are external
  overlay documents; their content is not in scope.
- **Rendering, simulation and visualisation techniques**, beyond the requirement
  that the normative sampling algorithm be reproduced faithfully.
- **Any other file format**, including the formats DSX converts to or from.
  Observations about third-party formats recorded in this repository are
  descriptive and confer no rights in those formats.

## Note on the safety chapters

Sections of the specification that concern termination, geofencing, integrity
and ground safety are in scope **as data definitions only** — the names,
types, units, ranges and meanings of fields, and the consistency rules a
validator applies to them. Methods of achieving the described behaviour in an
aircraft are out of scope, as listed above. This split is deliberate: DSX must
be implementable by every manufacturer without any of them conceding rights in
how their aircraft actually flies.
