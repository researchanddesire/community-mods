# Printing and assembly

This is an unprinted ABS prototype for a nominal 25.4 × 25.4 mm closed metal tube.
The provisional wall thickness is 2.4 mm. Measure the actual tube, corners,
coating and available tool space before adapting or drilling it. Physical fit,
assembly feel, tightening torque and load capacity have not been established.

[Assembly diagram](../img/separate-keys.png) · [Print orientation](../img/print-orientation.png)

## Files and printing

- [Full print set](../print/full-print-set.3mf): two identical main halves and
  two identical keystones, already oriented. The colors in the CAD distinguish
  instances; they do not require different filament materials.
- Individual [main-half STL](../print/main-half-print-two.stl) and
  [keystone STL](../print/keystone-print-two.stl): print two of each.
- Print main halves seam-face-down, curve up. Print keys with their enlarged
  end faces on the bed. Support the approximately 25.8 mm rail-opening roof;
  inspect the channels, nut ports and key notches after support removal.
- [P2S 0.4 mm ABS project](../print/p2s-abs-prototype.3mf): 0.20 mm layers,
  six walls, 35% gyroid, supports enabled. Its estimate is about 5 h 44 min / 105 g.
  Check the plate and actual filament before slicing for your printer.
- [Short fit-test set](../print/fit-test-print-set.3mf): two receivers and two keys.
  The receiver M5 holes are retention-pin trials without head/nut seats;
  do not tighten bolts against these coupons as a clamped joint.

## Hardware for the nominal model

All dimensions are millimetres.

| Qty | Item | Specification |
|---:|---|---|
| 2 | Main-half prints | Same source part, ABS |
| 2 | Keystone prints | Same source part, ABS |
| 2 | Primary cap screws | ISO 4762 M5 × 40; head Ø8.5 × 5, 4 mm hex drive |
| 4 | Locator cap screws | ISO 4762 M5 × 45 |
| 6 | Nuts | DIN 934 M5, 8 across flats × 4 high |
| 8 | Locator washers | M5 clearance, outside Ø10 × 1 thick |
| 4 | Custom metal compression limiters | Outside Ø8 / inside Ø5.5; barrel 36.1; integral flange Ø11 × 1 |

The [limiter STEP](../cad/One-Custom-Metal-Limiter.step) shows one custom part,
not a printable spacer. Its overall length is 37.1. The nominal outside-pad grip
is 35.8; the 36.1 barrel leaves 0.15 stand-off at each end so locator preload
passes through the metal limiter rather than crushing ABS or tube walls.
Fit its length to the measured grip. A thicker ISO 4032 nut does not fit the
selected 4 mm DIN 934 envelope without changing the model.

## Assembly order

1. Rotate one main half 180° around the rail axis and place both around the
   tube. Register them without sliding the main halves lengthwise.
2. Insert both keystones from the same axial end (+X in the CAD), notches facing
   the primary bolt shafts. Seat them by hand. Allow about 31 mm of local key
   insertion travel and access from the opposite end for a 3 mm pusher.
3. Load the two primary nuts through their axial ports, then fit the opposed
   M5 × 40 screws, one from above and one below. Their axes clear the rail;
   the shafts retain the keys. Keep key insertion ahead of all locator hardware.
4. Check the locator pattern against the actual frame: four holes at X=±32,
   Z=±6.5, a 64 × 13 rectangle. Remove the printed parts before drilling. Drill
   both tube walls coaxially Ø8.2 with a suitable fixture; deburr and remove swarf.
   The [marking reference](locator-marking-reference.svg) is not a drill guide;
   check both 100 mm scale bars before using its dimensions.
5. Refit the adapter. Insert the four metal limiters from outside through both
   pads and tube walls, then fit the M5 × 45 locators with two washers and a nut
   each. The flange stays outside the bore. Hand-fit aligned parts; do not pull
   a binding limiter into place with a bolt.
6. Fit the matching PitClamp last and check its complete latch/removal motion.

For removal, take off the PitClamp and locator hardware, withdraw the primary
shafts clear of the key notches, then push the keys toward +X. Both the locator
hardware and primary shafts obstruct key extraction when installed.

## Parametric editing

Download and extract the [editable source ZIP](../cad/bedframe-adapter-source.zip).
Open its FreeCAD file, then execute the adjacent `Open-Adapter.FCMacro` to load
its Python dependencies. Edit `SourceHalf` rail dimensions and fit allowances,
recompute, and export the updated source half and key separately. Print two of
each. Preserve the fixed round PitClamp interface. Resizing may change the
required bolt lengths and limiter stack; use the regenerated values.

## Credits

**Yous34** contributed the original two-piece bedframe mounting-ring idea in the
KinkyMakers community. **Lucy Chapar** developed this parametric adapter revision.
The PitClamp Mini interface is by **armpit / KinkyMakers**, from
[OSSM-hardware commit b7f01bf6df1be6f3ebf17dc0e31ed64ddf4c15b7](https://github.com/KinkyMakers/OSSM-hardware/tree/b7f01bf6df1be6f3ebf17dc0e31ed64ddf4c15b7).
Hosted project files use [CERN-OHL-S-2.0](../../../../LICENSES/CERN-OHL-S-2.0.txt).
