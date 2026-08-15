# Conformance suite

Normative. See spec §9.

```
sampling/      bit-exact test vectors for the normative sampler (§4.4)
roundtrip/     unknown fields and extensions survive read -> write (§8.2)
identity/      device binding, mode existence, envelope comparison, firmware gating (§5)
errors/        each REJECT / BLOCK-FLIGHT / WARN condition fires at exactly the right level
safety/        termination completeness, RTH feasibility, fall containment, authority rule (§6.2, §7)
coordinates/   altitude reference, handedness, bearing; correct refusal when absent (§3)
determinism/   .dsx -> .dsb byte-identical across runs and platforms (§1.2)
```

## What exists today

Four suites, all offline. `$ref` resolution uses a local registry, because a
validator that reaches the network cannot be used on an air-gapped show site.

```
python3 conformance/run_schema_checks.py    # schema-level
python3 conformance/check_rotation.py       # semantic rules of section 10
python3 conformance/check_archive.py        # archive-level
python3 conformance/run_sampling_checks.py  # normative sampler (section 4.4)
```

| Script | What it proves |
|---|---|
| `run_schema_checks.py` | the schema accepts the examples and **rejects** every field whose absence causes conversion accidents — including misspelt safety fields, since a closed core is what makes a typo an error instead of a silent deletion (section 8.1.1) |
| `check_rotation.py` | the semantic rules of section 10 that JSON Schema cannot express: interval coverage, exclusivity, turnaround and energy closure, the steady-state inequalities of 10.8 |
| `check_archive.py` | the archive around the manifest: every referenced resource is carried (2.1), every track and light file validates against `schema/resource.schema.json` (section 4), `content_hash` recomputes and the signature verifies (2.3.1), and a declared loop actually closes in its own trajectory (R10.21) — see `eval_seam`, which needs the boundary segments to be `bezier` (A37) |
| `run_sampling_checks.py` | `tools/dsx_sample.py` reproduces five hand-computed vectors byte for byte (`sampling/`, see its `INDEX.md` for the derivations), plus that a `strobe` op without `duty` is rejected — by the tool *and* by the schema — and that a channel beyond R/G/B is reported as a WARN, not dropped silently (§4.4.5) |

Each script prints its own `n/n passed`. Counts are deliberately not repeated
here: a number maintained in prose drifts from the number the suite produces,
and this README already carried two different ones.

Requires `jsonschema`, `referencing` and — for signature verification —
`cryptography`. A skipped check is reported as SKIP, never as a pass.

## The planned suite

**Status: `sampling/` exists and runs in CI; `roundtrip/`, `identity/`,
`errors/` and `determinism/` are not written yet.** They describe the intended
shape of the full suite. `sampling/` is not exhaustive either — see A36 in
`spec/A-open-questions.md` for exactly which segment types, interpolation
modes and boundary cases are not yet vectorised. This is stated plainly
because the alternative — implying conformance testing that does not exist —
is exactly the behaviour this project was created to replace.

An implementation declares a **profile** (L0/L1/L2) and a **role**
(`reader`, `writer`, `validator`, `uploader`, `visualiser`). Roles matter: a
visualiser MAY be permissive where an uploader MUST NOT be.
