# Trademark status and naming policy

**Status: the project holds no registered trademark anywhere, needs none to
publish the specification under the name DSX, and has no plan to apply for one.
The only place a mark would do real work is the conformance badge, and that is
a later decision with a different name.**

Search date: 2026-08-15. Searcher: project maintainers, not counsel. This is a
knock-out search, not a clearance opinion.

---

## 0. Does a file format need a trademark? No.

This document originally overstated the risk, and the overstatement came from
one omission: it never distinguished **trademark use** from **technical use**.

A trademark is infringed by using a sign **in the course of trade as an
indicator of commercial origin**, in a way likely to confuse the relevant
public. Naming a data format, defining a file extension and publishing a
specification is none of those things. It is a technical designation, the same
way `.zip`, `.json`, `.csv`, `.png` and `.yaml` are — none of which is anyone's
trademark, and all of which coexist with unrelated registrations of the same
letters.

Concretely, the following carry **no meaningful trademark exposure**:

- calling the format DSX and the extension `.dsx`
- registering the media type `application/vnd.dsx+zip`
- schema `$id`s under `urn:dsx:…`
- naming the reference tooling `dsx-tools`, because referring to a format by its
  name is descriptive/nominative use, not branding
- a third party writing "imports and exports DSX" on their product

Exposure begins only where the letters are used **as a brand for goods or
services sold in trade** — a product marketed as "DSX", a paid certification
sold under that name, a logo positioned as a badge of origin. That is a
different activity from publishing a standard, and this project is not doing it.

The findings in §1 are therefore recorded as **background**, not as an
obstacle. They matter for one decision only: whether the project could ever
*own* the letters DSX. It cannot, and it does not need to.

---

## 1. What was found (background)

### 1.1 Live registrations for the bare word "DSX"

| Jurisdiction | Number | Owner | Classes | Relevance |
|---|---|---|---|---|
| **EU** | EUTM 017940461 | DSX Holdings Limited (Isle of Man) | **9, 35, 36, 42** | **direct conflict** |
| **US** | Reg. 2679754 (Ser. 76179804) | DSX Access Systems, Inc. (Dallas, TX) | 9 | serious |
| EU | EUTM 018012905 | Gerdes Holding GmbH & Co. KG (Lüneburg) | 11 | none (water heaters) |

**EUTM 017940461 is the problem.** It is a **word mark** — not a logo — filed
2018-08-08, registered 2019-02-19, still live. Its Class 9 specification begins
"Computers, computer software; computer programs" and includes "electronic
publications"; Class 42 begins "Computer programming". The only carve-out is for
music production. A specification document distributed as an electronic
publication, and the tooling that reads it, fall squarely inside that wording.

**US Reg. 2679754** was filed 2000, registered 2003, and has been renewed twice,
most recently 2023-01-20. Sections 8 and 15 were accepted in 2008, which makes
it **incontestable**. Goods are access-control equipment "and computers at
access locations and central monitoring stations". Two mitigating details: it is
a composite mark (drawing code 3 — design plus letters), and the goods are a
different field from drone shows. Neither removes the Class 9 overlap.

### 1.2 Other DSX marks and uses encountered

Not exhaustively verified, but enough to establish a crowded field: Evident
Corporation (the Olympus microscope spin-off, `DSX1000` digital microscopes,
USPTO Ser. 99415548); Cognis IP Management GmbH (Ser. 74449310); an older US
Reg. 1726931; "DSX TUNING"; "dsX flex-pack" (WIPO IR 1173413); and Fluke
Networks' `DSX-5000` / `DSX-8000` CableAnalyzer line, which is widely known in
exactly the technical-buyer population DSX would address.

### 1.3 "DSX" is partly generic in an adjacent industry

**DSX-1** and **DSX-3** are long-established generic terms in telecommunications
— *digital signal cross-connect* — used descriptively by ADC, Telect and others.
This cuts both ways. It weakens everyone's mark, including any we might obtain,
and it means the letters alone will never be strongly distinctive.

### 1.4 The file extension `.dsx` is already in use

At least four unrelated formats use it: DAZ Studio Content Install Info, DAZ
Install Manifest, DAZ Product Supplement Install, and Vivid DiffSet. IBM
Rational Publishing Engine is also reported to open `.dsx` files.

This is a nuisance, not a blocker — extension collisions are normal (`.bin`,
`.dat`, `.prj`) and are resolved by magic bytes, which DSX has. It does mean
`.dsx` cannot be claimed as exclusively ours.

### 1.5 Namespaces

| Namespace | `dsx` | Alternatives |
|---|---|---|
| GitHub org/user | **taken** | `dsx-format` free, `opendsx` free |
| PyPI | **taken** | `dsx-tools`, `dsx-spec` free |
| npm | **taken** | `dsx-tools` free |
| Domain | `dsx.org` taken (since 2000), `dsx.dev` taken (2024), `odsx.org` taken (2025) | **`dsx-format.org`, `opendsx.org`, `dsxformat.org`, `dsx.io` free** |
| IANA media type | free — no `dsx` registration exists | — |

The URN scheme currently used for schema `$id` (`urn:dsx:schema:0.1:…`) is
unaffected by all of this: URNs in an unregistered namespace assert no rights
and collide with nothing. That was the right call and it stays.

---

## 2. What was NOT checked

**China — not verified.** CNIPA's register was not reachable by the means
available here. This is the largest gap in the search. It is **not** a blocker
on publishing, for the reasons in §0 — it becomes relevant only if the project
later wants to own a name in China:

- China is **first-to-file** with no use requirement to register, and trademark
  squatting on foreign brands is routine.
- CNIPA examines **relative grounds on its own motion** — unlike EUIPO. A prior
  Chinese registration for DSX in class 9 would block an application outright,
  not merely expose it to opposition.
- Most of the manufacturers this project needs are Chinese, and the intended
  steward is a Shenzhen industry association. A Chinese conflict is not a
  peripheral risk here; it is the core market.

Also unchecked: UK (separate register post-Brexit), Japan, Korea, Singapore,
UAE, and Madrid international registrations designating any of these.

**Source caveat.** The register data above came from commercial aggregators
(TrademarkElite), because the official interfaces — USPTO TSDR, EUIPO eSearch,
WIPO Global Brand Database — were unreachable or JavaScript-only from this
environment. Aggregator data is generally accurate but is not the register.
Anything relied on commercially must be confirmed against the official source.

---

## 3. What follows

### 3.1 Registering "DSX" as our mark is not a viable plan

In the EU, an application would face EUTM 017940461. EUIPO does not refuse on
relative grounds by itself, so the application would probably proceed to
registration — and then sit exposed to an opposition or cancellation the owner
can bring at a time of their choosing, most likely the moment DSX becomes worth
attacking. That is a worse position than having no mark, because it invites
reliance.

In the US, an application in Class 9 would likely draw a §2(d) refusal citing
the incontestable registration.

A three-letter mark in a field this crowded, partly generic in an adjacent
industry, would in any case have a narrow scope of protection — too narrow to do
the one job we need a mark for.

### 3.2 The one job a mark actually has to do

Not to own the format name. Anyone may implement DSX; that is the point. The
mark exists so that **"DSX conformant" cannot be claimed by something that is
not** — the conformance badge is the project's only enforcement mechanism, and
an unenforceable badge is worse than none.

### 3.3 The Wi-Fi precedent

IEEE 802.11 is the specification: an unprotectable technical designation that
anyone may name. **Wi-Fi** is a coined word, owned by the Wi-Fi Alliance and
registered as a certification mark, and it is what actually governs who may
claim compliance. The technical name was left unprotected on purpose; the
certification brand was invented to be strong.

The same split fits here:

| Layer | Name | Protection |
|---|---|---|
| Format / extension / media type / URN | **DSX** | none claimed; treated as a technical designation |
| Reference tooling | `dsx-tools` | none needed |
| Vendor extension prefix | `XOFFI_*` | Xoffi's own name, unaffected by any of this |
| **Conformance programme and badge** | **to be coined — a distinctive word, cleared before use** | **certification mark, registered in EU + US + CN** |

A certification mark is the correct instrument and is a different animal from an
ordinary trademark: its owner must not itself sell the certified goods, must
apply the standard even-handedly to all comers, and the mark is refused or
cancelled if applied discriminatorily. That fits a neutral steward exactly, and
it makes the neutrality claim in `GOVERNANCE.md` legally enforceable rather than
merely stated.

### 3.4 Recommended actions

**Now, before publishing:**

1. **Keep the name DSX and do nothing else.** Per §0, publishing a
   specification under a technical designation is not trademark use, and the
   registrations in §1 are not enforceable against it. The cost of proceeding
   is zero and there is nothing to buy.
2. **Do not assert trademark rights in project documents.** Corrected in this
   repository as of this commit; see §4.
3. **Register `dsx-format.org`** (free as of the search date) — a domain, not a
   mark. Cheap, and it stops someone else from taking the obvious home of the
   documentation.

**Later, when the conformance programme becomes real:**

4. **Coin the certification-programme name separately** and clear *that* name
   properly — a coined word in an empty field is cheap to clear and strong to
   own, which is the opposite of the situation with "DSX". This is the only
   registration the project should ever pay for.
5. **Run a Chinese knock-out search** at that point, in classes 9 and 42, for
   the coined name. Searching "DSX" itself is optional and mostly of academic
   interest — the project will not be applying for it either way. The one
   residual reason to look is squatting: if a Chinese party holds DSX in class
   9, a manufacturer might get nervous about putting the word in its own
   marketing, which is a soft commercial friction, not a legal exposure for
   this project.

---

## 4. Naming policy in force today

Because the project owns no mark, it makes no trademark claim, and no document
in this repository should imply otherwise. What it *can* do rests on other
ground:

- **Anyone may implement the specification.** The licence says so and nothing
  here limits it.
- **The conformance suite is the test.** `conformance/` is normative and
  machine-runnable. A claim of conformance that the suite contradicts is a false
  statement about a product, actionable as misleading advertising or unfair
  competition in most jurisdictions regardless of trademark ownership.
- **Attribution is required by licence, not by mark.** CSL §1.2 requires
  derivative works to name the material, its version and its source.
- **Forks must not misrepresent themselves.** A modified specification presented
  as the original is a licence and attribution matter under CSL §1.2, and a
  factual misrepresentation. It is not, today, a trademark matter.

This section is deliberately narrower than the paragraph it replaces, which
asserted rights in "the name DSX, the DSX logo, or the DSX conformance badge".
None of those rights exist yet.
