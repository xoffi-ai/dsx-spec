# Governance

## 1. Current state — and the pledge that goes with it

DSX is currently edited by **Xoffi**, published in the `xoffi` GitHub
organisation. That is a starting condition, not a destination.

> **Stewardship pledge.** Once **three independent implementers** (organisations
> other than the initial editor) have shipped a DSX reader or writer, the
> specification, the schemas, the conformance suite and the trademark will be
> transferred to a **neutral steward** — a working group, an industry
> association, or an established standards body (candidates: ASTM F38 /
> committee item WK95240, the Shenzhen UAV Industry Association, or a purpose-
> formed consortium). The reference implementation may remain with its authors.

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

The conformance suite in `conformance/` is normative. The trademark exists for
one purpose: to make "DSX conformant" a statement that can be checked. Passing
implementations may use the badge; the suite and its results are public.
