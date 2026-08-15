# Provenance and Separation-of-Roles Notice

> **A note on terminology.** This process is deliberately **not** called a
> clean room. In a clean room, the people writing the specification have never
> seen the original code. Section 2 states plainly that GPL-licensed source
> code *was* read to establish externally observable facts. What this project
> practises is a **one-way separation of roles**: those who have read that code
> may write specification text, but may not write the Apache-2.0 reference
> implementation. Calling this a clean room would misdescribe it — and a
> provenance notice that misdescribes its own process is worthless.

This document records how the DSX specification was developed, what sources
were consulted, and what boundaries apply to contributors. It exists so that
the question "did you copy this from an existing implementation?" has a
written, verifiable
answer *before* anyone asks it.

## 1. Legal basis

A **file format is not protectable by copyright**. Copyright subsists in the
*expression* — source code, documentation text, diagrams — not in the layout of
bytes in a file or the names of fields. Observing, describing and
re-implementing a format is lawful. Copying the code that implements it is not.

DSX is built on that distinction, deliberately and narrowly.

## 2. What was observed

The following were examined in order to understand the state of the art:

- **Publicly published specifications**: VVIZ, WPML, GDTF / MVR (DIN SPEC
  15800 / 15801), glTF 2.0, OpenTimelineIO, ASTM F3322, MAVLink message
  definitions.
- **Publicly distributed test fixtures**: the `.skyb` fixture files shipped in
  a publicly readable GPL-licensed reference library, cited by SHA-256 in
  Appendix B.1 so the observation can be reproduced by anyone who has or
  obtains the same bytes. These were parsed to confirm container framing,
  block typing and event encoding. Observations recorded: magic marker, version
  byte, feature byte, optional CRC32, `uint8 type | uint16 LE length | body`
  framing, non-fixed block ordering, and the 10-byte event record layout.
- **Publicly readable source code of GPL-licensed projects**, read for the sole
  purpose of understanding externally observable data layouts and hardware
  constraints (e.g. that one exporter emits at a fixed 30 Hz and another at a
  fixed 5 Hz — facts about hardware, not expression).
- **Vendor documentation, datasheets and public regulatory texts.**

## 3. What was NOT done

- **No source code was copied, translated, transliterated or adapted** from any
  GPL-licensed project into this specification or into any reference
  implementation published alongside it.
- **No encoder, decoder, solver or scheduling algorithm** was reproduced from
  another project's implementation.
- **No confidential material** — no NDA-covered documentation, no leaked
  specification, no decompilation of proprietary binaries — was used.
- DSX **does not claim compatibility with, endorsement by, or derivation from**
  any third-party format or product. All third-party names are used
  nominatively, to identify the systems being interoperated with.

## 4. Rule for contributors

> **If you have read the source code of a GPL-licensed drone show
> implementation, you may contribute to the *specification*, but you must not
> contribute to the Apache-2.0 reference implementation** of the corresponding
> component.

The separation is between *knowing how a format is laid out* (a fact, freely
usable) and *knowing how someone else's code expresses it* (protected).
Contributors are asked to state, in their pull request, which side of that line
they are on. See `CONTRIBUTING.md`.

## 5. Third-party trademarks

All product names, format names and company names referred to anywhere in this
repository are the property of their respective owners. Their use is nominative
and descriptive only — to identify a format or to cite a source, never to imply
endorsement, affiliation or a defect in anyone else's product.

This project does not publish comparative claims about identifiable third-party
products, and does not name any third party anywhere in the specification.
Where a source had to be cited so a reader can reproduce an observation
(Appendix B), the citation is a SHA-256 per file, generically described —
sufficient to prove which bytes were examined to anyone who already has them,
without identifying where they came from.

## 6. Amendments

Any future concern about the provenance of a specific section should be raised
as an issue. Sections whose provenance cannot be defended will be rewritten
from first principles or removed — not defended.
