#!/usr/bin/env python3
"""Archive-level conformance checks.

run_schema_checks.py proves the schema rejects malformed manifests. It cannot
see the archive around the manifest, so these three classes of defect used to
pass unnoticed -- and did:

  * a manifest referencing resources the archive does not carry (spec 2.1),
  * a provenance block whose content_hash and signature are decorative
    rather than recomputable (spec 2.3.1),
  * a role declaring loop continuity that its own trajectory does not have
    (spec 10).

Run:  python3 conformance/check_archive.py
"""
import json
import math
import pathlib
import shutil
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import dsx_seal  # noqa: E402

results = []
warnings = []
skipped = []


def record(ok, name, detail=""):
    results.append((ok, name, detail))


# --- which manifest members are archive paths? ---------------------------
def archive_ref_names():
    """Read the marker out of the schemas instead of hand-maintaining a list.

    A hand-kept list silently rots the moment someone adds a new path-valued
    field, which is the failure this check exists to catch.
    """
    names = set()

    def walk(n):
        if not isinstance(n, dict):
            return
        for k, v in (n.get("properties") or {}).items():
            if isinstance(v, dict) and v.get("x-archive-ref"):
                names.add(k)
            walk(v)
        for c in ("allOf", "anyOf", "oneOf"):
            for b in n.get(c, []) or []:
                walk(b)
        for k in ("if", "then", "else", "not", "items", "contains",
                  "additionalProperties"):
            if isinstance(n.get(k), dict):
                walk(n[k])
        for v in (n.get("$defs") or {}).values():
            walk(v)

    for f in sorted((ROOT / "schema").glob("*.json")):
        walk(json.loads(f.read_text()))
    return names


REF_NAMES = archive_ref_names()


def collect_refs(doc):
    found = set()

    def walk(n):
        if isinstance(n, dict):
            for k, v in n.items():
                if k in REF_NAMES and isinstance(v, str):
                    found.add(v)
                walk(v)
        elif isinstance(n, list):
            for v in n:
                walk(v)

    walk(doc)
    return found


# --- checks --------------------------------------------------------------
def check_complete(base):
    doc = json.loads((base / "show.json").read_text())
    missing = sorted(r for r in collect_refs(doc) if not (base / r).exists())
    external = sorted(r for r in collect_refs(doc)
                      if r.startswith(("/", "http://", "https://", "../")))
    detail = ""
    if missing:
        detail = f"{len(missing)} referenced entries absent: {missing[:3]}"
    if external:
        detail += f" external refs not permitted (2.1): {external[:3]}"
    record(not missing and not external,
           f"{base.name}: every referenced entry is carried in the archive", detail)


def check_resources(base):
    """Validate every referenced trajectory/light file against schema/resource.

    Section 4 is normative, but until resource.schema.json existed nothing
    enforced it -- including on the reference examples themselves.
    """
    try:
        import jsonschema
        from referencing import Registry, Resource
    except ImportError:
        skipped.append(f"{base.name}: resources not validated (jsonschema missing)")
        return
    res = []
    for f in sorted((ROOT / "schema").glob("*.json")):
        d = json.loads(f.read_text())
        r = Resource.from_contents(d)
        res.append((d["$id"], r))
        res.append((f.name, r))
    reg = Registry().with_resources(res)
    schema = json.loads((ROOT / "schema" / "resource.schema.json").read_text())
    V = jsonschema.Draft202012Validator(schema, registry=reg)

    doc = json.loads((base / "show.json").read_text())
    bad, n = [], 0
    for rel in sorted(collect_refs(doc)):
        if not rel.endswith(".json"):
            continue
        if rel.split("/")[0] not in ("traj", "light"):
            continue
        p = base / rel
        if not p.exists():
            continue
        errs = list(V.iter_errors(json.loads(p.read_text())))
        n += 1
        if errs:
            bad.append(f"{rel}: {errs[0].message[:70]}")
    if n:
        record(not bad, f"{base.name}: all {n} track/light resources validate",
               "; ".join(bad[:3]))


def check_seal(base):
    doc = json.loads((base / "show.json").read_text())
    prov = doc.get("provenance", {})
    if doc.get("profile") != "L2":
        return
    claimed = prov.get("content_hash")
    actual = dsx_seal.content_hash(base)
    record(claimed == actual, f"{base.name}: content_hash recomputes",
           "" if claimed == actual else f"claimed {claimed} != actual {actual}")

    sig = prov.get("signature") or {}
    pub = sig.get("public_key")
    if not pub or not (base / pub).exists():
        record(False, f"{base.name}: signature verifies", "no in-archive public key")
        return
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        from cryptography.exceptions import InvalidSignature
    except ImportError:
        skipped.append(f"{base.name}: signature not verified "
                       "(cryptography not installed)")
        return
    pk = Ed25519PublicKey.from_public_bytes((base / pub).read_bytes())
    try:
        pk.verify((base / sig["file"]).read_bytes(), actual.encode("ascii"))
        record(True, f"{base.name}: signature verifies")
        if sig.get("key_id") == dsx_seal.DEMO_KEY_ID:
            warnings.append(
                f"{base.name}: sealed with the public demo key "
                f"({dsx_seal.DEMO_KEY_ID}) -- proves the mechanism, "
                "guarantees nothing about the show")
    except InvalidSignature:
        record(False, f"{base.name}: signature verifies", "signature mismatch")


def check_tamper(base):
    """A seal that does not notice an edit is worse than no seal.

    Done on a throwaway copy. Mutating the real archive during a conformance
    run means an interrupted run leaves a corrupted geofence and a broken hash
    behind -- a test that can damage the thing it inspects is not a test.
    """
    doc = json.loads((base / "show.json").read_text())
    if doc.get("profile") != "L2":
        return
    with tempfile.TemporaryDirectory() as td:
        work = pathlib.Path(td) / base.name
        shutil.copytree(base, work)
        victim = work / (doc.get("safety", {}).get("geofence")
                         or doc["termination"]["geofence"]["hard"]["ref"])
        before = dsx_seal.content_hash(work)
        # a single appended byte: the smallest edit an archive can suffer
        victim.write_bytes(victim.read_bytes() + b"\n")
        after = dsx_seal.content_hash(work)
    record(before != after,
           f"{base.name}: editing a geofence changes the content hash",
           "" if before != after else "the digest did not move")


def eval_seam(traj):
    """Position and velocity mismatch between the end and the start of a loop."""
    segs = traj["segments"]
    start = traj["start_point"]
    pos_err = math.dist(start, segs[-1]["p"])
    pts = [start] + [s["p"] for s in segs]

    def v_start(i):
        s, p0 = segs[i], pts[i]
        return [(s["c1"][k] - p0[k]) * 3.0 / (s["dt_ms"] / 1000.0) for k in range(3)]

    def v_end(i):
        s = segs[i]
        return [(s["p"][k] - s["c2"][k]) * 3.0 / (s["dt_ms"] / 1000.0) for k in range(3)]

    return pos_err, math.dist(v_end(len(segs) - 1), v_start(0))


def check_loops(base):
    doc = json.loads((base / "show.json").read_text())
    bad = []
    checked = 0
    for r in doc.get("roles", []):
        loop = r.get("loop")
        if not loop:
            continue
        tp = base / r["trajectory"]
        if not tp.exists():
            bad.append(f"{r['id']}: trajectory absent")
            continue
        traj = json.loads(tp.read_text())
        if traj.get("kind") != "segments":
            continue
        total = sum(s["dt_ms"] for s in traj["segments"])
        if total != loop["period_ms"]:
            bad.append(f"{r['id']}: track is {total}ms, loop period is {loop['period_ms']}ms")
        pos_err, vel_err = eval_seam(traj)
        tol = loop.get("tolerance", {})
        if pos_err > tol.get("position_m", 0.0):
            bad.append(f"{r['id']}: seam position error {pos_err:.4f}m > {tol.get('position_m')}m")
        if loop.get("continuity") == "c1" and vel_err > tol.get("velocity_ms", 0.0):
            bad.append(f"{r['id']}: declares c1 but seam velocity jumps {vel_err:.4f}m/s")
        checked += 1
    if checked:
        record(not bad, f"{base.name}: declared loop continuity holds in the trajectory",
               "; ".join(bad[:3]))


def check_loop_detects_break(base):
    """Prove the loop check can fail, not just pass."""
    doc = json.loads((base / "show.json").read_text())
    role = next((r for r in doc.get("roles", []) if r.get("loop")), None)
    if not role:
        return
    tp = base / role["trajectory"]
    traj = json.loads(tp.read_text())
    if traj.get("kind") != "segments":
        return
    traj["segments"][-1]["p"] = [traj["segments"][-1]["p"][0] + 1.0,
                                 *traj["segments"][-1]["p"][1:]]
    pos_err, _ = eval_seam(traj)
    record(pos_err > role["loop"]["tolerance"]["position_m"],
           f"{base.name}: a loop that does not close is detected",
           f"seam error {pos_err:.3f}m")


def main():
    # Discovered, not listed: a hand-maintained list is how a new example ends
    # up shipping unchecked, which is exactly what happened to show-l1.
    for base in sorted((ROOT / "examples").iterdir()):
        if not (base / "show.json").exists():
            continue
        check_complete(base)
        check_resources(base)
        check_seal(base)
        check_tamper(base)
        check_loops(base)
        check_loop_detects_break(base)

    for ok, name, detail in results:
        print(("PASS  " if ok else "FAIL  ") + name + (f"   [{detail[:80]}]" if detail else ""))
    for s in skipped:
        print("SKIP  " + s)
    for w in warnings:
        print("WARN  " + w)
    failed = sum(1 for ok, _, _ in results if not ok)
    print(f"\n{len(results) - failed}/{len(results)} passed"
          + (f", {len(skipped)} skipped" if skipped else "")
          + (f", {len(warnings)} warning(s)" if warnings else ""))
    if skipped:
        print("a skipped check is not a passed check; install cryptography to run it")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
