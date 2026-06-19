<!-- One mod per PR. See CONTRIBUTING.md. Both hosted and external/linked mods welcome. -->

## Mod

- **Product:** <!-- lockbox | dtt | ossm | radr -->
- **Folder:** `mods/<product>/<your-username>/<mod_name>/`
- **Type:** <!-- hosted (files in this repo) | external/linked (lives in my own repo) -->
- **What it does:**

## Submission checklist (all mods)

- [ ] One mod, at `mods/<product>/<author>/<mod_name>/` (no extra nesting, no spaces in names)
- [ ] `mod.yml` + `README.md` present, with the `safety` block filled (no blank fields)
- [ ] At least one image (an `img/` file, or an image URL for external mods)
- [ ] No per-mod `LICENSE` file; no referral/affiliate links in the README
- [ ] All commits are signed off (`git commit -s` → DCO)

## If hosted (files in this repo)

- [ ] `cad/` has a STEP file (print files, if any, go in `print/` via Git LFS)
- [ ] No `license` field in `mod.yml` (hosted license is fixed by the repo)

## If external / linked (lives in my own repo)

- [ ] `mod.yml` has `source_url:` (my repo) and `license:` (my repo's SPDX id — may differ from the default)
- [ ] README links to the upstream repo and notes the license if it differs

## Safety

- [ ] This mod does **not** affect restraint-release, applied force, or electrical/charging
- [ ] **or** it does, and I described it in `mod.yml` → `safety.notes` (expect a safety review)
