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
    if doc.get("wave_cycle"):
        return rep                      # cyclic shows are checked by check_cyclic
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
        turn_ms = doc.get("turnaround", {}).get("min_s", 0) * 1000
        for a, b in zip(ws, ws[1:]):
            earliest = a["land_complete_ms"] + turn_ms
            if b["takeoff_ms"] < earliest:
                rep.err("R10.5", f"group {gid}: wave {b['id']} launches at "
                        f"{b['takeoff_ms']}, but {a['id']} is down at "
                        f"{a['land_complete_ms']} and needs {turn_ms}ms "
                        f"turnaround: earliest is {earliest}ms")

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
    # R10.14 - exclusive in TIME. Reuse by another airframe after the previous
    # occupant has left is the whole point of a rotation launch field, so this
    # compares intervals, not sets of users.
    def _k(sl):
        return (sl["module"], sl["column"], sl["row"], sl["level"])

    occ = defaultdict(list)
    for d in doc.get("drones", []):
        ss = sorted(d.get("sorties", []), key=lambda s: s["takeoff_ms"])
        for i, s in enumerate(ss):
            prev_land = ss[i - 1]["land_ms"] if i else 0
            if s.get("slot"):                       # waiting to depart
                occ[_k(s["slot"])].append((prev_land, s["takeoff_ms"], d["id"], s["id"]))
            back = s.get("return_slot") or s.get("slot")
            if back:                                # parked after landing
                nxt = ss[i + 1]["takeoff_ms"] if i + 1 < len(ss) else None
                occ[_k(back)].append((s["land_ms"], nxt, d["id"], s["id"]))
    for slot, iv in occ.items():
        iv.sort(key=lambda x: x[0])
        for a, b in zip(iv, iv[1:]):
            if a[2] == b[2]:
                continue                            # same airframe
            a_end = a[1] if a[1] is not None else float("inf")
            if b[0] < a_end:
                rep.err("R10.14", f"slot {slot}: {b[2]}/{b[3]} occupies it from "
                        f"{b[0]}ms while {a[2]}/{a[3]} holds it until "
                        f"{a[1] if a[1] is not None else 'end of show'}")

    return rep



# ======================================================================
#  Cyclic rotation - spec section 10.8
#
#  An indefinite show has no timeline to simulate. Validation is inductive:
#  prove one cycle closes and that the state at the end of a cycle is at
#  least as good as at its start. The capacity rules therefore become
#  closed-form inequalities rather than event simulations.
# ======================================================================
import math


def derive_waves(cyc, n):
    """R10.16 - normative derivation. Two conforming tools MUST agree."""
    order, out, seen = cyc["order"], [], defaultdict(int)
    for k in range(n):
        g = order[k % len(order)]
        seen[g] += 1
        t0 = cyc["first_takeoff_ms"] + k * cyc["period_ms"]
        tpl = cyc["template"]
        out.append({
            "id": f"{g}#{seen[g]}", "group": g, "index": k,
            "takeoff_ms": t0,
            "land_complete_ms": t0 + tpl["flight_ms"],
            "performs_ms": [t0 + tpl["ingress_ms"],
                            t0 + tpl["flight_ms"] - tpl["egress_ms"]],
        })
    return out


def check_cyclic(doc, rep):
    cyc = doc.get("wave_cycle")
    if not cyc:
        return rep

    tpl     = cyc["template"]
    period  = cyc["period_ms"]
    flight  = tpl["flight_ms"]
    perform = flight - tpl["ingress_ms"] - tpl["egress_ms"]
    order   = cyc["order"]
    groups  = {g["id"] for g in doc.get("wave_groups", [])}
    turn    = doc.get("turnaround", {})
    turn_s  = turn.get("min_s", 0)
    gs      = turn.get("ground_service", {})
    roles   = doc.get("roles", [])

    if doc.get("waves"):
        rep.err("S10.8", "'waves' and 'wave_cycle' are mutually exclusive")

    # R10.4 applies to cyclic files too (S10.9): a module cannot be the
    # standing ground of two groups that are in the air at different times.
    seen_mod = {}
    for g in doc.get("wave_groups", []):
        for m in g.get("modules", []):
            if m in seen_mod and seen_mod[m] != g["id"]:
                rep.err("R10.4", f"module {m} claimed by groups "
                        f"{seen_mod[m]} and {g['id']}")
            seen_mod[m] = g["id"]

    # ---- group references and uniqueness ------------------------------
    for g in order:
        if g not in groups:
            rep.err("R10.16", f"wave_cycle.order references unknown group {g}")
    if len(set(order)) != len(order):
        rep.err("R10.5", "a group appears twice in one rotation of "
                "wave_cycle.order; two of its waves would be airborne at once")

    # ---- R10.15 minimum group count -----------------------------------
    g_min = math.ceil((flight + turn_s * 1000) / period)
    if len(order) < g_min:
        rep.err("R10.15", f"{len(order)} wave groups declared, needs "
                f"{g_min} = ceil(({flight} + {turn_s * 1000}) / {period}); "
                f"the fleet would have a hole of "
                f"{(flight + turn_s * 1000) - (len(order) * period)}ms per cycle")

    # ---- gapless, conflict-free role coverage --------------------------
    if perform < period:
        rep.err("R10.1", f"each wave performs {perform}ms but launches are "
                f"{period}ms apart: {period - perform}ms unserved every cycle")
    elif perform > period:
        rep.err("R10.3", f"each wave performs {perform}ms with a {period}ms "
                f"period: two waves would serve the same role for "
                f"{perform - period}ms")

    # ---- aircraft per wave and slot binding ----------------------------
    per_group = defaultdict(dict)
    for d in doc.get("drones", []):
        if d.get("group") is not None and d.get("slot_index") is not None:
            per_group[d["group"]].setdefault(d["slot_index"], []).append(d["id"])
    n_wave = len(roles)
    if tpl.get("role_binding") == "by_slot_index":
        for g in order:
            slots = per_group.get(g, {})
            want = set(range(n_wave))
            have = set(slots)
            if have != want:
                rep.err("R10.16", f"group {g}: slot indices {sorted(have)} do "
                        f"not match roles 0..{n_wave - 1}")
            for i, ids in slots.items():
                if len(ids) > 1:
                    rep.err("R10.16", f"group {g} slot {i} claimed by {ids}")

    # ---- steady state: lambda = aircraft launched per second -----------
    lam = n_wave / (period / 1000.0)

    # R10.17 airframes
    need_air = math.ceil(lam * (flight / 1000.0 + turn_s))
    have_air = len([d for d in doc.get("drones", []) if d.get("group") in groups])
    if have_air < need_air:
        rep.err("R10.17", f"{have_air} airframes, steady state needs "
                f"{need_air} = {lam:.4f}/s x ({flight/1000:.0f}s flight + "
                f"{turn_s:.0f}s turnaround)")

    # R10.18 batteries
    pool = gs.get("battery_pool")
    if pool and turn.get("policy") == "swap":
        need_bat = math.ceil(lam * (flight / 1000.0 + pool["charge_time_s"]))
        if pool["count"] < need_bat:
            rep.err("R10.18", f"battery pool {pool['count']}, steady state "
                    f"needs {need_bat} = {lam:.4f}/s x ({flight/1000:.0f}s "
                    f"flight + {pool['charge_time_s']:.0f}s charge); the show "
                    f"fails at the charger, not in the air")

    # R10.19 ground capacity
    bays = gs.get("bays")
    if bays is not None:
        need_bays = math.ceil(lam * turn_s)
        if bays < need_bays:
            rep.err("R10.19", f"{bays} bays, steady state needs {need_bays}")
    thr = gs.get("throughput_per_min")
    if thr is not None and thr < lam * 60 - 1e-9:
        rep.err("R10.19", f"throughput {thr}/min, steady state needs "
                f"{lam * 60:.2f}/min")

    # ---- R10.12 energy closure (per sortie, from the template) ---------
    en = doc.get("energy", {}).get("per_sortie", {})
    if en.get("budget_s") is not None:
        allowance = en["budget_s"] * (1 - en.get("reserve_pct", 0) / 100.0)
        use = tpl.get("energy_use_s", flight / 1000.0)
        if use > allowance + 1e-9:
            rep.err("R10.12", f"template sortie uses {use:.0f}s of "
                    f"{allowance:.0f}s allowance")

    # ---- R10.20 consumable closure -------------------------------------
    pools = {c["actuator_class"]: c for c in gs.get("consumable_pools", [])}
    fired = set()
    for d in doc.get("drones", []):
        for pl in d.get("payloads", []):
            if pl.get("events"):
                fired.add(pl.get("actuator_class") or pl.get("device_profile"))
    for cls in sorted(fired):
        c = pools.get(cls)
        if c is None:
            rep.err("R10.20", f"actuator '{cls}' is fired every cycle but has "
                    f"no consumable pool; batteries recirculate, charges do not")
            continue
        if c.get("reload_time_s", 0) > turn_s:
            rep.err("R10.20", f"'{cls}' reload {c['reload_time_s']}s exceeds "
                    f"turnaround {turn_s}s")
        need = math.ceil(lam * (flight / 1000.0 + c.get("reload_time_s", 0)))
        if c.get("replenished", True) and c["count"] < need:
            rep.err("R10.20", f"'{cls}' pool {c['count']}, steady state needs {need}")

    # ---- R10.21 loop continuity ----------------------------------------
    for r in roles:
        lp = r.get("loop")
        if lp is None:
            rep.err("R10.21", f"role {r['id']} has no loop declaration in a "
                    f"cyclic show")
            continue
        if lp.get("continuity") != "c1":
            rep.warn("R10.21", f"role {r['id']} loops with "
                     f"{lp.get('continuity')} continuity; velocity may jump "
                     f"at the seam")
        if lp["period_ms"] % period and period % lp["period_ms"]:
            rep.warn("R10.22", f"role {r['id']} loop {lp['period_ms']}ms and "
                     f"wave period {period}ms are unrelated; the changeover "
                     f"drifts through the piece")

    # ---- R10.22 handover masking ---------------------------------------
    seam = cyc.get("seam", {})
    loop_p = seam.get("loop_period_ms")
    masking = seam.get("handover_masking")
    if masking == "aligned":
        if loop_p % period:
            rep.err("R10.22", f"handover declared aligned but the loop period "
                    f"{loop_p}ms is not a multiple of the wave period "
                    f"{period}ms; the changeover drifts and cannot be masked "
                    f"by a fixed window")
        else:
            # The window is a phase within ONE wave period. An aligned loop of
            # k wave periods holds k changeovers; they all share this phase,
            # which is exactly why one window is enough.
            win = seam.get("masked_window_ms")
            transfer = tpl["ingress_ms"] % period
            if win and not (win[0] <= transfer <= win[1]):
                rep.err("R10.22", f"handover is aligned but the role transfer "
                        f"at phase {transfer}ms lies outside the masked window "
                        f"{win}: the audience sees the same swap every "
                        f"{period // 1000}s, forever")
            for k in range(1, loop_p // period):
                assert (tpl["ingress_ms"] + k * period) % period == transfer
    elif masking == "drifting" and loop_p % period == 0:
        rep.err("R10.22", f"handover declared drifting but the loop period "
                f"{loop_p}ms is a multiple of the wave period {period}ms: the "
                f"changeover does not drift, it recurs at the same phase")

    # ---- R10.23 cyclic termination map ---------------------------------
    rth = doc.get("termination", {}).get("rth_availability", {})
    if rth:
        if not rth.get("cyclic"):
            rep.err("R10.23", "cyclic show: rth_availability must be declared "
                    "cyclic and cover one period")
        elif rth.get("period_ms") != period:
            rep.err("R10.23", f"rth_availability period {rth.get('period_ms')} "
                    f"!= wave period {period}")
        else:
            merged, overlaps = _merge([(w["from_ms"], w["to_ms"])
                                       for w in rth.get("windows", [])])
            if not merged or merged[0][0] > 0 or merged[-1][1] < period or \
                    len(merged) > 1:
                rep.err("R10.23", f"rth_availability does not cover [0,{period}] "
                        f"without gaps: {merged}")
    else:
        rep.err("R10.23", "cyclic show without an RTH availability map")

    # ---- R10.24 drain ---------------------------------------------------
    oe = doc.get("open_ended")
    if cyc.get("repeat") == "indefinite":
        if oe is None:
            rep.err("R10.24", "indefinite repeat without an open_ended block")
        else:
            drain = oe.get("drain", {})
            if drain.get("duration_ms", 0) < flight:
                rep.err("R10.24", f"drain takes {drain.get('duration_ms')}ms but "
                        f"an airborne wave needs {flight}ms to come down")
            if not drain.get("stop_launching"):
                rep.err("R10.24", "drain plan does not stop launching")
        if doc.get("show", {}).get("duration_ms") is not None:
            rep.err("R10.24", "indefinite repeat requires show.duration_ms = null")
    return rep


def check_separation(doc, rep):
    """R10.6 - cross-wave separation must not undercut the show minimum.

    Applies to enumerated and cyclic files alike: a handover is the one moment
    where two waves share airspace, so it is the one moment where a laxer
    number would be least defensible.
    """
    floor = doc.get("safety", {}).get("min_separation_m")
    if floor is None:
        return rep
    for h in doc.get("handovers", []):
        s = h.get("cross_wave_separation_m")
        if s is not None and s < floor:
            rep.err("R10.6", f"handover {h['id']}: cross-wave separation {s}m "
                    f"is below the show minimum {floor}m")
    for f in doc.get("fleet", []):
        d = f.get("declared_envelope", {}).get("min_separation_m")
        if d is not None and d > floor:
            rep.err("R10.6", f"fleet {f['id']} declares {d}m but safety."
                    f"min_separation_m is {floor}m")
    return rep


def main(paths):
    failed = False
    for p in paths:
        doc = json.load(open(p))
        rep = Report()
        check(doc, rep)
        check_cyclic(doc, rep)
        check_separation(doc, rep)
        status = "REJECT" if rep.rejected else "OK"
        print(f"{status:7s} {p}")
        rep.print()
        failed |= rep.rejected
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or ["examples/rotation-l2/show.json"]))
