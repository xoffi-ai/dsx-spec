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

# Offline $ref resolution. DSX tools MUST run air-gapped (spec 7, and the
# Wuhan operating rules require the toolchain to be disconnected), so schema
# validation must never reach the network.
from referencing import Registry, Resource
_res = []
for _f in sorted((ROOT / "schema").glob("*.json")):
    _d = json.loads(_f.read_text())
    _r = Resource.from_contents(_d)
    _res.append((_d["$id"], _r))
    _res.append((_f.name, _r))          # relative refs used inside the schemas
REGISTRY = Registry().with_resources(_res)

_V = jsonschema.Draft202012Validator
V = lambda schema: _V(schema, registry=REGISTRY)

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

# --- rotation operation (spec 10) ----------------------------------------
ROT = load("examples/rotation-l2/show.json")
check("rotation example is valid", SHOW, ROT, True)

import copy as _c
r_nogrp = _c.deepcopy(ROT); del r_nogrp["wave_groups"]
check("waves without wave_groups is rejected", SHOW, r_nogrp, False)

r_l1 = _c.deepcopy(ROT); r_l1["profile"] = "L1"
check("multi-wave outside L2 is rejected", SHOW, r_l1, False)

r_noturn = _c.deepcopy(ROT); del r_noturn["turnaround"]
check("rotation without turnaround is rejected", SHOW, r_noturn, False)

r_nodev = _c.deepcopy(ROT); del r_nodev["assignments"][0]["sortie"]
check("assignment without sortie is rejected", SHOW, r_nodev, False)

# --- semantic rotation rules (spec 10, not expressible in JSON Schema) ----
sys.path.insert(0, str(ROOT / "conformance"))
from check_rotation import check as rot_check, Report


def sem(name, mutate, expect_reject):
    doc = _c.deepcopy(ROT)
    mutate(doc)
    rep = rot_check(doc, Report())
    results.append((rep.rejected == expect_reject, name,
                    rep.items[0][2] if rep.items else ""))


sem("valid rotation passes semantic checks", lambda d: None, False)


def _break_turnaround(d):
    s = d["drones"][0]["sorties"][1]
    s["takeoff_ms"] = d["drones"][0]["sorties"][0]["land_ms"] + 1000


sem("R10.9 short turnaround is rejected", _break_turnaround, True)


def _break_coverage(d):
    d["assignments"] = [a for a in d["assignments"]
                        if a["sortie"] != "B-001/s1"]


sem("R10.1 gap in role coverage is rejected", _break_coverage, True)


def _break_modules(d):
    d["wave_groups"][1]["modules"] = d["wave_groups"][0]["modules"]


sem("R10.4 shared modules are rejected", _break_modules, True)


def _break_energy(d):
    d["drones"][0]["sorties"][0]["energy_use_s"] = 9999


sem("R10.12 energy overrun is rejected", _break_energy, True)


def _break_overlap(d):
    ws = [w for w in d["waves"] if w["group"] == "A"]
    ws[1]["takeoff_ms"] = ws[0]["land_complete_ms"] - 60000


sem("R10.5 overlapping waves of one group are rejected", _break_overlap, True)


def _break_bays(d):
    d["turnaround"]["ground_service"]["bays"] = 1


sem("R10.10 insufficient service bays is rejected", _break_bays, True)


def _break_pool(d):
    d["turnaround"]["ground_service"]["battery_pool"]["count"] = 1


sem("R10.11 battery pool exhaustion is rejected", _break_pool, True)


def _break_window(d):
    d["assignments"][0]["serves_ms"][0] = 0     # before ingress completes


sem("R10.3 serving outside performing window is rejected", _break_window, True)

# -------------------------------------------------------------------------
for passed, name, msg in results:
    print(("PASS  " if passed else "FAIL  ") + name + (f"   [{msg[:70]}]" if msg else ""))
failed = sum(1 for p, _, _ in results if not p)
print(f"\n{len(results) - failed}/{len(results)} passed")
sys.exit(1 if failed else 0)
