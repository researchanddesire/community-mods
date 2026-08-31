<!-- One project per PR. Indexed and hosted projects are equally welcome. See CONTRIBUTING.md. -->

## Project

- **Ecosystem:** <!-- lockbox | dtt | ossm | radr; stored in `product` -->
- **Folder:** `mods/<ecosystem>/<your-username>/<project_slug>/`
- **Contribution path:** <!-- indexed (maintained upstream) | hosted (files live here) -->
- **What it does:**

## Submission checklist — every project

- [ ] One project at exactly `mods/<ecosystem>/<author>/<project_slug>/`, with no spaces in those catalog directory names
- [ ] `mod.yml` and `README.md` are present
- [ ] `mod.yml` declares a non-empty compatibility list, a license, at least one image, and a complete safety block
- [ ] `product` identifies the ecosystem and `mod_version` identifies the catalog-entry version
- [ ] The README contains no referral or affiliate links
- [ ] All commits are signed off (`git commit -s` → DCO)

## If indexed (maintained upstream)

- [ ] `mod.yml` has `source_url` and the license disclosed upstream, as an SPDX identifier or `LicenseRef-*`
- [ ] `images` contains a working upstream URL or a local image in `img/`
- [ ] The README links to the upstream project
- [ ] There is no project-local `LICENSE` in this repository

## If hosted (files live here)

- [ ] `source_url` is omitted and `images` references at least one local image
- [ ] An OSSM project declares exactly `CERN-OHL-S-2.0` and has no project-local `LICENSE`
- [ ] A non-OSSM project declares its SPDX identifier or `LicenseRef-*` and includes matching text in a project-root `LICENSE`
- [ ] Optional CAD, print, source, and documentation files are in the project folder; CAD or source code is not required

## Safety

- [ ] The project does **not** affect restraint release, applied force, or electrical or charging behavior
- [ ] **or** it does, each relevant flag is `true`, and the behavior is explained in `mod.yml` → `safety.notes`

> Inclusion in the R+D Project Hub is not endorsement, safety certification, or
> warranty by Research and Desire.

## Repository policy

- [ ] This pull request does not change the repository-wide license or trademark notice, **or** the project owner and a qualified legal reviewer have approved those changes before merge
