# 2. Container and manifest

## 2.1 Container

A `.dsx` file is a **ZIP archive** (stored or deflated). It **MUST** contain a
manifest named `show.json` at the archive root.

```
show.json                 REQUIRED — the manifest
audio/                    audio assets
traj/                     trajectory resources
light/                    light program resources
devices/                  device profiles (.dsxp), see §5
geo/                      geofence / zone geometry (GeoJSON)
plans/                    RTH and landing plans
media/                    optional previews, thumbnails
signature/                detached signatures over the content hash
```

Referenced resources **MUST** be relative paths inside the archive. External
references (URLs, absolute paths) are **NOT** permitted: a show file must be
complete offline. This is not only a robustness preference — at least one
jurisdiction requires the show network to be air-gapped from the internet, and
a format that requires a server call at load time cannot be used there.

Device profiles referenced by the show **MUST** be embedded in the archive
(`devices/`). A show that references a profile it does not carry is invalid.

## 2.2 Manifest skeleton

```jsonc
{
  "dsx": "0.1",
  "profile": "L1",

  "show": {
    "title": "…",
    "duration_ms": 480000,
    "acts": [ { "id": "act1", "from_ms": 0, "to_ms": 480000 } ],
    "audio": { "file": "audio/track.mp3", "media_type": "audio/mpeg",
               "offset_ms": 0, "sync": "gnss" }
  },

  "frame": { … },              // §3 — REQUIRED
  "time":  { … },              // §3 — REQUIRED

  "fleet": [ { … } ],          // §5 — groups binding drones to device profiles
  "drones": [ { … } ],         // per-aircraft: id, home, trajectory, light, payloads
  "takeoff": { … },            // grid, slots, spacing, batching

  "safety": { … },             // §7
  "termination": { … },        // §7 — REQUIRED for L2

  "extensions_used":     [],   // §8
  "extensions_required": [],   // §8
  "regulatory_profiles": [],   // §8

  "provenance": { … }          // §2.3
}
```

## 2.3 Provenance

```jsonc
"provenance": {
  "created_by":  { "tool": "…", "version": "…", "date": "…" },
  "content_hash": "sha256:…",          // over all archive entries except signature/
  "validated_by": { "tool": "…", "version": "…", "date": "…",
                    "profile": "L2", "regulatory_profiles": ["CN-WUHAN-2026"],
                    "result": "pass", "report": "media/validation.pdf" },
  "signature": { "alg": "ed25519", "key_id": "…", "file": "signature/show.sig" }
}
```

A show file is a safety-relevant artefact that is submitted to authorities,
insurers and clients. Recording **who validated it, with which tool version,
against which regulatory profile, with what result** is therefore part of the
file — not an email attachment. No existing format does this.

`content_hash` and `signature` are OPTIONAL at L0/L1 and REQUIRED at L2.
