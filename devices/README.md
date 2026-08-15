# Device profiles (`.dsxp`)

Naming: `vendor@model@revision.dsxp` (lowercase, no spaces) — e.g.
`acme@x1@2026-rev1.dsxp`.

Rules (see spec §5 and `CONTRIBUTING.md`):

1. `device_type_id` is a **UUID** and MUST NOT change across revisions of the
   same model.
2. Write `null` for anything you do not know. **Do not guess.** A wrong number
   in a device profile silently authorises a show that the hardware cannot fly.
3. Record a `source` for each figure: `"datasheet 2026-03"`, `"measured"`,
   `"vendor email"`. Where public vendor documentation contradicts itself —
   which does happen — record both and mark the field `null` until resolved.
4. Never widen a limit to make a show validate. That is what
   `declared_envelope` in the show is for, and the validator is supposed to
   catch the difference.

Profiles here are contributed by vendors and operators. A profile is a factual
claim about hardware; it carries the contributor's name.

`_template-aircraft.dsxp` and `_template-actuator.dsxp` are starting points.
