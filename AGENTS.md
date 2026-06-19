# AGENTS.md — community-mods

Guidance for agents working in the RAD community mods repository.

## What this repo is

Community-contributed mods for RAD products, one per folder at
`mods/<product>/<author>/<mod_name>/` where `<product>` is one of
`lockbox`, `dtt`, `ossm`, `radr`. The gallery at mods.researchanddesire.com is
**generated** from this tree — never hand-edit a top-level index.

## Hard rules

- Keep exactly the `mods/<product>/<author>/<mod_name>/` depth. No spaces in
  names. No nesting deeper than `<mod_name>/`.
- Each mod must have: a `cad/` file (STEP), at least one `img/` image, a
  `README.md`, and a `mod.yml`. Print files go in `print/` (LFS).
- **License is fixed, not a choice:** hardware/printable → CERN-OHL-S v2;
  software → MPL 2.0; docs/images → CERN-OHL-S v2. Never add a per-mod `LICENSE`
  or a different license. The root `LICENSE` path-map governs.
- Fill the `mod.yml` `safety` block — never leave it blank. Set the
  restraint-release / applied-force / electrical flags honestly.
- Do not hand-edit `.github/workflows/scripts/mod.schema.json` — it is vendored
  read-only from `researchanddesire/dev-docs`.

## mod.yml contract

Required keys: `title`, `author`, `product` (enum), `description`,
`mod_version` (int ≥ 1), `compatibility` (non-empty list), `images` (non-empty
list of paths), `safety` (object with the three boolean flags + `notes`).
There is **no `license` key**. Full schema:
`.github/workflows/scripts/mod.schema.json`.

## Validation

`mod-lint` validates every mod's `mod.yml`, folder shape, and required files on
PR. Run it locally with `python .github/workflows/scripts/mod_lint.py`. If it
passes, the structure is good.
