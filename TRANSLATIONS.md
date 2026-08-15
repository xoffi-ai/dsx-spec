# Translations

DSX is published in English, Chinese (Simplified), Japanese, Korean, German and
Spanish. This file states how that is done without turning a convenience into a
hazard.

## 1. English governs

**English is the sole authoritative language.** Every other language is
informative. Where they differ, the English text governs.

The reason is specific to this document rather than general legal caution. A
DSX conformance keyword is a safety obligation: `MUST` in §7 is the difference
between a termination path that exists and one that does not. If a translation
renders it as a recommendation — and `should` / `sollte` / `应该` / `debería`
are all one careless step from `must` — an implementer working in that language
ships an aircraft-facing tool that omits a required check and believes itself
conformant. Nobody discovers this until a show behaves differently than its
file promised.

One authoritative text means such a disagreement always has an answer.

## 2. Every translated page says so

Each translated file **MUST** carry the governing-language notice, in its own
language and in English, above the content. `conformance/check_translations.py`
rejects a translation that omits it. A notice that can be dropped by whoever is
in a hurry is not a safeguard.

## 3. Every translation names the English commit it was made from

Each translated file carries a header block naming its source file and the
**SHA-256 of that source's bytes** at translation time:

```html
<!-- dsx-translation
source: spec/07-safety-and-termination.md
source_sha256: 3f2a…
language: zh-Hans
translated: 2026-08-16
translator: …
-->
```

When the English file changes, the hash no longer matches and the translation
is **stale**. `check_translations.py` reports this by name.

This is the part that most multilingual specifications get wrong. Translations
are made once, the source moves on, and three years later two languages
describe different formats with no indication which is current. Here, drift is
detected mechanically rather than noticed by a reader who has already been
misled.

**Stale is a WARN in CI, not an error.** Making it an error would block every
English correction until six translations catch up, and a check that blocks
ordinary work is a check that gets switched off. It is an error on the
**published site**: a stale page MUST render its staleness banner, and the site
build fails if it cannot.

## 4. Conformance keywords are not translated silently

In translated text, a BCP 14 keyword **MUST** be followed by the English term in
parentheses on first use in each section — `必须 (MUST)`, `muss (MUST)`,
`debe (MUST)`. The keyword is a term of art, not a word; a reader checking
against the English text needs to find it there.

## 5. What is translated, and in what order

| Priority | Scope | Why |
|---|---|---|
| 1 | landing page, README, §1 Overview | what a newcomer reads before deciding to care |
| 2 | §7 Safety and termination | the chapter whose misreading has physical consequences |
| 3 | §2, §3, §4 | what an implementer needs to write a reader |
| 4 | remaining chapters | completeness |

Appendix A (open questions) is **not** translated. It changes with almost every
commit, and a stale list of open questions actively misinforms.

## 6. Languages

| Code | Language | Status |
|---|---|---|
| `en` | English | **authoritative** |
| `zh-Hans` | 中文（简体） | planned |
| `ja` | 日本語 | planned |
| `ko` | 한국어 | planned |
| `de` | Deutsch | planned |
| `es` | Español | planned |

A language is listed as `planned` until at least the priority-1 scope exists in
it. Listing a language the project cannot maintain is a promise it will break.

## 7. Machine translation

Machine translation is permitted as a **starting point** and must be recorded
as such in the `translator` field (`machine, reviewed by …` or `machine,
unreviewed`). An unreviewed machine translation **MUST NOT** be published for
§7, and the site marks any unreviewed page accordingly.

Being explicit about this is better than the alternative, which is not that the
project avoids machine translation — it is that nobody can tell which pages
were.
