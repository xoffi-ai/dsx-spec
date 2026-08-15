#!/usr/bin/env python3
"""Compute, write and verify the DSX content hash and detached signature.

Reference implementation of spec/02 section 2.3.1. Deliberately dependency-free
for `hash`/`verify-hash`; only signing and signature verification need
`cryptography`.

    python3 tools/dsx_seal.py hash        examples/rotation-l2
    python3 tools/dsx_seal.py seal        examples/rotation-l2        # demo key
    python3 tools/dsx_seal.py seal        examples/rotation-l2 --key my.ed25519
    python3 tools/dsx_seal.py verify      examples/rotation-l2
    python3 tools/dsx_seal.py keygen      my

An archive directory is treated as the unpacked form of the .dsx ZIP; the
digest is defined on the entries, not on the ZIP container, so packing or
repacking with different compression does not change it.
"""
import argparse
import hashlib
import json
import pathlib
import struct
import sys

NULL_DIGEST = "sha256:" + "0" * 64
DEMO_KEY_ID = "dsx-demo-key-not-for-production"


def entries(root: pathlib.Path):
    """All archive entries except signature/, ordered by UTF-8 path bytes."""
    out = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(root).as_posix()
        if rel.split("/")[0] == "signature":
            continue
        out.append((rel, p))
    out.sort(key=lambda t: t[0].encode("utf-8"))
    return out


def manifest_with_null_digest(path: pathlib.Path) -> bytes:
    """Raw manifest bytes with content_hash replaced by the null digest.

    Textual replacement, not a JSON round-trip: re-serialising would change
    bytes that the digest covers, which is exactly what 2.3.1 avoids.
    """
    raw = path.read_bytes()
    doc = json.loads(raw)
    cur = doc.get("provenance", {}).get("content_hash")
    if cur is None or cur == NULL_DIGEST:
        return raw
    if len(cur) != len(NULL_DIGEST):
        raise SystemExit(f"content_hash has non-canonical length: {cur!r}")
    return raw.replace(cur.encode(), NULL_DIGEST.encode(), 1)


def content_hash(root: pathlib.Path) -> str:
    h = hashlib.sha256()
    for rel, p in entries(root):
        data = manifest_with_null_digest(p) if rel == "show.json" else p.read_bytes()
        h.update(rel.encode("utf-8"))
        h.update(b"\x00")
        h.update(struct.pack(">Q", len(data)))
        h.update(data)
    return "sha256:" + h.hexdigest()


def write_hash(root: pathlib.Path, digest: str):
    mp = root / "show.json"
    raw = mp.read_bytes()
    doc = json.loads(raw)
    cur = doc.get("provenance", {}).get("content_hash")
    if cur is None:
        raise SystemExit("manifest has no provenance.content_hash to write into")
    mp.write_bytes(raw.replace(cur.encode(), digest.encode(), 1))


# --- signing -------------------------------------------------------------
def _ed25519():
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import (
            Ed25519PrivateKey, Ed25519PublicKey)
        from cryptography.hazmat.primitives import serialization
        return Ed25519PrivateKey, Ed25519PublicKey, serialization
    except ImportError:
        raise SystemExit("signing needs: pip install cryptography")


DEMO_SEED = b"dsx-spec example key -- NOT FOR PRODUCTION USE"


def demo_key():
    """The key the bundled examples are sealed with.

    Derived from a seed printed in the clear rather than committed as a key
    file. A repository for a safety format has no business shipping a private
    key blob: it trips secret scanning, and it teaches exactly the wrong habit.
    Deriving it keeps the examples re-sealable by anyone while making it
    self-evident that the key guarantees nothing.
    """
    Priv, _, _s = _ed25519()
    return Priv.from_private_bytes(hashlib.sha256(DEMO_SEED).digest())


def keygen(stem: pathlib.Path):
    Priv, _, ser = _ed25519()
    k = Priv.generate()
    stem.parent.mkdir(parents=True, exist_ok=True)
    stem.with_suffix(".ed25519").write_bytes(k.private_bytes(
        ser.Encoding.Raw, ser.PrivateFormat.Raw, ser.NoEncryption()))
    stem.with_suffix(".pub").write_bytes(
        k.public_key().public_bytes(ser.Encoding.Raw, ser.PublicFormat.Raw))
    print(f"wrote {stem.with_suffix('.ed25519')} and {stem.with_suffix('.pub')}")


def seal(root: pathlib.Path, key: pathlib.Path | None):
    digest = content_hash(root)
    write_hash(root, digest)
    print(f"content_hash = {digest}")
    if key:
        Priv, _, _s = _ed25519()
        sk = Priv.from_private_bytes(key.read_bytes())
    else:
        sk = demo_key()
        print("signing with the derived demo key (not a secret)")
    doc = json.loads((root / "show.json").read_text())
    sig_rel = doc.get("provenance", {}).get("signature", {}).get("file")
    if not sig_rel:
        raise SystemExit("manifest declares no provenance.signature.file")
    out = root / sig_rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(sk.sign(digest.encode("ascii")))
    pub_rel = doc["provenance"]["signature"].get("public_key")
    if pub_rel:
        _, _P, ser = _ed25519()
        (root / pub_rel).parent.mkdir(parents=True, exist_ok=True)
        (root / pub_rel).write_bytes(sk.public_key().public_bytes(
            ser.Encoding.Raw, ser.PublicFormat.Raw))
    print(f"signed -> {sig_rel}")


def verify(root: pathlib.Path) -> int:
    doc = json.loads((root / "show.json").read_text())
    prov = doc.get("provenance", {})
    claimed = prov.get("content_hash")
    actual = content_hash(root)
    bad = 0
    if claimed is None:
        print("SKIP content_hash (absent — optional at L0/L1, required at L2)")
        return bad
    if claimed != actual:
        print(f"FAIL content_hash\n  claimed {claimed}\n  actual  {actual}")
        bad += 1
    else:
        print(f"OK   content_hash {actual}")

    sig = prov.get("signature")
    if not sig:
        return bad
    pub_rel = sig.get("public_key")
    if not pub_rel:
        print("SKIP signature (no in-archive public_key; verify out of band)")
        return bad
    try:
        _, Pub, _s = _ed25519()
    except SystemExit as e:
        print(f"SKIP signature ({e})")
        return bad
    from cryptography.exceptions import InvalidSignature
    pk = Pub.from_public_bytes((root / pub_rel).read_bytes())
    try:
        pk.verify((root / sig["file"]).read_bytes(), actual.encode("ascii"))
        print(f"OK   signature ({sig['alg']}, key_id {sig['key_id']})")
    except InvalidSignature:
        print("FAIL signature does not verify against the actual content hash")
        bad += 1
    return bad


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["hash", "seal", "verify", "keygen"])
    ap.add_argument("path", type=pathlib.Path)
    ap.add_argument("--key", type=pathlib.Path,
                    help="ed25519 private key; omit to use the derived demo key")
    a = ap.parse_args()
    if a.cmd == "keygen":
        keygen(a.path)
    elif a.cmd == "hash":
        print(content_hash(a.path))
    elif a.cmd == "seal":
        seal(a.path, a.key)
    else:
        sys.exit(1 if verify(a.path) else 0)


if __name__ == "__main__":
    main()
