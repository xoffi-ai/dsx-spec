# 5. Device profiles (`.dsxp`)

## 5.1 The problem this solves

No format in current use declares, in a machine-readable way, **what aircraft a
show was written for**.

- The dominant open-source binary format carries no device identity at all — no
  model, no firmware, no LED channel count, no flight limits.
- One major vendor's route format does carry a device identifier, but as a
  closed integer enumeration whose capability implications exist only as prose
  in a documentation table.
- One visualisation format carries `airframe`, `colorType` and `lumens`
  fields — and its own specification states that such auxiliary terms have no
  meaning and may be ignored by readers.

Where hardware requirements do exist, they are buried in exporter source code
as fixed frame rates and hard-coded flags, or in a closed-source server.

The result is that hardware compatibility is established by human memory. This
does not scale to mixed fleets, and mixed fleets are now normal: a single
operator may hold three vendor ecosystems simultaneously.

**Note on data quality.** Vendor documentation is not always self-consistent —
for at least one widely used show aircraft, the specification table and the
marketing text on the same page disagree about whether the LED has a white
channel. This is precisely why `null` (unknown) is a first-class value and why
profiles record the source of each number.

## 5.2 Structure: capability and intent are separate files

DSX adopts the split that the entertainment-lighting industry already
standardised (GDTF/MVR, DIN SPEC 15800/15801):

| File | Role | Answers |
|---|---|---|
| `.dsxp` | device profile | *what can this device do?* |
| `.dsx` | show | *which devices, doing what, in which mode?* |

An author cannot widen a hardware limit by editing the show, because the limit
is not in the show.

## 5.3 Aircraft profile

```jsonc
{
  "dsxp": "0.1",
  "device_type_id": "9F2C4E10-…-A1",     // UUID — STABLE across all revisions
  "device_class": "aircraft",
  "manufacturer": "…", "model": "…",
  "revision": { "id": "2024-rev3", "date": "…", "modified_by": "…" },

  "light": {
    "channels": ["R", "G", "B"],          // explicit; never inferred
    "emitters": [ { "channel": "R", "luminous_flux_lm": 270, "source": "datasheet 2024-06" } ],
    "color_space": { "mode": "sRGB", "gamma": 2.2 },
    "pwm_hz": null,
    "beam_angle_deg": 140
  },

  "flight": {
    "max_speed_xy_ms": 10.0, "max_speed_z_up_ms": 4.0, "max_speed_z_down_ms": 3.0,
    "max_accel_xy_ms2": null, "max_accel_z_ms2": null, "max_yaw_rate_dps": null,
    "min_nav_altitude_m": null,
    "endurance_s": null, "mass_kg": null,
    "position_accuracy_m": { "horizontal": 0.1, "vertical": 0.2, "requires": "rtk_fixed" }
  },

  "payload_slots": [
    { "index": 0, "position": "bottom", "max_mass_kg": 0.25,
      "interfaces": ["pwm", "i2c"], "power": { "v": 5, "max_a": 2 },
      "mount": { "pan_range_deg": [0, 0], "tilt_range_deg": [-90, 0] } }
  ],

  "modes": [
    { "name": "rgb-30hz-fixed",
      "trajectory_rate_hz": { "required": 30 },
      "light_rate_hz": { "required": 30 },
      "channels": ["R", "G", "B"],
      "capabilities": ["dsx.core", "dsx.light.rgb"] }
  ],

  "firmware": [
    { "range": ">=4.1.0", "modes": ["rgb-4hz", "rgb-30hz-fixed"] }
  ]
}
```

## 5.4 Binding a show to a profile

```jsonc
"fleet": [
  { "id": "grp-A", "count": 300,
    "device_profile": "devices/vendor@model@2024-rev3.dsxp",
    "device_type_id": "9F2C4E10-…-A1",   // redundant on purpose: catches swapped profiles
    "device_mode": "rgb-4hz",            // MUST exist in the profile's modes[]
    "min_firmware": "4.1.0",
    "declared_envelope": {               // what the show actually demands
      "peak_speed_xy_ms": 7.4, "peak_speed_z_up_ms": 3.1,
      "peak_accel_xy_ms2": 3.0,
      "min_separation_m": 2.5,
      "uses_channels": ["R", "G", "B"]
    } }
]
```

`declared_envelope` states the **measured demand of this show**, computed by the
authoring tool. The validator's job is then a comparison, not a simulation.

## 5.5 Identity rules

1. `device_type_id` is a **UUID and MUST NOT change** across revisions of the
   same model. Revision and firmware are separate axes.
2. Capabilities are **prefixed strings**, never a bitmask. Bitfields age badly;
   the reserved-and-deprecated flags in long-lived protocols are the evidence.
3. A profile value of `null` means **unknown** and MUST NOT be treated as zero,
   unlimited, or any other default.
4. Every numeric value SHOULD carry a `source`.

## 5.6 Error semantics — three levels

This separation does not exist in any current format, and it is the reason DSX
can be used as a gate rather than as a hint.

| Level | Trigger | Required behaviour |
|---|---|---|
| **REJECT** | unknown entry in `extensions_required`; `device_mode` absent from the profile; missing REQUIRED field | refuse to load the file |
| **BLOCK-FLIGHT** | `declared_envelope` exceeds a profile limit; firmware below `min_firmware`; a channel used that the mode does not have; rate mismatch with a `required` rate | visualisation MAY proceed; **upload to aircraft MUST be refused** |
| **WARN** | a relevant profile value is `null`; unknown entry in `extensions_used`; sampled track deviates from segments within tolerance | proceed, log, surface to the operator |

A visualiser may be permissive. An uploader **MUST NOT** be. Conflating the two
is how a show reaches the flight line unchecked.
