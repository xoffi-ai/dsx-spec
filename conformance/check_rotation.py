#!/usr/bin/env python3
"""
DSX rotation-operation validator (spec section 10).

Implements the rules that JSON Schema structurally cannot express: interval
coverage, exclusivity, turnaround closure, energy closure and ground-service
capacity. These are the rules that decide whether a rotation show is flyable,
so they are the ones that matter.

Exit code 0 = conformant, 1 = violations found.
"""
import json, sys
from collections import defaultdict


class Report:
    def __init__(self):
        self.items = []          # (severity, rule, message)

    def err(self, rule, msg):
        self.items.append(("REJECT", rule, msg))

    def warn(self, rule, msg):
        self.items.append(("WARN", rule, msg))

    @property
    def rejected(self):
        return any(s == "REJECT" for s, _, _ in self.items)

    def print(self):
        for sev, rule, msg in self.items:
            print(f"  {sev:7s} {rule:7s} {msg}")
        if not self.items:
            print("  (no findings)")


def _merge(intervals):
    """Merge sorted intervals, reporting overlaps."""
    out, overlaps = [], []
    for a, b in sorted(intervals):
        if out and a < out[-1][1]:
            overlaps.append((out[-1], (a, b)))
            out[-1] = (out[-1][0], max(out[-1][1], b))
        elif out and a == out[-1][1]:
            out[-1] = (out[-1][0], b)
        else:
            out.append((a, b))
    return out, overlaps


def check(doc, rep):
    is_rotation = len(doc.get("waves", [])) > 1 or any(
        len(d.get("sorties", [])) > 1 for d in doc.get("drones", []))
    if not is_rotation:
        return rep

    waves = {w["id"]: w for w in doc.get("waves", [])}
    groups = {g["id"]: g for g in doc.get("wave_groups", [])}
    turn = doc.get("turnaround", {})
    min_turn = turn.get("min_s", 0)
    energy = doc.get("energy", {}).get("per_sortie", {})
    allowance = None
    if energy.get("budget_s") is not None:
        allowance = energy["budget_s"] * (1 - energy.get("reserve_pct", 0) / 100.0)

    # index sorties
    sorties = {}
    for d in doc.get("drones", []):
        for s in d.get("sorties", []):
            sorties[f"{d['id']}/{s['id']}"] = (d, s)

    # ---- R10.4 module exclusivity across groups -------------------------
    owner = {}
    for gid, g in groups.items():
        for m in g.get("modules", []):
            if m in owner:
                rep.err("R10.4", f"module {m} claimed by groups {owner[m]} and {gid}")
            owner[m] = gid

    # ---- R10.5 waves of one group must not overlap ----------------------
    by_group = defaultdict(list)
    for w in doc.get("waves", []):
        by_group[w.get("group")].append(w)
    for gid, ws in by_group.items():
        ws.sort(key=lambda w: w["takeoff_ms"])
        for a, b in zip(ws, ws[1:]):
            if b["takeoff_ms"] < a["land_complete_ms"]:
                rep.err("R10.5", f"group {gid}: wave {b['id']} launches at "
                        f"{b['takeoff_ms']} before {a['id']} is down at "
                        f"{a['land_complete_ms']}")

    # ---- R10.9 turnaround closure per airframe --------------------------
    for d in doc.get("drones", []):
        ss = sorted(d.get("sorties", []), key=lambda s: s["takeoff_ms"])
        for a, b in zip(ss, ss[1:]):
            gap = (b["takeoff_ms"] - a["land_ms"]) / 1000.0
            if gap < min_turn:
                rep.err("R10.9", f"{d['id']}: {gap:.0f}s between {a['id']} and "
                        f"{b['id']}, needs {min_turn:.0f}s")
            if b["takeoff_ms"] < a["land_ms"]:
                rep.err("R10.9", f"{d['id']}: sortie {b['id']} starts before "
                        f"{a['id']} lands")

    # ---- R10.12 energy closure per sortie -------------------------------
    if allowance is not None:
        for key, (d, s) in sorties.items():
            use = s.get("energy_use_s")
            if use is None:
                air = (s["land_ms"] - s["takeoff_ms"]) / 1000.0
                use = air
                rep.warn("R10.12", f"{key}: no energy_use_s, using airborne time "
                         f"{air:.0f}s")
            if use > allowance + 1e-9:
                rep.err("R10.12", f"{key}: uses {use:.0f}s of {allowance:.0f}s "
                        f"allowance ({energy['budget_s']:.0f}s minus "
                        f"{energy.get('reserve_pct',0):.0f}% reserve)")

    # ---- R10.1 role coverage, R10.3 sortie exclusivity ------------------
    per_role = defaultdict(list)
    per_sortie = defaultdict(list)
    for a in doc.get("assignments", []):
        lo, hi = a["serves_ms"]
        if hi <= lo:
            rep.err("R10.1", f"assignment {a['role']}<-{a['sortie']} has "
                    f"non-positive duration")
        per_role[a["role"]].append((lo, hi))
        per_sortie[a["sortie"]].append((lo, hi, a["role"]))
        if a["sortie"] not in sorties:
            rep.err("R10.1", f"assignment references unknown sortie {a['sortie']}")

    for r in doc.get("roles", []):
        want = r.get("active_ms")
        got = per_role.get(r["id"], [])
        if not got:
            rep.err("R10.1", f"role {r['id']} has no assignment")
            continue
        merged, overlaps = _merge(got)
        for x, y in overlaps:
            rep.err("R10.1", f"role {r['id']}: overlapping assignments {x} and {y}")
        if want:
            if len(merged) > 1:
                gaps = [(merged[i][1], merged[i+1][0]) for i in range(len(merged)-1)]
                rep.err("R10.1", f"role {r['id']} unserved during {gaps}")
            elif merged[0][0] > want[0] or merged[0][1] < want[1]:
                rep.err("R10.1", f"role {r['id']} active {want} but only served "
                        f"{list(merged[0])}")

    for sid, items in per_sortie.items():
        merged, overlaps = _merge([(a, b) for a, b, _ in items])
        for x, y in overlaps:
            rep.err("R10.3", f"sortie {sid} serves two roles at once: {x} / {y}")
        if sid in sorties:
            _, s = sorties[sid]
            lo = s.get("ingress", {}).get("window_ms", [s["takeoff_ms"]])[-1]
            hi = s.get("egress", {}).get("window_ms", [s["land_ms"]])[0]
            for a, b, role in items:
                if a < lo or b > hi:
                    rep.err("R10.3", f"sortie {sid} serves {role} during "
                            f"[{a},{b}], outside performing window [{lo},{hi}]")

    # ---- R10.10 ground service capacity ---------------------------------
    gs = turn.get("ground_service", {})
    bays = gs.get("bays")
    if bays:
        events = []
        for d in doc.get("drones", []):
            ss = sorted(d.get("sorties", []), key=lambda s: s["takeoff_ms"])
            for i, s in enumerate(ss[:-1]):
                events.append((s["land_ms"], +1))
                events.append((s["land_ms"] + int(min_turn * 1000), -1))
        cur = peak = 0
        for t, delta in sorted(events):
            cur += delta
            peak = max(peak, cur)
        if peak > bays:
            rep.err("R10.10", f"{peak} airframes in service simultaneously, "
                    f"only {bays} bays")

    # ---- R10.11 battery pool closure ------------------------------------
    pool = gs.get("battery_pool")
    if pool and turn.get("policy") == "swap":
        charge_ms = int(pool["charge_time_s"] * 1000)
        launches = sorted((s["takeoff_ms"], f"{d['id']}/{s['id']}")
                          for d in doc.get("drones", [])
                          for s in d.get("sorties", []))
        returns = sorted(s["land_ms"] for d in doc.get("drones", [])
                         for s in d.get("sorties", []))
        available = pool["count"]
        ri = 0
        for t, key in launches:
            while ri < len(returns) and returns[ri] + charge_ms <= t:
                available += 1
                ri += 1
            if available <= 0:
                rep.err("R10.11", f"no charged battery available for {key} at "
                        f"t={t}ms (pool {pool['count']}, charge "
                        f"{pool['charge_time_s']:.0f}s)")
            available -= 1

    # ---- slot occupancy -------------------------------------------------
    occ = defaultdict(list)
    for key, (d, s) in sorties.items():
        sl = s.get("slot")
        if sl:
            occ[(sl["module"], sl["column"], sl["row"], sl["level"])].append(
                (d["id"], s["takeoff_ms"]))
    for slot, users in occ.items():
        owners = {u for u, _ in users}
        if len(owners) > 1:
            rep.err("R10.7", f"slot {slot} used by several airframes: "
                    f"{sorted(owners)}")

    return rep


def main(paths):
    failed = False
    for p in paths:
        doc = json.load(open(p))
        rep = check(doc, Report())
        status = "REJECT" if rep.rejected else "OK"
        print(f"{status:7s} {p}")
        rep.print()
        failed |= rep.rejected
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or ["examples/rotation-l2/show.json"]))
