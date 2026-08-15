#!/usr/bin/env python3
"""Container-level checks: spec 2.1.1 (entry names) and 2.1.2 (resource limits).

These run *before* anything in the archive is parsed. That order is the whole
point: 2.1.1 C4/C5 are a signature bypass against 2.3.1, and a bypass detected
after the manifest has been read has already been trusted once.

The name rules operate on a list of names, so the same code serves a ZIP and an
unpacked directory tree. The limit rules need the ZIP directory, so they are
separate.

Usage:
    python3 tools/dsx_container.py <archive.dsx | directory> [...]

Exit code 0 if every argument passes, 1 otherwise.
"""
from __future__ import annotations

import pathlib
import stat
import sys
import unicodedata
import zipfile
from dataclasses import dataclass

# --- 2.1.2 defaults. RECOMMENDED by the spec, configurable by contract. ---
#
# There is no ratio limit on purpose; see spec 2.1.2. DEFLATE is bounded at
# ~1032:1, so a ratio cap either rejects legitimate content or never fires.
DEFAULT_MAX_TOTAL_BYTES = 4 * 1024**3   # 4 GiB
DEFAULT_MAX_ENTRIES = 100_000
READ_CHUNK = 1 << 16

C0_CONTROL = {chr(c) for c in range(0x20)} | {chr(0x7F)}
DRIVE_PREFIXES = ("\\\\?\\", "\\\\.\\")


@dataclass
class Limits:
    max_total_bytes: int = DEFAULT_MAX_TOTAL_BYTES
    max_entries: int = DEFAULT_MAX_ENTRIES


def _has_drive_prefix(name: str) -> bool:
    if name.startswith(DRIVE_PREFIXES):
        return True
    if name.startswith("\\\\"):                       # UNC \\server\share
        return True
    # C:  or  c:/  -- a single letter followed by a colon
    return len(name) >= 2 and name[1] == ":" and name[0].isalpha()


def check_names(names: list[str]) -> list[str]:
    """Spec 2.1.1 C1-C5. Returns one message per violation; empty means clean."""
    bad: list[str] = []
    seen: dict[str, str] = {}
    folded: dict[str, str] = {}

    for name in names:
        # --- C3: non-empty, no control characters ---
        if not name:
            bad.append("C3: an entry has an empty name")
            continue
        ctrl = sorted({c for c in name if c in C0_CONTROL})
        if ctrl:
            codes = ", ".join(f"U+{ord(c):04X}" for c in ctrl)
            bad.append(f"C3: {name!r} contains control character(s) {codes}")

        # --- C1: relative, '/' only, no drive or UNC prefix ---
        if _has_drive_prefix(name):
            bad.append(f"C1: {name!r} carries a drive or device prefix")
        elif name.startswith("/"):
            bad.append(f"C1: {name!r} is an absolute path")
        if "\\" in name:
            bad.append(f"C1: {name!r} contains a backslash; '/' is the only separator")

        # --- C2: no '.' or '..' component ---
        parts = name.split("/")
        if any(p in (".", "..") for p in parts):
            bad.append(f"C2: {name!r} contains a '.' or '..' component")

        # --- C4: exact duplicate ---
        if name in seen:
            bad.append(
                f"C4: {name!r} appears more than once -- one entry can be hashed "
                f"and another parsed (signature bypass against 2.3.1)"
            )
        seen[name] = name

        # --- C5: collision after NFC + case folding ---
        key = unicodedata.normalize("NFC", name).casefold()
        if key in folded and folded[key] != name:
            bad.append(
                f"C5: {name!r} and {folded[key]!r} collide after NFC + case folding "
                f"-- one file after extraction, two entries before it"
            )
        folded.setdefault(key, name)

    return bad


def check_zip(path: pathlib.Path, limits: Limits | None = None) -> list[str]:
    """Spec 2.1.1 (all) and 2.1.2, against a real ZIP."""
    lim = limits or Limits()
    bad: list[str] = []

    with zipfile.ZipFile(path) as zf:
        infos = zf.infolist()

        # Names as they were actually stored. zipfile falls back to cp437 when
        # the UTF-8 flag is clear, which never raises -- so a name that is not
        # valid UTF-8 would otherwise slip through C3 unnoticed.
        names = []
        for zi in infos:
            names.append(zi.filename)
            if not (zi.flag_bits & 0x800):
                try:
                    zi.orig_filename.encode("cp437").decode("utf-8")
                except (UnicodeDecodeError, UnicodeEncodeError):
                    bad.append(
                        f"C3: {zi.orig_filename!r} is neither flagged UTF-8 nor "
                        f"decodable as UTF-8"
                    )

        bad += check_names(names)

        # --- C6: regular files and directories only ---
        #
        # Judge only when the file-type bits are actually present. Many writers
        # -- Python's own zipfile among them -- store permission bits with
        # S_IFMT clear, so testing S_ISREG() directly would reject nearly every
        # ordinary archive. An absent type is "unspecified", not "special".
        for zi in infos:
            mode = zi.external_attr >> 16
            ftype = mode & 0o170000
            if ftype and not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
                kind = "symbolic link" if stat.S_ISLNK(mode) else f"type {ftype:#o}"
                bad.append(
                    f"C6: {zi.filename!r} is not a regular file or directory ({kind})"
                )

        # --- 2.1.2 limits ---
        if len(infos) > lim.max_entries:
            bad.append(f"2.1.2: {len(infos)} entries exceeds the limit of {lim.max_entries}")

        # Count what the archive actually produces. The sizes in the central
        # directory are the writer's claim, not a measurement: an entry may
        # declare 1 KiB and deliver gigabytes. Reading them and calling it a
        # check is the failure this loop exists to avoid.
        declared = sum(zi.file_size for zi in infos)
        produced = 0
        for zi in infos:
            if zi.is_dir():
                continue
            try:
                with zf.open(zi) as fh:
                    while True:
                        chunk = fh.read(READ_CHUNK)
                        if not chunk:
                            break
                        produced += len(chunk)
                        if produced > lim.max_total_bytes:
                            bad.append(
                                f"2.1.2: decompression exceeded {lim.max_total_bytes} "
                                f"bytes while reading {zi.filename!r}; stopped"
                            )
                            return bad
            except zipfile.BadZipFile as exc:
                # A declared size that does not match the stream shows up here:
                # the decompressor is cut off at the claimed length and the CRC
                # then fails. 2.1.2 requires this be reported as the reason for
                # rejection, not raised as a generic parse failure at the caller.
                bad.append(
                    f"2.1.2: {zi.filename!r} does not match its declared size or "
                    f"checksum, so the archive produces something other than what "
                    f"the directory claims ({exc})"
                )
                continue
        if produced != declared:
            bad.append(
                f"2.1.2: the directory declares {declared} uncompressed bytes but "
                f"the archive produces {produced}"
            )

    return bad


def check_dir(root: pathlib.Path) -> list[str]:
    """The name rules against an unpacked tree.

    A directory cannot hold two entries with the same name, so C4 is
    unreachable here -- but C5 is not, on a case-sensitive filesystem.
    """
    names = [p.relative_to(root).as_posix() for p in sorted(root.rglob("*")) if p.is_file()]
    bad = check_names(names)
    for p in root.rglob("*"):
        if p.is_symlink():
            bad.append(f"C6: {p.relative_to(root).as_posix()!r} is a symbolic link")
    return bad


def check(target: pathlib.Path, limits: Limits | None = None) -> list[str]:
    if target.is_dir():
        return check_dir(target)
    return check_zip(target, limits)


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    worst = 0
    for arg in sys.argv[1:]:
        target = pathlib.Path(arg)
        problems = check(target)
        if problems:
            worst = 1
            print(f"REJECT  {arg}")
            for p in problems:
                print(f"        {p}")
        else:
            print(f"ok      {arg}")
    return worst


if __name__ == "__main__":
    raise SystemExit(main())
