# Contributing to DSX

**Short version:** open an issue, say what breaks in your daily work, sign off
your commits with `git commit -s`, and you will be credited by name.

## Who this is for

Show producers, pilots, safety officers, manufacturers, software vendors,
regulators. Practical field knowledge is treated as evidence — a report of what
a specific aircraft actually does is more valuable here than an opinion about
what it should do.

If you find a statement in the specification that is wrong, saying so is a
contribution. Sections that cannot be defended get corrected, not defended.

## Ways to contribute

| Contribution | Where |
|---|---|
| Something is wrong / missing / unclear | open an **issue** |
| A concrete change to the format | `proposals/` — see `TEMPLATE.md` |
| A device profile for hardware you operate | `devices/`, as `vendor@model@revision.dsxp` |
| A regulatory overlay for your jurisdiction | `profiles/`, with a citation to the source document |
| A conformance test case | `conformance/` |

## Rules that are not negotiable

1. **Sign off your commits** (`git commit -s`) — Developer Certificate of
   Origin 1.1. No CLA.
2. **Cite sources for factual claims.** Numbers in this repository — separation
   distances, wind limits, latencies, altitude thresholds — must be traceable
   to a document, a datasheet, or a described measurement. An unsourced number
   is worse than a missing one. `null` meaning *unknown* is a valid, documented
   state; an invented default is not.
3. **Clean-room boundary.** If you have read the source code of a GPL-licensed
   drone show implementation, you may contribute to the *specification* but not
   to the corresponding Apache-2.0 reference implementation. State which side
   you are on in your pull request. See [`NOTICE-PROVENANCE.md`](NOTICE-PROVENANCE.md).
4. **No confidential material.** Do not contribute anything covered by an NDA,
   and do not paste vendor documentation that is not public. Describe the
   observed behaviour instead, and say that the source is not public.
5. **Safety-relevant changes require a rationale**, not just a diff: what
   failure does this prevent, and how would a validator check it?

## Device profiles

A device profile describes what an aircraft or payload can do. Please:

- use a **stable UUID** for `device_type_id` — it must not change across
  revisions of the same model;
- write `null` for values you do not know, rather than guessing;
- record where each number came from (`"source": "datasheet 2024-06"` /
  `"source": "measured"`), especially where vendor documentation is
  self-contradictory — this happens more often than one would expect;
- never widen a limit to make a show validate.

## Attribution

Every accepted proposal names its author in the changelog and in the
acknowledgements. If you would prefer to be credited under an organisation
name, or not at all, say so in the pull request.
