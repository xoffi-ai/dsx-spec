# Appendix B — Observed Third-Party Formats

This appendix records **facts observed from publicly distributed files**. It
exists so that DSX importers and exporters can be written by people who have
never read another project's source code — see `NOTICE-PROVENANCE.md` §4.

Nothing here is derived from confidential material. Every statement below is
reproducible by anyone who downloads the same files and reads the bytes.

> **Separation of roles.** This appendix is *specification*. Contributors who
> have read the source code of the corresponding GPL-licensed implementation
> may write and review this text, but MUST NOT write the DSX reference
> importer/exporter for the same format. The implementation is written from
> this document alone.

---

## B.1 SKYB container (`.skyb`)

### B.1.1 Observation basis

Thirteen fixture files published in the `libskybrush` repository
(<https://github.com/skybrush-io/libskybrush>) under `test/fixtures/`.
Retrieved 15 Aug 2026. SHA-256 recorded so the observations
can be reproduced against the exact bytes examined:

| File | Bytes | SHA-256 |
|---|---|---|
| `forward_left_back.skyb` | 155 | `ce176ded67f2fdb05c6abd0c7c574077dcffab51cc5db862039618b7bb491c51` |
| `forward_left_back_no_lights.skyb` | 149 | `0cdc0623f3008352a4dc229e350c255ebfac86331804f5240bd3f46114202775` |
| `forward_left_back_truncated.skyb` | 64 | `e16b4de73e83470abda29c0541e3491d9ee36a86628a53ef7a8540899f27e49d` |
| `forward_left_back_v2.skyb` | 160 | `f1f77fc0c9d392bffb89f258871123b19108bda7c8637e2f9d2d318a49e772b0` |
| `forward_left_back_v2_invalid_chksum.skyb` | 160 | `5a4e133379e40aa3fb0fa32a3b16dd22105a0cd72738c84edc7f3846a5de0b8a` |
| `hover_3m.skyb` | 76 | `4fdda79702c27065a15fd50110a7d95c954aab2bad3c7bfec159f0c95f8a243d` |
| `hover_3m_with_rth_plan.skyb` | 134 | `3a07c766a22355c3e5ebaa1b3dbc0d052615c92fbc0e2896a6df44e3ec45b3a1` |
| `light_program_with_wait_until_cmd.skyb` | 169 | `ef7c3a0e3054b38679486033ae9e5c7f74df3f9bccb06626520f82a1bf0820c7` |
| `multiple_vertical_landing_segments.skyb` | 155 | `6f581605451e343351c3175acadf5b5cc1262a98df7afc7039a790cb35ee066e` |
| `pyro_events.skyb` | 87 | `20de3ebce4418a80dd63ed60b8b323279cee566c7e0f927968fb4c6537a4c32a` |
| `real_show.skyb` | 10457 | `bc328c3cef9dc449f47790ed33920649fa3648e6d4623f55fb277f4eda42cda7` |
| `test.skyb` | 110 | `27cb2189d0cf4b920270f6a0478f11039878cbeb988536419be6dc45a6e7d285` |
| `zero_scale.skyb` | 36 | `202722b7c13df3803a9f208e229e998b0f06348a8f7a3657ff069c11c82f557f` |

### B.1.2 Container framing — **verified**

```
offset 0   : "skyb"                 4 bytes, ASCII 73 6b 79 62
offset 4   : version                uint8    observed values: 1, 2
if version >= 2:
  offset 5 : feature byte           uint8    observed value: 0x01
  offset 6 : 4-byte field           see B.1.4 — purpose NOT confirmed
then, repeatedly, until end of file:
             block type             uint8
             block length           uint16, little-endian
             block body             <length> bytes
```

Verified by walking all thirteen files: in every non-truncated file the block
chain consumes the file exactly, with zero bytes left over.

Example, `real_show.skyb`: header 10 bytes, then `type=1 len=7043`
(10 + 3 + 7043 = 7056), then `type=2 len=3398` (7056 + 3 + 3398 = 10457) =
file length.

### B.1.3 Block types — **verified by fixture naming**

Block type numbers are matched to meaning by comparing which blocks appear in
which fixture, using the fixtures' own file names as the ground truth.

| Type | Meaning | Evidence |
|---|---|---|
| 1 | Trajectory | present in all 13 fixtures; always the first block |
| 2 | Light program | absent exactly in `forward_left_back_no_lights.skyb` |
| 3 | Comment | body of `test.skyb` block 3 is ASCII `"this is a te…"` |
| 4 | RTH plan | present only in `hover_3m_with_rth_plan.skyb` |
| 5 | Yaw control | present in `test.skyb`, `multiple_vertical_landing_segments.skyb` |
| 6 | Event list | present only in `pyro_events.skyb` |

**Block order is not fixed.** `test.skyb` yields 1, 3, 2, 5. An importer that
assumes a fixed order will fail on real files. DSX importers MUST dispatch on
the type byte.

### B.1.4 The 4-byte field at offset 6 — **NOT resolved**

The fixture pair `forward_left_back_v2.skyb` and
`forward_left_back_v2_invalid_chksum.skyb` have **byte-identical headers**
(including this field) and differ only from offset 131 onward. The file naming
implies the field is a checksum over the payload, and that the first file's
payload satisfies it.

It was not possible to reproduce the value. Tested and **excluded**:

- CRC-32 variants: ISO-HDLC, BZIP2, MPEG-2, POSIX, JAMCRC, XFER, CRC-32C,
  CRC-32D, CRC-32Q, AUTOSAR, CD-ROM-EDC
- over ranges: body only, header+body, whole file, whole file with the field
  zeroed, body minus trailing byte, all start offsets 0–15
- both little- and big-endian interpretations of the stored value
- Adler-32, Fletcher-32, additive sum32, word-wise XOR
- MD5 / SHA-1 / SHA-256 truncated to 4 bytes, leading and trailing

A useful additional observation: the payload of `forward_left_back.skyb` (v1)
is **byte-identical** to the payload of `forward_left_back_v2.skyb` (v2). The
v2 format therefore adds only the feature byte and this field; the block stream
is unchanged between versions.

**Consequence for DSX.** A DSX importer MUST NOT claim to verify SKYB
integrity. It SHOULD parse the block chain, confirm that it consumes the file
exactly — which is itself a strong structural check, and the one that caught
the truncated fixture — and report the 4-byte field as unverified.

Claiming a verification that has not been demonstrated is exactly the failure
mode DSX exists to remove.

### B.1.5 Event records — **verified**

`pyro_events.skyb`, block type 6, length 40 = 4 records of 10 bytes:

```
uint32 LE  time in milliseconds
uint8      event type
uint8      subtype / channel
uint32 LE  payload
```

Decoded content:

| t | type | channel | payload |
|---|---|---|---|
| 10 000 ms | 1 | 1 | `0x00000000` |
| 50 000 ms | 1 | 2 | `0x00000000` |
| 90 000 ms | 1 | 3 | `0x00000000` |
| 90 000 ms | 1 | 4 | `0x00000000` |

Two records share a timestamp: **simultaneous multi-channel firing is
representable and occurs in the vendor's own fixtures.** A DSX exporter
targeting SKYB MUST be able to emit coincident events, and a DSX validator MUST
apply actuator interlocks across all channels of one aircraft at a shared
instant (§6).

### B.1.6 What the event model does *not* contain

The on-aircraft representation carries a timestamp, a channel and an on/off
payload. It carries **no** duration, no pre-fire compensation, no orientation,
no arm/disarm state, no mass change and no hazard geometry.

Richer fields exist in the authoring-side JSON of that ecosystem, but they do
not survive into the file that flies. Any safety property expressed only in the
authoring layer is therefore unavailable to the aircraft and to any downstream
verifier.

This is the concrete gap that §6 (`prefire_latency_ms`, `dynamics`, `hazard`,
`interlocks`, `authority`) and §7 exist to close, and it is why DSX keeps
termination and payload state in the compiled layer rather than the manifest
alone.

---

## B.2 Formats not yet documented here

| Format | Status |
|---|---|
| `.skyc` outer container | ZIP; member layout to be documented from a published sample |
| `.dac` (HighGreat) | no public sample located |
| `.bin` (Litebee) | no public sample located |
| `.path` / `.path3` (DSS) | no public sample located |
| Drotek JSON | no public sample located |
| VVIZ | publicly specified by its vendors; no reverse observation required |
| DJI WPML | publicly specified by the vendor; no reverse observation required |

Contributions to this appendix are welcome and are governed by the separation-of-roles
boundary stated at the top.
