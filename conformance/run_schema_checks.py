#!/usr/bin/env python3
"""DSX v0.1-draft — schema-level conformance checks.

Run:  python3 conformance/run_schema_checks.py     (needs: pip install jsonschema)

These are the cheapest half of the suite: they prove the schema REJECTS the
things it must reject. The semantic checks (envelope comparison, RTH
feasibility, fall containment, sampler bit-exactness) are not here yet --
see spec/A-open-questions.md.
"""
import copy, json, pathlib, sys

try:
    import jsonschema
except ImportError:
    sys.exit("jsonschema not installed: pip install jsonschema")

ROOT = pathlib.Path(__file__).resolve().parent.parent
load = lambda p: json.loads((ROOT / p).read_text())
V = jsonschema.Draft202012Validator

SHOW = load("schema/dsx.schema.json")
DEV = load("schema/dsxp.schema.json")
OK = load("examples/minimal-l0/show.json")

results = []


def check(name, schema, inst, expect_valid):
    errs = list(V(schema).iter_errors(inst))
    passed = (not errs) == expect_valid
    results.append((passed, name, errs[0].message if errs else ""))


def without(obj, *path):
    d = copy.deepcopy(obj)
    t = d
    for k in path[:-1]:
        t = t[k]
    del t[path[-1]]
    return d


# --- positive -------------------------------------------------------------
check("L0 example is valid", SHOW, OK, True)
check("aircraft template is valid", DEV, load("devices/_template-aircraft.dsxp"), True)
check("actuator template is valid", DEV, load("devices/_template-actuator.dsxp"), True)

# --- coordinates: the fields whose absence causes accidents (spec 3.1) ----
check("missing alt_ref is rejected", SHOW, without(OK, "frame", "origin", "alt_ref"), False)
check("AMSL without geoid is rejected", SHOW, without(OK, "frame", "origin", "geoid"), False)
check("missing handedness is rejected", SHOW, without(OK, "frame", "handedness"), False)
check("missing bearing_deg is rejected", SHOW, without(OK, "frame", "bearing_deg"), False)
check("missing frame is rejected", SHOW, without(OK, "frame"), False)
check("missing time is rejected", SHOW, without(OK, "time"), False)

# --- per-aircraft identity (spec 5, 3.1) ---------------------------------
check("missing home heading is rejected", SHOW, without(OK, "drones", 0, "home", "heading_deg"), False)

# --- profile gating (spec 1.3) -------------------------------------------
l2 = copy.deepcopy(OK); l2["profile"] = "L2"
check("L2 without termination/provenance is rejected", SHOW, l2, False)

# --- the authority rule (spec 6.2) ---------------------------------------
act = load("devices/_template-actuator.dsxp"); act["actuator"]["authority"] = "both"
check("actuator authority must be show|safety", DEV, act, False)

# -------------------------------------------------------------------------
for passed, name, msg in results:
    print(("PASS  " if passed else "FAIL  ") + name + (f"   [{msg[:70]}]" if msg else ""))
failed = sum(1 for p, _, _ in results if not p)
print(f"\n{len(results) - failed}/{len(results)} passed")
sys.exit(1 if failed else 0)
