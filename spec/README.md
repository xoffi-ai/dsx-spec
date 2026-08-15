# DSX Specification — v0.1-draft

**Status:** draft. Not stable. Published for review.
**Date:** 2026-08-15

| # | Chapter | State |
|---|---|---|
| 1 | [Overview and conformance model](01-overview.md) | draft |
| 2 | [Container and manifest](02-container.md) | draft |
| 3 | [Coordinates, altitude and time](03-coordinates-and-time.md) | draft |
| 4 | [Trajectories, light and normative sampling](04-trajectories-and-light.md) | draft |
| 5 | [Device profiles (`.dsxp`)](05-device-profiles.md) | draft |
| 6 | [Payloads and actuators](06-payloads-and-actuators.md) | draft |
| 7 | [Safety and termination](07-safety-and-termination.md) | draft |
| 8 | [Extensions, profiles and versioning](08-extensions-and-versioning.md) | draft |
| 9 | [Conformance](09-conformance.md) | outline |
| 10 | [Waves, sorties, rotation and continuous operation](10-waves-and-rotation.md) | draft |
| A | [Open questions](A-open-questions.md) | living |
| B | [Observed third-party formats](B-observed-formats.md) | living |

## Governing language

**English is the sole authoritative language of this specification.**
Translations are published as a convenience and are **informative, never
normative**. Where a translation and the English text differ — in wording, in a
conformance keyword, or in a numeric value — **the English text governs, and a
reader MUST resolve the question against it.**

This is not boilerplate. A conformance keyword carries the safety obligation:
if `MUST` is rendered as a recommendation in one language, an implementer in
that language builds an aircraft-facing tool that omits a required check and
believes itself conformant. The rule above exists so that such a defect is
always resolvable against a single text rather than argued between two.

Every translated page therefore states the English commit it was made from, and
`conformance/check_translations.py` marks it **stale** as soon as the English
source moves. A stale translation is a known defect with a name, not a silent
one. See [`TRANSLATIONS.md`](../TRANSLATIONS.md).

## Conformance keywords

The key words **MUST**, **MUST NOT**, **REQUIRED**, **SHALL**, **SHALL NOT**,
**SHOULD**, **SHOULD NOT**, **MAY** and **OPTIONAL** are to be interpreted as
described in BCP 14 (RFC 2119 / RFC 8174) when, and only when, they appear in
all capitals.
