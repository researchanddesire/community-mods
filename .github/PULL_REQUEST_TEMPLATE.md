<!-- One project per PR. Indexed and hosted projects are equally welcome. See CONTRIBUTING.md. -->

## Project

- **Ecosystem:** <!-- lockbox | dtt | ossm | radr; stored in `product` -->
- **Folder:** `mods/<ecosystem>/<project_slug>/`
- **Project credit:** <!-- person, team, or community named in `author` -->
- **Contribution path:** <!-- indexed (maintained upstream) | hosted (files live here) -->
- **What it does:**

## Submission checklist — every project

- [ ] One project at exactly `mods/<ecosystem>/<project_slug>/`, with no spaces in those catalog directory names
- [ ] The project slug is unique within its ecosystem, and `author` gives the public credit you want shown in the hub
- [ ] `mod.yml` and `README.md` are present
- [ ] `mod.yml` declares a non-empty compatibility list, a license, at least one image, and a complete safety block
- [ ] `product` identifies the ecosystem and `mod_version` identifies the catalog-entry version
- [ ] The README contains no referral or affiliate links

## If indexed (maintained upstream)

- [ ] `mod.yml` has `source_url` and the same license name used upstream
- [ ] `images` contains a working upstream URL or a local image in `img/`
- [ ] The README links to the upstream project
- [ ] The upstream project hosts its license terms; this catalog entry does not copy them

## If hosted (files live here)

- [ ] `source_url` is omitted and `images` references at least one local image
- [ ] An OSSM project declares exactly `CERN-OHL-S-2.0`; its files use the repository license, so no separate project-local `LICENSE` is needed
- [ ] A non-OSSM project enters its license name and includes matching text in a project-root `LICENSE`
- [ ] Optional CAD, print, source, and documentation files are in the project folder; CAD or source code is not required

## Safety

- [ ] The project does **not** affect restraint release, applied force, or electrical or charging behavior
- [ ] **or** it does, each relevant flag is `true`, and the behavior is explained in `mod.yml` → `safety.notes`

> Inclusion in the R+D Project Hub is not endorsement, safety certification, or
> warranty by Research and Desire.
