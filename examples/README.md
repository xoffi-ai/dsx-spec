# Examples

| Directory | Profile | Shows |
|---|---|---|
| `minimal-l0/` | L0 | the smallest valid DSX: mandatory frame + time, two sampled aircraft |
| `show-l1/` | L1 | *(to be written)* segment trajectories, device binding, geofence, RTH |
| `pyro-l2/` | L2 | *(to be written)* payloads, termination, provenance signature |

Each example directory is the **unzipped content** of a `.dsx` file. To build one:

```sh
cd minimal-l0 && zip -r ../minimal-l0.dsx .
```

Note that even the minimal example must declare `alt_ref`, `handedness` and
`bearing_deg`. That is intentional: those three fields are the ones whose
absence causes conversion accidents, so there is no profile in which they are
optional.
