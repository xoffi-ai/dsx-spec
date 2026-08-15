#!/usr/bin/env python3
"""DSX v0.1-draft — schema-level conformance checks.

Run:  python3 conformance/run_schema_checks.py     (needs: pip install jsonschema)

These are the cheapest half of the suite: they prove the schema REJECTS the
things it must reject. The semantic checks (envelope comparison, RTH
feasibility, fall containment, sampler bit-exactness) are not here yet --
see spec/A-open-questions.md.
"""
import copy, json, pathlib, sys
import copy as _c

try:
    import jsonschema
except ImportError:
    sys.exit("jsonschema not installed: pip install jsonschema")

ROOT = pathlib.Path(__file__).resolve().parent.parent
load = lambda p: json.loads((ROOT / p).read_text())

# Offline $ref resolution. A validator that reaches the network cannot be used
# on a show site without connectivity, and a schema fetch that silently fails
# is worse than no validation at all -- which is exactly the bug this replaced.
# (Whether any jurisdiction mandates an air-gapped toolchain is an open
# question, not an established fact: see spec/A-open-questions.md.)
try:
    from referencing import Registry, Resource
except ImportError:
    sys.exit("referencing not installed: pip install jsonschema referencing")
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

r_nogrp = _c.deepcopy(ROT); del r_nogrp["wave_groups"]
check("waves without wave_groups is rejected", SHOW, r_nogrp, False)

r_l1 = _c.deepcopy(ROT); r_l1["profile"] = "L1"
check("multi-wave outside L2 is rejected", SHOW, r_l1, False)

r_noturn = _c.deepcopy(ROT); del r_noturn["turnaround"]
check("rotation without turnaround is rejected", SHOW, r_noturn, False)

r_nodev = _c.deepcopy(ROT); del r_nodev["assignments"][0]["sortie"]
check("assignment without sortie is rejected", SHOW, r_nodev, False)

check("rotation without ground_service is rejected (R10.10)",
      SHOW, without(ROT, "turnaround", "ground_service"), False)
check("rotation without bays is rejected (R10.10)",
      SHOW, without(ROT, "turnaround", "ground_service", "bays"), False)
check("rotation without throughput is rejected (R10.10)",
      SHOW, without(ROT, "turnaround", "ground_service", "throughput_per_min"), False)
check("swap policy without battery_pool is rejected (R10.11)",
      SHOW, without(ROT, "turnaround", "ground_service", "battery_pool"), False)

r_charge = without(ROT, "turnaround", "ground_service", "battery_pool")
r_charge["turnaround"]["policy"] = "charge_in_place"
check("charge_in_place without battery_pool is accepted (R10.11 scope)",
      SHOW, r_charge, True)

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


def _break_turnaround_gap(d):
    # lands, then relaunches after only 60 s: legal under "after landing",
    # illegal once the turnaround is counted (the bug this test pins)
    w = [x for x in d["waves"] if x["group"] == "A"]
    w[1]["takeoff_ms"] = w[0]["land_complete_ms"] + 60000


sem("R10.5 group relaunch inside the turnaround is rejected",
    _break_turnaround_gap, True)


def _slot_reuse(d):
    # A-001 vacates M1/0,0,0 at takeoff and parks elsewhere for the rest of the
    # show; B-001 then uses the freed slot for its second sortie. This is the
    # launch-field reuse R10.14 exists to permit and MUST NOT be flagged.
    a = d["drones"][0]
    other = {"module": "M1", "column": 1, "row": 0, "level": 0}
    a["sorties"][0]["return_slot"] = dict(other)
    a["sorties"][1]["slot"] = dict(other)
    a["sorties"][1]["return_slot"] = dict(other)
    d["drones"][2]["sorties"][1]["slot"] = {"module": "M1", "column": 0,
                                            "row": 0, "level": 0}


sem("R10.14 slot reuse after the occupant left is accepted", _slot_reuse, False)


def _slot_clash(d):
    # same slot while the first airframe is still standing on it
    a, b = d["drones"][0], d["drones"][1]
    b["sorties"][0]["slot"] = dict(a["sorties"][0]["slot"])


sem("R10.14 two airframes on one slot at once is rejected", _slot_clash, True)


def _weak_separation(d):
    d["handovers"][0]["cross_wave_separation_m"] = 1.0


def _sep(name, mutate, expect_reject):
    from check_rotation import check_separation
    doc = _c.deepcopy(ROT)
    mutate(doc)
    rep = Report()
    check_separation(doc, rep)
    results.append((rep.rejected == expect_reject, name,
                    rep.items[0][2] if rep.items else ""))


_sep("R10.6 cross-wave separation below the show minimum is rejected",
     _weak_separation, True)
_sep("R10.6 valid separation passes", lambda d: None, False)


# --- continuous / cyclic rotation (spec 10.8) -----------------------------
CON = load("examples/continuous-l2/show.json")
check("continuous example is valid", SHOW, CON, True)

c_dur = _c.deepcopy(CON); c_dur["show"]["duration_ms"] = 3600000
check("indefinite show with a fixed duration is rejected", SHOW, c_dur, False)

c_noe = _c.deepcopy(CON); del c_noe["open_ended"]
check("indefinite show without open_ended is rejected", SHOW, c_noe, False)

c_both = _c.deepcopy(CON)
c_both["waves"] = [{"id": "A1", "group": "A", "takeoff_ms": 0,
                    "land_complete_ms": 465000}]
check("waves and wave_cycle together are rejected", SHOW, c_both, False)

c_mask = _c.deepcopy(CON); del c_mask["wave_cycle"]["seam"]["masked_window_ms"]
check("aligned handover without a masked window is rejected", SHOW, c_mask, False)

c_loop = _c.deepcopy(CON); del c_loop["roles"][0]["loop"]
check("open-ended role without a loop is rejected", SHOW, c_loop, False)

c_l1 = _c.deepcopy(CON); c_l1["profile"] = "L1"
check("cyclic rotation outside L2 is rejected", SHOW, c_l1, False)

from check_rotation import check_cyclic, derive_waves


def cyc(name, mutate, expect_reject):
    doc = _c.deepcopy(CON)
    mutate(doc)
    rep = Report()
    check_cyclic(doc, rep)
    results.append((rep.rejected == expect_reject, name,
                    rep.items[0][2] if rep.items else ""))


cyc("valid continuous show passes steady-state checks", lambda d: None, False)


def _too_few_groups(d):
    d["wave_cycle"]["order"] = ["A", "B"]        # 3 required by arithmetic


cyc("R10.15 too few wave groups is rejected", _too_few_groups, True)


def _coverage_gap(d):
    d["wave_cycle"]["template"]["flight_ms"] = 450000   # performs 405s < 420s


cyc("R10.1 cyclic coverage gap is rejected", _coverage_gap, True)


def _small_pool(d):
    d["turnaround"]["ground_service"]["battery_pool"]["count"] = 20


cyc("R10.18 battery pool too small for steady state is rejected",
    _small_pool, True)


def _few_airframes(d):
    # explicit binding, so the slot-index check does not mask this one:
    # under by_slot_index, R10.17 is implied by R10.15 and cannot fail alone.
    d["wave_cycle"]["template"]["role_binding"] = "explicit"
    d["drones"] = d["drones"][:8]


cyc("R10.17 airframe population too small is rejected", _few_airframes, True)


def _few_bays(d):
    d["turnaround"]["ground_service"]["bays"] = 2


cyc("R10.19 ground capacity too small is rejected", _few_bays, True)


def _unmasked(d):
    d["wave_cycle"]["seam"]["masked_window_ms"] = [200000, 300000]


cyc("R10.22 aligned handover outside the masked window is rejected",
    _unmasked, True)


def _aligned_multiple(d):
    # the spec's own worked example: a loop of three wave periods
    d["wave_cycle"]["seam"]["loop_period_ms"] = 1260000
    for r in d["roles"]:
        r["loop"]["period_ms"] = 1260000


cyc("R10.22 an aligned loop spanning three wave periods is accepted",
    _aligned_multiple, False)


def _aligned_not_multiple(d):
    d["wave_cycle"]["seam"]["loop_period_ms"] = 500000


cyc("R10.22 aligned masking with an unrelated loop period is rejected",
    _aligned_not_multiple, True)


def _drifting_but_aligned(d):
    d["wave_cycle"]["seam"]["handover_masking"] = "drifting"


cyc("R10.22 drifting declared where the loop is aligned is rejected",
    _drifting_but_aligned, True)


def _rth_gap(d):
    d["termination"]["rth_availability"]["windows"][1]["to_ms"] = 300000


cyc("R10.23 cyclic RTH map with a gap is rejected", _rth_gap, True)


def _short_drain(d):
    d["open_ended"]["drain"]["duration_ms"] = 60000


cyc("R10.24 drain shorter than a flight is rejected", _short_drain, True)


def _pyro_no_pool(d):
    d["drones"][0]["payloads"] = [{
        "slot": 0, "device_profile": "devices/_template-actuator.dsxp",
        "device_type_id": "00000000-0000-4000-8000-0000000000a1",
        "actuator_class": "pyro",
        "events": [{"t_ms": 120000, "action": "fire"}]}]


cyc("R10.20 consumable fired every cycle without a pool is rejected",
    _pyro_no_pool, True)


def _dup_group(d):
    d["wave_cycle"]["order"] = ["A", "B", "A"]


cyc("R10.5 a group launching twice per rotation is rejected", _dup_group, True)

# R10.16 - the derivation is normative, so it is pinned by a test.
_w = derive_waves(CON["wave_cycle"], 7)
_expect = [("A#1", 0), ("B#1", 420000), ("C#1", 840000), ("A#2", 1260000),
           ("B#2", 1680000), ("C#2", 2100000), ("A#3", 2520000)]
results.append((
    [(w["id"], w["takeoff_ms"]) for w in _w] == _expect,
    "R10.16 wave derivation is deterministic", ""))
_perf = [w["performs_ms"] for w in _w]
results.append((
    all(a[1] == b[0] for a, b in zip(_perf, _perf[1:])),
    "R10.16 derived performing windows tile the timeline", ""))


# --- rotation members are L2-only (S10.9) --------------------------------
l0_rot = _c.deepcopy(OK)
l0_rot["turnaround"] = {"policy": "swap", "min_s": 420}
check("L0 carrying a turnaround block is rejected", SHOW, l0_rot, False)

l0_two = _c.deepcopy(OK)
l0_two["drones"][0]["sorties"] = [
    {"id": "s1", "wave": "A1", "slot": {"module": "M1", "column": 0, "row": 0,
                                        "level": 0}, "takeoff_ms": 0, "land_ms": 1000},
    {"id": "s2", "wave": "A2", "slot": {"module": "M1", "column": 0, "row": 0,
                                        "level": 0}, "takeoff_ms": 2000, "land_ms": 3000}]
check("L0 airframe with two sorties is rejected", SHOW, l0_two, False)

# --- device binding resolves (spec 5) ------------------------------------
# The schema cannot see inside a referenced profile, so a show could name a
# device_type_id or a mode that does not exist and still validate. That is the
# failure spec/05 calls REJECT and BLOCK-FLIGHT, so the suite checks it here.
def binding(name, show_rel):
    d = load(show_rel)
    base = (ROOT / show_rel).parent
    bad = []
    for fl in d.get("fleet", []):
        prof_path = base / fl["device_profile"]
        if not prof_path.exists():
            bad.append(f"{fl['device_profile']} not carried in the archive")
            continue
        prof = json.loads(prof_path.read_text())
        if fl.get("device_type_id") != prof.get("device_type_id"):
            bad.append(f"device_type_id {fl.get('device_type_id')} != "
                       f"profile {prof.get('device_type_id')}")
        if fl.get("device_mode") not in [m["name"] for m in prof.get("modes", [])]:
            bad.append(f"mode {fl.get('device_mode')} not in profile")
        env = fl.get("declared_envelope", {})
        lim = prof.get("flight", {})
        if env.get("peak_speed_xy_ms") and lim.get("max_speed_xy_ms") and \
                env["peak_speed_xy_ms"] > lim["max_speed_xy_ms"]:
            bad.append(f"declared {env['peak_speed_xy_ms']} m/s exceeds "
                       f"profile limit {lim['max_speed_xy_ms']} m/s")
    results.append((not bad, name, "; ".join(bad)))


binding("rotation example: device binding resolves", "examples/rotation-l2/show.json")
binding("continuous example: device binding resolves", "examples/continuous-l2/show.json")

# --- closed objects: a misspelt safety field must not be silently dropped ---
# Before objects were closed, renaming min_separation_m to min_seperation_m
# removed the show-wide separation floor and the file still validated. A
# safety-critical value that disappears on a typo is the worst failure mode a
# format can have, because nothing anywhere reports it.
ROT = load("examples/rotation-l2/show.json")

typo = copy.deepcopy(ROT)
typo["safety"]["min_seperation_m"] = typo["safety"].pop("min_separation_m")
check("a misspelt min_separation_m is rejected", SHOW, typo, False)

invented = copy.deepcopy(ROT)
invented["saftey_override"] = {"ignore_all": True}
check("an unknown top-level member is rejected", SHOW, invented, False)

no_sep = copy.deepcopy(ROT)
del no_sep["safety"]["min_separation_m"]
check("L2 without min_separation_m is rejected", SHOW, no_sep, False)

l1_no_safety = copy.deepcopy(ROT)
l1_no_safety["profile"] = "L1"
del l1_no_safety["safety"]
check("L1 without a safety block is rejected", SHOW, l1_no_safety, False)

# ...but the documented extension carrier still works, or the format would be
# closed to exactly the vendor additions spec/08 promises (§8.1, §8.2).
ext_ok = copy.deepcopy(ROT)
ext_ok["extensions"] = {"XOFFI_solver_report": {"runtime_s": 41}}
ext_ok["show"]["extensions"] = {"VENDOR_cue_list": {"cues": []}}
check("vendor extensions in the extensions carrier are accepted", SHOW, ext_ok, True)

ext_bad = copy.deepcopy(ROT)
ext_bad["extensions"] = {"solverReport": {"runtime_s": 41}}
check("an unprefixed extension name is rejected", SHOW, ext_bad, False)

# --- newly modelled safety objects reject typos too (spec 7.4, 7.5) ---
pi = copy.deepcopy(ROT)
pi["position_integrity"] = {"required": {"min_sats": 6, "max_pdop": 2.5, "rtk": "fixed"}}
check("a well-formed position_integrity block is accepted", SHOW, pi, True)

pi_typo = copy.deepcopy(pi)
pi_typo["position_integrity"]["required"]["max_pdop_"] = pi_typo["position_integrity"]["required"].pop("max_pdop")
check("a misspelt GNSS integrity limit is rejected", SHOW, pi_typo, False)

gz = copy.deepcopy(ROT)
gz["ground_zones"] = {"audience_distance_m": 150,
                      "disarmed_fall_containment": "verified"}
check("ground_zones reusing the termination object's name is rejected",
      SHOW, gz, False)

no_fc = copy.deepcopy(ROT)
del no_fc["termination"]["disarmed_fall_containment"]
check("L2 without disarmed_fall_containment is rejected", SHOW, no_fc, False)

# --- termination completeness -------------------------------------------
no_crth = copy.deepcopy(ROT)
del no_crth["termination"]["coordinated_rth"]
check("escalation naming coordinated_rth without defining it is rejected",
      SHOW, no_crth, False)

cyc = copy.deepcopy(load("examples/continuous-l2/show.json"))
del cyc["termination"]["rth_availability"]["period_ms"]
check("a cyclic RTH map without period_ms is rejected", SHOW, cyc, False)

# -------------------------------------------------------------------------
for passed, name, msg in results:
    print(("PASS  " if passed else "FAIL  ") + name + (f"   [{msg[:70]}]" if msg else ""))
failed = sum(1 for p, _, _ in results if not p)
print(f"\n{len(results) - failed}/{len(results)} passed")
sys.exit(1 if failed else 0)
