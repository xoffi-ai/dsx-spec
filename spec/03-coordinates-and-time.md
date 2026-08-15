# 3. Coordinates, altitude and time

Both objects in this chapter are **REQUIRED at every profile, including L0.**
They are the single largest source of conversion error between existing tools,
because every existing format leaves at least one of them implicit.

## 3.1 Coordinate frame

```jsonc
"frame": {
  "type": "ENU",                     // ENU | NED  — REQUIRED, no default
  "handedness": "right",             // REQUIRED — declared, never assumed
  "units": "m",
  "origin": { "lat": 22.5431, "lon": 114.0579,
              "alt_m": 12.4,
              "alt_ref": "AMSL",     // AGL | AMSL | ELLIPSOID | TAKEOFF — REQUIRED
              "geoid": "EGM2008",    // REQUIRED when alt_ref = AMSL
              "datum": "WGS84" },
  "bearing_deg": 0.0                 // rotation of show +Y (ENU north) — REQUIRED
}
```

Rules:

- `alt_ref` **MUST** be present. There is no default. A show authored against
  AGL and flown against AMSL is a documented category of accident.
- `geoid` **MUST** be present when `alt_ref` is `AMSL`.
- `handedness` **MUST** be present. At least one widely used show format is
  Y-up with an inverted Z relative to its own authoring tool; without an
  explicit declaration, importers guess.
- Geographic coordinate order in DSX is always **`lat`, `lon`** as named
  fields, never a positional pair. (Positional `[lon, lat]` in GeoJSON
  resources under `geo/` follows RFC 7946 and is unaffected.)
- `bearing_deg` rotates the show frame relative to true north. A rotation error
  of a few degrees has been a contributing factor in a public accident.

## 3.2 Time

```jsonc
"time": {
  "base": "ms",                       // integer milliseconds from t=0
  "start": { "mode": "gnss_tow" },    // gnss_tow | countdown | external
  "timecode": { "smpte": "30", "offset_ms": 0 },   // OPTIONAL, for pyro/media sync
  "time_source": {
    "primary": "gnss",
    "holdover": { "source": "rtc_disciplined",
                  "max_drift_ms_per_min": null,   // null = not characterised
                  "on_exceed": "hold" },
    "fallback": "countdown"
  }
}
```

- Show time is **integer milliseconds** from `t = 0`. Frame rate is a property
  of *sampling*, never of the data (§4).
- **Interval convention.** Every time interval in DSX — every `*_ms` pair,
  every `[from_ms, to_ms]`, `active_ms`, `serves_ms`, `window_ms` and every
  `windows[]` entry — is **half-open**: `[from, to)`. The start instant belongs
  to the interval, the end instant does not. Two intervals that share an
  endpoint (`[0, 435000)` and `[435000, 855000)`) are therefore **contiguous,
  not overlapping**, and together they cover `[0, 855000)` without a gap.
  Readers and validators MUST use this convention; without it, rules that
  forbid gaps *and* overlaps at the same time (R10.1) cannot be satisfied.
- `time_source` exists because of a structural property of the state of the
  art: in a typical implementation the show clock and the position solution
  come from **the same GNSS receiver**. Loss of GNSS therefore costs the
  aircraft both *where it is* and *when it is*, simultaneously.
- **No public source characterises show-clock holdover behaviour after GNSS
  loss.** `max_drift_ms_per_min` is therefore `null` by default and SHOULD be
  populated from measurement. Declaring the value is the point; DSX does not
  invent one.
- `on_exceed` states what happens when holdover drift exceeds the declared
  budget. It is a safety decision and belongs in the file, not in a manual.
