# Change parameters and generate a new enclosure

## First use

1. Install FreeCAD and Qhull's `qconvex` executable. This project was tested with FreeCAD 1.1.3 on Linux. Ensure `qconvex` is on the `PATH` visible to FreeCAD; a sandboxed installation may need extra access. Merely opening the saved models needs no Qhull.
2. Download and extract the **whole repository**, or clone it. Keep `build_mount.py` and `Rebuild.FCMacro` together in the root directory.
3. Open `output/corner/apollo-mount.FCStd` or another supplied CAD file in FreeCAD. Use **File → Open**, not Import of an STL.
4. Use **File → Save As** to save a working copy if you want to preserve that preset. The macro still exports to `output/custom`; saving under a different name does not change its output destination.
5. Select the tree item labelled **Parameters – edit, then run Rebuild.FCMacro** (internal name `Parameters`). In the Property view, choose the **Data** tab. If hidden, enable **View → Panels → Property view** or **Combo view**, depending on your FreeCAD layout.

## Make your changes

Double-click the value beside a property. Groups include Mount, Clearances, Retention, Printing and Cable. Enter lengths in **millimetres** and angles in **degrees**, as plain numbers: these are float properties rather than unit-aware expressions.

For example, a corner model aimed mainly along one wall:

| Property | Example value |
|---|---:|
| Corner | Yes |
| CornerAngle | 90 |
| CornerSetback | 10 |
| Yaw | -39 |
| Pitch | 4 |
| RearChamberDepth | 30 |
| CableEnabled | No |

Press Enter or click another property to finish the edit. Boolean values use Yes/No, and `FastenerSize` offers an M2/M3 dropdown. Read-only calculated values cannot drive geometry: for example, change `RearChamberDepth`, not `BoardDistance`.

Yaw 0 faces perpendicular to a flat wall, or along the bisector of an inside corner. Positive yaw points along the model's +X direction; positive pitch points downward. When looking at the back of the model, visual left/right is reversed. Use the PCB/front-cover direction in the 3D view to confirm the sign for your installation. Pitch is not the corner angle.

## Rebuild: the essential step

1. Activate the tab containing your working Apollo model. With several documents open, the active tab is the one the macro reads.
2. Open **Macro → Macros…**.
3. Set the macro location/user macros path to the repository root if needed, so `Rebuild.FCMacro` appears. Select it and click **Execute**. Alternatively open the macro file through FreeCAD's macro editor and execute it there.
4. Wait for the geometry operations and exports to finish. Complex angles/cable routes can take tens of seconds or longer; avoid starting a second rebuild.
5. Look for the **“Apollo rebuilt…”** success message in the status bar/Report view. The visible body and lid should update. Use **View → Standard views → Fit all** if the new position is off-screen.
6. Inspect the PCB grip, module space, mounting-wall clearance and cable route before slicing.

**Changing a parameter, saving the file, or pressing Recompute/F5 is not enough. Run the macro.** The geometry comes from the Python generator; FreeCAD does not automatically call it when a float property changes.

The macro saves and writes the following into `output/custom/`, overwriting matching files:

| File | Purpose |
|---|---|
| `apollo-mount.FCStd` | Editable inputs, native solids and reference objects |
| `body.stl`, `lid.stl` | Individual parts oriented for slicing |
| `fit-ring.stl` | Small optional PCB/hardware fit coupon |
| `body.step`, `lid.step`, `fit-ring.step` | Oriented CAD solids for exchange |
| `assembly.step` | Body and cover in assembled positions; no reference PCB/cable |

It does **not** update an Orca project, reslice, send a print, rerun stress tests, or refresh old PNG previews. Import the new STLs or use your slicer's replace/reload feature and inspect orientation/supports again. Do not manually export all visible objects: that would risk including PCB/cable references.

## Keep multiple locations

After a successful rebuild:

1. Copy the whole `output/custom` folder to a new folder such as `output/living-room` using your file manager.
2. Open that folder's `.FCStd` when you next want to edit its parameters.
3. Rebuild still writes into `output/custom`; copy the new exports back to the named folder after checking them.

The snapshot includes both compatible body and lid. If you change fasteners, fit, dimensions or angle, use the newly exported matching parts; do not assume a lid from another preset still fits. Keep the complete parameter set with the CAD file, rather than recording only yaw and pitch.

## Reference visibility

Select a tree object and press **Space**:

- `SourcePCB`: original component/PCB mesh, missing the optional daughterboards.
- `Cover`: generated front cover; normally transparent after rebuilding.
- `ModuleClearance`: orange envelope reserved for components.
- `CablePreview`: actual cable diameter, shown only when cable processing is enabled.
- `PlugClearance`: provisional plug/boot envelope.
- `CableCentreline`: routing curve.

Hiding a cable preview does **not** disable cable processing. Set `CableEnabled = No` and rebuild to remove routing constraints, cutouts and reinforcement. No cable tube is printed.

## If rebuilding fails

- **Nothing changed:** finish the property edit, select the correct active document, then execute the macro rather than just recomputing. Check **View → Panels → Report view**.
- **No Parameters object:** open a supplied `.FCStd`, not an imported STL/STEP or the PCB-only reference.
- **qconvex not found:** install Qhull and ensure FreeCAD can find that executable. Restart FreeCAD after changing its environment.
- **FreeCAD module cannot be imported in a terminal:** use FreeCAD's GUI macro, or configure the matching Python/module paths for your installation. Ordinary `pip install` is not the solution.
- **Source OBJ missing on a new build:** decompress `r-pro-1-pcb.obj.gz` to `r-pro-1-pcb.obj` in the repository root. On Linux use `gzip -dk r-pro-1-pcb.obj.gz`; an archive utility also works. The `.mtl` file referenced in the OBJ is absent; the scripts use geometry and assign their own display colours.
- **Invalid clearance, bend radius or solid:** follow the specific error message. Change the conflicting parameters or disable the cable if it will not be used. Do not remove validation checks to force an export.
- **Old geometry still visible after an error:** it represents the previous successful build, not the newly entered values. Existing or partly written exports must not be treated as a successful new build. Correct the problem and rerun until success.

The supported numeric ranges are described in the [parameter reference](PARAMETERS.md). A value being within range does not guarantee every combination will produce printable geometry.
