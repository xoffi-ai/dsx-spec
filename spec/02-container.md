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

### 2.1.1 Entry names

A DSX archive is opened by ground stations, validators and vendor tooling —
software that must not be harmed by the file it is asked to inspect. ZIP
permits entry names that no sane archive needs, and permits two entries to
carry the same name. Both are constrained here.

All rules in this section are **REJECT** (§5.6): the archive **MUST NOT** be
parsed further. A reader **MUST NOT** attempt to repair a violating archive,
because every repair is a guess about which of two readings the author meant —
and the attacker chose the ambiguity precisely so that the guess would differ
between implementations.

For every entry name:

| # | Rule |
|---|---|
| **C1** | The name **MUST** be a relative path whose only separator is `/`. A leading `/`, a backslash anywhere, and a drive or device prefix (`C:`, `\\?\`, `\\server\`) are all invalid. |
| **C2** | No path component may be `.` or `..`, in any position. |
| **C3** | The name **MUST NOT** be empty, and **MUST NOT** contain a NUL or any C0 control character. It **MUST** be valid UTF-8. |
| **C4** | No two entries may have the same name. |
| **C5** | No two entries may have names that become equal after Unicode NFC normalisation and case folding. |
| **C6** | Only regular files and directories are permitted. An entry whose external attributes encode a symbolic link, a device node or any other special type is invalid. |

**C1–C3 and C6 exist because extraction must not escape the archive.** A name
like `../../etc/cron.d/x`, an absolute path, or a symlink pointing outside the
tree lets a file write anywhere the reading process can write. A DSX reader
that extracts to disk **MUST** verify that the resolved destination of every
entry remains inside the extraction root — checking the name alone is not
sufficient, because a symlink created by an earlier entry can redirect a later
one.

**C4 and C5 exist because duplicate names break §2.3.1, and break it
silently.** Step 3 of the digest orders entries by path and assumes a path
identifies one entry. If an archive carries `show.json` twice, a hashing
implementation that takes the first and a parsing implementation that takes the
last — both defensible readings of ZIP, and both found in the wild — will agree
that the signature is valid while disagreeing about what was signed. The
signed manifest may declare a 20 m separation minimum and the parsed one 2 m.
This is a **signature bypass, not a tidiness rule**: it defeats §2.3 entirely,
and it is why C4 is REJECT rather than WARN. C5 extends the same reasoning to
readers on case-insensitive or normalising filesystems (Windows, macOS), where
`Show.json` and `show.json` are one file after extraction and two entries
before it.

### 2.1.2 Resource limits

A reader **MUST** enforce a limit on each of the following, and **MUST** reject
the archive when a limit is exceeded rather than continue with partial data:

| Limit | Purpose | RECOMMENDED default |
|---|---|---|
| total uncompressed bytes | bounded memory and disk | 4 GiB |
| entry count | bounded bookkeeping | 100 000 |

**The total-size limit is the load-bearing one, and it MUST be enforced while
decompressing** — counting bytes actually produced, and stopping at the limit.
Two reasons, both of which have defeated real implementations:

1. The sizes in the ZIP central directory are **claims by the writer**. An
   archive may declare 1 KiB and deliver 8 GiB. A reader that sums the declared
   sizes and then extracts has validated nothing.
2. A limit checked afterwards is a limit checked after the memory was already
   allocated.

DSX deliberately specifies **no compression-ratio limit**, which is worth
stating explicitly because such a limit is the conventional advice. It does not
transfer to this container: DEFLATE cannot exceed roughly **1032:1** on any
input, and approaches it asymptotically — measured at 1028.6:1 for 50 MB of a
single repeated byte. A cap below that bound rejects legitimate content (a
near-silent audio track in this repository's own `continuous-l2` example
reaches 243:1), and a cap above it never triggers. The ratio is bounded by the
algorithm, so the quantity that actually needs bounding is the total.

This reasoning is specific to the codecs permitted in §2.1. Should a later
version admit a codec whose expansion is not bounded — LZMA and Brotli are not
— a per-entry ratio limit becomes necessary again, and this section must be
revisited rather than inherited.

Both defaults are RECOMMENDED, not normative, and **MUST** be configurable: a
long-running rotation show with a full-length audio track can legitimately
approach them. What is normative is that the limits exist, that the total is
counted during decompression rather than read from the directory, and that
exceeding one is reported as the reason for rejection rather than surfacing as
a generic parse failure.

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
  "position_integrity":   { … },  // §7.4 — GNSS/RTK quality and degradation policy
  "interference_policy":  { … },  // §7.4 — jamming/spoofing monitoring
  "environment_envelope": { … },  // §7.5 — wind, temperature, humidity limits
  "ground_zones":         { … },  // §7.5 — cleared areas, fall containment

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
file — not an email attachment. None of the formats surveyed in Appendix B
carries this.

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
   using `/` as separator. This step assumes a path identifies exactly one
   entry, which is what §2.1.1 C4/C5 guarantee — **the container checks are a
   precondition of this digest, not an independent nicety.** An implementation
   that computes `content_hash` without first enforcing them is signing an
   archive whose contents it cannot pin down.
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
