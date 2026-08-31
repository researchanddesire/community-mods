# R+D Project Hub

Community-built OSSM variants, controllers, software, hardware, accessories, and
tools across R+D-adjacent ecosystems.

> **Independently maintained.** Inclusion in this directory is not endorsement,
> safety certification, or warranty by Research and Desire. Review each
> project's documentation and safety disclosure before using it.

## Browse projects

Every accepted project appears automatically in the gallery at
**[mods.researchanddesire.com](https://mods.researchanddesire.com)** (built from
the `mods/` tree on merge), or you can browse the catalog directly under
[`mods/`](mods/).

Search by keyword, filter by ecosystem, or combine tags to find variants,
controllers, software, hardware, accessories, and other related work. Tags come
from the optional `tags:` field in each project's metadata.

## Catalog format

Every project uses the same established file and validation interfaces:

```text
mods/<ecosystem>/<author>/<project_slug>/
├── img/        # at least one local image for a hosted project
├── cad/        # optional design files
├── print/      # optional STL / 3MF files (Git LFS)
├── src/        # optional software or firmware
├── docs/       # optional BOMs, assembly guides, and other documentation
├── LICENSE     # required only for hosted, non-OSSM projects
├── mod.yml     # required project metadata
└── README.md   # required project description
```

The catalog path is `mods/<ecosystem>/<author>/<project_slug>/mod.yml`. Within
`mod.yml`, `product` identifies the ecosystem and `mod_version` tracks the
catalog-entry version. Run the validator with `mod-lint`. These stable technical
names support projects of every kind, including complete variants, controllers,
software, hardware, accessories, and mods.

## Submit a project

There are two equally welcome contribution paths. See the Project Hub's
**[Contributing guide](https://mods.researchanddesire.com/contributing/)** for
the complete contract; its source lives in [CONTRIBUTING.md](CONTRIBUTING.md).

- **Index a project** — keep the project in its maintainer's repository and add
  metadata plus a short README here. Set `source_url` and the upstream project's
  disclosed `license`; an image URL is accepted. Indexed entries have no local
  `LICENSE` file.
- **Host a project** — keep the project's files in this repository. Every
  hosted entry needs metadata, a README, a safety disclosure, at least one
  image, and a declared license. CAD and source code are optional, not minimum
  requirements.

Either way, open a pull request. CI runs `mod-lint` to check the catalog
structure and metadata before maintainer review. Indexed and hosted projects
are presented on equal footing in the gallery.

## Licensing

Every project declares `license` in `mod.yml`. Copy the license name the project
already uses, such as `MIT`, `GPL-3.0-only`, or `CERN-OHL-S-2.0`. If a project
has its own terms, use a plain descriptive name such as `Community Use Terms`.
Indexed projects may use any clearly stated upstream license. Hosted projects
follow the ecosystem rules below.

- **Indexed projects:** the disclosed upstream license governs. Set
  `source_url` and do not add a project-local `LICENSE` here.
- **Hosted OSSM projects:** declare exactly `CERN-OHL-S-2.0`. Do not add a
  project-local `LICENSE`; the repository's license notice governs this content.
- **Other hosted projects:** enter their license name and include the
  full license terms in a `LICENSE` file at the project root.

Hub-authored catalog summaries, metadata, and general documentation use
`CC-BY-4.0`; repository tooling uses `MPL-2.0`. Hosted project files follow the
rules above. OSSM is described here as a shared ecosystem name, while names and
branding clearly owned by Research and Desire remain reserved. See
[LICENSE](LICENSE) for the complete path-specific terms.

## Related

| | |
|---|---|
| R+D user docs | [docs.researchanddesire.com](https://docs.researchanddesire.com) |
| R+D developer docs | [dev.researchanddesire.com](https://dev.researchanddesire.com) |
| Current ecosystems | [Lockbox](https://github.com/researchanddesire/Lockbox) · [Deep Throat Trainer](https://github.com/researchanddesire/DT_Trainer) · [OSSM](mods/ossm/) · [RADR](https://github.com/researchanddesire/radr-wireless-remote) |

The gallery is hosted by [Research and Desire](https://researchanddesire.com).
