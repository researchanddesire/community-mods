# Build notes and provisional BOM

All dimensions are millimetres. These describe the CAD prototype, not a
released manufacturing specification. Inspect actual stock and hardware before
making parts.

## BOM

| Quantity | Component | Nominal specification |
|---:|---|---|
| 1 | Formed frame | 3.0 mm low-carbon steel sheet; eight bends; R3 inside bend radius |
| 1 | Near brace | 30 × 20 × 2 rectangular steel tube, 230 long |
| 1 | Far brace | 30 × 20 × 2 rectangular steel tube, 80 long |
| 1 | Arm | 30 × 30 × 2 square steel tube, 450 long |
| 7 | Brace screws | DIN 7981 F ST4.8 × 9.5, case-hardened steel pan head |
| 1 | Pivot sleeve | Metal, Ø10 outside × Ø6.4 inside × 30 long |
| 1 | Pivot bolt | M6 × 50 button head, simplified ISO 7380-type envelope |
| 2 | Pivot washers | M6; Ø6.4 inside × Ø12 outside × 1.6 thick |
| 1 | Pivot locknut | M6 nylon-insert nut; modeled 10 across flats × 6 high |
| 2 | Mini mount nuts | PEM S-M6-1ZI, pressed into the mounting wall |
| 2 | Mini mount screws | M6 × 20 socket head |
| 1 set | PitClamp Mini | Matching 70 mm lower-base revision; upper clamp and its hardware obtained separately |
| 2 | Arm end plugs | norelem 29056-430200, specified for 30 mm tube with 1–2.5 mm walls |
| 4 | Foot caps | One STL for each named corner; two mirrored hands |
| 4 | Foot-cap screws | Nominal 4 × 10 rounded-head self-tapping screw; plastic pilot and retention to qualify |
| 4 | Rubber pads | 20 × 24 × 3, with nominal 0.2 adhesive allowance |
| TBD | Slotted angle lock | Only a Ø6 guide-pin envelope is modeled; select and validate a complete clamp mechanism |

No material grade, heat treatment, coating, print material, tightening torque
or adhesive product has been qualified. Fasteners and purchased end plugs are
dimensional references, not production-detail CAD.

## Frame and tubes

The sheet thickness is explicitly **3.0 mm**, not a gauge number. The unfold
uses an ANSI K-factor of **0.4** and an inside bend radius of **3 mm**. Both
must be matched to the fabricator's material and tooling before cutting a
blank. The supplied flat STEP is a reference, not a ready-to-cut file.

The frame's nominal plan envelope is approximately 570.8 × 304.8; the feet
bring the overall envelope to approximately 574.8 × 309.6. The model uses a
37 mm pivot height above the base datum and a 30 mm clear ear spacing. Form
that spacing to the measured, finished arm width: the design intentionally
has direct contact, without an axial gap or internal washers.

Tube outside/inside corner radii are provisionally 4/2 mm. Confirm the actual
stock profile, sheet-to-tube contact, hole tolerances and bend accessibility.
Brace screw pilots are nominal Ø4.1 in the tube, with Ø5.2 sheet clearances;
confirm the pilot for the actual screw and steel. The native sketches and
individual STEP files carry the hole placements.

## Pivot and Mini mounting

The pivot center is 20 mm from the arm's tail. Drill both arm walls coaxially
to Ø10.1 for the Ø10 sleeve. Match the sleeve length to the finished arm width,
with square deburred ends. The sleeve limits tube crushing but does not make
excessive torque harmless. The locknut is the pivot's assembly setting; use a
separate slotted clamp to adjust and lock angle.

The two Mini installation holes are centered on the mounting face, **20 and
90 mm from the free end**. Cut only that 2 mm wall: Ø8.75 +0.08/−0, without
countersinking. The opposite wall remains intact. See
[arm-mount-holes.csv](arm-mount-holes.csv).

The PEM bodies sit inside the tube. The [manufacturer's S-M6-1ZI specification](https://catalog.pemnet.com/item/nuts-types-s-ss-cls-clss-cla-sp/self-clinching-nuts-types-s-ss-cls-clss-sp-metric/s-m6-1zi)
requires at least 1.4 mm sheet and no more than HRB80/HB150 substrate hardness.
Confirm those requirements for the sourced tube and establish internal press
support at both holes, including the station 90 mm from the end. Install the
nuts and pivot sleeve before fitting the end plugs.

The arm-end plugs are conservative **catalog clearance envelopes**, not exact
supplier geometry or printable parts: 30 × 30 × 5 heads and 11.5 insertion
reserves. Nominal tail-cap clearance above the bend roots is at least 1.845 mm
over the bare arm's travel. Actual cap ribs, molding residue, coating and stock
tolerances still need checking. Full actuator clearance is outside that check.

## Feet

Each named foot file represents one installed corner. The files are translated
to the origin without choosing or qualifying a printing orientation. The
wraparound lip covers the cut metal edge. Nominal engagement is 28 mm with
0.4 mm slide clearance, a Ø3.2 × 9 blind screw pilot and a 2 mm closed floor
beyond it. Trial-fit the printed material and screw before loading the stand.
Vertical load passes from the steel return through the plastic cap shelf to
the bonded rubber. Qualify the shelf's strength and creep resistance, screw
retention and adhesive compatibility; these caps carry load.

## Source attribution

- **PitClamp Mini:** developed by armpit; [official project README](https://github.com/KinkyMakers/OSSM-hardware/blob/b7f01bf6df1be6f3ebf17dc0e31ed64ddf4c15b7/Printed%20Parts/Mounting/PitClamp%20Mini/README.md).
  Lower V1.1 geometry comes from OSSM-hardware commit
  `b7f01bf6df1be6f3ebf17dc0e31ed64ddf4c15b7`,
  `Printed Parts/Mounting/STEP/OSSM - Base - PitClamp Mini - Lower V1.1.stp`.
  It is positioned as an unmodified reference solid in this stand.
- **M6 mounting screw heads:** same upstream revision,
  `CAD Project/MAIN/RELEASE_02.27.2025/OSSM/Base/PitClamp Mini/Hardware/(M6 x 15 Cap Head Screw,M6 x 20 Cap Head Screw for 4040 Extrusion).stp`.
  The heads were retained and nominal cylindrical shanks substituted; thread
  geometry and the original neck fillet are omitted.
- Both upstream assets are covered by the [pinned CERN-OHL-S-2.0 license](https://github.com/KinkyMakers/OSSM-hardware/blob/b7f01bf6df1be6f3ebf17dc0e31ed64ddf4c15b7/LICENCE).
- **Arm plug dimensions:** [norelem square tube end-plug catalog](https://www.norelem.co.uk/en/Product-overview/Systems-and-components-for-machine-and-plant-construction/29000/Round-tubes-square-tubes/Tube-end-plugs-plastic-for-round-and-square-tubes-Form-B-square/p/agid.27799).
  The included envelopes are constructed from published dimensions; no supplier
  CAD is redistributed.
- **PEM nut installation:** [manufacturer installation bulletin](https://www.pemnet.com/wp-content/uploads/sites/2/2022/06/cldata.pdf).
  Nut references omit threads, serrations and clinching material flow.

No actuator model, TA clamp, operating system image or historical design
variant is part of this project package.
