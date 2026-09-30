# Build notes

Dimensions are millimetres. This prototype has no established load or torque rating.

## BOM

| Qty | Part | Specification |
|---:|---|---|
| 1 | Frame | 3.0 low-carbon steel sheet; eight bends |
| 1 each | Braces | 30 × 20 × 2 steel tube, lengths 230 and 80 |
| 1 | Arm | 30 × 30 × 2 steel tube, length 450 |
| 7 | Brace screws | DIN 7981 F ST4.8 × 9.5, case-hardened pan head |
| 1 | Pivot sleeve | Metal, Ø10 outside × Ø6.4 inside × 30 |
| 1 | Pivot bolt | M6 × 50 button head |
| 2 | Pivot washers | Ø6.4 × Ø12 × 1.6 |
| 1 | Pivot locknut | M6 nyloc; 10 across flats × 6 high |
| 2 each | Mini mounting hardware | PEM S-M6-1ZI nuts; M6 × 20 socket-head screws |
| 1 set | PitClamp Mini | Matching 70 mm lower base; obtain upper clamp separately |
| 2 | Arm plugs | norelem 29056-430200, for 1–2.5 tube walls |
| 4 | Foot caps | One of each named corner STL |
| 4 | Foot screws | Nominal 4 × 10 rounded-head self-tapping screws |
| 4 | Rubber pads | 20 × 24 × 3; 0.2 adhesive allowance |
| TBD | Angle lock | Complete the clamp; CAD includes only a Ø6 guide pin |

## Fabrication

Confirm provisional **R3 bends, ANSI K-factor 0.4**, bend order and tool access
before cutting the flat reference. Tube corner radii are provisionally R4/R2.
Brace holes use Ø5.2 sheet clearance and Ø4.1 tube pilots; test with actual screws.

Pivot height is 37 above the base datum. Form the 30 mm ear gap to the finished
arm width for direct contact. The pivot is 20 from the arm tail: drill both walls
coaxially Ø10.1 and fit the sleeve flush with square, deburred ends. It limits
crushing but does not prevent over-tightening.

Mini holes are **20 and 90 from the free end**, Ø8.75 +0.08/−0 through **one wall
only**, without countersinking; see [hole stations](arm-mount-holes.csv).
Check the physical base against the pinned 70 mm reference. PEM installation
requires ≥1.4 wall, ≤HRB80/HB150 hardness and internal press support at both
stations. Install nuts and sleeve before plugs. Plug CAD represents clearance
envelopes, not printable parts.

Foot engagement is 28 with 0.4 slide clearance; blind pilots are Ø3.2 × 9 with
a 2 mm floor. **Caps carry load** through their shelves to the bonded rubber.
Qualify print orientation, polymer creep, screw retention and adhesive adhesion.
Complete-machine folding, loaded stiffness and tipping remain untested.

## Sources

**armpit / OSSM-hardware:** [Mini Lower V1.1][base] is an unchanged reference;
[M6 screw heads][heads] retain their geometry with simplified shanks and omitted
threads/neck fillets. Both are pinned to `b7f01bf6df1be6f3ebf17dc0e31ed64ddf4c15b7`
under [CERN-OHL-S-2.0][license].

[PEM installation][pem] and [norelem plug dimensions][plugs] supply catalog data;
no supplier CAD is redistributed.

[base]: https://github.com/KinkyMakers/OSSM-hardware/blob/b7f01bf6df1be6f3ebf17dc0e31ed64ddf4c15b7/Printed%20Parts/Mounting/STEP/OSSM%20-%20Base%20-%20PitClamp%20Mini%20-%20Lower%20V1.1.stp
[heads]: https://github.com/KinkyMakers/OSSM-hardware/blob/b7f01bf6df1be6f3ebf17dc0e31ed64ddf4c15b7/CAD%20Project/MAIN/RELEASE_02.27.2025/OSSM/Base/PitClamp%20Mini/Hardware/(M6%20x%2015%20Cap%20Head%20Screw,M6%20x%2020%20Cap%20Head%20Screw%20for%204040%20Extrusion).stp
[license]: https://github.com/KinkyMakers/OSSM-hardware/blob/b7f01bf6df1be6f3ebf17dc0e31ed64ddf4c15b7/LICENCE
[pem]: https://www.pemnet.com/wp-content/uploads/sites/2/2022/06/cldata.pdf
[plugs]: https://www.norelem.co.uk/en/Product-overview/Systems-and-components-for-machine-and-plant-construction/29000/Round-tubes-square-tubes/Tube-end-plugs-plastic-for-round-and-square-tubes-Form-B-square/p/agid.27799
