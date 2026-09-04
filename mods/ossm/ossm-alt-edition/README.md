# OSSM ALT Edition

A community-driven, ground-up OSSM variant. It centers on a
custom **28V 140W USB-C Power Delivery PCB** (ESP32-S3 + integrated RS485), with
**MGN12H / MGN15H** rail options, comprehensive power-protection circuits, and a
fully open hardware design optimized for 3D printing and European parts sourcing.

![OSSM ALT Edition](https://raw.githubusercontent.com/jollydodo/OSSM-ALT-Edition/main/Images/cover.jpg)

> **Indexed project.** This project is maintained in the author's own
> repository. All design files (PCB schematics and layouts, STEP / STL / 3MF,
> BOM, print manual, and assembly guides) live upstream:
>
> **Project source → https://github.com/jollydodo/OSSM-ALT-Edition**

## License

> This project is licensed
> [CERN-OHL-S-2.0](https://ohwr.org/cern_ohl_s_v2.txt) (CERN Open Hardware
> Licence Version 2 – Strongly Reciprocal). The work is authored and hosted
> upstream by [jollydodo](https://github.com/jollydodo); respect the upstream
> terms when you build, remix, or redistribute it.

## Highlights

- **Custom 28V 140W USB-C PD board**: CH224Q PD negotiation, 4-layer design,
  over/under-voltage, reverse-current, inrush, and ESD protection.
- **ESP32-S3** microcontroller with integrated **RS485**; made for the
  [OSSM Rust (ossm-rs)](https://github.com/orange-gem/ossm-rs) firmware, with
  step/dir control for adaptation to KinkyMakers OSSM firmware.
- **Dual rail options**: MGN15H (heavy, up to 15mm belts) and MGN12H (light, up
  to 12mm belts).
- **Optional brake-chopper PCB** for back-EMF spike suppression on heavy use.
- Optimized for 3D printing (~500g filament, minimal supports) with
  single-color, embossed, and multi-color branded variants.

## Important

- This is a **DIY hardware project** involving USB-C PD power and a motor —
  follow the upstream assembly and 3D-printing guides carefully and observe all
  safety precautions.
- Currently in **beta testing**; expect occasional issues and report feedback
  upstream.
- BOM, print manual, video assembly guides, and tested power sources are all in
  the [upstream repo](https://github.com/jollydodo/OSSM-ALT-Edition).

## Why it's indexed here

The R+D Project Hub indexes independently maintained projects so they are
discoverable alongside projects hosted in this repository, while leaving
ownership, maintenance, and licensing with their authors.
