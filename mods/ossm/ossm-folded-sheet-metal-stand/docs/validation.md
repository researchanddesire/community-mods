# Publication checks

Checked on 30 September 2026 using FreeCAD 1.1.4 and Sheet Metal 0.8.23 on
Linux ARM64. These checks concern CAD integrity and exported geometry; they
are not manufacturing, strength or application-stability certification.

## Native model

- Removed 209 unrelated actuator/import objects from a separate publication
  copy, leaving **187 objects**. The source design file was not overwritten.
- Retained the native `SMBaseBend`, eight `SMBendWall` features and `SMUnfold`.
- Forced native recomputation after cleanup. Frame, flat, arm, two braces and
  pivot sleeve retained their face/solid counts, volume, area and bounds within
  numerical tolerances (1e−4 mm³, 1e−4 mm², 1e−5 mm respectively).
- The unfolded frame remains one solid with **16 profile wires** on its main
  face, including the outline and internal openings.
- Saved and reopened the cleaned document, compared the same component
  geometry, and checked for invalid/error feature states.
- Changed the arm angle to 0°, 45°, 90°, −90° and −20° and checked arm-solid
  validity. The last value is the presentation pose. This is not a new
  full-machine collision sweep.

## Exports

- Regenerated every supplied STEP from this current model, including the frame
  and its flat reference after the pivot-height change to 37 mm.
- Reopened all ten individual-part STEP files: each has one valid solid and
  matches the exported part's volume within 0.001 mm³.
- Reopened the assembly STEP: **41 components / 41 valid solids**. Construction
  tools, hidden actuator imports and historical variants are excluded.
- Generated the four foot meshes at 0.06 mm linear / 0.12 rad angular
  deflection; each mesh is closed and contains 3,512 facets.

## What remains unverified

No physical stand has been validated by these checks. Bend allowance and order,
press-brake access, stock/coating fits, nut pressing access, foot material and
creep, loaded stiffness, tipping, fatigue and fastener retention remain open.
The angle-locking mechanism is incomplete, and full actuator folding/motion
clearance is not established. The end-plug solids are catalog envelopes.

Development encountered macOS Qt accessibility crashes. Successful recompute,
save/reopen and export tests in Linux do not guarantee sustained interactive
stability on another machine or FreeCAD version.
