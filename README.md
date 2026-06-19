# RAD Community Mods

Community-built upgrades, accessories, and printable parts for Research and
Desire products — **Lockbox**, **Deep Throat Trainer**, **OSSM**, and **RADR**.

> **Community-maintained, not official.** Mods here are contributed by the
> community and are **not** safety-tested or warranted by Research and Desire.
> Use at your own risk.

## Browse

Every accepted mod appears automatically in the gallery at
**[mods.researchanddesire.com](https://mods.researchanddesire.com)** (built from
the `mods/` tree on merge), or browse the source directly under
[`mods/`](mods/).

```
mods/
├── lockbox/<author>/<mod_name>/
├── dtt/<author>/<mod_name>/
├── ossm/<author>/<mod_name>/
└── radr/<author>/<mod_name>/
    ├── cad/        # STEP required (open format); native (F3D, etc.) optional
    ├── print/      # STL / 3MF print files (Git LFS)
    ├── img/        # at least one render or photo
    ├── docs/       # optional: BOM, assembly PDF, extras
    ├── mod.yml     # metadata (lint-gated)
    └── README.md   # description, BOM, vendor links
```

## Submit a mod

Read **[CONTRIBUTING.md](CONTRIBUTING.md)**, then open a pull request that adds a
single `mods/<product>/<your-github-username>/<mod_name>/` folder. CI
(`mod-lint`) checks the structure and metadata; a reviewer from the ModHelpers
rotation handles the rest.

## License

**Hosted mods** follow the unified RAD license model — **CERN-OHL-S v2** for
hardware/printable design files, **MPL 2.0** for any software. No contributor
license choice. See [LICENSE](LICENSE).

**External / linked mods** (hosted in the author's own repo and indexed here)
keep their **upstream license**, declared in `mod.yml` — it may differ from the
default. Example: [`mods/ossm/ortlof/m5-remote/`](mods/ossm/ortlof/m5-remote/)
is CC-BY-SA-4.0. See [CONTRIBUTING.md](CONTRIBUTING.md) §3b.

## Related

| | |
|---|---|
| User docs | [docs.researchanddesire.com](https://docs.researchanddesire.com) |
| Developer docs | [dev.researchanddesire.com](https://dev.researchanddesire.com) |
| Products | [Lockbox](https://github.com/researchanddesire/Lockbox) · [DT_Trainer](https://github.com/researchanddesire/DT_Trainer) · [ossm](https://github.com/researchanddesire/ossm) · [radr-wireless-remote](https://github.com/researchanddesire/radr-wireless-remote) |
