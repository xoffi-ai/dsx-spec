# 10. Waves, Sorties and Rotation Operation

> Status: v0.1-draft. No prior art for the functionality described in this
> section was found in the formats surveyed in Appendix B. Formats for which no
> sample could be obtained (A28) were not assessed.

## 10.1 The problem

Of the formats for which a sample or a public specification was actually
obtained — `.skyc` / `.skyb` (Appendix B.1), Skybrush CSV, VVIZ — none models
more than **one** takeoff and **one** landing per airframe. The identity of an
aircraft and its place in the choreography are the same thing: drone *n* flies
trajectory *n*, from the ground, back to the ground, once.

For `.dac`, `.bin`, `.path` / `.path3` and Drotek JSON **no sample was
obtained** (A28), so nothing is claimed about them here. If any of them does
model aircraft rotation, this section is wrong and the correction is welcome —
see [`CONTRIBUTING.md`](../CONTRIBUTING.md).

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

**Rule R10.13 — Planned energy is per sortie, not per model.** Endurance in
practice is a property of *this* airframe, with *this* battery, at *this*
temperature. The device profile MAY declare `endurance_s` as a **type
capability** (§5.3) — that is what the profile is for — but a planner or
validator **MUST NOT** take the planned energy budget of a sortie from it. The
budget MUST come from `energy.per_sortie` or from the airframe. The profile
declares what the type is *capable* of; the show declares what this unit is
*planned* to do. This is the same capability/intent split as §5, and violating it is how a
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
different slot than it departed from; the file states both.

**Rule R10.14 — Slot occupancy is exclusive in time, not for the whole show.**
An airframe occupies its departure slot until `takeoff_ms`, and its
`return_slot` (defaulting to `slot`) from `land_ms` until it next departs. Two
airframes MUST NOT occupy the same slot over overlapping intervals. Reuse of a
slot by a *different* airframe once the previous occupant has left is explicitly
permitted and is how a launch field smaller than the fleet is flown — a
validator that forbids it has misread this rule and has forbidden rotation
itself. This constraint does not exist in single-launch formats, where
occupancy is trivially static.

§7's requirement that a disarmed aircraft's fall be contained applies during
stacked departure and return as well, where an aircraft may be directly above
another.

## 10.8 Unbounded rotation and continuous operation

§10.1–§10.7 describe a show that rotates a *finite* number of times. The
limiting case is a show that does not stop: a fleet circulating indefinitely,
the audience seeing one uninterrupted piece for an entire evening, a festival
night, or the opening hours of a permanent installation.

Two things are required for this, and DSX provides both.

### 10.8.1 No upper bound

**Rule R10.15 — The number of wave groups and the number of waves per group
are unbounded.** A conforming file MAY declare any number of wave groups, and
any number of waves per group. A reader, validator or exporter MUST NOT impose
a fixed maximum, and MUST NOT assume two groups, or three, or any other count.

This is a statement about implementations, not about files. Every observed
format hard-codes exactly one launch and one landing; the natural next mistake
is to hard-code two alternating groups, because two is what a single changeover
looks like. Two is almost never the right number. The group count follows from
arithmetic:

```
G_min  =  ceil( (flight_ms + turnaround_ms) / period_ms )
```

where `period_ms` is the interval between successive launches — for gapless
role coverage, the time one wave actually performs. A group is unavailable from
its takeoff until it is serviced and ready again; the fleet needs as many
groups as fit into that unavailability.

With 465 s of flight and 420 s of turnaround at a 420 s period, `G_min` is 3,
not 2: two groups leave a 30 s hole in the choreography on every cycle. The
same arithmetic with a faster turnaround yields 2, and with hot-swap crews and
long endurance it can yield 2 again at a much longer period. There is no
correct constant. A validator MUST compute `G_min` and MUST reject a file that
declares fewer groups.

### 10.8.2 Cyclic declaration

An indefinite show cannot enumerate its waves, its sorties or its assignments —
there are infinitely many. It declares the *rule* that generates them instead.

```jsonc
"wave_cycle": {
  "period_ms": 420000,
  "order": ["A", "B", "C"],          // round-robin launch order
  "first_takeoff_ms": 0,
  "repeat": "indefinite",            // or an integer number of launches
  "template": {
    "flight_ms":  465000,            // takeoff -> landed
    "ingress_ms":  15000,            // takeoff -> takes over its role
    "egress_ms":   30000,            // leaves its role -> landed
    "role_binding": "by_slot_index"  // slot k of the performing wave serves role k
  },
  "seam": {
    "loop_period_ms": 1260000,       // choreography period: 3 x period_ms
    "continuity": "c1",
    "handover_masking": "aligned",   // aligned | drifting
                                     // window below is phase within period_ms
    "masked_window_ms": [10000, 25000]
  }
}
```

`wave_cycle` and the explicit `waves` array are mutually exclusive. In cyclic
mode the wave, sortie and assignment enumerations are *derived*, not written:

```
launch index k = 0, 1, 2, …
  group     = order[k mod len(order)]
  wave id   = "<group>#<n>"          n = number of previous launches of that group, 1-based
  takeoff   = first_takeoff_ms + k * period_ms
  performs  = [takeoff + ingress_ms, takeoff + flight_ms - egress_ms]
  role r_i  = served by the airframe at slot index i of the performing wave
```

**Rule R10.16 — Derivation is normative.** The generation rule above is part of
the specification, not an implementation detail. Two conforming tools MUST
derive identical wave identifiers, takeoff times and role assignments from the
same `wave_cycle`. Generated identifiers are stable and may be referenced from
elsewhere in the file, from logs and from approval documents.

`role_binding: "by_slot_index"` is what makes this scale: a 5000-aircraft
continuous show declares three groups, one template and one role list. Nothing
grows with the running time, and nothing grows with the number of cycles.

### 10.8.3 Steady state replaces simulation

A finite rotation show is validated by simulating its timeline (§10.6). An
indefinite show has no timeline to simulate. Its validation is inductive: prove
that **one** cycle is internally valid, and that the state at the end of a cycle
is at least as good as the state at its start. If both hold, every cycle holds.

This turns the capacity rules into closed-form inequalities. With a launch rate

```
λ = aircraft_per_wave / period_s      [aircraft per second]
```

the steady-state requirements are:

| Resource | Requirement | Rule |
|---|---|---|
| Airframes | `count >= λ · (flight_s + turnaround_s)` | R10.17 |
| Batteries (`policy: swap`) | `pool.count >= λ · (flight_s + charge_time_s)` | R10.18 |
| Service bays | `bays >= λ · service_s` | R10.19 |
| Crew throughput | `throughput_per_min >= λ · 60` | R10.19 |

**Rule R10.17 — Airframe closure.** The declared airframe population MUST
satisfy the inequality above. Aircraft that are flying or being serviced are not
available to launch.

**Rule R10.18 — Battery closure in steady state.** Where `turnaround.policy` is
`swap`, the battery pool MUST satisfy the inequality above. A battery is out of
circulation for its flight *and* its entire charge time; a pool sized for one
changeover is not a pool sized for continuous operation, and the difference is
usually a factor of several. A validator MUST compute this and MUST reject a
file that cannot sustain its own cycle. **A continuous show fails at the
charger, not in the air.**

**Rule R10.19 — Ground capacity in steady state.** Bays and crew throughput
MUST satisfy the inequalities above. Peak simultaneous service in cyclic mode is
a steady-state quantity, not a one-off event.

**Rule R10.20 — Consumable closure.** Any actuator (§6) with a finite
`trigger.shots` that is fired in a cyclic show MUST declare a reload in
`turnaround.components_s` and a consumable pool that closes exactly like the
battery pool. Batteries recirculate; pyrotechnic charges, confetti loads and
recovery devices do not. An aircraft that returns to the air with an empty
launcher will fly the choreography and produce no effect, and nothing in any
existing format makes that visible before the show. In DSX the file states it or
is rejected.

### 10.8.4 The seam

A looping show has a moment where the choreography returns to its beginning.
That moment is visible to the audience on every cycle, which is more scrutiny
than any other instant of the show receives.

**Rule R10.21 — Loop continuity.** Where a role's trajectory loops, position
and velocity at the end of the loop period MUST match those at its start to
within the declared tolerance (`continuity: "c1"`). A file whose roles jump at
the seam MUST be rejected. Colour SHOULD be continuous across the seam as well;
where it is not, the discontinuity MUST be declared, because an intentional
blackout at the seam and an accidental colour jump are indistinguishable to a
validator but not to an audience.

**Rule R10.22 — Handover masking is declared, not accidental.** The
choreography's loop period and the wave period interact. Where
`loop_period_ms` is an integer multiple of `period_ms` (including equal), the
handover is **aligned**: every changeover falls on the same instant of the
artwork, on every cycle, forever. Such a file MUST declare
`handover_masking: "aligned"` and a `masked_window_ms` — the passage in which
the changeover is artistically intended, typically a dark or sparse bar written
to hide it.

`masked_window_ms` is expressed as a phase **within one wave period**, not
within the loop period. This matters: an aligned loop of three wave periods
contains three changeovers, at phases `ingress_ms`, `ingress_ms + period_ms`
and `ingress_ms + 2 × period_ms`. All of them land on the same phase of the
wave period and therefore on the same masked window, which is precisely why a
single declared window suffices. Expressing the window in loop time would
describe only the first of them and silently leave the rest unmasked.

A validator MUST reject a file in which the role transfer at
`ingress_ms mod period_ms` falls outside the declared window, and MUST reject
`handover_masking: "aligned"` where `loop_period_ms` is not a multiple of
`period_ms` — that combination is a declaration the geometry does not support.

Where the two periods are unrelated, the handover is **drifting**: the
changeover migrates through the piece and MUST therefore be flyable, and
acceptable to watch, at every phase. Both are legitimate; leaving it undeclared
is not, because an aligned handover in a bright, dense passage is the one the
audience sees on every single cycle and the designer never tested.

**Rule R10.23 — Termination maps are cyclic too.** In cyclic mode the RTH
feasibility map (§7) and the handover windows (R10.7) are declared over **one**
period and apply modulo that period. A validator MUST verify that the map covers
the full period with no gap. An indefinite show without a defined abort at every
phase of its cycle is not conformant.

### 10.8.5 An endless show still has to end

`repeat: "indefinite"` describes the choreography, not the operation. Every real
continuous show ends: an approval expires, a crew reaches its duty limit,
weather moves in, the venue closes.

```jsonc
"open_ended": {
  "min_ms": 3600000,               // planned minimum running time
  "max_continuous_ms": 21600000,   // hard stop: permit, duty time, wear
  "limited_by": ["permit", "crew_duty", "battery_cycles"],
  "drain": {
    "trigger": "operator_command",
    "stop_launching": true,
    "roles_release": "on_cycle_end",
    "duration_ms": 465000
  }
}
```

**Rule R10.24 — A drain plan is mandatory.** Where `show.duration_ms` is `null`
and `open_ended` is present, the file MUST declare `max_continuous_ms` and a
`drain` plan describing how the show comes to a planned end: launching stops,
airborne waves complete their current assignment, roles are released in a
declared order, the fleet lands. Draining is not terminating (§7): it is the
normal, unhurried ending of a show that had no fixed length. A file that can
start indefinitely but cannot stop deliberately is not conformant.

### 10.8.6 Field summary

Everything §10.8 adds, in one place, so an implementer reading only the
specification can write a conforming cyclic file:

| Member | Where | Meaning |
|---|---|---|
| `wave_cycle` | top level | generative wave declaration; excludes `waves` |
| `wave_cycle.period_ms` | | interval between successive launches |
| `wave_cycle.order` | | round-robin launch order of groups; unbounded (R10.15) |
| `wave_cycle.first_takeoff_ms` | | phase of the first launch |
| `wave_cycle.repeat` | | `"indefinite"` or an integer launch count |
| `wave_cycle.template` | | `flight_ms`, `ingress_ms`, `egress_ms`, `role_binding`, `energy_use_s` — one sortie, applied to every derived wave |
| `wave_cycle.seam` | | `loop_period_ms`, `continuity`, `handover_masking`, `masked_window_ms` (R10.21) |
| `roles[].loop` | role | `period_ms`, `continuity`, `tolerance`, `colour_continuous` (R10.21) |
| `drones[].group`, `drones[].slot_index` | airframe | binding under `role_binding: "by_slot_index"` (R10.16) |
| `handovers[].cyclic`, `.phase_ms` | handover | cycle-relative template instead of `from_wave`/`to_wave`/`window_ms` |
| `corridors[].cyclic`, `.phase_ms`, `.group` | corridor | cycle-relative template instead of `wave`/`active_ms` |
| `turnaround.ground_service.consumable_pools[]` | ground | `actuator_class`, `count`, `reload_time_s`, `replenished` (R10.20) |
| `termination.rth_availability.cyclic`, `.period_ms` | termination | the map repeats every period and MUST cover it (R10.23) |
| `open_ended` | top level | `min_ms`, `max_continuous_ms`, `limited_by[]`, `drain{}` (R10.24) |
| `show.duration_ms: null` | show | REQUIRED with `repeat: "indefinite"`, forbidden otherwise |

In cyclic mode `handovers` and `corridors` carry **one** entry each per
recurring pattern, expressed as a phase within `period_ms` — not one entry per
occurrence. A file that enumerated them per occurrence would grow without bound
and defeat the purpose of §10.8.

## 10.9 Conformance

Rotation operation is an **L2 (Production)** feature.

| Level | Requirement |
|---|---|
| L0 / L1 | `wave_groups`, `waves`, `wave_cycle`, `handovers`, `corridors`, `assignments`, `turnaround`, `open_ended` MUST be absent; each airframe has at most one sortie |
| L2, explicit waves | ALL of R10.1 – R10.14 apply |
| L2, cyclic (`wave_cycle`) | R10.2, R10.4, R10.6 – R10.8, R10.13, R10.14 and R10.15 – R10.24 apply; the enumerated rules R10.1, R10.3, R10.5, R10.9 – R10.12 are discharged by their steady-state equivalents. R10.2 applies because the template owns ingress/egress exactly as a sortie does; R10.13 applies because the planned energy budget is still taken per airframe, never from the device profile; R10.14 applies because derived sorties occupy slots over intervals across all cycles |

`waves` and `wave_cycle` MUST NOT both be present. `wave_cycle` with
`repeat: "indefinite"` REQUIRES `show.duration_ms: null` and `open_ended`
(R10.24).

**Rule R10.25 — No silent degradation.** A reader that does not implement this
section MUST treat a multi-wave or cyclic file as `REJECT` (§5.6). Partially
interpreting a rotation show — by reading only the first wave, only the first
sortie of each airframe, or by treating a `wave_cycle` as a single launch —
produces a file that flies, is missing most of its aircraft, and gives no
indication that anything is wrong. This is the one case in DSX where degrading
gracefully is explicitly forbidden.
