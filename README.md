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

In the gallery you can search by keyword, filter by product, and **browse by
tag** using the sidebar — pick one or more tags to narrow the list. Tags come
from the optional `tags:` field in each mod's `mod.yml`, so adding relevant tags
makes your mod easier to discover.

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

*(That's the **hosted** layout. An **external/linked** mod is just `mod.yml` +
`README.md` — its files stay in the author's own repo. See below.)*

## Submit a mod

There are **two equally-welcome ways** to contribute — see
**[CONTRIBUTING.md](CONTRIBUTING.md)**:

- **Host it here** — add the design files in a
  `mods/<product>/<your-github-username>/<mod_name>/` folder (layout above).
- **Link an external mod** — already have it in **your own repo**? You don't need
  to move or relicense it. Just add a tiny `mod.yml` + `README.md` with
  `source_url:` and your `license:`, and we **index and link** it in the gallery.
  Your project stays yours; **its license may differ from this repo's default.**
  See the worked example: [`mods/ossm/ortlof/m5-remote/`](mods/ossm/ortlof/m5-remote/)
  (CC-BY-SA-4.0), and [CONTRIBUTING §3b](CONTRIBUTING.md#3b-linking-an-external-mod-how-to).

Either way, open a pull request — CI (`mod-lint`) checks structure and metadata,
and a reviewer from the ModHelpers rotation handles the rest.

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
