# 4. Trajectories, light and normative sampling

This section is the wire format. Everything else in DSX describes context; this
describes the numbers that make an aircraft move and glow. It is written to be
implementable from this document alone, without reference to any existing
product, and every rule here is exercised by `conformance/run_sampling_checks.py`.

Key words per BCP 14, as stated in `spec/README.md`.

## 4.1 Two representations, side by side

DSX supports **segment** tracks and **sampled** tracks, and a file MAY contain
both for the same aircraft.

This is not redundancy for its own sake. Real target hardware expects fixed
frame arrays at rates it does not negotiate — export rates observed in the
material surveyed for Appendix B include 30 Hz, 5 Hz and 4 Hz for trajectory
with 24 Hz for light. A purely spline-based format cannot address that half of
the market without an implicit, undocumented conversion. Making both
representations first-class, and the conversion between them normative, removes
the ambiguity.

Where both are present, the **segment track is authoritative** and the sampled
track is a derived cache. A validator MUST verify that the sampled track equals
the output of §4.4 within a declared tolerance, and MUST report a mismatch.

All three resource kinds are separate JSON documents inside the archive (§2.1),
each validated against `schema/resource.schema.json`.

### 4.1.1 Units and frames, restated

Positions are metres in the show frame of §3. Times are **integer
milliseconds**. A resource carries no coordinate metadata of its own: it
inherits the frame, handedness, altitude reference and time origin declared in
the manifest. A resource file separated from its manifest is not interpretable,
and MUST NOT be treated as if it were.

### 4.1.2 Evaluation is a pure function

For every track kind this section defines a function

```
value(t) : integer milliseconds → position (metres) or channel levels
```

Two conforming implementations MUST return the same `value(t)` for the same
input, up to the rounding rules of §4.4.4. `value` MUST NOT depend on the
evaluation order, on previously requested instants, on frame rate, or on any
state carried between calls. Playback systems that integrate state across
frames cannot be validated, and their output cannot be compared against a
reference — which is why this constraint is normative rather than advisory.

## 4.2 Segment tracks

```jsonc
{ "kind": "segments",
  "interp": "bezier",                  // declared default; each segment may override
  "start_ms": 15000,
  "start_point": [20.0, 0.0, 40.0],
  "segments": [
    { "dt_ms": 2000, "type": "bezier",
      "p":  [19.777, 2.981, 40.0],
      "c1": [20.000, 0.998, 40.0],
      "c2": [19.925, 1.994, 40.0] }
  ] }
```

### 4.2.1 Anchors and extent

`start_point` is the position at `start_ms` and is REQUIRED.

Segments are consecutive and share endpoints. Writing

- `P₀(0) = start_point`
- `P₀(i) = p(i−1)` for `i > 0`
- `T(0) = start_ms`, `T(i) = T(i−1) + dt_ms(i−1)`

the segment `i` covers the half-open interval `[T(i), T(i) + dt_ms(i))`, per the
interval convention of §3.2. The track covers
`[start_ms, start_ms + Σ dt_ms)`, and the final instant
`start_ms + Σ dt_ms` evaluates to `p` of the last segment.

Outside `[start_ms, start_ms + Σ dt_ms]` the value is the nearest boundary
value — `start_point` before the track, the final `p` after it. This is the
same clamp §4.3.4 states for sampled tracks, and it is not a corner case: a
track belonging to a later sortie legitimately begins thousands of milliseconds
into the show, so **every** consumer that reduces from show time zero
evaluates this region on its first row.

Each segment stores only its **endpoint**. The start point is never repeated,
so a C⁰ discontinuity cannot be expressed by construction — a segment track is
always positionally continuous. This is deliberate: a gap between two waypoints
is a data error in every case DSX cares about, and a format that can represent
it will eventually contain it.

### 4.2.2 Local parameter

Within segment `i`, for an instant `t` in that segment:

```
u = (t − T(i)) / dt_ms(i)          u ∈ [0, 1]
```

`u` is **linear in time**. It is not arc length, and it is not
re-parameterised for constant speed. An implementation that redistributes `u`
by distance produces different positions from the same file and is
non-conforming. (Constant-speed motion is achieved by placing control points
accordingly, not by re-timing at playback.)

`u` is computed in binary64 from integer millisecond operands. `dt_ms` is
constrained to be strictly positive by the schema, so the division is always
defined.

### 4.2.3 Segment types

Let `P₀` be the segment's start anchor per §4.2.1 and `P₃ = p` its endpoint.
Each formula is applied independently to the x, y and z components.

**`constant`** — holds the start anchor for the whole segment:

```
value(u) = P₀
```

`p` MUST equal `P₀` exactly. A `constant` segment whose `p` differs from its
start anchor is a REJECT-class error (§5.6): the file states both that the
position does not change and that it ends somewhere else.

**`linear`** — straight line, uniform in time:

```
value(u) = (1 − u)·P₀ + u·P₃
```

**`bezier`** — cubic Bézier with control points `c1`, `c2`, both REQUIRED:

```
value(u) = (1−u)³·P₀ + 3(1−u)²·u·c1 + 3(1−u)·u²·c2 + u³·P₃
```

`c1` and `c2` are **absolute positions in the show frame**, in metres — not
offsets from the anchors, and not normalised tangents. This is stated because
both alternative conventions exist in the field and produce plausible-looking
but wrong curves when confused; a reader that guesses will usually still
render something.

**`poly`** — polynomial in `u`, ascending powers:

```
coeffs = [[ax0, ax1, …, axn], [ay0, …, ayn], [az0, …, azn]]

x(u) = Σ axk · u^k          k = 0 … n
```

`coeffs` MUST contain exactly three arrays, in x, y, z order. The arrays MAY
differ in length; an absent higher coefficient is zero. The variable is the
normalised `u` of §4.2.2, **not** seconds and not milliseconds — a polynomial
expressed against absolute time cannot be relocated on the timeline, which is
precisely what wave rotation (§10) requires.

For consistency, a `poly` segment MUST satisfy

```
| value(0) − P₀ | ≤ 1 mm      and      | value(1) − p | ≤ 1 mm
```

per component. Violating it is a **BLOCK-FLIGHT**-class finding (§5.6), not a
REJECT: the file is still evaluable — §4.2.1 makes `p` the value at the final
instant, so the endpoint is never in doubt — but a producer whose polynomial
does not reach its own declared endpoint has a defect somewhere upstream, and
that defect MUST NOT reach an aircraft. (Contrast `constant`, where a
mismatched `p` makes the segment self-contradictory and is therefore REJECT.)

`p` is therefore redundant for `poly` segments — and that is the
point: it lets every reader, including one that does not implement polynomial
evaluation, obtain the segment endpoints and fall back to §4.4 sampling
performed by the producer.

Evaluation MUST use Horner's method, which is both the numerically stable
choice and, being a fixed operation order, the reason two implementations agree
bit-for-bit in binary64.

### 4.2.4 Mixed types and continuity

`interp` at track level declares the predominant type for readers that
pre-allocate; each segment's own `type` governs. A track MAY mix types freely.

Positional continuity (C⁰) is guaranteed by construction (§4.2.1). **Velocity
continuity (C¹) is not.** DSX does not silently smooth: if consecutive segments
imply a velocity step, that step is what the file says, and a validator MUST
NOT round it away. Where a producer intends C¹ — for a closed loop especially
(§10.8) — it MUST place control points so that the one-sided derivatives match,
and MAY declare `continuity: "c1"` on the role. A declared `continuity` is
checked, not trusted: `conformance/check_rotation.py` recomputes the seam.

The one-sided derivative at the end of a segment, needed for that check, is

```
d/dt value  at u = 1  =  3·(P₃ − c2) / dt_ms      (bezier)
                      =  (P₃ − P₀) / dt_ms        (linear)
                      =  0                        (constant)
```

in metres per millisecond, and at the start of the next segment

```
d/dt value  at u = 0  =  3·(c1 − P₀) / dt_ms      (bezier)
```

## 4.3 Sampled tracks

```jsonc
{ "kind": "sampled",
  "rate_hz": 30,
  "interp": "linear",                 // hold | linear | cubic — REQUIRED
  "time_semantics": "at_sample",      // at_sample | until_next | since_previous
  "t0_ms": 0,
  "data": [ [0.0, 0.0, 0.0], [0.0, 0.0, 5.0], [0.0, 0.0, 10.0] ] }
```

### 4.3.1 The grid

`data` is an array of `N` positions, each an array of exactly three numbers
`[x, y, z]` in metres. The nominal instant of sample `i` is

```
t(i) = t0_ms + round(i · 1000 / rate_hz)          i = 0 … N−1
```

with `round` as defined in §4.4.4. `rate_hz` MAY be fractional. The grid is
computed from `i` directly and **MUST NOT** be accumulated by repeated
addition: at 30 Hz an accumulating reader drifts by 10 ms over a five-minute
show, which is a third of a frame and enough to fail a seam check.

The track covers `[t0_ms, t(N−1)]`.

Above 1000 Hz the millisecond grid can place two samples on the same instant,
i.e. `t(i) = t(i+1)`. The interpolation weight `w` of §4.3.3 is then undefined;
it MUST be taken as `0`, so the earlier sample governs. Producers SHOULD NOT
emit rates above 1000 Hz, which the millisecond time base cannot represent.

### 4.3.2 `time_semantics` — what a sample asserts

This field is REQUIRED and has **no default**. It answers a question that is
invisible until two systems disagree: does a sample describe the instant, the
interval after it, or the interval before it?

| value | sample `i` asserts | `interp` |
|---|---|---|
| `at_sample` | the value **at** `t(i)`; values between grid points follow `interp` | any |
| `until_next` | the value across `[t(i), t(i+1))` | MUST be `hold` |
| `since_previous` | the value across `(t(i−1), t(i)]`; sample 0 applies at `t0_ms` only | MUST be `hold` |

The interval forms are piecewise constant by definition, so combining them with
`linear` or `cubic` is contradictory and is a REJECT-class error.

For identical `data`, `until_next` and `since_previous` describe motions
displaced by exactly one sample period. An importer that assumes the wrong one
produces a uniform one-sample offset across the whole show — visible, but
easily misread as a timing or latency fault anywhere else in the chain.
Declaring the semantics costs one field and removes an entire class of
misattributed bugs.

### 4.3.3 `interp` — between the grid points

**`hold`** — the value of the governing sample. For the interval forms that
is the sample whose interval contains `t` (§4.3.2). For `at_sample` it is the
**last sample at or before `t`**, never the nearest one: nearest-sample hold
disagrees with previous-sample hold across half of every sample interval, and
only the latter is consistent with `until_next` on identical data.

**`linear`** — for `t` in `[t(i), t(i+1))`, with `w = (t − t(i)) / (t(i+1) − t(i))`:

```
value(t) = (1 − w)·data[i] + w·data[i+1]
```

**`cubic`** — **uniform Catmull–Rom**, evaluated on the same `w`, using the two
neighbouring samples:

```
value(w) = 0.5 · ( 2·P₁
                 + (−P₀ + P₂)·w
                 + (2·P₀ − 5·P₁ + 4·P₂ − P₃)·w²
                 + (−P₀ + 3·P₁ − 3·P₂ + P₃)·w³ )

P₁ = data[i]      P₂ = data[i+1]
P₀ = data[i−1]    (i = 0:      P₀ = data[0])
P₃ = data[i+2]    (i+2 ≥ N:    P₃ = data[N−1])
```

The variant is named because "cubic" alone is not a specification: natural
cubic splines, centripetal Catmull–Rom and Hermite forms all deserve the label
and all produce different curves. Uniform Catmull–Rom is chosen because it
interpolates its control points, requires no global solve — so a reader can
evaluate any instant without loading the whole track — and its endpoint rule
above is simple enough to reimplement identically. Its known weakness,
overshoot at sharp direction changes, is acceptable here because sampled tracks
in this format are machine-generated caches of segment tracks, and because the
alternative is silent disagreement between readers.

The endpoint duplication is normative. It is the single most likely source of
divergence between two otherwise correct implementations.

### 4.3.4 Outside the track

Before `t0_ms` and after the final instant, the value is the nearest boundary
sample — a clamp, never an extrapolation. A cubic that extrapolates past its
last control point can produce arbitrarily large positions, and this format is
used to plan flight over people.

## 4.4 Normative sampling algorithm

The reduction from any DSX track to `t, x, y, z, R, G, B` at rate *f* is
**normative and bit-exact**. This is the guarantee of §1.4: it is what allows a
vendor with a fixed-rate frame uploader to consume any DSX file without
negotiating.

### 4.4.1 Instants

```
t_k = round(k · 1000 / f)            k = 0 … floor(duration_ms · f / 1000)
```

inclusive, in integer milliseconds, relative to the show time origin (§3).
`duration_ms` is taken from the manifest. For a show declared `indefinite`
(§10.8) `duration_ms` is null and this clause does not apply — see A25; a
producer targeting a fixed-rate consumer MUST supply an explicit window.

### 4.4.2 Which track

If both a segment and a sampled track are bound for the same aircraft, the
**segment track** is evaluated (§4.1). The sampled track is never used as
input to §4.4 when a segment track exists, even where it is denser: two readers
that disagree about which cache to trust produce two different shows from one
file.

### 4.4.3 Evaluation

1. Evaluate position per §4.2 or §4.3 at each `t_k`.
2. Evaluate the light program per §4.5 at the same `t_k`.
3. All arithmetic is IEEE-754 **binary64** throughout. Single precision is
   insufficient: at a 500 m stand-off, float32 spacing exceeds 30 µm, and
   accumulated over the operations above it can move a rounded millimetre.

### 4.4.4 Rounding

`round(x)` in this specification means **round half away from zero**, applied
to the exact binary64 value. Banker's rounding is explicitly excluded — not
because it is worse, but because the two differ on exactly the half-integer
cases that a machine-generated grid produces constantly.

- Positions are rounded to **millimetres**.
- Colour channels are quantised to 8 bit after the colour-space handling of
  §4.5, using the same rule.
- Time instants are already integers by construction.

Two implementation traps are called out because both produce plausible output
that fails byte comparison:

- `floor(x + 0.5)` is **not** this rule. It double-rounds: the binary64 value
  immediately below 0.5 becomes exactly 1.0 when 0.5 is added. Round the exact
  value, e.g. via a decimal conversion.
- The three decimals of §4.4.5 MUST be formatted from the already-rounded
  integer millimetre, not by formatting the float a second time. Most standard
  formatters round half-to-even, so a second rounding pass reintroduces exactly
  the discrepancy the first pass removed.

### 4.4.5 Output form

The canonical reduction is a CSV with the header

```
t_ms,x_m,y_m,z_m,r,g,b
```

one row per `t_k`, positions written in metres with exactly three decimal
places, channels as integers 0–255, `.` as decimal separator, LF line endings,
no BOM.

Where no light program is bound to the aircraft, the channel columns are `0`,
consistent with §4.5.1. The columns are always present: a consumer of the
canonical reduction MUST NOT have to discover the column count from the data.

Where the track carries channels beyond R, G and B (§4.5.5), the canonical
reduction still emits exactly `r,g,b`: the R, G and B channels are written as
they are, any channel the track does not carry is `0`, and the remaining
channels (W, UV, STROBE, INTENSITY) are dropped. A producer MUST report that
loss as a WARN-class finding — the reduction itself has no field in which to
declare it, which is precisely why the obligation sits on the producer. The
canonical reduction is a guaranteed floor for interchange, not a complete
rendering of the show. Two conforming producers MUST emit byte-identical files for the same
input and rate. This exact form is what `conformance/run_sampling_checks.py`
compares.

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

### 4.5.1 Op sequence

`ops` MUST be ordered by strictly increasing `t_ms`. Each op occupies
`[t_ms, t_ms + dur_ms)`; `set` has zero extent. Ops MUST NOT overlap: the
extent of an op MUST NOT contain the `t_ms` of any later op. Overlapping ops
are a REJECT-class error — two simultaneous fades to different targets have no
defined result, and picking one by array order makes the file order-dependent.

**Before the first op every channel is 0.** A light program that does not begin
at `t_ms: 0` starts dark; this is defined rather than left to the reader,
because "undefined initial state" in a light show means one fleet lights up
during positioning and another does not.

After the last op the value holds to the end of the track.

### 4.5.2 Op semantics

Let `C` be the channel vector in effect immediately before the op.

**`set`** — the value becomes the op's target instantaneously at `t_ms` and
holds until the next op.

**`fade`** — for `t` in `[t_ms, t_ms + dur_ms)`, with `w = (t − t_ms) / dur_ms`:

```
value(t) = (1 − w)·C + w·target
```

per channel. At `t_ms + dur_ms` the value is exactly `target` and holds.
`dur_ms: 0` is equivalent to `set`.

**`strobe`** — modulates the colour in effect at `t_ms`, which is held as the
underlying value for the whole op:

```
phase = frac( (t − t_ms) · hz / 1000 )
value(t) = C            if phase < duty        (on)
         = 0            otherwise              (off)
```

The op begins **on** at `t_ms`. `duty` is the on-fraction, `0 < duty ≤ 1`,
and is REQUIRED — a strobe without a declared duty is not reproducible, and any
default would be a house style silently imposed on every file that omits it.

A `strobe` op MAY carry a target (`rgb` or `channels`). If present, that target
**is** `C`: it replaces the colour in effect for the duration of the op and
remains in effect after it. If absent, `C` is the colour already in effect. The
alternative readings — ignore the target, or reject the op — were both
available to a reader of an earlier draft of this text, which is why it now
says so.
After `t_ms + dur_ms` the value returns to `C` and holds.

Strobe phase is derived from the op's own start, not from show time. A strobe
that is phase-locked to the show clock changes appearance when its op is moved,
which makes a rotating wave (§10) visibly different on its second pass — the
one place where this format cannot afford a surprise.

### 4.5.3 Targets and channels

An op MUST carry exactly one of `rgb` (three integers 0–255, valid only when
`channels` is exactly `["R","G","B"]`) or `channels` (an object naming the
channels explicitly). Channels present in the track's `channels` list but
absent from an op's object are **unchanged**, not zeroed.

### 4.5.4 Interpolation space

`fade` interpolates **numerically on the encoded channel values**, in the space
named by `color_space`. It does not linearise first.

This is a choice, and the reasoning belongs in the document rather than in a
reader's source: the encoded values are what the hardware receives, so this
rule makes the result independent of the device profile's gamma, and makes the
reduction of §4.4 computable without a device profile at all. A producer that
wants photometrically linear blending sets `color_space: "linear"` and supplies
values in that space. What is not acceptable is leaving it to the reader, which
is the current situation across the material surveyed in Appendix B: the same
fade renders visibly differently on two systems and neither is wrong.

`color_space: "device"` means the values are passed through untouched; the
show is then bound to one luminaire model and is not portable, which a
validator MUST report as a WARN-class finding.

### 4.5.5 Consequences of binding light to the device profile

- A show authored for a four-channel (RGBW) fleet and replayed on a
  three-channel fleet is a **declared, detectable** mismatch (§5.6), not a
  silently wrong colour.
- Gamma, dimming curve and PWM frequency belong to the **device**, not the
  show. None of the formats surveyed in Appendix B carries them, which is why
  the same show looks different on different hardware.
- White-channel derivation (when a target has W and the source does not, or
  vice versa) is a reader-side mapping governed by the profile — not an
  exporter-side hack.

## 4.6 Reference implementation and test vectors

`tools/dsx_sample.py` implements this section and is the executable statement
of intent where prose is ambiguous. It is normative in the weak sense: where
the tool and this text disagree, **the text wins and the tool is a bug**.

`conformance/sampling/` holds the test vectors. Each case is a resource file, a
rate, and the expected CSV of §4.4.5. `conformance/run_sampling_checks.py`
compares byte-for-byte and is part of CI.

The vectors marked `analytic` in `conformance/sampling/INDEX.md` were computed
by hand from the formulas above and are the ones that establish agreement; the
remainder are regression vectors produced by the reference implementation and
prove only that behaviour does not drift. That distinction is stated because a
test suite generated entirely by the implementation it tests proves nothing
about the specification.
