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

**Status: empty.** The suite does not exist yet, and until `sampling/` contains
vectors, the interoperability guarantee in §1.4 is an intention rather than a
verifiable property. This is stated plainly because the alternative — implying
conformance testing that does not exist — is exactly the behaviour this project
was created to replace.

An implementation declares a **profile** (L0/L1/L2) and a **role**
(`reader`, `writer`, `validator`, `uploader`, `visualiser`). Roles matter: a
visualiser MAY be permissive where an uploader MUST NOT be.
