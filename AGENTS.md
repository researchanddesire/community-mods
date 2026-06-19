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
- **Hosted mod:** must have a `cad/` file (STEP), at least one `img/` image, a
  `README.md`, and a `mod.yml`. Print files go in `print/` (LFS). License is
  **fixed**: hardware/printable → CERN-OHL-S v2; software → MPL 2.0;
  docs/images → CERN-OHL-S v2. The root `LICENSE` path-map governs; `mod.yml`
  must NOT set a `license`.
- **External / linked mod:** files live in the author's own repo. `mod.yml` sets
  `source_url:` (upstream) and `license:` (upstream SPDX id — may differ from the
  default). No `cad/` required; an image URL is fine. Still no per-mod `LICENSE`
  file. `mod-lint` requires `license` iff `source_url` is set.
- Never add a per-mod `LICENSE` file in either case.
- Fill the `mod.yml` `safety` block — never leave it blank. Set the
  restraint-release / applied-force / electrical flags honestly.
- `.github/workflows/scripts/mod.schema.json` is the **canonical** mod schema
  (this repo is its only consumer — not vendored from dev-docs). Edit it
  deliberately when the standard changes; `mod-lint` enforces it.

## mod.yml contract

Required keys: `title`, `author`, `product` (enum), `description`,
`mod_version` (int ≥ 1), `compatibility` (non-empty list), `images` (non-empty
list of paths or URLs), `safety` (object with the three boolean flags + `notes`).
Optional: `tags`. External/linked mods add `source_url` (upstream repo) and
`license` (upstream SPDX id) — `license` is required iff `source_url` is set, and
forbidden otherwise. Full schema: `.github/workflows/scripts/mod.schema.json`.

## Validation

`mod-lint` validates every mod's `mod.yml`, folder shape, and required files on
PR. Run it locally with `python .github/workflows/scripts/mod_lint.py`. If it
passes, the structure is good.
