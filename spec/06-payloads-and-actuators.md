# 6. Payloads and actuators

## 6.1 State of the art, and why it is not enough

The only event type present in the dominant onboard show format is
pyrotechnics, and its encoding is a relay: a channel is switched **on** or
**off** at a timestamp. There is no duration, no pre-fire time, no direction,
no arm/disarm state, no mass change, no hazard description. Richer fields exist
in some authoring formats but are **not present in what is uploaded to the
aircraft**.

Verified against public test fixtures, the onboard event record is 10 bytes —
timestamp, type, subtype, payload — with exactly one defined type. Multiple
channels firing at the same instant is legal and occurs in the fixtures, so any
model must express simultaneity and check interlocks across all channels of an
aircraft at once.

DSX therefore does not hard-code "pyro". **A payload is itself a device**, with
its own profile, in the same way a fixture may contain child fixtures in
GDTF.

## 6.2 The authority rule

This is the load-bearing rule of the chapter.

> An actuator with `"authority": "show"` **MUST NOT** be triggered by the
> safety chain.
> An actuator with `"authority": "safety"` **MUST NOT** appear on the show
> timeline.

A recovery parachute is `authority: "safety"`. A choreography can therefore not
deploy it, and a validator **MUST** REJECT a file that tries. A gerb is
`authority: "show"`; the termination logic may *inhibit* it (§7) but never
*fire* it. Inhibiting and firing are different verbs and different privileges.

## 6.3 Actuator profile

```jsonc
{
  "dsxp": "0.1",
  "device_type_id": "…UUID…",
  "device_class": "actuator",
  "manufacturer": "…", "model": "…",
  "revision": { "id": "…", "date": "…" },   // REQUIRED in every .dsxp (§5)

  "actuator": {
    "class": "pyro",          // pyro | recovery | dispenser | smoke | flame
                              // | laser | audio | gimbal | release | generic
    "subtype": "gerb",
    "authority": "show",      // show | safety   — see §6.2

    "trigger": {
      "mode": "one_shot",             // one_shot | repeatable | continuous
      "reversible": false,
      "prefire_latency_ms": 380,      // command → visible effect
      "latency_jitter_ms": 40,
      "effect_duration_ms": 15000,
      "cooldown_ms": null,
      "shots": 1
    },

    "dynamics": {                     // effect on the aircraft
      "mass_before_kg": 0.180, "mass_after_kg": 0.095,
      "cg_shift_m": [0, 0, -0.01],
      "thrust_reaction_n": 1.2, "thrust_direction": [0, 0, -1]
    },

    "hazard": {                       // effect on the surroundings
      "ejecta_range_m": 12, "ejecta_cone_deg": 25,
      "thermal": true, "debris_fallout_m": 18,
      "sound_db_at_10m": null, "eye_hazard_class": null
    },

    "interlocks": {                   // when firing MUST NOT happen
      "min_altitude_agl_m": 25,
      "max_tilt_deg": 20,
      "requires_arm": true,
      "auto_disarm_on": ["hard_fence_breach", "link_loss",
                         "escalation>=land_in_place", "attitude_exceeded"],
      "inhibit_zones": ["geo/audience.json"],
      "auth": "signed_key_per_show"
    }
  }
}
```

## 6.4 Why these four groups exist

**`prefire_latency_ms`** — the effect must be visible *on* the beat, so ignition
must precede it. Without this field, musical synchronisation of pyrotechnics is
guesswork, and it is guesswork that differs per product.

**`dynamics`** — an aircraft that ejects 85 g flies differently afterwards.
This belongs in trajectory validation, not in a footnote. It is also why a
payload profile is bound per aircraft and not per fleet.

**`hazard`** — `ejecta_range_m` and `debris_fallout_m` are inputs from which a
validator computes the required ground safety area, together with the
containment requirement of §7. This connects the choreography to the ground
geometry that regulators actually specify.

**`interlocks`** — the conditions under which firing is forbidden, expressed so
that they can be enforced onboard rather than remembered by an operator.

## 6.5 Trust models are not uniform

Two different threats require two different protections, and treating them as
one produces the wrong design:

| Path | Threat | Requirement |
|---|---|---|
| Flight termination | an attacker **prevents** a legitimate shutdown | authenticity and availability; termination must not be blockable |
| Payload firing (pyro, flame, release) | an attacker **causes** an illegitimate discharge | access control; per-show key, arm state required |

The asymmetry is not symmetric in consequence: an unauthorised flight kill
drops an aircraft; an unauthorised discharge injures people on the ground.
Encrypted, addressed firing systems are documented in the pyrotechnic domain,
whereas link encryption is **not** uniformly present in show flight-control
systems — which is why DSX requires payload authentication at L2 and does not
require it of the flight channel.

DSX therefore requires payload authentication at L2 but does **not** claim that
encrypted flight control is current practice. Requiring it would make every
existing system non-conformant on day one; declaring it honestly makes the
gap visible.
