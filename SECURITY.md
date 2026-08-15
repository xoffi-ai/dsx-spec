# Reporting a security or safety issue

DSX describes files that decide where aircraft fly and when motors stop. A
defect in the specification, the schemas or the conformance suite can therefore
have physical consequences, and we would rather hear about it early and be
wrong than late and be right.

## What to report

- A rule that permits a file which is unsafe to fly.
- A check that passes when it should fail (a false green is worse than a red).
- A defect in `tools/dsx_seal.py` that would let an archive be altered without
  breaking `content_hash` or the signature.
- Anything in the specification that a reasonable implementer could read two
  ways, where one of the readings is dangerous.

## How

Open a GitHub issue for anything already public. For a report that should not
be public first, use GitHub's **private vulnerability reporting** on this
repository. We aim to acknowledge within five working days.

## Scope note on the example key

The bundled examples are signed with a key derived from a seed printed in
`tools/dsx_seal.py`. It is public by design and guarantees nothing; the
conformance suite prints a WARN whenever it sees it. Reports that it is
"compromised" are correct and expected.
