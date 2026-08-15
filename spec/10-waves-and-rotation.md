# 10. Waves, Sorties and Rotation Operation

> Status: v0.1-draft. No prior art exists in any published or observed show
> format for the functionality described in this section.

## 10.1 The problem

Every show format examined during the development of DSX — `.skyc`, Skybrush
CSV, `.dac`, `.path` / `.path3`, Drotek JSON, VVIZ — models exactly **one**
takeoff and **one** landing for the entire fleet. The identity of an aircraft
and its place in the choreography are the same thing: drone *n* flies
trajectory *n*, from the ground, back to the ground, once.

That model has a hard ceiling: **the show can never be longer than one battery
charge.**

A longer show swaps its aircraft while running. Groups land, are recharged or
re-batteried, and **launch again** into the same show. The audience sees one
continuous piece; underneath it the fleet circulates. With enough ground
capacity a show of a few hundred aircraft can run for hours on a population
sized for minutes.

This is **rotation operation**. It is not expressible in any existing format,
and it is not a niche feature — it is the precondition for any show that
outlasts a battery.

## 10.2 Three levels, not one

DSX separates three things that all other formats collapse into a single
object:

| Level | Object | Meaning | Lifetime |
|---|---|---|---|
| Artistic | **Role** (`roles[]`) | one voice in the choreography — a moving point of light in the artwork | the whole show |
| Physical | **Airframe** (`drones[]`) | one aircraft with a serial number | the whole show |
| Operational | **Sortie** (`drones[].sorties[]`) | one takeoff-to-landing flight of an airframe | one battery |

A role is served by a sequence of **sorties**. An airframe performs a sequence
of **sorties** separated by turnarounds. The two sequences are independent:
role *r0147* may be served by an airframe from group A in the first hour and by
a completely different airframe in the second, while airframe *A-017* may serve
three different roles across its three sorties.

```jsonc
"roles": [
  { "id": "r0147",
    "trajectory": "traj/r0147.poly",   // continuous, whole show
    "light":      "light/r0147.lp",
    "active_ms":  [15000, 3615000] }
],

"drones": [
  { "id": "A-017", "fleet": "grp-A", "serial": "UV-IFO-2291",
    "home": { "x": 42.0, "y": 18.0, "z": 0.0, "heading_deg": 0.0 },
    "battery_policy": "swap",
    "sorties": [
      { "id": "s1", "wave": "A1",
        "slot": { "module": "M1", "column": 2, "row": 1, "level": 0 },
        "takeoff_ms": 0, "land_ms": 465000,
        "ingress": { "path": "traj/in_A017_s1.poly",  "window_ms": [0, 15000] },
        "egress":  { "path": "traj/out_A017_s1.poly", "window_ms": [435000, 450000] },
        "energy_use_s": 450 },
      { "id": "s2", "wave": "A2",
        "slot": { "module": "M1", "column": 2, "row": 1, "level": 0 },
        "takeoff_ms": 900000, "land_ms": 1365000,
        "energy_use_s": 450 }
    ] }
],

"assignments": [
  { "role": "r0147", "sortie": "A-017/s1", "serves_ms": [15000, 435000] },
  { "role": "r0147", "sortie": "B-017/s1", "serves_ms": [435000, 855000] },
  { "role": "r0147", "sortie": "A-017/s2", "serves_ms": [915000, 1335000] }
]
```

**Rule R10.1 — Coverage.** For every role, the `serves_ms` intervals of its
assignments MUST cover the role's `active_ms` range with no gap and no overlap.
A validator MUST reject a file in which a role is unserved at any instant at
which its trajectory is defined.

**Rule R10.2 — Ingress and egress are not choreography.** The path from a
launch slot to the point where a sortie takes over a role, and from the point
where it leaves a role to its landing slot, is owned by the **sortie**, not by
the role. The artwork stays editable independently of the logistics: a designer
changes the choreography, the ingress/egress planner recomputes underneath it.
In `.skyc` these are the same polynomial and cannot be separated.

**Rule R10.3 — A sortie serves at most one role at a time.** Assignments
referring to the same sortie MUST NOT overlap in time, and each MUST lie
entirely within that sortie's airborne interval, inset by its ingress and
egress windows.

## 10.3 Wave groups and waves

Rotation requires distinguishing a recurring *group* from its individual
*launches*.

- A **wave group** is a set of launch modules and the aircraft stationed in
  them. It persists for the whole show.
- A **wave** is one launch instance of a group. A group launches many times.

```jsonc
"wave_groups": [
  { "id": "A", "modules": ["M1", "M2"] },
  { "id": "B", "modules": ["M3", "M4"] }
],

"waves": [
  { "id": "A1", "group": "A", "takeoff_ms":       0, "land_complete_ms":  465000 },
  { "id": "B1", "group": "B", "takeoff_ms":  420000, "land_complete_ms":  885000 },
  { "id": "A2", "group": "A", "takeoff_ms":  840000, "land_complete_ms": 1305000 },
  { "id": "B2", "group": "B", "takeoff_ms": 1260000, "land_complete_ms": 1725000 }
]
```

**Rule R10.4 — Whole modules, exclusively owned.** Wave groups MUST own launch
modules exclusively; the module sets of two groups MUST NOT intersect.

The reason is operational. A group that owns whole modules empties them
completely and can return into them without conflict. A group spread across
mixed columns of shared modules has no conflict-free return, and in rotation
operation it has no conflict-free *re-launch* either, because the modules it
would return into are occupied by aircraft of another group waiting to depart.
This costs nothing if planned from the start and cannot be repaired later.
Deliberate sharing requires the extension `XOFFI_mixed_modules` and is not
conformant to the base specification.

**Rule R10.5 — A group's waves must not overlap.** Two waves of the same group
MUST NOT be airborne simultaneously: the second launch of a group cannot begin
before the first has completely landed and been serviced. Formally,
`takeoff_ms` of a wave MUST be greater than or equal to `land_complete_ms` of
the preceding wave of the same group, plus the applicable turnaround (§10.6).

## 10.4 Handover windows

The hazardous moment is when two waves are airborne at once: the outgoing wave
is descending with depleted batteries while the incoming wave has already taken
over the choreography. In rotation operation this is not a one-off event at the
end of the show — it recurs at every changeover, potentially dozens of times.
DSX models it as a first-class object rather than leaving it implicit.

```jsonc
"handovers": [
  { "id": "h1", "from_wave": "A1", "to_wave": "B1",
    "window_ms": [420000, 465000],
    "both_airborne": true,
    "cross_wave_separation_m": 4.0,
    "corridors": ["in-B1", "out-A1"],
    "roles_transferred": ["r0001", "…", "r0300"],
    "abort_action": "hold_incoming" }
]
```

**Rule R10.6 — Cross-wave separation is an independent value.** The minimum
separation between aircraft of *different* waves during a handover window MUST
be declared separately and MUST be greater than or equal to the in-show
separation. Descending aircraft near their reserve and climbing aircraft on
full batteries have different failure behaviour; the distance that is safe
inside a formation is not automatically safe between waves.

**Rule R10.7 — Handover windows are termination-aware.** Every handover window
MUST appear in the RTH feasibility map (§7). A rotation show has, by
construction, recurring moments in which two populations share a volume with
different energy reserves. Where no coordinated RTH exists for such a window,
the file MUST declare which escalation levels remain available, exactly as for
any other infeasible window.

## 10.5 Corridors

Ingress and egress paths are how one wave passes through the airspace of
another. They are declared explicitly and are machine-checkable.

```jsonc
"corridors": [
  { "id": "out-A1", "wave": "A1", "type": "egress",
    "polygon": "geo/corridor_out_a.json",
    "alt_band_m": [5, 30],
    "active_ms": [435000, 465000],
    "must_not_intersect": ["flight_volume:B1"] }
]
```

**Rule R10.8 — Corridors must not cross an active flight volume.** An ingress
or egress corridor MUST NOT intersect the flight volume of any wave performing
during the corridor's active window. A validator MUST compute this intersection
and MUST reject the file if it is non-empty, unless the corridor carries an
explicit, signed `accepted_risk` annotation.

The practical consequence is a layout rule: **the modules of the group that is
currently landing belong at the edge of the launch field**, not in its centre.
Central placement forces every descending aircraft through the volume of the
performing wave. In rotation operation this repeats at every changeover, so a
poor layout is not paid for once but on every cycle. DSX therefore makes it a
declared and validated property of the file rather than an operator habit.

## 10.6 Turnaround and ground service — the real limit

In a single-wave show, endurance is an operational concern. In rotation
operation the **ground** is the bottleneck, not the air. How long a show can
run is decided by how fast landed aircraft can be made ready again, and by how
many can be serviced in parallel.

```jsonc
"turnaround": {
  "policy": "swap",                    // swap | charge_in_place | none
  "min_s": 420,                        // land -> ready to launch again
  "components_s": {
    "cooldown": 60, "recover": 120, "service": 90, "stage": 150
  },
  "ground_service": {
    "bays": 120,                       // aircraft serviceable in parallel
    "crew": 8,
    "throughput_per_min": 30,          // aircraft made ready per minute
    "battery_pool": { "count": 900, "charge_time_s": 2700 }
  }
}
```

**Rule R10.9 — Turnaround closure.** For two consecutive sorties of the same
airframe, `takeoff_ms` of the later sortie minus `land_ms` of the earlier MUST
be greater than or equal to `turnaround.min_s`. A validator MUST reject a file
that violates this. This is the single most common way a rotation plan fails on
paper, and it is trivially checkable.

**Rule R10.10 — Ground service capacity.** At no instant may the number of
airframes simultaneously in ground service exceed `ground_service.bays`, and
the rate at which aircraft must be made ready MUST NOT exceed
`throughput_per_min`. A show whose changeovers are individually valid can still
be infeasible because two groups need servicing at the same time.

**Rule R10.11 — Battery pool closure.** Where `policy` is `swap`, the number of
charged batteries available at each launch MUST be at least the number of
aircraft launching, given `count` and `charge_time_s`. A validator MUST simulate
the pool over the show timeline. A rotation show is a queueing system, and its
batteries are the queue.

**Rule R10.12 — Energy closure per sortie.** For every sortie:

```
ingress_s + served_s + egress_s  <=  budget_s * (1 - reserve_pct / 100)
```

`budget_s` is the gross usable endurance of a full battery; `reserve_pct` is the
fraction that MUST remain unflown at landing. A validator MUST reject a file in
which any sortie exceeds this allowance.

**Rule R10.13 — Energy is per sortie, not per model.** Endurance is a property
of this airframe with this battery at this temperature, declared on the sortie
or the airframe — never on the device profile (`.dsxp`). The profile declares
what the type is *capable* of; the show declares what this unit is *planned* to
do. This is the same capability/intent split as §5, and violating it is how a
designer silently writes flight limits larger than the hardware supports.

```jsonc
"energy": {
  "model": "declared",                 // declared | measured | conservative
  "per_sortie": {
    "budget_s": 620, "reserve_pct": 25,
    "margin_policy": "reject_on_exceed"
  }
}
```

## 10.7 Launch stack and silo slots

Rotation presumes a structured launch field. DSX describes it in three
dimensions, because racked and multi-level launch systems place aircraft above
one another and the vertical index is part of both departure and return order.

```jsonc
"launch_stack": {
  "modules": [
    { "id": "M1", "origin_m": [42.0, 18.0], "bearing_deg": 0.0,
      "columns": 4, "rows": 4, "levels": 3,
      "spacing_m": { "x": 1.2, "y": 1.2, "z": 0.35 } }
  ]
}
```

A sortie's `slot` is `{ module, column, row, level }`. A sortie MAY return to a
different slot than it departed from; the file states both, and a validator
checks that no slot is occupied by two airframes at the same time across the
whole show — a constraint that does not exist in single-launch formats because
there, occupancy is trivially static.

§7's requirement that a disarmed aircraft's fall be contained applies during
stacked departure and return as well, where an aircraft may be directly above
another.

## 10.8 Conformance

Rotation operation is an **L2 (Production)** feature.

| Level | Requirement |
|---|---|
| L0 / L1 | `wave_groups`, `waves`, `handovers`, `corridors`, `assignments`, `turnaround` MUST be absent; each airframe has at most one sortie |
| L2 | Where more than one wave is declared, ALL of R10.1 – R10.13 apply |

**Rule R10.14 — No silent degradation.** A reader that does not implement this
section MUST treat a multi-wave file as `REJECT` (§5.6). Partially interpreting
a rotation show — for example by reading only the first wave, or by reading only
the first sortie of each airframe — produces a file that flies, is missing most
of its aircraft, and gives no indication that anything is wrong. This is the one
case in DSX where degrading gracefully is explicitly forbidden.
