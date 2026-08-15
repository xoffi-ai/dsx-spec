# 7. Safety and termination

## 7.1 Principles

**Termination is a ladder, not a button.** Independently developed systems have
converged on the same four rungs, which DSX adopts as normative vocabulary:

| Step | Meaning | Reversible |
|---|---|---|
| `hold` | freeze the show timeline; aircraft hold position | yes |
| `coordinated_rth` | pre-computed, collision-free return | no — it runs to completion |
| `land_in_place` | descend where you are | no |
| `disarm` | motors off | no — last resort |

**One action per rung.** Each rung MUST be triggerable by a **single operator
action**.

> **Scope note (normative).** This is a requirement on the *operating system* —
> the ground station and its interface — not on the file, and §1.1 places
> ground-station behaviour outside what DSX specifies. It is therefore **not
> verifiable by `conformance/`**, which tests files and readers. It is stated
> here because the vocabulary above is worthless if the rungs cannot be reached
> in time, and it is the one requirement in this document addressed to
> integrators rather than to files. A file-level, checkable representation
> (declaring the action count per rung) is an open question — see A29.

This is stated normatively because of a documented accident in which
aircraft were already falling and the pilot did not abort — the reported reason
being the number of steps involved in pausing the show, which made continuing
appear to be the safer option. A termination path that is too cumbersome to use
is not a termination path.

**Independent of playback.** The termination channel is **not** sampled at the
show frame rate and is **not** a function of the player. Termination data MUST
be evaluable **onboard**, without a connection to the ground station, and is
therefore part of the compiled `.dsb`, not only of the `.dsx` manifest. At
fleet sizes now normal, per-aircraft manual intervention is not physically
possible; automatic onboard mitigation is the only mechanism that scales.

### 7.1.1 The `safety` object — the show-wide floor

```jsonc
"safety": {
  "min_separation_m": 2.5,
  "geofence": "geo/fence.json"
}
```

`safety` is REQUIRED at **L1 and L2**. `min_separation_m` is the minimum
permitted centre-to-centre distance between any two aircraft at any instant,
and it is the single most safety-critical scalar in the file.

It sits at document level, not per fleet, because separation is a property of
the **airspace**, not of a device type. A show flying two fleets with different
airframes still has exactly one distance that must not be undercut, and the
larger of two per-type values is not automatically the correct one for the pair.

Per-type limits stay in the device profile (§5). The relationship is one-way: a
fleet's `declared_envelope.min_separation_m` **MUST NOT** be smaller than the
show-wide floor. A fleet may need *more* room than the show demands; it may
never be allowed less. `conformance/check_rotation.py` enforces this direction.

At L0 the object is optional, because an L0 file makes no safety claim at all —
it is a position and colour track and nothing more (§9).

## 7.2 The termination object

```jsonc
"termination": {
  "channel": "independent",
  "escalation": ["hold", "coordinated_rth", "land_in_place", "disarm"],

  // naming a rung obliges the file to define it
  "coordinated_rth": { "precomputed": true, "recompute_interval_ms": 15000,
                       "cancellable": false },

  "rth_availability": {
    "default_interval_ms": 15000,
    "adaptive": true,
    "windows": [
      { "from_ms": 0,      "to_ms": 92000,  "interval_ms": 15000, "feasible": true },
      { "from_ms": 92000,  "to_ms": 108000, "feasible": false,
        "reason": "dense_transition",
        "available_escalation": ["hold", "land_in_place", "disarm"] },
      { "from_ms": 108000, "to_ms": 480000, "interval_ms": 15000, "feasible": true }
    ]
  },

  "geofence": {
    "soft": { "type": "bubble", "radius_m": 4.0,
              "action": "auto_land", "timeout_ms": 1500 },
    "hard": { "type": "polygon", "ref": "geo/hardfence.json", "action": "disarm" }
  },

  "link_loss": { "heartbeat_timeout_ms": 5000, "action_on_loss": "autonomous_fts" },

  "fallback_channel": { "required_for_profile": "L2",
                        "independent_hardware": true, "auth": "signed_key" },

  "disarmed_fall_containment": { "required": true, "verified": false }
}
```

REQUIRED members of `termination`: `channel`, `escalation`, `geofence` and
`link_loss`. At **L2**, `disarmed_fall_containment` is REQUIRED as well (§7.5),
and naming a rung in `escalation` obliges the file to define the object that
configures it — an escalation ladder with an undefined rung is a ladder with a
missing step.

## 7.3 RTH availability — a map, not an interval

Pre-computing return branches periodically is established practice. DSX changes
one thing: **the interval is not the whole answer.**

The interval is the **maximum additional exposure time** — trigger at t=47 s
with the next branch at t=60 s and the show continues for 13 s while something
is going wrong. A default of **15 000 ms** is specified for that reason. The
cost is modest: a return branch is on the order of a few kilobytes per aircraft,
so halving the interval roughly doubles a per-aircraft budget that remains well
within typical onboard flash. The real cost is deconfliction computation, which
is a pre-flight expense.

But a fixed interval is the wrong construct on its own: **in a dense
transition, a collision-free return may not exist at all.** Branches every 15 s
do not help if six of them are infeasible.

Therefore `windows` is a **feasibility map over the show timeline**. For every
instant, the file states which rungs are actually available. Two consequences:

- The operator interface shows *"RTH unavailable — hold or land"* instead of an
  RTH button that would not work.
- The validator can report, before the show: *"between 92 s and 108 s there is
  no safe retreat for 16 s — do you want to change the choreography?"*

This is the point at which a file format becomes a safety tool.

## 7.4 GNSS integrity — position **and** time

Loss of GNSS is commonly modelled as a position problem. It is also a **time**
problem (§3.2): show clock and position solution typically originate in the
same receiver.

```jsonc
"position_integrity": {
  "required": { "min_sats": 6, "max_pdop": 2.5, "max_eph_m": 3.0, "rtk": "fixed" },
  "degradation_policy": {
    "rtk_fixed_to_float": { "action": "continue", "min_separation_scale": 1.5 },
    "rtk_to_single":      { "action": "hold" },
    "position_lost":      { "action": "coordinated_rth_if_available_else_land" }
  },
  "estimator_trust": {
    "independent_check_required": true,
    "dead_reckoning_budget_s": 8
  }
},

"interference_policy": {
  "monitor": ["jamming_state", "spoofing_state", "authentication_state",
              "agc", "noise_per_ms"],
  "on_jamming_detected":  { "fleet_action": "hold", "notify": true },
  "on_spoofing_detected": { "fleet_action": "land_in_place", "reject_gnss": true },
  "glitch_reset_guard": { "max_glitch_s": 5 }
}
```

Rationale for the three non-obvious fields:

**`estimator_trust.independent_check_required`** — a bubble geofence compares
the *estimated* position against the commanded position. If the estimator
diverges, the fence diverges with it: it stops protecting precisely when
protection is needed. An integrity check that does not depend on the same
estimate is therefore required, and DSX records whether one exists.

**`glitch_reset_guard.max_glitch_s`** — a common autopilot implementation
resets its state estimate to the GNSS solution after a glitch persists for a
period documented as roughly seven seconds. A spoofer that pulls slowly rather
than jumping is therefore rewarded by the recovery logic, and conventional
failsafes do not fire because everything appears self-consistent. The guard
value is specified below that window.

**`interference_policy.monitor`** — the relevant fields (jamming state,
spoofing state, GNSS authentication status including OSNMA) already exist in
mainstream autopilot telemetry. **No regulation currently requires anyone to
act on them.** Multiple mass-loss events at public shows have been publicly
attributed to interference or "compromised positional accuracy", with the
common pattern that the standard reaction to lost positioning is *land* — so
under area-wide interference every aircraft does the correct thing
simultaneously, and they descend simultaneously. The systems do not
malfunction; the response does not scale. Declaring a fleet-level policy is the
minimum a file format can contribute.

## 7.5 Environment and ground geometry

```jsonc
"environment_envelope": {
  "wind_max_ms": 8.0, "temp_min_c": -5.0, "humidity_max_pct": 90,
  "precipitation": "none"
},

"ground_zones": {
  "projection_clearance_m": 30,
  "audience_distance_m": 150,
  "rings": [ { "to_m": 10, "type": "isolation" },
             { "to_m": 20, "type": "buffer" } ],
  "fall_containment_status": "verified"
}
```

`projection_clearance_m` is the margin around the **vertical projection of the
maximum image area** that must be clear of people — a geometry that is
computable directly from the choreography, and one that at least one
jurisdiction specifies numerically.

**`disarmed_fall_containment`** is REQUIRED at L2. The safety area MUST contain
the fall trajectory of a disarmed aircraft from **every** position the show
reaches. Where payloads are present, `hazard.debris_fallout_m` (§6) enters the
same computation.

> **What `v0.1` requires, and what it does not.** DSX does **not** yet define
> the fall model — drag, tumbling, mass and area assumptions and the wind case
> are not specified, so two validators can legitimately reach different
> verdicts on the same geometry. Until a model is specified (A30), the
> **checkable** obligation is one of disclosure, not of geometry: the file MUST
> record `model`, the tool and version that computed it, the wind case used,
> and the result — and a reader MUST NOT report the containment as verified
> when `verified: false`. A declared, attributable, falsifiable claim is worth
> more than a number whose derivation nobody can reproduce; claiming a
> geometric guarantee the specification cannot yet define would be exactly the
> behaviour this project exists to replace.

Audience are **uninvolved persons** for risk-assessment purposes; this cannot
be defined away organisationally and must be carried geometrically.

## 7.6 Recovery systems

Recovery devices are actuators with `authority: "safety"` (§6.2). Where fitted,
DSX follows the structure of the applicable industry standard for parachute
systems: an **autonomous trigger independent of the flight-critical system**, a
**manual trigger** independent of it, and a **flight termination** function that
stops the motors.

Deployment altitude is **not** a fixed value in DSX. It is a per-type, tested
property and belongs in the device profile.

Recovery systems are **OPTIONAL**, including at L2. They are available as an
option on show aircraft in this class but are not standard equipment, and the
documented mitigation strategy for swarms is coordinated return plus contained
fallout rather than per-aircraft recovery. Requiring them would make the
specification describe a world that does not exist.
