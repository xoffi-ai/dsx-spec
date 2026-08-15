#!/usr/bin/env python3
"""Translation integrity: TRANSLATIONS.md sections 1-4.

A translated safety specification fails in two ways that a reader cannot see:
the governing-language notice gets dropped, and the English source moves on
while the translation stays behind. Both are mechanical, so both are checked
here rather than left to review.

  ERROR  malformed header, unknown language, missing or vanished source,
         missing governing-language notice, unreviewed machine translation
         of a safety chapter
  WARN   stale (source hash moved), untranslated conformance keywords

Run:  python3 conformance/check_translations.py
"""
from __future__ import annotations

import hashlib
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TRANSLATIONS = ROOT / "translations"

LANGUAGES = {"zh-Hans", "ja", "ko", "de", "es"}

# Section 2: the notice must be present and machine-findable.
NOTICE_MARKER = "dsx-governing-language"

# Section 5: appendix A is deliberately not translated.
NOT_TRANSLATED = {"A-open-questions.md"}

# Section 7: an unreviewed machine translation of this chapter is refused.
SAFETY_CRITICAL = {"07-safety-and-termination.md"}

HEADER_RE = re.compile(r"<!--\s*dsx-translation\s*(.*?)-->", re.S)
KEYWORDS = ("MUST NOT", "MUST", "SHALL NOT", "SHALL", "SHOULD NOT", "SHOULD",
            "REQUIRED", "OPTIONAL", "MAY")

errors: list[str] = []
warnings: list[str] = []
ok: list[str] = []


def sha256_file(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def parse_header(text: str) -> dict[str, str] | None:
    m = HEADER_RE.search(text)
    if not m:
        return None
    out = {}
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        k, v = line.split(":", 1)
        out[k.strip()] = v.strip()
    return out


def check_file(path: pathlib.Path) -> None:
    rel = path.relative_to(ROOT).as_posix()
    text = path.read_text(encoding="utf-8")

    hdr = parse_header(text)
    if hdr is None:
        errors.append(f"{rel}: no <!-- dsx-translation --> header block")
        return

    missing = [k for k in ("source", "source_sha256", "language", "translator")
               if k not in hdr]
    if missing:
        errors.append(f"{rel}: header is missing {', '.join(missing)}")
        return

    lang_dir = path.relative_to(TRANSLATIONS).parts[0]
    if lang_dir not in LANGUAGES:
        errors.append(f"{rel}: {lang_dir!r} is not a declared language")
        return
    if hdr["language"] != lang_dir:
        errors.append(
            f"{rel}: header says language {hdr['language']!r} but the file "
            f"lives under {lang_dir!r}"
        )
        return

    src = ROOT / hdr["source"]
    if not src.is_file():
        errors.append(f"{rel}: source {hdr['source']!r} does not exist")
        return
    if src.name in NOT_TRANSLATED:
        errors.append(
            f"{rel}: {src.name} is on the do-not-translate list "
            f"(TRANSLATIONS.md section 5) -- it changes too often to stay true"
        )
        return

    # --- section 2: the notice ---
    if NOTICE_MARKER not in text:
        errors.append(
            f"{rel}: no governing-language notice (marker {NOTICE_MARKER!r})"
        )
        return

    # --- section 7: unreviewed machine translation of a safety chapter ---
    translator = hdr["translator"].lower()
    unreviewed = "machine" in translator and "reviewed by" not in translator
    if unreviewed and src.name in SAFETY_CRITICAL:
        errors.append(
            f"{rel}: unreviewed machine translation of {src.name}, which "
            f"TRANSLATIONS.md section 7 forbids publishing"
        )
        return

    # --- section 3: staleness ---
    actual = sha256_file(src)
    declared = hdr["source_sha256"]
    if declared != actual:
        warnings.append(
            f"{rel}: STALE -- {hdr['source']} has changed since translation "
            f"(declared {declared[:12]}…, actual {actual[:12]}…)"
        )
        return

    # --- section 4: keywords carry the English term ---
    body = HEADER_RE.sub("", text)
    if any(re.search(rf"\b{re.escape(k)}\b", body) for k in KEYWORDS):
        pass
    elif re.search(r"\b(必须|应当|muss|debe|해야|しなければ)\b", body):
        warnings.append(
            f"{rel}: uses a conformance keyword without the English term in "
            f"parentheses (TRANSLATIONS.md section 4)"
        )
        return

    if unreviewed:
        warnings.append(f"{rel}: unreviewed machine translation")
        return

    ok.append(rel)


def selftest() -> int:
    """Prove each error class actually fires.

    A checker whose failure path is never exercised is indistinguishable from
    one that returns success unconditionally, and it is trusted for exactly as
    long as nobody looks.
    """
    import tempfile

    global ROOT, TRANSLATIONS, errors, warnings, ok

    real = (ROOT, TRANSLATIONS)
    cases = [
        ("missing header",      "no <!-- dsx-translation --> header",
         "just text, no header\n"),
        ("missing field",       "is missing",
         "<!-- dsx-translation\nsource: spec/x.md\nlanguage: de\n-->\nx\n"),
        ("unknown language",    "not a declared language", None),   # built below
        ("vanished source",     "does not exist",
         "<!-- dsx-translation\nsource: spec/gone.md\nsource_sha256: 00\n"
         "language: de\ntranslator: h\n-->\n<!-- dsx-governing-language -->\nx\n"),
        ("do-not-translate",    "do-not-translate list",
         "<!-- dsx-translation\nsource: spec/A-open-questions.md\n"
         "source_sha256: 00\nlanguage: de\ntranslator: h\n-->\nx\n"),
        ("missing notice",      "no governing-language notice",
         None),
        ("unreviewed safety",   "section 7 forbids",
         None),
    ]

    failures = []
    for name, expect, body in cases:
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            (root / "spec").mkdir()
            src = root / "spec" / "x.md"
            src.write_text("english source\n")
            (root / "spec" / "A-open-questions.md").write_text("a\n")
            digest = sha256_file(src)

            lang = "de"
            if name == "unknown language":
                lang = "kl"
                body = (f"<!-- dsx-translation\nsource: spec/x.md\n"
                        f"source_sha256: {digest}\nlanguage: kl\ntranslator: h\n-->\n"
                        f"<!-- dsx-governing-language -->\nx\n")
            elif name == "missing notice":
                body = (f"<!-- dsx-translation\nsource: spec/x.md\n"
                        f"source_sha256: {digest}\nlanguage: de\ntranslator: h\n-->\nx\n")
            elif name == "unreviewed safety":
                safety = root / "spec" / "07-safety-and-termination.md"
                safety.write_text("safety\n")
                body = (f"<!-- dsx-translation\nsource: spec/07-safety-and-termination.md\n"
                        f"source_sha256: {sha256_file(safety)}\nlanguage: de\n"
                        f"translator: machine, unreviewed\n-->\n"
                        f"<!-- dsx-governing-language -->\nx\n")

            d = root / "translations" / lang / "spec"
            d.mkdir(parents=True)
            (d / "x.md").write_text(body)

            ROOT, TRANSLATIONS = root, root / "translations"
            errors, warnings, ok = [], [], []
            check_file(d / "x.md")

            hit = [e for e in errors if expect in e]
            if hit:
                print(f"PASS  {name:<20} {hit[0].split(': ', 1)[-1][:60]}")
            else:
                print(f"FAIL  {name:<20} expected {expect!r}, got {errors or 'nothing'}")
                failures.append(name)

    ROOT, TRANSLATIONS = real
    errors, warnings, ok = [], [], []
    print(f"\n{len(cases) - len(failures)}/{len(cases)} self-tests pass")
    return 1 if failures else 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()

    print("DSX translation integrity (TRANSLATIONS.md)\n")

    if not TRANSLATIONS.is_dir():
        print("no translations/ directory yet -- nothing to check")
        return 0

    files = sorted(p for p in TRANSLATIONS.rglob("*.md") if p.is_file())
    for p in files:
        check_file(p)

    for r in ok:
        print(f"OK      {r}")
    for w in warnings:
        print(f"WARN    {w}")
    for e in errors:
        print(f"ERROR   {e}")

    # --- coverage, per language ---
    spec_files = sorted(p.name for p in (ROOT / "spec").glob("*.md")
                        if p.name not in NOT_TRANSLATED)
    print(f"\nCoverage ({len(spec_files)} translatable spec files)")
    for lang in sorted(LANGUAGES):
        d = TRANSLATIONS / lang / "spec"
        have = sorted(p.name for p in d.glob("*.md")) if d.is_dir() else []
        state = "planned" if not have else f"{len(have)}/{len(spec_files)}"
        print(f"  {lang:<9} {state:<8} {', '.join(have) if have else ''}")

    print(f"\n{len(ok)} ok, {len(warnings)} warning(s), {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
