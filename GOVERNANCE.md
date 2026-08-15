# Governance

## 1. Current state — and the pledge that goes with it

DSX is currently edited by **Thomas Fleißner**, trading as **FLEITEC**
(sole proprietorship, Austria), and published in the `xoffi-ai` GitHub
organisation. That is a starting condition, not a destination.

The editor is named as a natural person on purpose. "Xoffi" is a brand, and a
brand cannot make the pledge below — the promise to hand over the
specification, the schemas and any marks is only worth something if it is
traceable to someone who can be held to it. It also means the pledge survives
a change of brand and does not survive a change of mind unnoticed.

> **Stewardship pledge.** Once **three independent implementers** (organisations
> other than the initial editor) have shipped a DSX reader or writer, the
> specification, the schemas, the conformance suite and any marks the project
> holds by then will be transferred to a **neutral steward** — a working group,
> an industry
> association, or an established standards body (candidates: ASTM F38 /
> committee item WK95240, the Shenzhen UAV Industry Association, or a purpose-
> formed consortium). The reference implementation may remain with its authors.
>
> **No contact or commitment with any of these bodies exists yet.** They are
> listed as candidates the editor considers appropriate, not as parties who
> have agreed to anything. Naming them is a statement of intent; reading it as
> endorsement would be a misreading this paragraph exists to prevent.

The reason is simple and worth stating plainly: **a format owned by one vendor
is not adopted by that vendor's competitors.** glTF succeeded at Khronos.
OpenTimelineIO succeeded at the Academy Software Foundation. Formats that stayed
in-house stayed in-house.

The same standard is applied to ourselves that we apply to others: a "standard"
whose tiers happen to rank its sponsor's product first is a marketing document.
DSX must be defensible when read by a competitor.

## 2. Decision process

Changes are made by **proposal**, using `proposals/TEMPLATE.md`.

1. **Open** — anyone may open a proposal or an issue. Issue creation is not
   restricted and will not be restricted.
2. **Discussion** — in public, on the issue or PR.
3. **Decision** — by the editors, in writing, with a stated reason. A proposal
   may be *accepted*, *deferred with conditions*, or *declined with reasons*.
   "Closed as not planned" without a reason is not an acceptable outcome.
4. **Landing** — accepted proposals land on `next`. `main` always reflects the
   current published draft.

Partial acceptance is explicitly allowed. A proposal containing five features
may have three accepted and two deferred; contributors are not required to
have their work merged all-or-nothing.

## 3. Attribution

Contributors are **credited by name** in the specification's acknowledgements
and in the changelog entry for the proposal they authored. Attribution is not
discretionary and is not conditional on employment, affiliation or the size of
the contribution.

## 4. Contribution licensing — DCO, not CLA

Contributions are accepted under the **Developer Certificate of Origin 1.1**
(see [`DCO`](DCO)), signed off per commit (`git commit -s`).

There is **no Contributor License Agreement**. A CLA that assigns rights to a
single company would contradict Section 1 and would deter exactly the
independent show producers this project needs.

## 5. Versioning

Semantic versioning, with one hard rule:

- **Minor** versions may only add **optional** fields and new extensions.
- Changing, removing or making a field **required** is a **major** version.
- Readers MUST reject a file whose major version they do not implement.

Drafts are marked `0.x-draft` and carry no stability guarantee. `1.0` will not
be declared until the conformance suite exists and at least two independent
implementations pass it.

## 6. Extensions and maturity

Extensions follow the glTF model:

- `extensions_required` — a reader that does not understand an entry **MUST
  reject the file**.
- `extensions_used` — may be ignored, but **MUST be preserved on re-export**.
  Silently dropping unknown data is a conformance failure.
- Vendor-prefixed names (`XOFFI_`, `KHR_`-style) are registered in the
  extension registry; a vendor prefix does not require permission.
- An extension may be promoted from *vendor* to *multi-vendor* to *ratified*.
  Promotion beyond *vendor* requires **at least one independent
  implementation**.
- Extensions **MUST NOT change the meaning of core fields**. They may only add.

## 7. Regulatory profiles

Jurisdictional requirements are expressed as **overlay profiles**
(`profiles/`), which may make existing fields mandatory and narrow permitted
value ranges. They **MUST NOT** alter the core schema. A new national
regulation therefore produces a new profile — never a breaking change to the
format, and never invalidates existing archived files.

## 8. Conformance and the badge

The conformance suite in `conformance/` is normative. Its purpose is to make
"DSX conformant" a statement that can be checked rather than asserted. The suite
and its results are public, so any claim can be falsified by anyone.

**There is no badge yet, because there is no mark to back one.** A knock-out
search found "DSX" to be a crowded acronym with a live EU word mark covering
software and electronic publications, and the position in China — the market
that matters most here — is unverified. The findings and the consequences are in
[`TRADEMARK.md`](TRADEMARK.md). Until a certification mark exists and is
cleared, conformance rests on the public suite and on the ordinary law against
misrepresenting a product, not on trademark enforcement.

This is stated plainly because the alternative — implying a badge programme that
cannot be enforced — would be the same kind of claim this project criticises
others for making.
