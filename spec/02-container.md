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

  "safety": { … },             // §7 — REQUIRED for L1 and L2
  "termination": { … },        // §7 — REQUIRED for L2

  // §10 — only for shows that rotate aircraft through the air.
  // Present as a group or not at all: "roles" without "assignments" is
  // an incomplete file, not a simpler one.
  "roles":       [ { … } ],    // the choreography, decoupled from the airframe
  "wave_groups": [ { … } ],    // which aircraft fly together
  "waves":       [ { … } ],    // finite rotation  — or:
  "wave_cycle":  { … },        //   open-ended rotation
  "assignments": [ { … } ],    // which airframe performs which role, when
  "handovers":   [ { … } ],    // role passed from one airframe to the next
  "corridors":   [ { … } ],    // ingress/egress volumes, separate from the show
  "launch_stack":{ … },        // pads, bays, batteries
  "energy":      { … },
  "turnaround":  { … },
  "open_ended":  { … },        // an endless show still has to end (R10.24)

  "extensions_used":     [],   // §8
  "extensions_required": [],   // §8
  "extensions":  { … },        // §8.1.1 — vendor payloads; any object may carry one
  "regulatory_profiles": [],   // §8

  "provenance": { … }          // §2.3
}
```

Every member outside `extensions` is core, and core objects are **closed**: a
member the schema does not define is an error, not an extension (§8.1.1).

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

`validated_by.scope` states **what was actually checked**. A validator that
reports a bare `"result": "pass"` invites the reader to assume it checked
everything; naming the scope is what makes the claim auditable.

`signature.public_key` MAY carry an in-archive copy of the verifying key. It is
a convenience for offline verification, **not** a trust anchor: an archive that
vouches for its own key proves only internal consistency. Trust still comes
from out-of-band key distribution.

### 2.3.1 How `content_hash` is computed

A provenance claim that cannot be recomputed by a third party is decoration.
The digest is therefore defined on **raw archive bytes**, with no canonical
JSON step. Canonicalisation was deliberately avoided: number formatting and key
ordering differ between languages, so a canonicalising rule would produce
digests that disagree across implementations — the one failure a provenance
field must not have.

The **null digest** is the literal string `sha256:` followed by 64 `0`
characters.

1. `provenance.content_hash` **MUST** hold the null digest while the digest is
   being computed.
2. The digest covers every archive entry **except** those under `signature/`.
3. Entries are ordered by the UTF-8 bytes of their archive-relative path,
   using `/` as separator.
4. For each entry, the following is fed to SHA-256, in order:
   `utf8(path)` ‖ `0x00` ‖ `uint64be(byte length)` ‖ `contents`.
5. `content_hash` is `sha256:` followed by the lowercase hex digest.

Because the null digest and the final digest have the same length, writing the
result back into `show.json` moves no other byte, and step 2 stays exact.

**Verification** is the same procedure in reverse: replace the value of
`provenance.content_hash` with the null digest, recompute, compare.

`signature.file` is a **detached signature over the ASCII bytes of the final
`content_hash` string**, including the `sha256:` prefix. `signature/` is
excluded from the digest for the obvious reason that it cannot exist yet when
the digest is taken.

Reference implementation: `tools/dsx_seal.py` (`seal` / `verify`).
