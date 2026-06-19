# Contributing a mod

Thanks for sharing a mod for a Research and Desire product. This guide covers the
folder layout, metadata, license, and review process. It mirrors the
gold-standard [VoronUsers](https://github.com/VoronDesign/VoronUsers) flow.

## 1. Folder layout

Add **one mod per pull request** at exactly this depth:

```
mods/<product>/<your-github-username>/<mod_name>/
```

- `<product>` is one of `lockbox`, `dtt`, `ossm`, `radr`.
- No spaces in file or folder names.
- Do not nest deeper than `<mod_name>/`.

Inside `<mod_name>/`:

| Path        | Required | Contents |
|-------------|----------|----------|
| `cad/`      | **yes**  | At least one **CAD** file. STEP (`.step`) is required (open format); native (`.f3d`, etc.) optional. |
| `print/`    | optional | Print-ready `.stl` / `.3mf` (tracked via Git LFS). |
| `img/`      | **yes**  | At least one render or photo of the mod. |
| `docs/`     | optional | BOM, assembly PDF, extra documentation. |
| `mod.yml`   | **yes**  | Metadata (see below). |
| `README.md` | **yes**  | Description, BOM, assembly notes, vendor links (no referral/affiliate links). |

A starter is provided at [`mods/ossm/SAMPLE_AUTHOR/sample_mount/`](mods/ossm/SAMPLE_AUTHOR/sample_mount/) — copy it and edit.

## 2. `mod.yml`

```yaml
title: Quick-release wall mount
author: your-github-username
product: ossm            # lockbox | dtt | ossm | radr
description: A wall bracket with a quick-release dovetail.
mod_version: 1           # start at 1; bump when you change the mod
compatibility:           # only list what you (or someone) actually tested
  - OSSM v2
images:
  - img/printed.jpg
safety:                  # required block — do not leave blank
  affects_restraint_release: false
  affects_applied_force: false
  affects_electrical: false
  notes: "–"             # describe any safety-relevant behavior, or '–'
```

The schema is enforced by `mod-lint` and is canonical here at
`.github/workflows/scripts/mod.schema.json`.
There is **no `license` field** — license is fixed (see §4).

## 3. Safety

These are intimate devices, not 3D printers. If your mod changes how a device
**releases a restraint**, the **force/torque** it can apply, or anything
**electrical / charging**, set the relevant `safety` flag to `true` and describe
it in `notes`. Flagged mods get an explicit **safety review** before merge.

## 4. License (fixed — not your choice)

By submitting you agree your contribution is licensed under the unified RAD
model, matching the product it modifies:

- Hardware / printable design files (`cad/`, `print/`) → **CERN-OHL-S v2**
- Software / firmware (any code) → **MPL 2.0**
- Docs and images → **CERN-OHL-S v2**

Do **not** add a per-mod `LICENSE` file or a different license. See
[LICENSE](LICENSE).

### DCO sign-off (required)

Every commit must be signed off under the
[Developer Certificate of Origin](https://developercertificate.org/) — it
affirms you have the right to contribute under the license above:

```bash
git commit -s -m "Add my mod"
```

This adds a `Signed-off-by: Your Name <you@example.com>` line. PRs without
sign-off on every commit fail CI.

## 5. Open the PR

1. Fork this repo and create a branch (not `main`).
2. Add your `mods/<product>/<author>/<mod_name>/` folder, `git commit -s`, push.
3. Open a pull request and fill in the checklist.

`mod-lint` runs automatically. Once it's green, a **ModHelpers** reviewer will
check structure, CAD, images, and safety, then merge — and your mod shows up on
[mods.researchanddesire.com](https://mods.researchanddesire.com).
