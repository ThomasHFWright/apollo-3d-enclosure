# Complete parameter reference

The tables cover every editable entry in `build_mount.py:PARAMETERS`. Defaults below are **generator defaults**; the value in your saved FreeCAD document is what the GUI rebuild uses. All numbers are millimetres unless marked as angles; boolean values appear as Yes/No. Edit the Data tab and **run Rebuild.FCMacro** afterwards.

## Coordinates and interactions

PCB X is left/right, Y is bottom/top, and Z points through the front cover. The PCB is 44.474688 × 56.974716 mm, 1.586157 mm thick; the rear PCB face is Z=0 and front face Z=PCB_T. PCB coordinates rotate with the device. The mounting frame remains fixed, with +Z toward the room; in corner mode its reference plane bridges the wall pads. RearChamberDepth is measured to the electronics bay, not directly to the PCB.

Positive pitch tilts down. Positive yaw rotates front-facing +Z toward +X. A corner mount at zero yaw faces its corner bisector. Viewing from behind reverses apparent left/right. Rotating the PCB can increase stand-off to avoid walls; it also shifts the PCB sideways. Parameters interact, so listed ranges alone do not guarantee a valid combination.

When CableEnabled is No, other Cable-group inputs are ignored. Module, structural and wall checks continue. All active numeric inputs must be finite.

## Mount

| Parameter | Default | Meaning and how to use it |
|---|---:|---|
| `Corner` | No | Yes selects two angled wall-contact pads; No selects a flat-wall frame. Rebuild and inspect screw access after changing. |
| `CornerAngle` | 90 | 60–150°. Measure the included wall angle, not the PCB aim. 90° is a square inside corner. Validated even in flat mode. |
| `CornerSetback` | 10 | Nonnegative. For corner mode, removes the rear tip along the bisector to clear rounded plaster. A geometry-dependent maximum protects screw material (about 17.59 mm at the default 90°/70 mm frame). 0 restores the sharp tip; ignored on flat mounts. |
| `CornerSpine` | No | No retains 4 mm thick closures at the top/bottom only. Yes fills the same flat-backed strip over the height. Relevant only to corner mounts with nonzero setback. |
| `Yaw` | 0 | −90 to +90°. Rotation about model Y. 0 is straight ahead for flat mounts and along the corner bisector for corner mounts. The PCB shifts sideways by half its width × sin(yaw); verify direction visually. |
| `Pitch` | 0 | −40 to +40°. Positive tilts down, negative tilts up. Combined with yaw; the geometry may move forward to avoid the wall. |
| `RearChamberDepth` | 30 | Must be positive. Sets the rear chamber length, excluding the electronics bay. Short values can omit short vents. Rotated components may still need extra stand-off; inspect AdditionalWallClearance. It is not the full wall-to-PCB distance. |

## Clearances

| Parameter | Default | Meaning and how to use it |
|---|---:|---|
| `FrontHeight` | 13.9 | Positive. Measure from the main PCB front face to the tallest module or pin; the default 13.9 includes the short radar module pins. Increasing it deepens the cover. |
| `RearHeight` | 16.9 | Positive. Main PCB rear face to the back of the PoE socket. Also locates the plug start plane; changing this alters cable and bay geometry. |
| `SideOverhang` | 1.4 | Nonnegative. Additional component width outside each PCB side. The measured black part extends 1.4 mm; this reserve is applied symmetrically. |
| `TopOverhang` | 0.5 | Nonnegative. Additional component height above the PCB top edge. The measured installation has at most about 0.5 mm. |
| `SideClearance` | 1 | Positive. Gap beyond the board/component outline; changes the enclosure width/height. This is separate from the close-fitting PCB RegistrationGap. |
| `FrontClearance` | 1.5 | Positive. Additional room above the tallest front component/pin, before the cover skin. |
| `RearClearance` | 3 | Positive. Extra bay depth behind the rear component envelope. It changes the PCB distance while preserving the requested rear-chamber input. |

## Retention

| Parameter | Default | Meaning and how to use it |
|---|---:|---|
| `BoardSlotGap` | 0.3 | Positive. Vertical free play above the PCB before the lid keeper contacts it. Too little can clamp the board; too much allows movement. Check the printed fit ring and lid. |
| `RegistrationGap` | 0.3 | Positive and strictly less than EdgeBite. In-plane clearance at locating stops. Too large lets the PCB slide off its ledges. |
| `EdgeBite` | 0.8 | Greater than 0, at most 1.2 mm. Rail overlap onto the PCB edge. More overlap is not always better: nearby components must remain clear. |
| `EdgeReliefMargin` | 0.8 | Positive. Extra gap around mapped edge components when generating the segmented rails. Increasing it shortens supporting rail segments. |
| `BlackReliefStartY` | 0 | PCB-centred Y coordinate. Together with EndY defines an extra rear-left rail interruption. Must satisfy −H/2 ≤ start < end ≤ H/2. This location is a conservative keep-out, not detailed optional-module CAD. |
| `BlackReliefEndY` | 21 | Upper end of the extra black-part interruption. EdgeReliefMargin expands the blocked interval. Physical PCB height H is 56.974716 mm. |
| `CO2ReliefSize` | 13 | Nominal square side, at least 12.901624 mm to reach the PCB edge. Centred on the connector at X=15.786532, Y=−6.861016. The cut extends outward to the inner enclosure wall across the holder depth. |
| `CO2ReliefClearance` | 0.8 | Nonnegative, added on EACH side. Default square width is 13 + 2×0.8 = 14.6 mm before its outward extension. The cut must retain the outer wall and avoid PCB corners; excessive size/clearance is rejected. |
| `LowerContactY` | -20.062 | Y coordinate of the lower lid screw pair, in PCB coordinates. Must remain strictly inside −H/2+5 .. H/2−5 mm. Keep the lower and upper pairs well separated; inspect actual boss/rail fit if moving them. |
| `UpperContactY` | 21.938 | Y coordinate of the upper screw pair, with the same corner exclusion as LowerContactY. This relocates both left/right fastener housings at that height. |
| `FastenerSize` | M3 | Dropdown: M2 or M3 only. Changes bolt holes and ordinary hex-nut pockets together. M4/M5 do not fit the existing housings. Screw-head dimensions are independent; enter dimensions of your actual head. |
| `NutClearance` | 0.4 | Nonnegative TOTAL extra width across flats, not per side. Default M3 pocket is 5.9 mm across flats. Nut depth is nominal thickness + 0.5 mm. Excessive width is rejected to stop rotation and retain the access-throat/boss wall. |
| `ScrewClearance` | 0.4 | At least 0.1 mm TOTAL extra bolt-hole diameter. Default M3 hole is 3.4 mm. Excessive diameter is rejected to retain nut bearing material. |
| `ScrewHeadDiameter` | 5.3 | Measured head diameter, before clearance. When recesses are enabled it must exceed the bolt-hole diameter by at least 1.6 mm, and diameter + clearance must be at most 6.6 mm. |
| `ScrewHeadDepth` | 2.8 | Nonnegative. Head height before depth allowance; 0 disables recesses. A raised rim surrounds the head, preserving the existing 3.2 mm seat instead of thinning it. |
| `ScrewHeadClearance` | 0.4 | Nonnegative TOTAL diameter allowance; half is added to depth. Defaults produce a 5.7 mm diameter × 3.0 mm deep recess. It does not set nut fit. |
| `NutAccessDiameter` | 18 | Positive. Nominal finger pocket width, provisionally 18 mm. The opening is flattened near top/bottom panels. Larger values can collide with the enclosure; insert nuts before the PCB. |
| `NutAccessDepth` | 12 | Positive. Inward-sloping approach depth behind the nut seats. Exterior hood feet may continue farther to finish flush inside the chamber. Check access with real fingers/tweezers. |

## Printing

| Parameter | Default | Meaning and how to use it |
|---|---:|---|
| `WallThickness` | 2.8 | At least 2.4 mm. Governs perimeter, chamber, hoods and several clearances; changing it can change the outside appearance. It is not a slicer wall-count setting. |
| `FrontSkin` | 1.2 | At least 0.8 mm. Cover front-wall thickness, default 1.2 mm. The supplied official front measured 1.25–1.75 mm. Increasing it above 1.25 fails the comparison test; no thickness guarantees RF performance. |
| `CornerRadius` | 2.5 | 0 .. WallThickness. Circular outer rounds, not a flat chamfer. 0 gives sharp outer corners. Inner/base junctions remain plain; locally invalid rounds may be omitted. |
| `VentSlot` | 6 | Positive. Width of ventilation openings. Larger slots reduce material and change appearance; preserve strong edges/ribs and inspect support needs. |
| `VentRib` | 3 | At least 2.4 mm. Material between ventilation slots; changes the slot spacing and appearance. Slots are also kept away from fasteners and panel edges. |
| `SideVentOffset` | 4 | 0–10 mm. Shifts side-wall slot layout upward to leave more solid material near the lower edge. It is not a global vent margin. |

## Cable

| Parameter | Default | Meaning and how to use it |
|---|---:|---|
| `CableEnabled` | Yes | No skips ALL cable checks, previews, cutouts and cable reinforcement; saved cable values are retained for re-enabling. PCB/module/wall checks remain active. Hiding CablePreview alone does not disable processing. |
| `PortX` | -0.025 | Socket-centre X in PCB coordinates. Source default −0.025 mm. Change only after checking the real connector position. |
| `PortY` | -8.907 | Socket-centre Y in PCB coordinates. Source default −8.907 mm. This is not the cable entry position on the wall. |
| `PlugWidth` | 17 | Positive. Provisional rigid plug/boot cross-section width. Measure your plug, including moulded boot; the passage must contain it. |
| `PlugHeight` | 18 | Positive. Provisional rigid plug/boot/latch height. Rounded passage corners must also clear the rectangular envelope. |
| `PlugLength` | 15 | Positive. Socket opening to flexible-cable start. Default starts the bend 15 mm behind the socket. Include the boot and protruding rigid plug length. |
| `CableDiameter` | 6 | Positive. Physical wire outside diameter, used for the visible cable and actual-material-intersection test that triggers a cut. |
| `CableClearance` | 0.8 | Positive radial allowance. The rounded hole must contain the wire diameter plus clearance. This does not enlarge the displayed physical wire. |
| `CableHoleWidth` | 20 | Positive clear width of the connector passage; independent of CableDiameter. Both width and height must clear the cable and provisional plug. |
| `CableHoleHeight` | 22 | Positive clear height of the connector passage. An opening only cuts body material where the physical wire actually intersects remaining geometry, not where the larger passage is merely nearby. |
| `CableHoleRadius` | 3 | Nonnegative and smaller than half the smaller hole dimension. Large corner radii can clip the plug rectangle; the generator checks this. |
| `CableEntryX` | 0 | Cable entry X in the fixed mounting frame. 0 is centred horizontally. Unlike PortX, this is not rotated with the PCB. |
| `CableEntryY` | -68 | Entry Y in the fixed mounting frame. Negative is toward the model bottom. Default −68 lies below the frame. |
| `CableEntryDepth` | 8 | Preferred Z offset ahead of the mounting-frame front plane. Negative values can place the route behind the model, assuming a real wall opening there. AutoCableRoute may reduce this value. |
| `AutoCableRoute` | Yes | Yes searches rearward in 5 mm steps up to 200 mm, then tries 1.5× and 2× handle lengths. Preserves entry X/Y/direction and does not increase RearChamberDepth. No uses the exact requested route inputs. |
| `CableAzimuth` | -90 | Degrees in the mounting frame: 0 right, +90 up, −90 down. Sets outgoing direction from socket toward entry. Use with elevation to approach from different directions. |
| `CableElevation` | 0 | Degrees out of the mounting plane: 0 parallel to the wall/reference plane, positive toward the room. At ±90 the azimuth has no directional effect. |
| `CableTangentLength` | 34 | Positive Bezier handle length controlling the sweep. Longer is not always better; inspect the full route. AutoCableRoute may multiply it; see ActualCableTangentLength. |
| `MinBendRadius` | 20 | Positive minimum cable-centreline bend radius; use your cable specification. The larger hole/rim also imposes a radius bound, so reducing this alone may not make a tight route valid. Curvature checking is sampled. |
| `CableRimWidth` | 3 | Positive material margin around actual cable intersections, including across nearby vent slots. This reinforces the opening; it never creates a standalone printed cable tube. |

## Calculated, read-only properties

These update on a successful rebuild/export; change the driving inputs instead. Cable results are zero placeholders when the cable is disabled.

| Property | Meaning / driving inputs |
|---|---|
| `BoardDistance` | Actual PCB-centre Z offset ahead of the rear mounting-frame front plane, including bay depth and added wall clearance. Driven by RearChamberDepth, module dimensions and orientation. |
| `PCBOffsetX` | Automatic sideways shift = 44.474688 / 2 × sin(Yaw); about ±22.24 mm at ±90°. |
| `AdditionalWallClearance` | Extra forward stand-off needed to keep rotated geometry clear of the wall(s). Already included in BoardDistance. |
| `WallPlateWidth` | Nominal plate width, default 70 mm; depends on enclosure width, not automatically enlarged for yaw/pitch. |
| `WallPlateHeight` | Plate height including mounting ears, default 108 mm. |
| `NutPocketAcrossFlats` | Nominal nut width + NutClearance: M3 default 5.9 mm; M2 default 4.4 mm. |
| `NutPocketDepth` | Nominal nut thickness + fixed 0.5 mm allowance: M3 2.9 mm, M2 2.1 mm. |
| `ScrewHoleDiameter` | Nominal thread diameter + ScrewClearance: M3 default 3.4 mm, M2 default 2.4 mm. |
| `ScrewHeadRecessDiameter` | ScrewHeadDiameter + ScrewHeadClearance; 0 with head recess disabled. |
| `ScrewHeadRecessDepth` | ScrewHeadDepth + half ScrewHeadClearance; 0 with head recess disabled. |
| `ActualCableEntryDepth` | Entry depth actually used after automatic routing. Negative can require an opening behind the mount. |
| `ActualCableTangentLength` | Bezier handle length actually used after automatic routing. |

## Legacy names and fixed dimensions

- Old `BoardDistance` inputs are migrated to RearChamberDepth when reading legacy documents. Do not edit the new calculated field.
- Old `CornerChamfer` maps to CornerRadius. The current geometry uses circular rounds.
- Old `CableGuide` and `ContactLength` properties are removed during rebuilding; no printed cable tube remains.
- PCB dimensions, source alignment, mapped component bands, mounting-plate thickness (4 mm), wall-screw bore (4.6 mm), boss outside diameter (9 mm), holder depth (6.6 mm), cover screw-seat thickness (3.2 mm) and nut depth allowance (0.5 mm) are code constants, not exposed settings. An AI/source edit is needed to change those, followed by geometry/fit validation.

## Common changes

- Aim along a corridor: edit Yaw and Pitch; confirm direction in 3D. A target 6.2 m away, 0.62 m from the side wall and 0.45 m below the sensor gives approximately −39° yaw / +4° pitch for the illustrated 90° corner arrangement. Mirrored installations can require the opposite yaw sign.
- Shorten the chamber: reduce RearChamberDepth; inspect AdditionalWallClearance. Do not reduce measured module heights to force a smaller enclosure.
- Clear rounded plaster: increase CornerSetback within its allowed range. Use CornerSpine only if a full central strip is wanted.
- Remove the cable completely: CableEnabled = No, then rebuild. To keep the route but hide it, use Space on CablePreview instead.
- Loosen nut fit: increase NutClearance slightly and print another fit ring. This is total across-flats allowance, unlike CO2ReliefClearance which is per side.
- Change head recesses: use measured ScrewHeadDiameter/Depth. Changing M2/M3 does not automatically measure or select a matching head.
