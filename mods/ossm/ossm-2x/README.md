# OSSM 2X

![A built OSSM 2X actuator](img/ossm-2x-built.png)

OSSM 2X is an OSSM actuator variant that uses a continuous belt path to produce
approximately twice the output force of a regular OSSM in exchange for about
half the top speed. It is a useful trade-off for larger toys.

The project is maintained by [Lucy Chapar](https://github.com/lucy-chapar). The
OSSM 2X concept was conceived by **armpit** while under contract for
**Research and Desire**.

![CAD render of the OSSM 2X assembly](img/ossm-2x-render.png)

## Performance trade-off

The continuous-belt arrangement is intended to provide an approximately 2:1
force increase and 2:1 speed reduction relative to a regular OSSM actuator.
Actual force and speed depend on the motor, controller settings, belt setup,
and mechanical losses. Reduced speed is not a force limit.

## Configuration and compatibility

- The built/default configuration uses a **57AIM30** motor.
- The mount is designed for **42AIM**, **57AIM**, **iHSV57**, and other
  **NEMA 23** motors.
- The motor mount can be adjusted to support **NEMA 24 / 60AIM40F** motors.
- The standard linear-guide configuration is one 400 mm MGN12 rail with two
  MGN12C blocks.
- A single MGN12H block is an optional alternative.

## Files

| Path | Contents |
|---|---|
| `cad/ossm-2x.FCStd` | Editable FreeCAD assembly. |
| `cad/ossm-2x-actuator-base.step` | Open STEP export of the current actuator base in the FreeCAD assembly. |
| `cad/ossm-2x-actuator-base-print-plate.step` | Earlier supplied base STEP used to prepare the 3MF print plate. |
| `cad/ossm-2x-actuator-cap.step` | Open STEP source for the actuator cap and branding insert. |
| `cad/ossm-2x-pulley-core.step` | Open STEP source for a pulley end-effector core. Print two. |
| `cad/ossm-2x-tidy-ring.step` | Open STEP source for a tidy ring. Print two. |
| `print/ossm-2x-complete-plate.3mf` | Complete nine-object Bambu Studio print plate. |

The supplied 3MF contains one actuator base, one actuator cap, two pulley
cores, two tidy rings, two 24 mm nuts, and one hex-flower wrench. The two nuts
and wrench are present only in the 3MF; separate STEP files were not supplied
for those accessories.

## Print settings

The supplied 3MF is a Bambu Studio project with these saved settings:

- Printer: Bambu Lab P1S
- Nozzle: 0.4 mm
- Material: PLA
- Layer height: 0.2 mm
- Wall loops: 6
- Top layers: 6
- Bottom layers: 6
- Infill: 5% crosshatch
- Supports: per-part settings for the actuator base and pulley cores
- Colors: separate assignments for the cap and its branding
- Plate layout: saved orientations and duplicate part counts

## Hardware / BOM

### Motor

| Part | Qty | Notes |
|---|---:|---|
| 57AIM30 motor | 1 | Default; see the compatible motor families above. |

### Actuator

| Part | Qty | Source / notes |
|---|---:|---|
| MGN12 rail, 400 mm, with MGN12C blocks | 1 rail + 2 blocks | [AliExpress](https://www.aliexpress.us/item/3256804609221227.html). A single MGN12H block is optional. |
| GT2 pulley, 8 mm bore, 20 tooth, for 12 mm belt | 1 | [AliExpress](https://www.aliexpress.us/item/2255800930086012.html) |
| GT2 timing belt, 12 mm wide | 1 m | Continuous belt path. |
| MR115-2RS bearing, 5 × 11 × 4 mm | 6 | [AliExpress](https://www.aliexpress.us/item/2251832638392545.html) |
| M5 × 25 mm socket-head cap bolt | 2 | — |
| M4 × 25 mm socket-head cap bolt | 5 | — |
| M4 nut | 5 | — |
| M3 × 12 mm socket-head cap bolt | 8 | For two MGN12C blocks; use 4 with one MGN12H block. |

### Pulley end effectors

Quantities below are for two pulley end effectors.

| Part | Qty | Source / notes |
|---|---:|---|
| MR115-2RS bearing, 5 × 11 × 4 mm | 6 | [AliExpress](https://www.aliexpress.us/item/2251832638392545.html) |
| M5 × 18 mm stainless-steel dowel pin | 2 | [AliExpress](https://www.aliexpress.us/item/2255800287548941.html) |

The complete build uses 12 MR115-2RS bearings across the actuator and the two
pulley end effectors.

## Build notes

- Use eight M3 × 12 mm bolts with two MGN12C blocks, or four bolts with the
  optional single MGN12H block.
- The FreeCAD assembly is saved with the single-MGN12H alternative visible and
  the dual-MGN12C rail assembly hidden; change component visibility to inspect
  the default dual-block configuration.
- Use the FreeCAD assembly and the built-unit photo as geometry references;
  detailed step-by-step assembly instructions have not yet been supplied.
- Before applying power, move the mechanism through its full travel by hand and
  check belt routing and tracking, tension, rail alignment, fastener retention,
  end clearances, and pinch-point clearance.

## Known issues and help wanted

Contributions, test results, and design improvements are welcome, especially
for these known issues:

- **Belt tensioning:** The design has no dedicated belt-tensioning
  mechanism, so tension must be set manually during assembly. A simple,
  repeatable adjustment mechanism would make setup and maintenance easier.
- **Nut capture:** The base in the supplied 3MF and
  `cad/ossm-2x-actuator-base-print-plate.step` uses side-loaded hex nuts. They
  can spin freely in their pockets when the surrounding print has too few wall
  loops. `cad/ossm-2x-actuator-base.step` contains a proposed revision with
  nuts pressed into backside hex pockets; print and build validation—and an
  updated complete 3MF plate—would be especially helpful.

## Safety

OSSM 2X intentionally changes the force an OSSM can apply. Start with
conservative motion and motor settings, test unloaded, keep clear of the belt
and pulley pinch points, and verify emergency-stop operation and safe travel
limits before use. Secure the actuator and inspect the belt, pulleys, fasteners,
rail, carriage, printed parts, and end effectors regularly. Stop using the build
if any component is cracked, loose, misaligned, or worn.

If using a motor other than the default 57AIM30, confirm its mechanical,
electrical, and controller compatibility before connecting it.

## License

The hardware, documentation, and images are licensed under CERN-OHL-S v2. The
R+D mark is excluded from this license and remains all rights reserved.
