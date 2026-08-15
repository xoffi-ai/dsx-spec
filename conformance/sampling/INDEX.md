# Sampling test vectors

Each case is a resource file, an optional light program, a rate, a duration and
the expected canonical CSV of §4.4.5. `run_sampling_checks.py` compares
**byte for byte**.

## Provenance of the expected values — read this first

| class | meaning | worth |
|---|---|---|
| **analytic** | expected values computed **by hand** from the formulas in §4, before any implementation existed | establishes that the prose and the code agree |
| **regression** | expected values produced by `tools/dsx_sample.py` | proves only that behaviour does not drift |

A suite generated entirely by the implementation it tests proves nothing about
the specification — it proves the implementation equals itself. Every vector
below is therefore marked, and the analytic ones are the ones that matter.

## Cases

| case | class | rate | duration | what it pins down |
|---|---|---|---|---|
| `a1-bezier` | **analytic** | 4 Hz | 1000 ms | cubic Bézier with absolute control points (§4.2.3); `u` linear in time (§4.2.2). At `u=¼` and `u=¾` the exact x is 1.5625 m and 8.4375 m — **half-millimetre** values that separate round-half-away-from-zero from banker's rounding (§4.4.4). A reader using banker's rounding emits `1.562` and `8.438` and fails on row 2 only. |
| `a2-light` | **analytic** | 4 Hz | 4000 ms | `set` → `fade` → `strobe` (§4.5.2). The fade midpoint is exactly 127.5 on two channels — the same rounding rule, on colour. The strobe sample at `t=3250` has `phase = 0.5` against `duty = 0.5`: the comparison is **strict** `<`, so it is **off**. An implementation using `≤` inverts the entire strobe. |
| `a3-until-next` | **analytic** | 2 Hz | 2000 ms | `time_semantics: until_next` with identical data to `a4` (§4.3.2). |
| `a4-since-previous` | **analytic** | 2 Hz | 2000 ms | `time_semantics: since_previous`. Same `data` as `a3`; the two outputs are displaced by **exactly one sample period**. This pair is the reason the field has no default. |
| `a5-cubic` | **analytic** | 2 Hz | 3000 ms | uniform Catmull–Rom (§4.3.3), including the **endpoint-duplication** rule at both ends. The interior value at `t=1500` is 1.875 m; the final interval at `t=2500` is 4.625 m and is reachable only with `P₃ = data[N−1]` duplicated. A natural cubic spline or a centripetal parameterisation fails here — which is the point: "cubic" alone was never a specification. |

## Hand computation, shown

So the analytic claim can be audited rather than believed.

**`a1` at `u = ¼`** — `P₀=[0,0,0]`, `c1=[0,0,10]`, `c2=[10,0,10]`, `P₃=[10,0,0]`:

```
(1−u)³ = 0.421875   3(1−u)²u = 0.421875   3(1−u)u² = 0.140625   u³ = 0.015625

x = 0.140625·10 + 0.015625·10 = 1.5625 m   → 1562.5 mm → 1563 → 1.563
z = 0.421875·10 + 0.140625·10 = 5.625  m   → 5625.0 mm        → 5.625
```

**`a2` fade at `t = 1500`** — `w = 0.5`, from `[255,0,0]` to `[0,0,255]`:

```
r = 0.5·255 + 0.5·0   = 127.5 → 128
b = 0.5·0   + 0.5·255 = 127.5 → 128
```

**`a2` strobe at `t = 3250`** — op starts at 3000, `hz = 2`, `duty = 0.5`:

```
phase = frac((3250 − 3000) · 2 / 1000) = frac(0.5) = 0.5
0.5 < 0.5  is false  → off → 0,0,0
```

**`a5` at `t = 2500`** — final interval, `i = 2`, `w = 0.5`,
`P₀=data[1]=1`, `P₁=3`, `P₂=6`, `P₃=data[3]=6` (duplicated):

```
z = 0.5 · ( 2·3
          + (−1 + 6)·0.5
          + (2·1 − 5·3 + 4·6 − 6)·0.25
          + (−1 + 3·3 − 3·6 + 6)·0.125 )
  = 0.5 · ( 6 + 2.5 + 1.25 − 0.5 ) = 4.625
```

## Negative and side-effect cases

Not every rule in section 4 produces a CSV to diff. Two fixtures in this
directory back checks that live at the end of `run_sampling_checks.py` instead
of in the `CASES` table above:

| fixture | proves |
|---|---|
| `reject-strobe-no-duty.light.json` | §4.5.2: `duty` is REQUIRED on a `strobe` op with no default. Rejected both by `tools/dsx_sample.py` (`load_resource`) and by `schema/resource.schema.json` — found to disagree with each other until the 2026-08-15 audit (see `CHANGELOG.md`); now both reject it, and the harness checks both. |
| `reject-rgbw-drop-warns.light.json` | §4.4.5: a channel beyond R/G/B dropped by the canonical reduction MUST be reported as a WARN-class finding. `sample_to_csv` prints it to stderr once; the harness asserts the warning fires and names the dropped channel. |

## Adding a vector

Analytic vectors are worth more than regression vectors. If you add one, show
the computation here as above; if you cannot show it, mark the case
`regression` and say so. Silently promoting a regression vector to analytic is
the one contribution this directory cannot absorb.
