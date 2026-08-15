#!/usr/bin/env python3
"""DSX v0.1-draft -- the profile matrix, checked rather than asserted (A34).

Run:  python3 conformance/check_profiles.py
      python3 conformance/check_profiles.py --update-enforcement

`profiles/profile-matrix.json` is the normative source; `spec/C-profile-matrix.md`
is generated from it. This harness checks four different things, and they are
worth separating because they fail for different reasons:

1.  **Shape.** Every member of `schema/dsx.schema.json` appears in the matrix and
    every matrix path resolves in a schema. A member nobody classified is the
    exact state A34 was raised about.
2.  **Coherence.** Profiles are cumulative: no member may go from REQUIRED at a
    lower profile to FORBIDDEN at a higher one, and the schema's unconditional
    `required` list may not contradict a cell.
3.  **Enforcement.** For every REQUIRED and FORBIDDEN cell the harness *mutates*
    a real reference file -- deletes the member, or inserts it -- and asks
    whether the schema rejects the result. A rule that no schema enforces is
    marked `text` and stays visible. `--update-enforcement` writes the measured
    result back into the matrix, so that a schema rule silently disappearing
    later shows up here as a regression rather than as nothing at all.
4.  **The examples themselves.** Each reference file must satisfy its own row,
    including the resource-level rules (yaw is L2; an L0 file carries no segment
    tracks and no light channel beyond R/G/B) and referential integrity of
    `drones[].fleet` from L1 upwards.

Exit code 1 on any failure.
"""
import argparse
import copy
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
MATRIX_PATH = ROOT / "profiles" / "profile-matrix.json"
SCHEMA_DIR = ROOT / "schema"
PROFILES = ("L0", "L1", "L2")
STATUSES = ("REQUIRED", "OPTIONAL", "FORBIDDEN", "CONDITIONAL")

fail = 0
notes = []


def report(ok: bool, label: str, detail: str = "") -> bool:
    global fail
    print(f"{'PASS' if ok else 'FAIL'}  {label:52s} {detail}".rstrip())
    if not ok:
        fail += 1
    return ok


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

matrix = json.loads(MATRIX_PATH.read_text())
members = matrix["members"]
by_path = {m["path"]: m for m in members}

dsx_schema = json.loads((SCHEMA_DIR / "dsx.schema.json").read_text())
resource_schema = json.loads((SCHEMA_DIR / "resource.schema.json").read_text())

try:
    import jsonschema
    from referencing import Registry, Resource

    resources = []
    for f in sorted(SCHEMA_DIR.glob("*.json")):
        doc = json.loads(f.read_text())
        r = Resource.from_contents(doc)
        resources.append((doc["$id"], r))
        resources.append((f.name, r))
    REGISTRY = Registry().with_resources(resources)
    VALIDATOR = jsonschema.Draft202012Validator(dsx_schema, registry=REGISTRY)
except ImportError:                                          # pragma: no cover
    VALIDATOR = None


def valid(doc) -> bool:
    return not list(VALIDATOR.iter_errors(doc))


# ---------------------------------------------------------------------------
# 1. Shape
# ---------------------------------------------------------------------------

print("1. Shape -- is every member classified, and does every path exist?\n")

schema_top = set(dsx_schema["properties"].keys())
matrix_top = {m["path"] for m in members if m["scope"] == "manifest" and "." not in m["path"]
              and "[" not in m["path"]}
missing = sorted(schema_top - matrix_top)
report(not missing, "every top-level schema member is in the matrix",
       f"unclassified: {missing}" if missing else f"{len(schema_top)} members")

invented = sorted(matrix_top - schema_top)
report(not invented, "the matrix invents no top-level member",
       f"not in schema: {invented}" if invented else "")


SCHEMA_DOCS = {}
for _f in sorted(SCHEMA_DIR.glob("*.json")):
    _doc = json.loads(_f.read_text())
    SCHEMA_DOCS[_doc.get("$id", _f.name)] = _doc
    SCHEMA_DOCS[_f.name] = _doc


def deref(node):
    """Follow $ref across schema files -- termination, safety and the resource
    kinds live in their own documents, and a path that stops at the $ref would
    look unresolvable when it is merely one hop away."""
    seen = 0
    while isinstance(node, dict) and "$ref" in node and seen < 8:
        ref = node["$ref"]
        seen += 1
        if ref.startswith("#/$defs/"):
            return node  # local $defs are resolved by the caller's context
        target = SCHEMA_DOCS.get(ref) or SCHEMA_DOCS.get(ref.rsplit("/", 1)[-1])
        if target is None:
            return node
        node = target
    return node


def resolve(path: str):
    """Resolve a matrix path in its schema. Returns the subschema or None."""
    if path.startswith("resource:"):
        _, rest = path.split(":", 1)
        head, _, tail = rest.partition(".")
        node = resource_schema["$defs"].get(head)
        parts = tail.split(".") if tail else []
    else:
        node = dsx_schema
        parts = path.split(".")
    for part in parts:
        node = deref(node)
        if part.endswith("[]"):
            part = part[:-2]
            node = (node.get("properties") or {}).get(part)
            if node is None:
                return None
            node = deref(node).get("items")
        else:
            node = (node.get("properties") or {}).get(part)
        if node is None:
            return None
    return deref(node)


unresolved = [m["path"] for m in members if resolve(m["path"]) is None]
report(not unresolved, "every matrix path resolves in a schema",
       f"unresolved: {unresolved}" if unresolved else f"{len(members)} paths")

bad_status = [(m["path"], p, m[p]) for m in members for p in PROFILES if m[p] not in STATUSES]
report(not bad_status, "every cell carries a legal status", str(bad_status) if bad_status else "")

no_condition = [m["path"] for m in members
                if any(m[p] == "CONDITIONAL" for p in PROFILES) and not m.get("condition")]
report(not no_condition, "every CONDITIONAL cell states its condition",
       str(no_condition) if no_condition else "")

# ---------------------------------------------------------------------------
# 2. Coherence
# ---------------------------------------------------------------------------

print("\n2. Coherence -- do the cells contradict each other or the schema?\n")

regressions = [
    (m["path"], lo, hi)
    for m in members
    for lo, hi in (("L0", "L1"), ("L1", "L2"), ("L0", "L2"))
    if m[lo] == "REQUIRED" and m[hi] == "FORBIDDEN"
]
report(not regressions, "profiles are cumulative (no REQUIRED -> FORBIDDEN)",
       str(regressions) if regressions else "")

hard_required = set(dsx_schema.get("required", []))
contradictions = [
    (p, [m[x] for x in PROFILES])
    for p in hard_required
    if (m := by_path.get(p)) and any(m[x] != "REQUIRED" for x in PROFILES)
]
report(not contradictions,
       "schema's unconditional required list matches the matrix",
       str(contradictions) if contradictions else f"{sorted(hard_required)}")

# ---------------------------------------------------------------------------
# 3. Enforcement -- mutate real files and see whether the schema notices
# ---------------------------------------------------------------------------

print("\n3. Enforcement -- which cells does the schema actually enforce?\n")

L0_BASE = json.loads((ROOT / "examples" / "minimal-l0" / "show.json").read_text())
L2_BASE = json.loads((ROOT / "examples" / "rotation-l2" / "show.json").read_text())
L2_ALT = json.loads((ROOT / "examples" / "continuous-l2" / "show.json").read_text())

# There is no L1 reference show in the repository (A38). For the mutation test a
# manifest is enough, so one is derived from the L0 file and its validity is
# asserted before it is used -- a fixture that is itself invalid would make
# every L1 result meaningless.
L1_BASE = copy.deepcopy(L0_BASE)
L1_BASE["profile"] = "L1"
L1_BASE["fleet"] = copy.deepcopy(L2_BASE["fleet"][:1])
L1_BASE["fleet"][0]["id"] = "default"
L1_BASE["safety"] = {"min_separation_m": 2.0}
for d in L1_BASE["drones"]:
    d["fleet"] = "default"

BASES = {"L0": L0_BASE, "L1": L1_BASE, "L2": L2_BASE}

if VALIDATOR is None:
    print("SKIP  jsonschema/referencing not installed -- enforcement unmeasured\n")
else:
    for prof, base in BASES.items():
        report(valid(base), f"the {prof} mutation base is itself valid",
               "" if valid(base) else str(list(VALIDATOR.iter_errors(base))[:1]))


# Members that no reference file happens to carry, so the FORBIDDEN mutation has
# nothing to insert. The values are minimal but schema-shaped: the test is
# whether the profile rule fires, and a value the schema rejects for an
# unrelated reason would answer a different question.
FALLBACK_VALUES = {
    "drones[].trajectory": "traj/0001.json",
    "drones[].payloads": [{"slot": 0, "device_profile": "dev/pyro.json",
                           "device_type_id": "example.pyro.v1"}],
    "termination.fallback_channel": {"required_for_profile": "L2",
                                     "independent_hardware": True},
}


def sample_value(path: str):
    """A realistic value for `path`, taken from a reference file where possible."""
    if path in FALLBACK_VALUES:
        return copy.deepcopy(FALLBACK_VALUES[path])
    for src in (L2_BASE, L2_ALT):
        node = src
        ok = True
        for part in path.split("."):
            if part.endswith("[]"):
                part = part[:-2]
                if not isinstance(node, dict) or part not in node or not node[part]:
                    ok = False
                    break
                node = node[part][0]
            elif isinstance(node, dict) and part in node:
                node = node[part]
            else:
                ok = False
                break
        if ok:
            return copy.deepcopy(node)
    return None


def get_parent(doc, path: str):
    """(container, key) for a dotted path, following the FIRST array element."""
    parts = path.split(".")
    node = doc
    for part in parts[:-1]:
        if part.endswith("[]"):
            part = part[:-2]
            if part not in node or not node[part]:
                return None, None
            node = node[part][0]
        else:
            if part not in node:
                return None, None
            node = node[part]
    key = parts[-1]
    if key.endswith("[]"):
        key = key[:-2]
    return node, key


def ensure_parent(doc, path: str):
    """Create missing intermediate objects by copying them from the L2 file.

    Needed for cells like termination.fallback_channel: the L0 and L1 bases
    carry no termination object at all, so without this the FORBIDDEN rule
    would be recorded as untested rather than tested.
    """
    parts = path.split(".")
    node, src = doc, L2_BASE
    for part in parts[:-1]:
        if part.endswith("[]"):
            return get_parent(doc, path)
        src = src.get(part) if isinstance(src, dict) else None
        if part not in node:
            if not isinstance(src, dict):
                return None, None
            node[part] = copy.deepcopy(src)
        node = node[part]
    return node, parts[-1]


measured = {}
counts = {"schema": 0, "text": 0, "unproven": 0, "resource": 0}

for m in members:
    if m["scope"] != "manifest":
        # resource-level cells are proven in section 4 against the real files,
        # not by mutating a manifest
        counts["resource"] += sum(1 for p in PROFILES if m[p] in ("REQUIRED", "FORBIDDEN"))
        continue
    for prof in PROFILES:
        status = m[prof]
        if status not in ("REQUIRED", "FORBIDDEN") or VALIDATOR is None:
            continue
        doc = copy.deepcopy(BASES[prof])
        container, key = get_parent(doc, m["path"])
        if status == "REQUIRED":
            if container is None or key not in container:
                counts["unproven"] += 1
                measured.setdefault(m["path"], {})[prof] = "unproven"
                continue
            del container[key]
        else:  # FORBIDDEN
            value = sample_value(m["path"])
            if container is None:
                container, key = ensure_parent(doc, m["path"])
            if value is None or container is None:
                counts["unproven"] += 1
                measured.setdefault(m["path"], {})[prof] = "unproven"
                continue
            container[key] = value
        enforced = not valid(doc)
        measured.setdefault(m["path"], {})[prof] = "schema" if enforced else "text"
        counts["schema" if enforced else "text"] += 1

text_only = sorted((p, pr) for p, d in measured.items() for pr, v in d.items() if v == "text")
unproven = sorted((p, pr) for p, d in measured.items() for pr, v in d.items() if v == "unproven")
for path, prof in text_only:
    print(f"      text-only: {path:44s} {by_path[path][prof]:10s} at {prof}")
for path, prof in unproven:
    print(f"      unproven:  {path:44s} {by_path[path][prof]:10s} at {prof}")
print(f"      {counts['schema']} cells enforced by the schema, "
      f"{counts['text']} by specification text only, "
      f"{counts['unproven']} not mutable from a reference file, "
      f"{counts['resource']} checked at resource level (section 4 below)")

# Regression guard: a cell recorded as schema-enforced must stay so.
downgraded = [
    (path, prof)
    for path, per_prof in measured.items()
    for prof, got in per_prof.items()
    if by_path[path].get("enforced", {}).get(prof) == "schema" and got != "schema"
]
report(not downgraded, "no cell lost its schema enforcement",
       str(downgraded) if downgraded else "")

# ---------------------------------------------------------------------------
# 4. The reference files against their own row
# ---------------------------------------------------------------------------

print("\n4. Reference files -- does each example satisfy its declared profile?\n")

EXAMPLES = sorted((ROOT / "examples").glob("*/show.json"))

for show_path in EXAMPLES:
    doc = json.loads(show_path.read_text())
    prof = doc["profile"]
    name = show_path.parent.name
    problems = []
    for m in members:
        if m["scope"] != "manifest":
            continue
        container, key = get_parent(doc, m["path"])
        present = container is not None and key in container
        if m[prof] == "REQUIRED" and not present:
            problems.append(f"missing {m['path']}")
        if m[prof] == "FORBIDDEN" and present:
            problems.append(f"carries {m['path']} (FORBIDDEN at {prof})")
    report(not problems, f"{name} ({prof}) satisfies the matrix",
           "; ".join(problems) if problems else "")

    # resource-level rules
    res_problems = []
    for res_path in sorted(show_path.parent.rglob("*.json")):
        if res_path == show_path:
            continue
        try:
            res = json.loads(res_path.read_text())
        except json.JSONDecodeError:
            continue
        rel = res_path.relative_to(show_path.parent)
        kind = res.get("kind")
        if kind == "segments":
            yawed = "start_yaw_deg" in res or any("yaw_deg" in s for s in res.get("segments", []))
            if yawed and prof != "L2":
                res_problems.append(f"{rel}: yaw at {prof} (4.2.5 -- L2 only)")
            if prof == "L0":
                res_problems.append(f"{rel}: segment track in an L0 file (4.1)")
        if kind == "light_program" and prof == "L0":
            extra = [c for c in res.get("channels", []) if c not in ("R", "G", "B")]
            if extra:
                res_problems.append(f"{rel}: L0 light program carries {extra}")
    report(not res_problems, f"{name} ({prof}) resources satisfy the matrix",
           "; ".join(res_problems) if res_problems else "")

    # referential integrity of drones[].fleet, from L1 upwards
    if prof in ("L1", "L2"):
        ids = {f["id"] for f in doc.get("fleet", [])}
        dangling = sorted({d.get("fleet") for d in doc["drones"]} - ids)
        report(not dangling, f"{name} ({prof}) fleet references resolve",
               f"dangling: {dangling}" if dangling else f"{len(ids)} fleet(s)")

# ---------------------------------------------------------------------------
# 5. Appendix C is generated, not maintained
# ---------------------------------------------------------------------------

print("\n5. Appendix C -- is the published table still the generated one?\n")

sys.path.insert(0, str(ROOT / "tools"))
try:
    import gen_profile_matrix

    generated = gen_profile_matrix.render(matrix)
    published_path = ROOT / "spec" / "C-profile-matrix.md"
    published = published_path.read_text() if published_path.exists() else ""
    report(generated == published, "spec/C-profile-matrix.md matches profiles/profile-matrix.json",
           "" if generated == published else "run: python3 tools/gen_profile_matrix.py --write")
except ImportError as e:                                     # pragma: no cover
    report(False, "tools/gen_profile_matrix.py importable", str(e))

# ---------------------------------------------------------------------------

if "--update-enforcement" in sys.argv:
    for m in members:
        if m["path"] in measured:
            m["enforced"] = measured[m["path"]]
    MATRIX_PATH.write_text(json.dumps(matrix, indent=2, ensure_ascii=False) + "\n")
    print(f"\nwrote measured enforcement for {len(measured)} members into "
          f"{MATRIX_PATH.relative_to(ROOT)}")

print()
sys.exit(1 if fail else 0)
