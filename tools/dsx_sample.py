#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""The normative DSX sampler — reference implementation of spec section 4.

Reduces any DSX trajectory resource plus an optional light program to the
canonical CSV of section 4.4.5:

    python3 tools/dsx_sample.py --traj examples/minimal-l0/traj/0001.json \\
                                --light examples/minimal-l0/light/0001.json \\
                                --rate 5 --duration-ms 10000

Importable API:

    load_resource(path)                                   -> dict
    eval_position(res, t_ms)                              -> (x, y, z) metres
    eval_light(res, t_ms)                                 -> {channel: value}
    sample_to_csv(traj, light, rate_hz, duration_ms)      -> str

Every rule below cites the subsection it implements. Where this file and
spec/04-trajectories-and-light.md disagree, the text wins and this file is a
bug (section 4.6). Points where the text left a choice open are collected in
the module-level list AMBIGUITIES.

Pure standard library. All arithmetic is IEEE-754 binary64 (Python float),
per section 4.4.3.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import sys
from decimal import Decimal, ROUND_HALF_UP

__all__ = [
    "DsxError",
    "load_resource",
    "eval_position",
    "eval_light",
    "sample_to_csv",
    "dsx_round",
]

# ---------------------------------------------------------------------------
# Audited 2026-08-15 against the final text of spec/04-trajectories-and-light.md.
# This list previously named six points as open ambiguities. On re-reading
# against the completed section 4, five were already resolved by the prose
# (segment-track clamping 4.2.1, at_sample+hold 4.3.3, RGBW drop 4.4.5,
# strobe-target semantics 4.5.2, grid-collision w=0 4.3.1) -- the code already
# matched the spec, the list was simply stale. The sixth (strobe `duty`) was a
# real bug: the text makes `duty` REQUIRED with no default (4.5.2), but this
# file silently substituted 0.5 and the schema did not require it either. Both
# are fixed (schema `resource.schema.json` now requires `duty` on `strobe`;
# `_validate_light` below rejects its absence). See CHANGELOG.md.
#
# One further gap surfaced during that audit and is fixed here, not merely
# noted: 4.4.5 requires a producer to report dropped RGBW channels as a
# WARN-class finding; this file dropped them silently. `sample_to_csv` now
# prints that warning once per call when it applies.
#
# Remaining open points belong in spec/A-open-questions.md, not here, because
# they are gaps in the specification rather than in this implementation:
# vector coverage (A36) and the archive seam check's bezier-only assumption
# (A37).
# ---------------------------------------------------------------------------
AMBIGUITIES: list = []


class DsxError(ValueError):
    """A REJECT-class condition of section 5.6 detected while sampling."""


# ---------------------------------------------------------------------------
# 4.4.4 Rounding
# ---------------------------------------------------------------------------


def dsx_round(x: float) -> int:
    """round half away from zero, applied to the exact binary64 value (4.4.4).

    Banker's rounding is explicitly excluded by 4.4.4, and the naive
    ``math.floor(x + 0.5)`` is also wrong: the addition can itself round up
    (0.49999999999999994 + 0.5 == 1.0 in binary64). ``Decimal(float)`` is
    exact, so quantising it with ROUND_HALF_UP — which Decimal defines as
    "away from zero" — is precisely the rule the text states.
    """
    return int(Decimal(x).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def _frac(x: float) -> float:
    """Fractional part in [0, 1), used by the strobe phase of 4.5.2."""
    return x - math.floor(x)


# ---------------------------------------------------------------------------
# Loading and validation
# ---------------------------------------------------------------------------


def load_resource(path) -> dict:
    """Load a resource JSON document and check the invariants of section 4.

    Accepts the three kinds of schema/resource.schema.json: ``segments``,
    ``sampled`` and ``light_program``. Structural validation is the schema's
    job; what is checked here are the semantic MUSTs that a schema cannot
    express (4.2.3 constant, 4.3.2 semantics/interp pairing, 4.5.1 ordering).

    Note 4.1.1: a resource carries no coordinate metadata. Times and positions
    are only interpretable together with the manifest that binds them.
    """
    with open(path, "r", encoding="utf-8") as handle:
        res = json.load(handle)
    if not isinstance(res, dict) or "kind" not in res:
        raise DsxError(f"{path}: not a DSX resource (no 'kind')")
    kind = res["kind"]
    if kind == "segments":
        _validate_segments(res)
    elif kind == "sampled":
        _validate_sampled(res)
    elif kind == "light_program":
        _validate_light(res)
    else:
        raise DsxError(f"{path}: unknown resource kind {kind!r}")
    return res


def _validate_segments(res: dict) -> None:
    """4.2.1 / 4.2.3 semantic checks on a segment track."""
    if "start_point" not in res:
        # 4.2.1: "start_point is the position at start_ms and is REQUIRED."
        raise DsxError("segments: start_point is REQUIRED (4.2.1)")
    if not res.get("segments"):
        raise DsxError("segments: at least one segment is required")
    # 4.2.5: yaw is all-or-nothing. Checked before anything else because a
    # partially yawed track is REJECT-class: the reader would have to invent an
    # orientation for the gaps, and every reader would invent a different one.
    yawed = ["yaw_deg" in seg for seg in res["segments"]]
    if "start_yaw_deg" in res:
        if not all(yawed):
            missing = [i for i, has in enumerate(yawed) if not has]
            raise DsxError(
                f"segments: start_yaw_deg is present but segment(s) {missing} "
                "carry no yaw_deg; yaw is all-or-nothing (4.2.5, REJECT)"
            )
    elif any(yawed):
        carrying = [i for i, has in enumerate(yawed) if has]
        raise DsxError(
            f"segments: segment(s) {carrying} carry yaw_deg but the track has "
            "no start_yaw_deg; yaw is all-or-nothing (4.2.5, REJECT)"
        )

    anchor = tuple(float(v) for v in res["start_point"])
    for idx, seg in enumerate(res["segments"]):
        if seg["dt_ms"] <= 0:
            raise DsxError(f"segment {idx}: dt_ms MUST be strictly positive (4.2.2)")
        stype = seg.get("type", res.get("interp"))
        end = tuple(float(v) for v in seg["p"])
        if stype == "constant" and end != anchor:
            # 4.2.3: a constant segment whose p differs from its start anchor
            # is a REJECT-class error (5.6).
            raise DsxError(
                f"segment {idx}: constant segment ends at {end} but starts at "
                f"{anchor} (4.2.3, REJECT)"
            )
        if stype == "bezier" and ("c1" not in seg or "c2" not in seg):
            raise DsxError(f"segment {idx}: bezier requires c1 and c2 (4.2.3)")
        if stype == "poly":
            coeffs = seg.get("coeffs")
            if coeffs is None or len(coeffs) != 3:
                raise DsxError(
                    f"segment {idx}: poly coeffs MUST be exactly three arrays "
                    "in x, y, z order (4.2.3)"
                )
            # 4.2.3 consistency: |value(0) - P0| <= 1 mm, |value(1) - p| <= 1 mm.
            # The text states this as a MUST but does not put it in a severity
            # class, so we warn rather than reject and keep evaluating.
            for u, ref, label in ((0.0, anchor, "value(0) vs P0"),
                                  (1.0, end, "value(1) vs p")):
                got = _poly_at(coeffs, u)
                if any(abs(a - b) > 1e-3 for a, b in zip(got, ref)):
                    print(
                        f"warning: segment {idx}: poly {label} differs by more "
                        f"than 1 mm ({got} vs {ref}) (4.2.3)",
                        file=sys.stderr,
                    )
        anchor = end


def _validate_sampled(res: dict) -> None:
    """4.3.1 / 4.3.2 semantic checks on a sampled track."""
    if not res.get("data"):
        raise DsxError("sampled: data MUST contain at least one sample (4.3.1)")
    for i, point in enumerate(res["data"]):
        if len(point) != 3:
            raise DsxError(f"sampled: data[{i}] MUST have exactly three numbers (4.3.1)")
    if res.get("rate_hz", 0) <= 0:
        raise DsxError("sampled: rate_hz MUST be positive (4.3.1)")
    semantics = res.get("time_semantics")
    if semantics is None:
        # 4.3.2: "This field is REQUIRED and has no default."
        raise DsxError("sampled: time_semantics is REQUIRED and has no default (4.3.2)")
    if semantics in ("until_next", "since_previous") and res.get("interp") != "hold":
        # 4.3.2: the interval forms are piecewise constant by definition.
        raise DsxError(
            f"sampled: time_semantics {semantics!r} MUST use interp 'hold', "
            f"got {res.get('interp')!r} (4.3.2, REJECT)"
        )
    if res.get("interp") not in ("hold", "linear", "cubic"):
        raise DsxError("sampled: interp MUST be hold | linear | cubic (4.3.3)")


def _validate_light(res: dict) -> None:
    """4.5.1 / 4.5.3 semantic checks on a light program."""
    ops = res.get("ops") or []
    channels = res.get("channels") or []
    if not channels:
        raise DsxError("light_program: channels MUST be a non-empty list (4.5)")
    previous_t = None
    previous_end = None
    for idx, op in enumerate(ops):
        t_ms = op["t_ms"]
        if previous_t is not None and t_ms <= previous_t:
            # 4.5.1: ops MUST be ordered by strictly increasing t_ms.
            raise DsxError(
                f"light op {idx}: t_ms {t_ms} does not strictly increase (4.5.1, REJECT)"
            )
        if previous_end is not None and t_ms < previous_end:
            # 4.5.1: the extent of an op MUST NOT contain the t_ms of a later op.
            raise DsxError(
                f"light op {idx}: starts at {t_ms}, inside the extent of the "
                f"previous op which ends at {previous_end} (4.5.1, REJECT)"
            )
        has_rgb = "rgb" in op
        has_channels = "channels" in op
        if op["op"] in ("set", "fade") and has_rgb == has_channels:
            # 4.5.3: exactly one of rgb or channels.
            raise DsxError(
                f"light op {idx}: MUST carry exactly one of 'rgb' or 'channels' (4.5.3)"
            )
        if has_rgb and list(channels) != ["R", "G", "B"]:
            # 4.5.3: rgb is valid only when channels is exactly ["R","G","B"].
            raise DsxError(
                f"light op {idx}: 'rgb' is valid only when the track's channels "
                f"are exactly [\"R\",\"G\",\"B\"], got {channels} (4.5.3)"
            )
        if op["op"] == "strobe" and "duty" not in op:
            # 4.5.2: "duty ... is REQUIRED -- a strobe without a declared duty
            # is not reproducible, and any default would be a house style
            # silently imposed on every file that omits it." No default here.
            raise DsxError(
                f"light op {idx}: strobe MUST declare 'duty', no default exists (4.5.2, REJECT)"
            )
        # 4.5.1: set has zero extent.
        previous_end = t_ms + (0 if op["op"] == "set" else int(op.get("dur_ms", 0)))
        previous_t = t_ms


# ---------------------------------------------------------------------------
# 4.2 Segment tracks
# ---------------------------------------------------------------------------


def _point(raw) -> tuple:
    return (float(raw[0]), float(raw[1]), float(raw[2]))


def _poly_at(coeffs, u: float) -> tuple:
    """Evaluate the three polynomials of a poly segment at u by Horner (4.2.3).

    ``coeffs`` is [[ax0..axn], [ay0..ayn], [az0..azn]] in ascending powers; the
    arrays MAY differ in length and an absent higher coefficient is zero.
    Horner's method is mandated by 4.2.3: it fixes the operation order, which
    is why two binary64 implementations agree bit-for-bit.
    """
    out = []
    for axis in coeffs:
        acc = 0.0
        for coefficient in reversed(axis):  # highest power first
            acc = acc * u + float(coefficient)
        out.append(acc)
    return (out[0], out[1], out[2])


def _segment_table(res: dict):
    """Anchors and absolute start times of every segment (4.2.1).

    Returns (start_ms, [(T_i, dt_i, P0_i, segment_i), ...], end_ms, last_p).

    P0(0) = start_point and P0(i) = p(i-1): each segment stores only its
    endpoint, so a C0 discontinuity cannot be expressed. T(i) is accumulated
    over *integer* milliseconds, which is exact — unlike the sampled grid of
    4.3.1, where accumulation is forbidden because the step is fractional.
    """
    start_ms = int(res["start_ms"])
    anchor = _point(res["start_point"])
    table = []
    t_at = start_ms
    for seg in res["segments"]:
        dt_ms = int(seg["dt_ms"])
        table.append((t_at, dt_ms, anchor, seg))
        anchor = _point(seg["p"])
        t_at += dt_ms
    return start_ms, table, t_at, anchor


def _eval_segment(seg: dict, anchor: tuple, u: float, default_type: str) -> tuple:
    """Position inside one segment at local parameter u (4.2.3).

    Each formula is applied independently to x, y and z. The track-level
    ``interp`` is only a declared default for readers that pre-allocate; the
    segment's own ``type`` governs (4.2.4).
    """
    stype = seg.get("type", default_type)
    p3 = _point(seg["p"])

    if stype == "constant":
        # 4.2.3: holds the start anchor for the whole segment.
        return anchor

    if stype == "linear":
        # 4.2.3: value(u) = (1-u)*P0 + u*P3
        return tuple((1.0 - u) * anchor[k] + u * p3[k] for k in range(3))

    if stype == "bezier":
        # 4.2.3: cubic Bezier with c1, c2 as ABSOLUTE positions in the show
        # frame, in metres — not offsets from the anchors, not tangents.
        c1 = _point(seg["c1"])
        c2 = _point(seg["c2"])
        mu = 1.0 - u
        b0 = mu * mu * mu
        b1 = 3.0 * mu * mu * u
        b2 = 3.0 * mu * u * u
        b3 = u * u * u
        return tuple(
            b0 * anchor[k] + b1 * c1[k] + b2 * c2[k] + b3 * p3[k] for k in range(3)
        )

    if stype == "poly":
        # 4.2.3: the variable is the normalised u of 4.2.2, not seconds.
        return _poly_at(seg["coeffs"], u)

    raise DsxError(f"unknown segment type {stype!r} (4.2.3)")


def _eval_segments(res: dict, t_ms: int, table=None) -> tuple:
    """Position of a segment track at t (4.2.1, 4.2.2, 4.2.3)."""
    if table is None:
        table = _segment_table(res)
    start_ms, segments, end_ms, last_p = table

    # AMBIGUITY: 4.2.1 defines the covered interval but not the behaviour
    # outside it. We clamp, never extrapolate, by analogy with 4.3.4 — a
    # cubic continued past its last control point can produce arbitrarily
    # large positions, and this format is used to plan flight over people.
    if t_ms <= start_ms:
        return segments[0][2]
    if t_ms >= end_ms:
        # 4.2.1: the final instant start_ms + sum dt_ms evaluates to p of the
        # last segment.
        return last_p

    # Segment i covers the half-open interval [T(i), T(i) + dt_ms(i)) (4.2.1,
    # interval convention of 3.2). Times are integers, so this is exact.
    lo, hi = 0, len(segments) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if segments[mid][0] <= t_ms:
            lo = mid
        else:
            hi = mid - 1
    t_i, dt_ms, anchor, seg = segments[lo]

    # 4.2.2: u = (t - T(i)) / dt_ms(i), linear in time, computed in binary64
    # from integer millisecond operands. It is NOT arc length and MUST NOT be
    # re-parameterised for constant speed.
    u = (t_ms - t_i) / dt_ms
    return _eval_segment(seg, anchor, u, res.get("interp"))


# ---------------------------------------------------------------------------
# 4.2.5 Yaw
# ---------------------------------------------------------------------------


def has_yaw(res: dict) -> bool:
    """True if this resource carries a yaw track (4.2.5)."""
    return res.get("kind") == "segments" and "start_yaw_deg" in res


def _yaw_table(res: dict):
    """(start_ms, [(T_i, dt_i, yaw_start_i, yaw_end_i)], end_ms, last_yaw).

    Mirrors _segment_table: yaw_deg belongs to the END of a segment and the
    start anchor is the previous segment's value (4.2.5).
    """
    start_ms = int(res["start_ms"])
    anchor = float(res["start_yaw_deg"])
    table = []
    t_at = start_ms
    for seg in res["segments"]:
        dt_ms = int(seg["dt_ms"])
        end = float(seg["yaw_deg"])
        table.append((t_at, dt_ms, anchor, end))
        anchor = end
        t_at += dt_ms
    return start_ms, table, t_at, anchor


def eval_yaw(res: dict, t_ms: int, table=None) -> float:
    """Yaw in degrees at t (4.2.5), unwrapped and un-normalised.

    Linear in the local parameter u of 4.2.2 for EVERY segment type, including
    bezier, poly and constant: yaw has no control points, and a constant
    position segment with a changing yaw_deg is how a rotation on the spot is
    written. Outside the extent the value clamps (4.2.1).

    The returned value is NOT reduced modulo 360. 4.2.5 forbids both
    normalisation and shortest-arc interpolation: 350 -> 10 is a -340 degree
    turn, and a reader that "helpfully" takes the short way round rewrites the
    choreography of every file that crosses the wrap point.
    """
    if not has_yaw(res):
        raise DsxError("resource carries no yaw track (4.2.5)")
    if table is None:
        table = _yaw_table(res)
    start_ms, segments, end_ms, last_yaw = table

    if t_ms <= start_ms:
        return segments[0][2]
    if t_ms >= end_ms:
        return last_yaw

    lo, hi = 0, len(segments) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if segments[mid][0] <= t_ms:
            lo = mid
        else:
            hi = mid - 1
    t_i, dt_ms, yaw_start, yaw_end = segments[lo]
    u = (t_ms - t_i) / dt_ms
    return yaw_start + u * (yaw_end - yaw_start)


def yaw_peak_rate_dps(res: dict) -> float:
    """Highest implied yaw rate over any segment, in degrees per second (4.2.5).

    This is the value a declared_envelope's peak_yaw_rate_dps MUST NOT
    understate, and the one compared against the device mode's
    max_yaw_rate_dps -- where it exceeds it, the finding is BLOCK-FLIGHT.
    """
    _, segments, _, _ = _yaw_table(res)
    return max(
        (abs(yaw_end - yaw_start) / dt_ms * 1000.0
         for _, dt_ms, yaw_start, yaw_end in segments),
        default=0.0,
    )


YAW_CSV_HEADER = "t_ms,yaw_deg"


def _format_degrees(value_deg: float) -> str:
    """Degrees with exactly three decimals, via the millidegree of 4.2.5.

    Same construction as _format_metres, and for the same reason: format from
    the already-rounded integer, never re-round in the formatter.
    """
    mdeg = dsx_round(value_deg * 1000.0)
    sign = "-" if mdeg < 0 else ""
    mdeg = abs(mdeg)
    return f"{sign}{mdeg // 1000}.{mdeg % 1000:03d}"


def sample_yaw_to_csv(traj: dict, rate_hz: float, duration_ms: int) -> str:
    """The yaw reduction of 4.2.5: t_ms,yaw_deg on the instants of 4.4.1.

    Deliberately a separate file and a separate function from sample_to_csv:
    the canonical reduction of 4.4.5 stays exactly t_ms,x_m,y_m,z_m,r,g,b, so
    that adding yaw to a show never changes what an L0 consumer receives
    (1.4).
    """
    if rate_hz <= 0:
        raise DsxError("rate must be positive (4.4.1)")
    if duration_ms is None:
        raise DsxError("duration_ms is null: supply an explicit window (4.4.1, A25)")
    table = _yaw_table(traj)
    k_max = int(math.floor(duration_ms * rate_hz / 1000.0))
    rows = [YAW_CSV_HEADER]
    for k in range(k_max + 1):
        t_k = dsx_round(k * 1000.0 / rate_hz)
        rows.append(f"{t_k},{_format_degrees(eval_yaw(traj, t_k, table))}")
    return "\n".join(rows) + "\n"


# ---------------------------------------------------------------------------
# 4.3 Sampled tracks
# ---------------------------------------------------------------------------


def _grid_t(t0_ms: int, rate_hz: float, i: int) -> int:
    """Nominal instant of sample i: t0_ms + round(i * 1000 / rate_hz) (4.3.1).

    Computed from i directly. 4.3.1: it MUST NOT be accumulated by repeated
    addition — at 30 Hz an accumulating reader drifts by 10 ms over a
    five-minute show.
    """
    return t0_ms + dsx_round(i * 1000.0 / rate_hz)


def _grid_index(t0_ms: int, rate_hz: float, count: int, t_ms: int) -> int:
    """Largest i with t(i) <= t, clamped to [0, count-1] (4.3.1).

    The grid is affine in i, so the index is guessed by inversion and then
    corrected locally; rounding can move a boundary by at most one sample, so
    the correction loop is bounded in practice.
    """
    guess = int(math.floor((t_ms - t0_ms) * rate_hz / 1000.0))
    guess = max(0, min(count - 1, guess))
    while guess > 0 and _grid_t(t0_ms, rate_hz, guess) > t_ms:
        guess -= 1
    while guess + 1 < count and _grid_t(t0_ms, rate_hz, guess + 1) <= t_ms:
        guess += 1
    return guess


def _catmull_rom(p0, p1, p2, p3, w: float) -> tuple:
    """Uniform Catmull-Rom on w, per the exact form printed in 4.3.3.

    The variant is named in the spec because "cubic" alone is not a
    specification. The coefficient grouping below is copied verbatim from the
    text so that the operation order — and therefore the binary64 result — is
    the same in every implementation.
    """
    out = []
    for k in range(3):
        a0, a1, a2, a3 = p0[k], p1[k], p2[k], p3[k]
        out.append(
            0.5
            * (
                2.0 * a1
                + (-a0 + a2) * w
                + (2.0 * a0 - 5.0 * a1 + 4.0 * a2 - a3) * w * w
                + (-a0 + 3.0 * a1 - 3.0 * a2 + a3) * w * w * w
            )
        )
    return (out[0], out[1], out[2])


def _eval_sampled(res: dict, t_ms: int) -> tuple:
    """Position of a sampled track at t (4.3.1 - 4.3.4)."""
    data = res["data"]
    count = len(data)
    t0_ms = int(res["t0_ms"])
    rate_hz = float(res["rate_hz"])
    semantics = res["time_semantics"]
    interp = res["interp"]

    last_t = _grid_t(t0_ms, rate_hz, count - 1)

    # 4.3.4: before t0_ms and after the final instant the value is the nearest
    # boundary sample — a clamp, never an extrapolation.
    if t_ms <= t0_ms:
        return _point(data[0])
    if t_ms >= last_t:
        return _point(data[count - 1])

    i = _grid_index(t0_ms, rate_hz, count, t_ms)
    t_i = _grid_t(t0_ms, rate_hz, i)

    if semantics == "since_previous":
        # 4.3.2: sample i asserts the value across (t(i-1), t(i)]; sample 0
        # applies at t0_ms only. interp is 'hold' by 4.3.2, checked on load.
        j = i if t_ms == t_i else min(i + 1, count - 1)
        return _point(data[j])

    if interp == "hold":
        # 4.3.2/4.3.3: the value of the governing sample. For until_next that
        # is sample i across [t(i), t(i+1)).
        # AMBIGUITY: at_sample + hold has no governing sample named in the
        # text; we use the same previous-sample rule.
        return _point(data[i])

    j = min(i + 1, count - 1)
    t_j = _grid_t(t0_ms, rate_hz, j)
    span = t_j - t_i
    # AMBIGUITY: two grid instants can collide when rate_hz > 1000, leaving w
    # undefined. We take w = 0, i.e. the earlier sample.
    w = (t_ms - t_i) / span if span > 0 else 0.0

    if interp == "linear":
        # 4.3.3: value(t) = (1-w)*data[i] + w*data[i+1]
        p_i, p_j = _point(data[i]), _point(data[j])
        return tuple((1.0 - w) * p_i[k] + w * p_j[k] for k in range(3))

    if interp == "cubic":
        # 4.3.3 endpoint duplication, normative and "the single most likely
        # source of divergence between two otherwise correct implementations":
        #   P0 = data[i-1], with P0 = data[0]     when i = 0
        #   P3 = data[i+2], with P3 = data[N-1]   when i+2 >= N
        p0 = _point(data[i - 1]) if i > 0 else _point(data[0])
        p1 = _point(data[i])
        p2 = _point(data[j])
        p3 = _point(data[i + 2]) if i + 2 < count else _point(data[count - 1])
        return _catmull_rom(p0, p1, p2, p3, w)

    raise DsxError(f"unknown interp {interp!r} (4.3.3)")


# ---------------------------------------------------------------------------
# 4.1.2 / 4.2 / 4.3 public position entry point
# ---------------------------------------------------------------------------


def eval_position(res: dict, t_ms: int) -> tuple:
    """Position in metres at integer millisecond t (4.1.2).

    A pure function: the result MUST NOT depend on evaluation order, on
    previously requested instants, on frame rate, or on any state carried
    between calls (4.1.2). Nothing in this module keeps such state.
    """
    kind = res.get("kind")
    if kind == "segments":
        return _eval_segments(res, t_ms)
    if kind == "sampled":
        return _eval_sampled(res, t_ms)
    raise DsxError(f"{kind!r} is not a trajectory resource (4.2, 4.3)")


# ---------------------------------------------------------------------------
# 4.5 Light
# ---------------------------------------------------------------------------


def _op_target(op: dict, channels, current: dict):
    """The op's target vector, or None if it carries no target (4.5.3).

    An op carries exactly one of ``rgb`` (only when channels is exactly
    ["R","G","B"]) or ``channels``. 4.5.3: channels present in the track's
    list but absent from an op's object are UNCHANGED, not zeroed — hence the
    merge onto ``current``.
    """
    if "rgb" in op:
        return {"R": float(op["rgb"][0]), "G": float(op["rgb"][1]), "B": float(op["rgb"][2])}
    if "channels" in op:
        target = dict(current)
        for name, value in op["channels"].items():
            if name in channels:
                target[name] = float(value)
        return target
    return None


def _op_end_state(op: dict, channels, before: dict) -> dict:
    """The value an op holds once it is over (4.5.2).

    ``set`` and ``fade`` hold their target; ``strobe`` returns to the
    underlying colour C. Ops MUST NOT overlap (4.5.1), so the value in effect
    immediately before op k is exactly the end state of op k-1 — which is what
    makes this sequential fold equivalent to a left limit at t_ms.
    """
    kind = op["op"]
    target = _op_target(op, channels, before)
    if kind in ("set", "fade"):
        return target
    # strobe: AMBIGUITY — 4.5.2 says the value returns to C, but the schema
    # still permits a target on a strobe op. If one is present we treat it as
    # the underlying colour, so that is what holds afterwards.
    return target if target is not None else dict(before)


def _op_value(op: dict, channels, before: dict, t_ms: int) -> dict:
    """The value of the governing op at t (4.5.2)."""
    kind = op["op"]
    start = int(op["t_ms"])
    target = _op_target(op, channels, before)

    if kind == "set":
        # 4.5.2: the value becomes the target instantaneously at t_ms and
        # holds until the next op.
        return target

    if kind == "fade":
        dur_ms = int(op.get("dur_ms", 0))
        # 4.5.2: dur_ms 0 is equivalent to set; at t_ms + dur_ms the value is
        # exactly the target and holds.
        if dur_ms <= 0 or t_ms >= start + dur_ms:
            return target
        # 4.5.2 / 4.5.4: w = (t - t_ms) / dur_ms, blended NUMERICALLY ON THE
        # ENCODED channel values in the space named by color_space. No
        # linearisation, so the result is independent of the device gamma.
        w = (t_ms - start) / dur_ms
        return {ch: (1.0 - w) * before[ch] + w * target[ch] for ch in before}

    if kind == "strobe":
        # 4.5.2: strobe modulates the colour in effect at t_ms, which is held
        # as the underlying value for the whole op.
        base = target if target is not None else dict(before)
        dur_ms = int(op.get("dur_ms", 0))
        if t_ms >= start + dur_ms:
            return base
        # 4.5.2: duty is REQUIRED with no default; load_resource/_validate_light
        # rejects an op missing it before evaluation ever reaches this line.
        duty = float(op["duty"])
        hz = float(op["hz"])
        # 4.5.2: phase is derived from the OP'S OWN START, not from show time,
        # so moving the op on the timeline does not change its appearance.
        phase = _frac((t_ms - start) * hz / 1000.0)
        if phase < duty:
            return base  # on; the op begins on at t_ms since phase(t_ms) = 0
        return {ch: 0.0 for ch in base}  # off

    raise DsxError(f"unknown light op {kind!r} (4.5.2)")


def eval_light(res: dict, t_ms: int) -> dict:
    """Channel levels at t as encoded values, unrounded (4.5).

    Returns a dict keyed by the track's channel names. Values are the encoded
    channel numbers in the space named by ``color_space`` (4.5.4); quantising
    them to 8 bit is the reduction step of 4.4.4 and is done in
    :func:`sample_to_csv`, not here.
    """
    if res.get("kind") != "light_program":
        raise DsxError(f"{res.get('kind')!r} is not a light program (4.5)")
    channels = list(res["channels"])

    # 4.5.1: before the first op every channel is 0. A light program that does
    # not begin at t_ms 0 starts dark.
    current = {ch: 0.0 for ch in channels}

    governing = None
    before = None
    for op in res["ops"]:
        if int(op["t_ms"]) > t_ms:
            break
        before = dict(current)
        governing = op
        current = _op_end_state(op, channels, before)

    if governing is None:
        return current
    # 4.5.1: after the last op the value holds to the end of the track — which
    # is what _op_value returns once t is past the op's extent.
    return _op_value(governing, channels, before, t_ms)


# ---------------------------------------------------------------------------
# 4.4 Normative sampling algorithm
# ---------------------------------------------------------------------------

CSV_HEADER = "t_ms,x_m,y_m,z_m,r,g,b"


def _format_metres(value_m: float) -> str:
    """Metres with exactly three decimals, via the millimetre of 4.4.4.

    4.4.4 rounds positions to millimetres and 4.4.5 prints three decimals, so
    the printed value is formatted from the rounded INTEGER millimetre rather
    than by re-rounding the float in the formatter — otherwise the two
    roundings could disagree (str.format rounds half to even) and the files of
    two conforming producers would not be byte-identical.
    """
    mm = dsx_round(value_m * 1000.0)
    sign = "-" if mm < 0 else ""
    mm = abs(mm)
    return f"{sign}{mm // 1000}.{mm % 1000:03d}"


def _channel_byte(value: float) -> int:
    """Quantise one channel to 8 bit with the rule of 4.4.4, clamped to 0-255."""
    return max(0, min(255, dsx_round(value)))


def sample_to_csv(traj: dict, light, rate_hz: float, duration_ms: int) -> str:
    """The canonical reduction of section 4.4 as a CSV string.

    ``traj`` is a loaded segment or sampled resource, ``light`` a loaded light
    program or None (no program means every channel stays 0, per 4.5.1).

    4.4.1: t_k = round(k * 1000 / f) for k = 0 .. floor(duration_ms * f / 1000),
    inclusive, in integer milliseconds relative to the show time origin.
    4.4.2: where both a segment and a sampled track exist for one aircraft the
    segment track is the one evaluated; that binding lives in the manifest, so
    here the caller passes the winner.
    4.4.3: all arithmetic in binary64.
    4.4.5: LF line endings, '.' as decimal separator, no BOM.
    """
    if rate_hz <= 0:
        raise DsxError("rate must be positive (4.4.1)")
    if duration_ms is None:
        # 4.4.1: for an indefinite show duration_ms is null and the clause does
        # not apply; a producer targeting a fixed-rate consumer MUST supply an
        # explicit window.
        raise DsxError("duration_ms is null: supply an explicit window (4.4.1, A25)")

    # Segment anchors are independent of t, so build them once. This is a
    # performance detail only: no state is carried between instants (4.1.2).
    table = _segment_table(traj) if traj.get("kind") == "segments" else None

    k_max = int(math.floor(duration_ms * rate_hz / 1000.0))
    rows = [CSV_HEADER]
    for k in range(k_max + 1):
        t_k = dsx_round(k * 1000.0 / rate_hz)

        if table is not None:
            x, y, z = _eval_segments(traj, t_k, table)
        else:
            x, y, z = eval_position(traj, t_k)

        if light is None:
            levels = {}
        else:
            levels = eval_light(light, t_k)
        # 4.4.5: the canonical reduction always emits exactly r,g,b. Any
        # channel the track does not carry is written as 0; channels beyond
        # R/G/B (W, UV, STROBE, INTENSITY) are dropped, and that loss MUST be
        # reported as a WARN-class finding -- printed once below, not per row.
        r = _channel_byte(levels.get("R", 0.0))
        g = _channel_byte(levels.get("G", 0.0))
        b = _channel_byte(levels.get("B", 0.0))

        rows.append(
            f"{t_k},{_format_metres(x)},{_format_metres(y)},{_format_metres(z)},{r},{g},{b}"
        )

    if light is not None:
        dropped = [ch for ch in light.get("channels", []) if ch not in ("R", "G", "B")]
        if dropped:
            # 4.4.5: "A producer MUST report that loss as a WARN-class
            # finding -- the reduction itself has no field in which to
            # declare it, which is precisely why the obligation sits on the
            # producer."
            print(
                f"warning: canonical reduction drops channel(s) {dropped} not "
                "carried by r,g,b (4.4.5, WARN)",
                file=sys.stderr,
            )

    return "\n".join(rows) + "\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Sample a DSX trajectory and light program to the "
        "canonical CSV of spec section 4.4.5.",
    )
    parser.add_argument("--traj", required=True, help="trajectory resource JSON (segments or sampled)")
    parser.add_argument("--light", help="light program resource JSON (optional)")
    parser.add_argument("--rate", required=True, type=float, help="output rate f in Hz")
    parser.add_argument("--duration-ms", required=True, type=int, help="window length in milliseconds")
    parser.add_argument("-o", "--output", help="write to this file instead of stdout")
    parser.add_argument(
        "--yaw",
        action="store_true",
        help="emit the yaw reduction of 4.2.5 (t_ms,yaw_deg) instead of the "
        "canonical reduction of 4.4.5; requires a segment track with yaw",
    )
    args = parser.parse_args(argv)

    try:
        traj = load_resource(args.traj)
        if traj["kind"] not in ("segments", "sampled"):
            raise DsxError(f"--traj must be a trajectory resource, got {traj['kind']!r}")
        light = load_resource(args.light) if args.light else None
        if light is not None and light["kind"] != "light_program":
            raise DsxError(f"--light must be a light_program, got {light['kind']!r}")
        if args.yaw:
            if not has_yaw(traj):
                raise DsxError("--yaw: this track carries no yaw (4.2.5)")
            csv_text = sample_yaw_to_csv(traj, args.rate, args.duration_ms)
        else:
            csv_text = sample_to_csv(traj, light, args.rate, args.duration_ms)
    except (DsxError, KeyError, OSError, json.JSONDecodeError) as exc:
        print(f"dsx_sample: {exc}", file=sys.stderr)
        return 2

    if args.output:
        # 4.4.5: LF line endings, UTF-8 without BOM.
        pathlib.Path(args.output).write_bytes(csv_text.encode("utf-8"))
    else:
        sys.stdout.write(csv_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
