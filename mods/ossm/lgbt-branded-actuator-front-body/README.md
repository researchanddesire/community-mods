# LGBT Branded Actuator Front Body

![LGBT branded OSSM actuator front body with trans flag stripes and black-on-white branding](img/front-body-preview.png)

A one-piece OSSM actuator front body with a trans flag across the top and
engraved **OSSM.TECH** and **R+D** branding. The cover and middle body print
together, removing two M3 bolts, their side-loaded nuts, and one separate
printed part.

The supplied version uses blue, pink, white, pink, and blue stripes with black
OSSM.TECH lettering and a black R+D mark on a white background. It has **17
separate material regions** so you can change the stripes, lettering, logo
background, enclosed spaces, and plus sign independently.

Maintained by [Lucy Chapar](https://github.com/lucy-chapar).

## Design

- The five stripes follow the lettering at **35°**.
- OSSM.TECH is scaled to about **73%** of the original size and sits entirely
  inside the white stripe, with **1.5 mm** of margin on both sides and at least
  **1 mm** of clearance from the motor access holes.
- Engraving remains **0.1 mm** deep. Color regions occupy the top **0.8 mm**.
- R+D regions that cross the pink–blue boundary are split at that boundary,
  giving you control over both the positive and negative space on either side.
- The native FreeCAD model keeps the editable sketches, a final Refine feature,
  and a named group of output color parts.

## Downloads

| File | Use |
|---|---|
| [Multipart 3MF](print/lgbt-branded-actuator-front-body.3mf) | One assembled print with 17 selectable color parts. |
| [Editable FreeCAD model](cad/lgbt-branded-actuator-front-body.FCStd) | Native sketches, construction features, and color parts. |
| [STEP model](cad/lgbt-branded-actuator-front-body.step) | Open CAD export with separate material regions. |
| [Color guide](docs/color-guide.txt) | Part order and starting color assignments. |
| [CAD validation](docs/cad-validation.json) | Saved geometry, material-part, and slicer-import checks. |

Use GitHub's **Download raw file** button when downloading individual CAD or
print files. They are stored through Git LFS.

## Printing and colors

Import the 3MF as **one object with multiple parts** and keep the parts in their
supplied positions. They combine into one housing; the letters and logo regions
are not separate loose prints.

Assign four filament colors: light blue (`#5BCEFA`), pink (`#F5A9B8`), white,
and black. Bambu Studio preserves all 17 parts, but its generic 3MF importer
may replace their names with numbered labels and does not retain the supplied
color assignments. The [color guide](docs/color-guide.txt) lists the exact part
order so you can assign colors and try your own combinations.

The file contains geometry, not a tuned printer profile. Choose your own
printer, material, layer height, supports, and orientation. Print settings and
physical print results have not yet been validated.

## Fit and assembly

This model was rebuilt in FreeCAD from the OSSM Body – Middle and supplied
RD branded front-cover STEP geometry, using the
[original OSSM Onshape document](https://cad.onshape.com/documents/d520ea9a8cadb4ae8681f59b/w/00b211a6fa3b76c59ef28f4e/e/3a318ae7a1136fe5757124ac)
as a reference. Compatibility with other actuator variants has not been tested.

The combined housing also omits the two unused M5 hex nut pockets and their
axial holes, removes the unused upper center hole, and extends only the two
selected motor counterbores through the cover. The two screws connecting the
cover extension to the lower body remain.

Check the full assembly before using this housing: the motor, belt, lower body,
fasteners, and access openings must fit and clear through the complete travel.
Confirm that components can be installed with the cover and middle joined.

## Validation and status

**Prototype — CAD validated; print and assembly testing still needed.**

The saved FreeCAD and STEP geometry are valid. All 17 material-part meshes are
closed, and Bambu Studio imports them as one assembled object without mesh
repairs. The material regions reconstruct the revised housing as one solid.

These checks verify the files and geometry. They do not establish printed fit,
strength, or assembled operation. Contributions with print settings, photos,
and fit checks are welcome.

## License and branding

Hosted OSSM project files use **CERN-OHL-S-2.0** under the repository license.
Research and Desire, OSSM, and the R+D mark remain subject to the repository's
branding and trademark exclusions.
