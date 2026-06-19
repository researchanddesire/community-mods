# Contributing a mod

Thanks for sharing a mod for a Research and Desire product. This guide covers the
folder layout, metadata, license, and review process. It mirrors the
gold-standard [VoronUsers](https://github.com/VoronDesign/VoronUsers) flow.

## Two kinds of mods — both equally welcome

You do **not** have to move your project into this repo to be listed. Pick
whichever fits:

- **Hosted mod** — you add the design files here, in your `mods/...` folder. Best
  for new parts you're happy to publish under the RAD license model.
- **External / linked mod** — your mod already lives in **your own repository**
  (any platform, any license) and we simply **index and link** it so people can
  find it on the [Mod Hub](https://mods.researchanddesire.com). **You keep
  ownership, maintenance, and your own license.** This is a fully first-class way
  to contribute — see [§3b](#3b-linking-an-external-mod-how-to). If you already
  have a great OSSM/Lockbox/DTT/RADR project out there, **linking it is
  encouraged** — no need to relicense or relocate anything.

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

> The table above is for **hosted** mods. **External / linked** mods are lighter
> — just `mod.yml` + `README.md` (no `cad/`/`print/` needed, files stay
> upstream). See [§3b](#3b-linking-an-external-mod-how-to).

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
tags:                    # optional; power the gallery's "browse by tag" sidebar
  - mount
  - quick-release
safety:                  # required block — do not leave blank
  affects_restraint_release: false
  affects_applied_force: false
  affects_electrical: false
  notes: "–"             # describe any safety-relevant behavior, or '–'
```

The schema is enforced by `mod-lint` and is canonical here at
`.github/workflows/scripts/mod.schema.json`.
There is **no `license` field** — license is fixed (see §4).

`tags` is optional but recommended: each tag becomes a filter in the gallery's
**"browse by tag"** sidebar, so good tags make your mod easier to discover.

## 3. Safety

These are intimate devices, not 3D printers. If your mod changes how a device
**releases a restraint**, the **force/torque** it can apply, or anything
**electrical / charging**, set the relevant `safety` flag to `true` and describe
it in `notes`. Flagged mods get an explicit **safety review** before merge.

## 3b. Linking an external mod (how-to)

Already have your mod in your own repo? **Link it — that's encouraged, and it
keeps your project yours.** We index it in the gallery and send people to your
repo; we don't copy your files or change your license.

**What's different from a hosted mod:**

- **No `cad/`, `print/`, or local image needed** — your files stay upstream.
- You **declare your own license** (it can differ from this repo's default).
- The gallery card shows a license badge and an **"Upstream source ↗"** link
  straight to your repo.

**Steps:**

1. Create just the folder `mods/<product>/<your-github-username>/<mod_name>/`
   with **two files**: `mod.yml` and `README.md`.
2. In `mod.yml`, set `source_url:` (your repo) and `license:` (your repo's SPDX
   id, e.g. `CC-BY-SA-4.0`, `MIT`, `GPL-3.0-or-later`). Use an image **URL**
   (e.g. a raw link to a photo in your repo) in `images:`.
3. In `README.md`, briefly describe the mod and link to your repo. Note the
   license if it differs from this repo's default.
4. Open the PR (see §5). `mod-lint` requires `license` exactly when `source_url`
   is set (and forbids it otherwise), so the difference is always explicit.

**Example `mod.yml`** (a linked mod under a different license):

```yaml
title: OSSM M5 Remote
author: ortlof
product: ossm
description: A wireless M5Stack remote for the OSSM (speed/depth/stroke).
mod_version: 1
compatibility:
  - OSSM (requires the OSSM-Stroke firmware)
  - M5Stack CoreS3 / Core2
source_url: https://github.com/ortlof/OSSM-M5-Remote   # your repo
license: CC-BY-SA-4.0                                   # your license (may differ)
images:
  - https://raw.githubusercontent.com/ortlof/OSSM-M5-Remote/master/image/remote.png
tags: [remote, external]
safety:
  affects_restraint_release: false
  affects_applied_force: true
  affects_electrical: false
  notes: "Commands OSSM motion; requires third-party OSSM-Stroke firmware."
```

See the live worked example at
[`mods/ossm/ortlof/m5-remote/`](mods/ossm/ortlof/m5-remote/).

> We **don't** require you to relicense or relocate an existing project to be
> listed. The only ask: declare the license honestly, keep your `README` links
> working, and fill in the `safety` block (it applies to every mod).

## 4. License (fixed for hosted mods — not your choice)

For a **hosted** mod, by submitting you agree your contribution is licensed
under the unified RAD model, matching the product it modifies:

- Hardware / printable design files (`cad`, `print`) → **CERN-OHL-S v2**
- Software / firmware (any code) → **MPL 2.0**
- Docs and images → **CERN-OHL-S v2**

Do **not** add a per-mod `LICENSE` file or pick a different license for a hosted
mod. See [LICENSE](LICENSE).

For an **external / linked** mod (§3b), the upstream license governs — declare
it in `mod.yml` `license:`. It can differ from the default; we link to it rather
than relicense it. Still no per-mod `LICENSE` file here — the declaration lives
in `mod.yml`.

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

`mod-lint` runs automatically (it knows hosted vs external from your `mod.yml`).
Once it's green, a **ModHelpers** reviewer will check structure, images, license,
and safety — plus CAD for hosted mods — then merge, and your mod shows up on
[mods.researchanddesire.com](https://mods.researchanddesire.com). **Both hosted
and linked mods are accepted on equal footing.**
