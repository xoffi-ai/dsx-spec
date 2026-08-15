#!/usr/bin/env python3
"""Container conformance: spec 2.1.1 (entry names) and 2.1.2 (resource limits).

The other suites all assume the archive has already been opened safely. This
one tests the step before that, including the reason 2.1.1 C4 is REJECT and not
a tidiness rule: with duplicate entry names, two conforming readers of the same
signed archive disagree about what was signed.

Run:  python3 conformance/check_container.py
"""
from __future__ import annotations

import io
import json
import pathlib
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import dsx_container  # noqa: E402

results: list[tuple[bool, str, str]] = []


def record(ok: bool, name: str, detail: str = "") -> None:
    results.append((ok, name, detail))


def zip_bytes(entries: list[tuple[str, bytes]], *, modes: dict[str, int] | None = None,
              compress: bool = False) -> bytes:
    """Build a ZIP verbatim -- duplicates and odd names included, on purpose."""
    buf = io.BytesIO()
    method = zipfile.ZIP_DEFLATED if compress else zipfile.ZIP_STORED
    with zipfile.ZipFile(buf, "w", method) as zf:
        for name, data in entries:
            zi = zipfile.ZipInfo(name)
            zi.compress_type = method
            if modes and name in modes:
                zi.external_attr = modes[name] << 16
            zf.writestr(zi, data)
    return buf.getvalue()


def expect_reject(name: str, entries, *, rule: str, mentions: str = "", modes=None,
                  compress=False, limits=None) -> None:
    """The archive must be rejected, for the stated rule, naming the entry.

    `mentions` is not decoration. Without it a check can pass because some
    *other* entry tripped the same rule -- which is how the first version of
    the C6 test passed while the implementation was rejecting every ordinary
    archive for an unrelated reason.
    """
    tmp = ROOT / ".tmp-container-test.dsx"
    tmp.write_bytes(zip_bytes(entries, modes=modes, compress=compress))
    try:
        problems = dsx_container.check_zip(tmp, limits)
    finally:
        tmp.unlink(missing_ok=True)
    hit = [p for p in problems if p.startswith(rule) and (not mentions or mentions in p)]
    if hit:
        record(True, name, hit[0][:110])
    elif mentions and any(p.startswith(rule) for p in problems):
        other = next(p for p in problems if p.startswith(rule))
        record(False, name, f"{rule} fired, but not for {mentions!r}: {other[:60]!r}")
    elif problems:
        record(False, name, f"rejected, but for {problems[0][:70]!r}, not {rule}")
    else:
        record(False, name, "ACCEPTED -- rule does not bite")


MANIFEST = json.dumps({"dsx": "0.1", "profile": "L0"}).encode()

# --- 2.1.1 C1-C3: extraction must not escape the archive -----------------
expect_reject("C1 absolute path rejected",
              [("/etc/cron.d/x", b"x"), ("show.json", MANIFEST)], rule="C1", mentions="/etc/cron.d/x")
expect_reject("C1 backslash separator rejected",
              [("traj\\a.json", b"{}"), ("show.json", MANIFEST)], rule="C1",
              mentions="traj")
expect_reject("C1 drive prefix rejected",
              [("C:/windows/x", b"x"), ("show.json", MANIFEST)], rule="C1", mentions="C:/windows/x")
expect_reject("C1 UNC prefix rejected",
              [("\\\\server\\share\\x", b"x"), ("show.json", MANIFEST)], rule="C1")
expect_reject("C2 path traversal rejected",
              [("../../etc/passwd", b"x"), ("show.json", MANIFEST)], rule="C2", mentions="etc/passwd")
expect_reject("C2 traversal mid-path rejected",
              [("traj/../../x", b"x"), ("show.json", MANIFEST)], rule="C2", mentions="traj/../../x")
expect_reject("C3 control character rejected",
              [("traj/a\nb.json", b"{}"), ("show.json", MANIFEST)], rule="C3", mentions="traj")

# --- 2.1.1 C4/C5: the signature bypass -----------------------------------
expect_reject("C4 duplicate entry rejected",
              [("show.json", MANIFEST), ("show.json", MANIFEST)], rule="C4")
expect_reject("C5 case-fold collision rejected",
              [("show.json", MANIFEST), ("Show.json", MANIFEST)], rule="C5")

# --- 2.1.1 C6: no symlinks -----------------------------------------------
expect_reject("C6 symlink entry rejected",
              [("show.json", MANIFEST), ("geo/fence.json", b"../../../etc/passwd")],
              rule="C6", mentions="geo/fence.json", modes={"geo/fence.json": 0o120777})

# --- 2.1.2 limits ---------------------------------------------------------
expect_reject("2.1.2 entry count rejected",
              [("show.json", MANIFEST)] + [(f"media/f{i}", b"x") for i in range(20)],
              rule="2.1.2", limits=dsx_container.Limits(max_entries=10))

# A 8 MB deflate bomb against a 100 KB budget. The point is not that it is
# caught but that it is caught *during* decompression: "stopped" means the
# reader never held the full expansion.
expect_reject("2.1.2 bomb stopped mid-stream",
              [("show.json", MANIFEST), ("audio/track.mp3", b"\0" * 8_000_000)],
              rule="2.1.2", mentions="stopped", compress=True,
              limits=dsx_container.Limits(max_total_bytes=100_000))


def patch_declared_size(raw: bytes, lie: int) -> bytes:
    """Rewrite the uncompressed size in the central directory to a lie.

    Central directory header: PK\\x01\\x02, uncompressed size at offset +24.
    """
    i = raw.index(b"PK\x01\x02")
    return raw[:i + 24] + lie.to_bytes(4, "little") + raw[i + 28:]


tmp = ROOT / ".tmp-lying-size.dsx"
tmp.write_bytes(patch_declared_size(
    zip_bytes([("audio/track.mp3", b"\0" * 400_000), ("show.json", MANIFEST)],
              compress=True), 64))
try:
    problems = dsx_container.check_zip(tmp)
    hit = [p for p in problems if p.startswith("2.1.2")
           and ("produces" in p or "declared size" in p)]
    record(bool(hit), "2.1.2 lying declared size caught",
           hit[0][:110] if hit else f"accepted or wrong reason: {problems[:1]}")
finally:
    tmp.unlink(missing_ok=True)

# --- the demonstration ----------------------------------------------------
# C4 is REJECT because of this, not because duplicates are untidy.
signed = json.dumps({"dsx": "0.1", "profile": "L2",
                     "safety": {"min_separation_m": 20.0}}).encode()
swapped = json.dumps({"dsx": "0.1", "profile": "L2",
                      "safety": {"min_separation_m": 2.0}}).encode()

tmp = ROOT / ".tmp-bypass.dsx"
tmp.write_bytes(zip_bytes([("show.json", signed), ("show.json", swapped)]))
try:
    with zipfile.ZipFile(tmp) as zf:
        # A hasher that walks the central directory in order takes the first.
        first = next(zi for zi in zf.infolist() if zi.filename == "show.json")
        hashed = json.loads(zf.read(first))["safety"]["min_separation_m"]
        # A parser that asks for the entry by name gets the last. Both readings
        # are defensible, both are stdlib, and the signature covers only one.
        parsed = json.loads(zf.read("show.json"))["safety"]["min_separation_m"]
    diverges = hashed != parsed
    rejected = any(p.startswith("C4") for p in dsx_container.check_zip(tmp))
    record(diverges and rejected,
           "C4 bypass demonstrated and blocked",
           f"signed {hashed} m, parsed {parsed} m -- rejected before parsing"
           if diverges and rejected else
           f"hashed={hashed} parsed={parsed} rejected={rejected}")
finally:
    tmp.unlink(missing_ok=True)

# --- the examples must still pass ----------------------------------------
# Both as trees and as real ZIPs. The ZIP pass is the regression guard for C6:
# an ordinary archive stores permission bits with no file-type bits, and an
# implementation that reads that as "not a regular file" rejects everything.
for ex in sorted((ROOT / "examples").iterdir()):
    if not ex.is_dir():
        continue
    problems = dsx_container.check_dir(ex)
    record(not problems, f"example {ex.name} conforms (tree)",
           "; ".join(problems)[:110] if problems else "")

    packed = ROOT / f".tmp-{ex.name}.dsx"
    with zipfile.ZipFile(packed, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(ex.rglob("*")):
            if f.is_file():
                zf.write(f, f.relative_to(ex).as_posix())
    try:
        problems = dsx_container.check_zip(packed)
    finally:
        packed.unlink(missing_ok=True)
    record(not problems, f"example {ex.name} conforms (zip)",
           "; ".join(problems)[:110] if problems else "")

# --- report ---------------------------------------------------------------
print("DSX container checks (spec 2.1.1 / 2.1.2)\n")
for ok, name, detail in results:
    print(f"{'PASS' if ok else 'FAIL'}  {name:<38}{detail}")
passed = sum(1 for ok, _, _ in results if ok)
print(f"\n{passed}/{len(results)} passed")
raise SystemExit(0 if passed == len(results) else 1)
