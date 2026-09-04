# KinkyMakers OSSM

An open-source OSSM variant built around a servo-powered, belt-driven linear
rail. Its printable hardware, control electronics, and firmware provide
software-defined stroke, depth, and speed control.

![KinkyMakers OSSM](https://raw.githubusercontent.com/KinkyMakers/OSSM-hardware/c1c70c3acef5ff5d891eb2d86b2c2a9e13f6d36c/assets/readme/ossm-banner.webp)

> **Indexed project.** This project is maintained in the KinkyMakers
> repository. Its hardware files, printed parts, software, documentation, and
> build instructions live upstream:
>
> **Project source → https://github.com/KinkyMakers/OSSM-hardware**

## License

This project is licensed
[CERN-OHL-S-2.0](https://github.com/KinkyMakers/OSSM-hardware/blob/main/LICENSE),
the CERN Open Hardware Licence Version 2 – Strongly Reciprocal. The upstream
project remains the source of truth for its files and license.

## Highlights

- Servo-powered, belt-driven actuator using a 57AIM30 motor and MGN12H rail.
- Printable actuator, remote, mounting, stand, and electronics-enclosure parts.
- OSSM PCB or supported ESP32 development-board control options.
- Standard 20–24 V DC and high-power configurations up to 36 V DC.
- Open firmware and hardware-test resources maintained with the project.

## Important

- The upstream project states force output up to **32 lb (14 kg)** at 20 V DC
  and **50 lb (22 kg)** in its 36 V high-power configuration. Higher voltage
  increases force.
- Verify power wiring, the documented actuator rail orientation, mounting,
  e-stop operation, and safe motion limits before use.
- Follow the upstream build and safety documentation for assembly, testing, and
  operation.

## Why it's indexed here

The R+D Project Hub indexes independently maintained projects so they are
discoverable alongside projects hosted in this repository, while leaving
ownership, maintenance, and licensing with their authors.
