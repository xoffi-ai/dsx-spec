# 4. Trajectories, light and normative sampling

## 4.1 Two representations, side by side

DSX supports **segment** tracks and **sampled** tracks, and a file MAY contain
both for the same aircraft.

This is not redundancy for its own sake. Real target hardware expects fixed
frame arrays at rates it does not negotiate — observed export rates in current
tooling include 30 Hz, 5 Hz, and 4 Hz for trajectory with 24 Hz for light. A
purely spline-based format cannot address that half of the market without an
implicit, undocumented conversion. Making both representations first-class, and
the conversion between them normative, removes the ambiguity.

Where both are present, the **segment track is authoritative** and the sampled
track is a derived cache. A validator MUST verify that the sampled track equals
the output of §4.4 within a declared tolerance, and MUST report a mismatch.

## 4.2 Segment tracks

```jsonc
{ "kind": "segments",
  "interp": "bezier",                  // constant | linear | bezier | poly
  "start_ms": 0,
  "segments": [
    { "dt_ms": 2000, "type": "bezier",
      "p": [x, y, z], "c1": [x, y, z], "c2": [x, y, z] }
  ] }
```

Each segment declares its own type; a track MAY mix types. Segment durations
are integer milliseconds and MUST be contiguous.

## 4.3 Sampled tracks — interpolation semantics are declared

```jsonc
{ "kind": "sampled",
  "rate_hz": 30,
  "interp": "linear",                 // hold | linear | cubic — REQUIRED
  "time_semantics": "at_sample",      // at_sample | until_next | since_previous
  "t0_ms": 0,
  "data": [ … ] }
```

`time_semantics` is REQUIRED and has **no default**. At least one published
format encodes time deltas *backwards* — the delta describes the interval
*ending* at the sample, not beginning at it. An importer that assumes the
common convention produces a systematic one-sample offset across the entire
show, which is visible but easy to misattribute. Declaring the semantics costs
one field.

## 4.4 Normative sampling algorithm

The reduction from any DSX track to `t, x, y, z, R, G, B` at rate *f* is
**normative and bit-exact**. Requirements:

1. Sample instants are `t_k = round(k * 1000 / f)` in integer milliseconds,
   with `k` from 0 to `floor(duration_ms * f / 1000)` inclusive.
2. Evaluation is performed in IEEE-754 binary64 throughout.
3. Position results are rounded to **millimetres**, half away from zero.
4. Colour channels are evaluated in the declared colour space (§4.5), then
   quantised to 8 bit with round-half-up, after gamma is applied.
5. Outside the defined interval the value is the nearest boundary value
   (clamp), never an extrapolation.

*(Reference pseudocode and test vectors: `conformance/sampling/`. This section
is not final until those vectors exist — see `A-open-questions.md`.)*

## 4.5 Light

Colour is not "RGB". A light track is expressed against the **luminaire model**
of the bound device profile (§5), which declares its channels, colour space,
gamma and — where known — per-emitter luminous flux.

```jsonc
{ "kind": "light_program",
  "channels": ["R", "G", "B"],        // MUST be a subset of the device mode's channels
  "color_space": "sRGB",
  "ops": [
    { "t_ms": 0,     "op": "set",    "rgb": [255, 0, 0] },
    { "t_ms": 1000,  "op": "fade",   "dur_ms": 500, "rgb": [0, 0, 255] },
    { "t_ms": 4000,  "op": "strobe", "hz": 8, "duty": 0.2, "dur_ms": 2000 }
  ] }
```

Consequences of binding light to the device profile:

- A show authored for a four-channel (RGBW) fleet and replayed on a
  three-channel fleet is a **declared, detectable** mismatch (§5.6), not a
  silently wrong colour.
- Gamma, dimming curve and PWM frequency belong to the **device**, not the show.
  None of the formats surveyed in Appendix B carries them, which is why the same
  show looks different on different hardware.
- White-channel derivation (when a target has W and the source does not, or
  vice versa) is a reader-side mapping governed by the profile — not an
  exporter-side hack.
