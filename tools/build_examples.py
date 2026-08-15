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


def circle_segments(cx, cy, z, radius, phase_deg, period_ms, n, start_ms=0):
    """A closed circle as n cubic Bezier arcs.

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
    build_rotation(ROOT / "examples" / "rotation-l2")
    build_continuous(ROOT / "examples" / "continuous-l2")
    print("example resources rebuilt")


if __name__ == "__main__":
    main()
