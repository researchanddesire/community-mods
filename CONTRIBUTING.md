# Contributing a project

Thanks for sharing a project with the R+D Project Hub. The directory welcomes
complete OSSM variants, controllers, software, hardware, accessories, tools,
and other work related to the ecosystems represented here. Projects may be
standalone builds, compatible variants, additions, or mods.

## Two contribution paths — equal in the hub

Choose the path that fits how the project is maintained:

- **Indexed project** — the project stays in its maintainer's own repository.
  This repository stores only its catalog metadata and a short README, and the
  gallery links people to the upstream source.
- **Hosted project** — the project and any files its maintainer wants to publish
  live in this repository. CAD and source code are supported but are not
  submission requirements.

Both paths receive equal placement in the gallery. Indexing does not transfer
ownership, maintenance, or licensing to Research and Desire.

## 1. Catalog layout

Add one project per pull request at exactly this depth:

```text
mods/<ecosystem>/<your-github-username>/<project_slug>/
```

- `<ecosystem>` is one of `lockbox`, `dtt`, `ossm`, or `radr`.
- Use no spaces in the `<ecosystem>`, `<author>`, or `<project_slug>` catalog
  directory names.
- Do not nest the catalog entry deeper than `<project_slug>/`.

Every project uses
`mods/<ecosystem>/<author>/<project_slug>/mod.yml`. In the metadata, `product`
identifies the ecosystem and `mod_version` tracks the catalog entry's version.
The validation command is named `mod-lint`.

For a hosted project, the root may contain:

| Path | Required | Contents |
|---|---:|---|
| `mod.yml` | yes | Catalog metadata, license, compatibility, and safety disclosure. |
| `README.md` | yes | Description, usage, attribution, and relevant project links. |
| `img/` | yes | At least one local project image referenced by `images`. |
| `LICENSE` | conditional | Required for hosted non-OSSM projects; forbidden for hosted OSSM projects. |
| `cad/` | no | Optional design files; use open formats where practical. |
| `print/` | no | Optional `.stl` or `.3mf` files, tracked through Git LFS. |
| `src/` | no | Optional software or firmware. |
| `docs/` | no | Optional BOMs, assembly guides, PDFs, or other supporting material. |

There is no minimum CAD or source-code requirement. An indexed project's local
entry usually contains only `mod.yml` and `README.md`; its image may be an
upstream URL, and it must not include a local `LICENSE` file.

A starter entry is available at
[`mods/ossm/SAMPLE_AUTHOR/sample_mount/`](mods/ossm/SAMPLE_AUTHOR/sample_mount/).

## 2. Metadata in `mod.yml`

This hosted OSSM example shows the required core:

```yaml
title: Quick-release wall mount
author: your-github-username
product: ossm            # ecosystem: lockbox | dtt | ossm | radr
description: A wall bracket with a quick-release dovetail.
mod_version: 1           # bump when the catalog entry changes
compatibility:
  - OSSM variant and revision actually tested
license: CERN-OHL-S-2.0
images:
  - img/printed.jpg
tags:
  - accessory
  - mount
safety:
  affects_restraint_release: false
  affects_applied_force: false
  affects_electrical: false
  notes: "–"
```

Required keys are `title`, `author`, `product`, `description`, `mod_version`,
`compatibility`, `license`, `images`, and `safety`. `compatibility` and `images`
must be non-empty. The `safety` object requires all three boolean flags plus
non-blank `notes`. `tags` is optional, free-form classification used by the
gallery. `source_url` is added only for an indexed project.

For `license`, copy the license name the project already uses, such as `MIT`,
`GPL-3.0-only`, or `CERN-OHL-S-2.0`. If the project has its own terms, use a
plain descriptive name such as `Community Use Terms`. Indexed projects may use
any clearly stated upstream license; hosted projects follow the ecosystem rules
below. If you are not sure what to enter, open the pull request anyway and a
maintainer can help.

The canonical schema is
`.github/workflows/scripts/mod.schema.json`, enforced by `mod-lint`.

## 3. Choose the project's hosting model

### 3a. Index a project maintained elsewhere

An indexed entry keeps its files, releases, issue tracking, and license in the
upstream repository.

1. Create `mods/<ecosystem>/<your-github-username>/<project_slug>/` with
   `mod.yml` and `README.md`.
2. Set `source_url` to the upstream project and copy its license name into
   `license`.
3. Add at least one image to `images`; an absolute upstream image URL is
   accepted.
4. Link the upstream source from the README. Do not add a project-local
   `LICENSE` to this repository.

Example indexed metadata:

```yaml
title: Example OSSM controller
author: your-github-username
product: ossm
description: A separately maintained controller for OSSM-compatible machines.
mod_version: 1
compatibility:
  - Tested OSSM-compatible firmware and hardware revision
source_url: https://github.com/your-github-username/example-controller
license: MIT
images:
  - https://raw.githubusercontent.com/your-github-username/example-controller/main/controller.jpg
tags:
  - controller
  - hardware
safety:
  affects_restraint_release: false
  affects_applied_force: true
  affects_electrical: true
  notes: "Controls machine motion and uses external electrical power; follow the upstream safety instructions."
```

The license declaration describes the upstream project; the hub indexes and
links the work rather than relicensing it.

### 3b. Host a project in this repository

Every hosted project includes `mod.yml`, `README.md`, a complete `safety` block,
and at least one local image. Add CAD, print, source, or supporting files only
when they are part of the project.

The license rule depends on ecosystem:

- A hosted project under `mods/ossm/` must declare exactly
  `CERN-OHL-S-2.0` and must not include a project-local `LICENSE`. The root
  repository notice supplies the applicable text.
- A hosted project under `mods/lockbox/`, `mods/dtt/`, or `mods/radr/` may
  use any license or custom terms. Enter the license name in `license`
  and include the matching license text at
  `mods/<ecosystem>/<author>/<project_slug>/LICENSE`.

Hub-authored catalog summaries, metadata, and general documentation use
`CC-BY-4.0`, while repository tooling uses `MPL-2.0`. See the repository
[LICENSE](LICENSE) notice for the complete path-specific terms.

## 4. Safety disclosure

Safety metadata is mandatory for every indexed and hosted project. If a project
changes how a restraint releases, the force or torque a machine can apply, or
anything electrical or charging-related, set the corresponding flag to `true`
and explain the behavior in `safety.notes`. Flagged entries receive explicit
human safety review before merge.

Inclusion is not endorsement, safety certification, or warranty by Research
and Desire. Maintainers and users remain responsible for evaluating the project
and its upstream documentation.

## 5. Open the pull request

1. Fork this repository and create a branch other than `main`.
2. Add one `mods/<ecosystem>/<author>/<project_slug>/` entry, commit it, and
   push it.
3. Open a pull request and complete the project checklist.

`mod-lint` checks the catalog structure, metadata, image presence, license field
and any required license file, and safety disclosure. Maintainers then review
the project entry, links, license, and safety information. OSSM is treated as a
shared ecosystem name rather than an R+D-owned trademark; names and branding
clearly owned by Research and Desire remain reserved.

After merge, indexed and hosted projects appear on equal footing at
[mods.researchanddesire.com](https://mods.researchanddesire.com).
