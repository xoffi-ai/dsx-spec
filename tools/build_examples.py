#!/usr/bin/env python3
"""Build the resource files the example manifests reference.

The examples used to reference trajectory, light and geometry files that were
never written. A DSX archive is required to be self-contained (spec 2.1), so a
manifest pointing at absent resources is not a valid archive -- and shipping
one as the reference example is worse than shipping none.

Rather than hand-writing ~50 files, this generator is driven by the manifest
itself: every string marked "x-archive-ref" in the schema is resolved, and a
resource of the right kind is produced for it, with time windows read from the
manifest so that the geometry and the choreography cannot drift apart.

Run:  python3 tools/build_examples.py
"""
import json
import math
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
M_PER_DEG_LAT = 111320.0


# --- helpers -------------------------------------------------------------
def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + "\n")
    return path


def enu_to_lonlat(origin, x, y):
    lat = origin["lat"] + y / M_PER_DEG_LAT
    lon = origin["lon"] + x / (M_PER_DEG_LAT * math.cos(math.radians(origin["lat"])))
    return [round(lon, 8), round(lat, 8)]


def polygon(origin, pts, name, props=None):
    ring = [enu_to_lonlat(origin, x, y) for x, y in pts]
    ring.append(ring[0])
    return {
        "type": "Feature",
        "properties": {"name": name, **(props or {})},
        "geometry": {"type": "Polygon", "coordinates": [ring]},
    }


def circle_arcs(cx, cy, z, radius, phase_deg, period_ms, n):
    """The n cubic Bezier arcs of a closed circle, without the track wrapper.

    Equal arc lengths and equal segment durations, so the tangent magnitude
    matches across every joint: the track is C1 at the seam as well, which is
    what a looping role has to declare (spec 10).
    """
    k = 4.0 / 3.0 * math.tan(math.pi / (2 * n))
    dt = period_ms // n
    segs = []
    for i in range(n):
        a0 = math.radians(phase_deg) + 2 * math.pi * i / n
        a1 = math.radians(phase_deg) + 2 * math.pi * (i + 1) / n
        p0 = (cx + radius * math.cos(a0), cy + radius * math.sin(a0))
        p1 = (cx + radius * math.cos(a1), cy + radius * math.sin(a1))
        t0 = (-math.sin(a0) * radius * k, math.cos(a0) * radius * k)
        t1 = (-math.sin(a1) * radius * k, math.cos(a1) * radius * k)
        segs.append({
            "dt_ms": dt,
            "type": "bezier",
            "p": [round(p1[0], 3), round(p1[1], 3), z],
            "c1": [round(p0[0] + t0[0], 3), round(p0[1] + t0[1], 3), z],
            "c2": [round(p1[0] - t1[0], 3), round(p1[1] - t1[1], 3), z],
        })
    return segs


def circle_tangent(radius, phase_deg, period_ms):
    """Velocity vector (m/s) at the circle's start point, travelling +phi."""
    a = math.radians(phase_deg)
    v = 2 * math.pi * radius / (period_ms / 1000.0)
    return (-math.sin(a) * v, math.cos(a) * v, 0.0)


def circle_segments(cx, cy, z, radius, phase_deg, period_ms, n, start_ms=0):
    """A closed circle as a complete segment track."""
    segs = circle_arcs(cx, cy, z, radius, phase_deg, period_ms, n)
    return {
        "kind": "segments",
        "interp": "bezier",
        "start_ms": start_ms,
        "start_point": [round(cx + radius * math.cos(math.radians(phase_deg)), 3),
                        round(cy + radius * math.sin(math.radians(phase_deg)), 3), z],
        "segments": segs,
    }


def light_program(period_ms, n, hue_offset):
    ops = []
    dt = period_ms // n
    for i in range(n):
        h = (hue_offset + i * 360.0 / n) % 360.0
        r, g, b = hsv_to_rgb8(h, 1.0, 1.0)
        ops.append({"t_ms": i * dt, "op": "fade", "dur_ms": dt, "rgb": [r, g, b]})
    return {"kind": "light_program", "channels": ["R", "G", "B"],
            "color_space": "sRGB", "ops": ops}


def hsv_to_rgb8(h, s, v):
    c = v * s
    x = c * (1 - abs((h / 60.0) % 2 - 1))
    m = v - c
    seg = int(h // 60) % 6
    rgb = [(c, x, 0), (x, c, 0), (0, c, x), (0, x, c), (x, 0, c), (c, 0, x)][seg]
    return [int(round((q + m) * 255)) for q in rgb]


def ramp(from_xyz, to_xyz, dur_ms, rate_hz=1):
    n = max(1, int(round(dur_ms * rate_hz / 1000)))
    data = []
    for k in range(n + 1):
        f = k / n
        data.append([round(from_xyz[i] + f * (to_xyz[i] - from_xyz[i]), 3) for i in range(3)])
    return {"kind": "sampled", "rate_hz": rate_hz, "interp": "linear",
            "time_semantics": "at_sample", "t0_ms": 0, "data": data}


# --- per-example builders ------------------------------------------------
def build_rotation(base):
    doc = json.loads((base / "show.json").read_text())
    origin = doc["frame"]["origin"]
    roles = doc["roles"]
    span = roles[0]["active_ms"]
    dur = span[1] - span[0]
    n_seg = 42
    period = dur // n_seg * n_seg

    for i, r in enumerate(roles):
        write_json(base / r["trajectory"],
                   circle_segments(0.0, 0.0, 40.0, 20.0, i * 180.0, period,
                                   n_seg, start_ms=span[0]))
        write_json(base / r["light"], light_program(period, 14, i * 180.0))

    # ingress / egress per sortie, from the manifest's own windows
    for d in doc["drones"]:
        home = d["home"]
        for s in d.get("sorties", []):
            for key, up in (("ingress", True), ("egress", False)):
                leg = s.get(key)
                if not leg:
                    continue
                w = leg["window_ms"]
                hold = [home["x"], home["y"], 40.0]
                ground = [home["x"], home["y"], 0.0]
                a, b = (ground, hold) if up else (hold, ground)
                write_json(base / leg["path"], ramp(a, b, w[1] - w[0]))

    build_geo(base, doc, origin)
    return doc


def build_continuous(base):
    path = base / "show.json"
    raw = path.read_text().replace(".poly\"", ".json\"").replace(".lp\"", ".json\"")
    path.write_text(raw)
    doc = json.loads(raw)
    origin = doc["frame"]["origin"]

    for i, r in enumerate(doc["roles"]):
        period = r["loop"]["period_ms"]
        write_json(base / r["trajectory"],
                   circle_segments(0.0, 0.0, 40.0 + 5.0 * (i % 2), 20.0,
                                   i * 60.0, period, 42))
        write_json(base / r["light"], light_program(period, 14, i * 60.0))

    build_geo(base, doc, origin)

    audio = doc.get("show", {}).get("audio", {}).get("file")
    if audio:
        out = base / audio
        out.parent.mkdir(parents=True, exist_ok=True)
        secs = doc["roles"][0]["loop"]["period_ms"] // 1000
        try:
            subprocess.run(
                ["ffmpeg", "-y", "-f", "lavfi", "-i",
                 f"anullsrc=r=8000:cl=mono", "-t", str(secs),
                 "-c:a", "libmp3lame", "-b:a", "8k", str(out)],
                check=True, capture_output=True)
        except (OSError, subprocess.CalledProcessError) as e:
            print(f"  ! could not generate {audio}: {e}", file=sys.stderr)
    return doc


# --- the L1 reference show ----------------------------------------------
# One figure, eight aircraft, built so that the velocity is continuous at every
# joint. That is not decoration: 4.2.2 forbids re-timing at playback, so a
# corner between two segments is a real velocity step, and an example that
# contains one would teach every importer that reads it the wrong lesson.
L1_CLIMB_END = 20000
L1_OUT_END = 30000
L1_CIRCLE_MS = 40000
L1_BACK_END = 80000
L1_DESCENT_END = 110000
L1_RADIUS = 20.0
L1_ALT = 40.0
L1_ARCS = 40


def _ease(p0, p3, dt_ms, v_end=None, v_start=None):
    """Cubic Bezier from p0 to p3 with prescribed end velocities (m/s).

    A cubic's velocity is 3(c1-P0)/T at u=0 and 3(P3-c2)/T at u=1, so the
    control points are where a joint is made C1 -- or not.
    """
    t = dt_ms / 1000.0
    v0 = v_start or (0.0, 0.0, 0.0)
    v1 = v_end or (0.0, 0.0, 0.0)
    c1 = [p0[i] + v0[i] * t / 3.0 for i in range(3)]
    c2 = [p3[i] - v1[i] * t / 3.0 for i in range(3)]
    return {"dt_ms": dt_ms, "type": "bezier",
            "p": [round(v, 3) for v in p3],
            "c1": [round(v, 3) for v in c1],
            "c2": [round(v, 3) for v in c2]}


def build_show_l1(base):
    doc = json.loads((base / "show.json").read_text())
    origin = doc["frame"]["origin"]
    total = doc["show"]["duration_ms"]

    offsets = {}
    for b in doc["takeoff"]["batches"]:
        for did in b["drones"]:
            offsets[did] = b["offset_ms"]

    for i, d in enumerate(doc["drones"]):
        phase = i * 360.0 / len(doc["drones"])
        a = math.radians(phase)
        home = d["home"]
        ground = [home["x"], home["y"], 0.0]
        hold = [home["x"], home["y"], L1_ALT]
        entry = [L1_RADIUS * math.cos(a), L1_RADIUS * math.sin(a), L1_ALT]
        tangent = circle_tangent(L1_RADIUS, phase, L1_CIRCLE_MS)
        off = offsets.get(d["id"], 0)

        segs = []
        if off > 0:
            # the batch it is not in has already left; this one still sits
            segs.append({"dt_ms": off, "type": "constant", "p": list(ground)})
        segs.append(_ease(ground, hold, L1_CLIMB_END - off))
        segs.append(_ease(hold, entry, L1_OUT_END - L1_CLIMB_END, v_end=tangent))
        segs += circle_arcs(0.0, 0.0, L1_ALT, L1_RADIUS, phase,
                            L1_CIRCLE_MS, L1_ARCS)
        segs.append(_ease(entry, hold, L1_BACK_END - (L1_OUT_END + L1_CIRCLE_MS),
                          v_start=tangent))
        segs.append(_ease(hold, ground, L1_DESCENT_END - L1_BACK_END))
        segs.append({"dt_ms": total - L1_DESCENT_END, "type": "constant",
                     "p": list(ground)})

        write_json(base / d["trajectory"], {
            "kind": "segments",
            "interp": "bezier",
            "start_ms": 0,
            "start_point": [round(v, 3) for v in ground],
            "segments": segs,
        })
        write_json(base / d["light"], l1_light(total, phase, off))

    build_geo(base, doc, origin)
    measure_envelope(base, doc)
    write_json(base / "show.json", doc)
    return doc


def l1_light(total_ms, hue_offset, off_ms):
    """Dark on the ground, colour in the air, one strobe cue, dark again."""
    r, g, b = hsv_to_rgb8(hue_offset % 360.0, 1.0, 1.0)
    ops = [{"t_ms": 0, "op": "set", "rgb": [0, 0, 0]},
           {"t_ms": off_ms, "op": "fade", "dur_ms": L1_CLIMB_END - off_ms,
            "rgb": [r, g, b]}]
    n = 8
    dt = L1_CIRCLE_MS // n
    for k in range(n):
        h = (hue_offset + (k + 1) * 360.0 / n) % 360.0
        cr, cg, cb = hsv_to_rgb8(h, 1.0, 1.0)
        ops.append({"t_ms": L1_OUT_END + k * dt, "op": "fade", "dur_ms": dt,
                    "rgb": [cr, cg, cb]})
    # 4.5.2: a strobe MUST declare its duty -- there is no default.
    ops.append({"t_ms": L1_OUT_END + L1_CIRCLE_MS, "op": "strobe", "hz": 4.0,
                "dur_ms": L1_BACK_END - (L1_OUT_END + L1_CIRCLE_MS),
                "duty": 0.25, "rgb": [255, 255, 255]})
    ops.append({"t_ms": L1_BACK_END, "op": "fade",
                "dur_ms": L1_DESCENT_END - L1_BACK_END, "rgb": [0, 0, 0]})
    return {"kind": "light_program", "channels": ["R", "G", "B"],
            "color_space": "sRGB", "ops": ops}


def measure_envelope(base, doc, rate_hz=50):
    """Fill fleet[].declared_envelope from the tracks that were just written.

    5 says the declared envelope is the measured demand of THIS show. Writing
    it by hand is how it silently stops being true; measuring it here is why
    the example cannot claim a limit its own trajectories break.
    """
    sys.path.insert(0, str(ROOT / "tools"))
    import dsx_sample

    tracks = [dsx_sample.load_resource(base / d["trajectory"])
              for d in doc["drones"]]
    total = doc["show"]["duration_ms"]
    step = int(1000 / rate_hz)
    ts = list(range(0, total + 1, step))
    pos = [[dsx_sample.eval_position(tr, t) for t in ts] for tr in tracks]

    peak = {"xy": 0.0, "zu": 0.0, "zd": 0.0, "axy": 0.0, "az": 0.0}
    dt = step / 1000.0
    for track in pos:
        vs = [tuple((track[k + 1][j] - track[k][j]) / dt for j in range(3))
              for k in range(len(track) - 1)]
        for v in vs:
            peak["xy"] = max(peak["xy"], math.hypot(v[0], v[1]))
            peak["zu"] = max(peak["zu"], v[2])
            peak["zd"] = max(peak["zd"], -v[2])
        for k in range(len(vs) - 1):
            a = tuple((vs[k + 1][j] - vs[k][j]) / dt for j in range(3))
            peak["axy"] = max(peak["axy"], math.hypot(a[0], a[1]))
            peak["az"] = max(peak["az"], abs(a[2]))

    sep = float("inf")
    at = None
    for ti in range(len(ts)):
        for i in range(len(pos)):
            for j in range(i + 1, len(pos)):
                pi, pj = pos[i][ti], pos[j][ti]
                d = math.dist(pi, pj)
                if d < sep:
                    sep, at = d, ts[ti]

    env = doc["fleet"][0]["declared_envelope"]
    env["peak_speed_xy_ms"] = round(peak["xy"], 2)
    env["peak_speed_z_up_ms"] = round(peak["zu"], 2)
    env["peak_speed_z_down_ms"] = round(peak["zd"], 2)
    env["peak_accel_xy_ms2"] = round(peak["axy"], 2)
    env["peak_accel_z_ms2"] = round(peak["az"], 2)
    env["min_separation_m"] = math.floor(sep * 100) / 100.0

    prof = json.loads((base / doc["fleet"][0]["device_profile"]).read_text())
    lim = prof["flight"]
    checks = [("peak_speed_xy_ms", "max_speed_xy_ms"),
              ("peak_speed_z_up_ms", "max_speed_z_up_ms"),
              ("peak_speed_z_down_ms", "max_speed_z_down_ms"),
              ("peak_accel_xy_ms2", "max_accel_xy_ms2"),
              ("peak_accel_z_ms2", "max_accel_z_ms2")]
    for e, l in checks:
        if env[e] > lim[l]:
            raise SystemExit(
                f"  ! {base.name}: measured {e}={env[e]} exceeds the device "
                f"profile's {l}={lim[l]} -- the example is not flyable")
    floor = doc["safety"]["min_separation_m"]
    if env["min_separation_m"] < floor:
        raise SystemExit(
            f"  ! {base.name}: closest approach {env['min_separation_m']} m "
            f"at t={at} ms is below safety.min_separation_m={floor} m")
    print(f"  {base.name}: closest approach {env['min_separation_m']} m "
          f"at t={at} ms; peak {env['peak_speed_xy_ms']} m/s xy, "
          f"{env['peak_speed_z_up_ms']} up / {env['peak_speed_z_down_ms']} down")


def build_geo(base, doc, origin):
    fence = doc.get("safety", {}).get("geofence")
    if fence:
        write_json(base / fence, {
            "type": "FeatureCollection",
            "features": [polygon(origin, [(-60, -60), (60, -60), (60, 60), (-60, 60)],
                                 "show geofence", {"alt_band_m": [0, 60]})]})
    hard = doc.get("termination", {}).get("geofence", {}).get("hard", {}).get("ref")
    if hard:
        write_json(base / hard, {
            "type": "FeatureCollection",
            "features": [polygon(origin, [(-80, -80), (80, -80), (80, 80), (-80, 80)],
                                 "hard fence - breach disarms", {"alt_band_m": [0, 80]})]})
    seen = set()
    for c in doc.get("corridors", []):
        p = c.get("polygon")
        if not p or p in seen:
            continue
        seen.add(p)
        write_json(base / p, {
            "type": "FeatureCollection",
            "features": [polygon(origin, [(-55, -55), (-25, -55), (-25, -25), (-55, -25)],
                                 "transit corridor edge",
                                 {"note": "outside the performing volume (R10.8)"})]})


# --- main ----------------------------------------------------------------
def main():
    build_show_l1(ROOT / "examples" / "show-l1")
    build_rotation(ROOT / "examples" / "rotation-l2")
    build_continuous(ROOT / "examples" / "continuous-l2")
    print("example resources rebuilt")


if __name__ == "__main__":
    main()
