# Tools

The specification is normative; tools are not. Reference implementations are
published separately under **Apache-2.0** so they can be embedded in
proprietary firmware and products.

## Exists today

| Tool | Purpose |
|---|---|
| `dsx_seal.py` | compute, write and verify `content_hash` and the detached ed25519 signature (spec 2.3.1). `hash` / `seal` / `verify` / `keygen`. |
| `build_examples.py` | regenerate the trajectory, light, geometry and audio resources of the bundled examples, driven by the manifests themselves |
| `observe_skyb.py` | print observations about a third-party `.skyb` file you supply. Reads only; ships no fixtures; states hypotheses as hypotheses (see `NOTICE-PROVENANCE.md`) |
| `dsx_sample.py` | the normative sampler (§4.4): resource JSON → the canonical `t_ms,x_m,y_m,z_m,r,g,b` CSV of §4.4.5. Clean-room from §4 alone; stdlib only. Points where §4 left a choice open are listed in its `AMBIGUITIES` constant |

```
python3 tools/dsx_sample.py --traj examples/minimal-l0/traj/0001.json \
                            --light examples/minimal-l0/light/0001.json \
                            --rate 5 --duration-ms 10000 -o frames.csv
```

After editing an example, re-seal it or the archive checks fail:

```
python3 tools/build_examples.py
python3 tools/dsx_seal.py seal examples/rotation-l2
```

## Planned

| Tool | Purpose |
|---|---|
| `dsx-validate` | schema + semantic validation, regulatory profile checking, human-readable and PDF report |
| `dsx-convert` | conversion to and from existing formats, each with a published **loss matrix** (§9) |

**The separation-of-roles rule applies** (`NOTICE-PROVENANCE.md` §4): contributors who
have read the source of a GPL-licensed drone show implementation may work on
the specification but not on the corresponding reference implementation.
