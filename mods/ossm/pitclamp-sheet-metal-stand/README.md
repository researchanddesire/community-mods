# PitClamp sheet-metal stand

![PitClamp Mini stand CAD prototype](img/stand-preview.png)

A freestanding OSSM stand prototype built around a **single bent sheet-metal
frame**, two rectangular-tube braces, a square-tube arm and four small
wraparound feet. The arm carries a rigid **PitClamp Mini** mount using two M6
self-clinching nuts at 70 mm pitch. Project by [Lucy Chapar](https://github.com/lucy-chapar).

This contribution contains only the Mini mounting variant. It is a geometry
prototype for further development, **not a fabrication-qualified or
load-tested stand**. The actuator and upper clamp are not included. The
slotted hinge's locking hardware still needs to be completed.

## Design

- One 3 mm low-carbon steel frame with eight bends and a continuous top surface.
- A 450 mm arm made from 30 × 30 × 2 mm hollow square tube.
- Two 30 × 20 × 2 mm tube braces, 230 mm and 80 mm long, secured by seven
  self-tapping screws.
- A flush metal pivot sleeve and locknut, with the hinge ears bearing directly
  against the arm. This is a friction pivot.
- A nominal 180° guide slot. Complete-machine fold-flat clearance is not
  established by the bare-arm travel.
- Wraparound foot caps with recessed rubber pads, plus purchased tube end caps.

The frame retains its **native FreeCAD Sheet Metal base, eight editable bends
and unfold**. The arm, braces, pivot sleeve, drilling sketches and driving
expressions remain editable. Foot caps and hardware are reference solids;
changing their dimension properties does not automatically rebuild every detail.

## Files

| Path | Contents |
|---|---|
| [cad/ossm-pitclamp-stand.FCStd](cad/ossm-pitclamp-stand.FCStd) | Editable stand; no unrelated actuator assembly or alternate mount. |
| [cad/ossm-pitclamp-stand.step](cad/ossm-pitclamp-stand.step) | Open-format assembly reference with named components. |
| [cad/frame-formed.step](cad/frame-formed.step) | Current formed sheet-metal frame. |
| [cad/frame-flat-reference.step](cad/frame-flat-reference.step) | Current unfolded blank, for review; bend allowance is provisional. |
| `cad/arm-30x30x2.step`, `cad/brace-*.step`, `cad/pivot-sleeve.step` | Individual metal components. |
| `cad/foot-*.step`, `print/foot-*.stl` | Four foot positions, one of each; handed pairs are retained explicitly. |
| [docs/build-notes.md](docs/build-notes.md) | BOM, assembly considerations, fit assumptions and attribution. |
| [docs/arm-mount-holes.csv](docs/arm-mount-holes.csv) | Mini installation-hole stations and tolerance. |
| [docs/validation.md](docs/validation.md) | Checks performed on this publication copy and their limits. |

Install **Sheet Metal 0.8.23** to edit the native model. The publication copy
was checked with **FreeCAD 1.1.4 on Linux**. Select this document as active
before recomputing its unfold. macOS FreeCAD accessibility crashes occurred
during development; successful geometry checks do not establish stability on
every operating system.

## PitClamp interface

Compatibility is tied to the [specific official Lower V1.1 STEP](https://github.com/KinkyMakers/OSSM-hardware/blob/b7f01bf6df1be6f3ebf17dc0e31ed64ddf4c15b7/Printed%20Parts/Mounting/STEP/OSSM%20-%20Base%20-%20PitClamp%20Mini%20-%20Lower%20V1.1.stp),
whose measured mounting axes are **70 mm apart**. The upstream Mini README
mentions 64 mm, so check your physical base or chosen revision before drilling.
This project does not claim compatibility with every Mini version.

## Status and next work

Complete the angle-locking hardware and review the blank, bend order, press
tool access, stock radii and coating allowances with a fabricator. Build and
test the stand's stiffness, stability, joint retention and full-machine motion
clearance before powered use. No load, fatigue-life or torque rating has been
established. Print settings and foot materials also remain to be qualified.

## Credits and license

The PitClamp Mini reference was developed by **armpit** and is included from
the CERN-OHL-S-2.0-licensed OSSM-hardware project. The two simplified mounting
screws reuse its screw-head geometry. Source revisions and modifications are
listed in the [build notes](docs/build-notes.md#source-attribution).

This hosted OSSM project's files use **CERN-OHL-S-2.0**, as specified in the
[repository license](../../../LICENSE). Names and trademarks remain with
their respective owners.
