# AGENTS.md — R+D Project Hub

Guidance for agents working in the Project Hub repository.

## What this repository is

This is a directory of independently maintained OSSM variants, controllers,
software, hardware, accessories, tools, and projects in related ecosystems.
Research and Desire hosts the directory; inclusion is not endorsement, safety
certification, or warranty.

Each project entry uses the catalog path
`mods/<ecosystem>/<author>/<project_slug>/`, where `<ecosystem>` is `lockbox`,
`dtt`, `ossm`, or `radr`. The gallery at mods.researchanddesire.com is generated
from this tree. Never hand-edit a generated top-level gallery.

## Hard rules

- Keep exactly the `mods/<ecosystem>/<author>/<project_slug>/` catalog depth.
  Use no spaces in those three catalog directory names and do not add another
  catalog level below `<project_slug>`.
- Every project requires `mod.yml`, `README.md`, a non-empty `images` list, a
  complete `safety` object, and a declared `license`.
- In `license`, copy the license name used by the project, such as `MIT`,
  `GPL-3.0-only`, or `CERN-OHL-S-2.0`. If the project has its own terms, use a
  plain descriptive name such as `Community Use Terms`.
- **Indexed project:** set `source_url` to the upstream project and `license` to
  the same short license name used there. An upstream image URL is allowed. The
  upstream repository keeps the license terms.
- **Hosted OSSM project:** omit `source_url`, set `license` to exactly
  `CERN-OHL-S-2.0`, and include at least one local image. These project files
  use the repository license, so a separate project-local `LICENSE` is not
  needed.
- **Other hosted project:** omit `source_url`, enter its license name,
  include at least one local image, and add the matching license text at the
  project root as `LICENSE`.
- CAD and source code are optional. A hosted project does not need a `cad/`,
  STEP file, or source directory to qualify. Put print files in `print/` and
  track applicable binaries through Git LFS.
- Indexed projects may use any clearly stated upstream license; hosted projects
  follow the ecosystem rules above.
- Fill every `safety` flag honestly and keep `safety.notes` non-blank. Applied
  force, restraint-release, and electrical or charging behavior require human
  safety review.
- `.github/workflows/scripts/mod.schema.json` is the canonical metadata schema.
  Edit it deliberately when the standard changes; `mod-lint` enforces it.

## Catalog interface

Use project-first and ecosystem-first wording in UI, documentation, reviews,
and validation output. Preserve these stable technical interfaces:

- catalog path: `mods/<ecosystem>/<author>/<project_slug>/mod.yml`
- metadata filename: `mod.yml`
- ecosystem key: `product`
- catalog-entry version key: `mod_version`
- validation command and script name: `mod-lint` / `mod_lint.py`

These names apply equally to complete variants, controllers, software,
hardware, accessories, tools, and mods.

## `mod.yml` contract

Required keys are `title`, `author`, `product` (ecosystem enum),
`description`, `mod_version` (integer at least 1), `compatibility` (non-empty
list), `license`, `images` (non-empty list of paths or URLs), and `safety` (the
three boolean flags plus non-blank `notes`). `tags` is optional and free-form.
An indexed project also sets `source_url`; a hosted project omits it.

Indexed and hosted submissions are first-class, equal contribution paths. Do
not imply that indexed projects are warnings or lesser entries.

## Validation

Run the catalog validator with:

```bash
python .github/workflows/scripts/mod_lint.py
```

Also run its regression tests and build the generated gallery when changing the
catalog contract or public project metadata. A passing `mod-lint` confirms the
structure and metadata contract; it is not a safety certification.
