# License for the DSX Specification

| Material | License | SPDX identifier |
|---|---|---|
| Specification text, JSON Schemas, examples, device profiles | **Community Specification License 1.0** | `Community-Spec-1.0` |
| Source code (`tools/`, `conformance/`) and the reference implementations | **Apache License 2.0** | `Apache-2.0` |

The full specification licence text is in
[`licenses/Community-Spec-1.0.md`](licenses/Community-Spec-1.0.md), reproduced
verbatim. The code licence is in [`LICENSE`](LICENSE).

Two files are part of the licence, not commentary on it:

- [`SCOPE.md`](SCOPE.md) — bounds every contributor's and licensee's patent
  commitment (CSL §9.13). Without it, each contributor's commitment shrinks to
  their own contributions.
- [`NOTICES.md`](NOTICES.md) — where implementers accept the licence (CSL
  §2.1.3.3) and where contributors file patent exclusions (CSL §3).

---

## Why this licence and not the obvious ones

A specification needs one thing a software licence does not reliably give it:
**a patent licence that covers implementing the document**, not merely copying
it. Two earlier drafts of this file got that wrong, in opposite directions.
Both errors are recorded here because an implementer's lawyer will reconstruct
them anyway, and finding them undisclosed is worse than finding them admitted.

### First error — OWFa 1.0 as a listed licence

The initial draft named the **Open Web Foundation Agreement 1.0** as the patent
mechanism. OWFa's patent scope is exactly right: §8.6 defines *Permitted Uses*
as "making, using, selling, offering for sale, importing or distributing any
implementation of the Specification".

But OWFa is an **executory agreement** — a document each party signs, with
signature blocks for name, email, date and bound entity. Listing it in a
repository binds nobody. The instrument was right; the delivery mechanism did
not exist.

### Second error — Apache-2.0 as the patent grant for the specification

The correction replaced OWFa with a dual licence, CC BY 4.0 **or** Apache-2.0,
on the reasoning that Apache-2.0 §3 supplies the missing patent grant. That
reasoning does not survive reading §3:

> each Contributor hereby grants to You a perpetual, worldwide, non-exclusive,
> no-charge, royalty-free, irrevocable […] patent license to make, have made,
> use, offer to sell, sell, import, and **otherwise transfer the Work** […]

When the Work is a specification document, the licensed acts are making, using
and transferring **the document**. Implementing what the document describes is
not among them. The Apache Software Foundation's own licensing FAQ confirms the
narrow reading: the licensed claims are those that "read on your contribution or
on the combination of your contribution with the specific Apache product to
which you contributed" — the product being the document itself.

So the dual licence delivered a patent grant that any competent adversary could
argue covers only redistribution of the PDF. That is precisely the assurance a
manufacturer's legal department is asked to rely on, and precisely where it
would fail.

### The instrument that does both jobs

The **Community Specification License 1.0** (Joint Development Foundation, now
part of the Linux Foundation; SPDX `Community-Spec-1.0`) has OWFa's patent scope
and Apache's delivery mechanism.

- **Scope.** §9.8 defines *Implementation* as "making, using, selling, offering
  for sale, importing or distributing any implementation of the Specification" —
  the same operative words as OWFa §8.6.
- **Delivery.** §2.1.3 lets a licensee accept by shipping the licence with their
  distribution or by a pull request to `NOTICES.md`. No signature ceremony.
- **Contribution.** §9.4 makes anyone who contributes a Contributor by that act.
- **Defensive termination** (§2.1.4) and **reciprocal grants between licensees**
  (§2.1.2) — implementers are protected from each other, not only from us.
- **Exclusions** (§3) are possible but must be filed publicly within 45 days,
  so a submarine patent has to surface.
- **Code stays separate.** §4 leaves source code to its own licence; ours is
  Apache-2.0, which is the correct licence for code and carries a patent grant
  whose scope genuinely fits code.

CC BY 4.0 is no longer offered for the specification. It grants no patent rights
at all — §2(b)(2) says so in terms — and offering it alongside a patent-bearing
licence lets an implementer take the copyright and leave the patent peace behind.

---

## What this does not do

**It does not clear third-party patents.** CSL §2.1.5 states this and it is
worth restating: nothing here is an assurance that implementing DSX avoids
somebody else's patent. The grant binds contributors to this repository.

**It does not create a standards body.** A formal IPR policy of the kind W3C or
Khronos operate requires a stewarding legal entity, which this project does not
have. CSL was chosen partly because it is designed to work *before* that entity
exists and to survive the transfer to one — CSL §1.1 expressly contemplates the
Working Group submitting the specification to another standards organisation.
[`GOVERNANCE.md`](GOVERNANCE.md) describes the intended path.

**It does not settle the name.** See [`TRADEMARK.md`](TRADEMARK.md) — the
project holds no registered mark, and the search results there are not
encouraging.

---

## Contributions

By contributing you become a Contributor under CSL §9.4 and grant the patent
licence in §2.1.1 for material within [`SCOPE.md`](SCOPE.md). Code contributions
are additionally under Apache-2.0. Sign-off is by DCO; note that the DCO
certifies origin and does **not** itself convey any licence — the grants come
from CSL §9.4 for specification text and Apache-2.0 §5 for code. See
[`CONTRIBUTING.md`](CONTRIBUTING.md).
