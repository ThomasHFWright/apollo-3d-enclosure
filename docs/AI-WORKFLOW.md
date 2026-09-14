# Changing this design with AI

## What the AI needs

Use an assistant that can read/edit the cloned repository and run local terminal commands. FreeCAD and Qhull must be installed on that computer. A FreeCAD MCP server is **not required**: the generator calls FreeCAD's Python API directly. An assistant without file/terminal access can propose a patch, but cannot claim to have built or tested it.

Start by asking it to read `README.md`, `AGENTS.md`, `docs/PARAMETERS.md`, `build_mount.py` and `Rebuild.FCMacro`. Give it the **exact saved CAD file** and the change you want. Saved values may differ from defaults; existing custom parameters must be read from that document.

### Example: another installation, no design change

> Open `output/corner/apollo-mount.FCStd` and read its complete saved parameter set. Create a new version with Yaw=-25, Pitch=8 and RearChamberDepth=20. Preserve all other settings, including clearances and screw sizes. Write the results to `output/study-corner`, preserving my existing models. Use the FreeCAD Python generator, validate the resulting body/lid and exported meshes, and report the actual wall clearance. Do not send a print.

### Example: change the physical design

> Read this repository's AI and parameter guides. On `output/custom/apollo-mount.FCStd`, enlarge the CO2 holder notch by 0.2 mm on each side, keeping the outer wall, PCB contact surfaces elsewhere, cover and screw seats intact. Prefer the existing CO2ReliefClearance parameter. Preserve every other saved value. Export a new named version, run the relevant clearance checks, and show the changed area before I print a fit sample.

### Example: add a new capability

> Add [specific feature] to the shared generator. Trace how it affects the body, cover, fit ring, references and exports. Keep existing parameter values compatible. Add an exposed setting only if users need to configure it. Update the parameter guide and add a small regression check that catches the original problem. Validate flat, corner and the affected extreme-angle examples. Regenerate only the agreed outputs after checking them.

Supply measured dimensions, the PCB face used as a datum, a photo with the relevant feature marked, desired units, and the physical purpose. Avoid requests such as “make it stronger” without identifying a load, a weak feature or a observed failure.

## Source map

| File/function | Responsibility |
|---|---|
| `build_mount.py:PARAMETERS` | Names, defaults, UI groups and tooltips |
| `defaults()` / `read_parameters()` | New-build defaults and saved-document values/legacy migration |
| `build()` | Solid construction, orientation, chamber, rails, screws, ventilation and cable geometry; validates the result |
| `parameters()` | Creates/updates FreeCAD editable and calculated properties |
| `export()` | Updates native objects; creates oriented STL/STEP and optional fit ring; saves the CAD document |
| `main()` | CLI arguments or active GUI-document workflow |
| `Rebuild.FCMacro` | Runs the generator and presents success/failure in FreeCAD |
| `prepare_reference.py` | Imports the upstream multi-object PCB mesh into a reference document |
| `test_mount.py` | Geometry, retention, routing and export checks |
| `test_lid_thickness.py` | Compares the actual cover skin with the supplied Apollo front case |
| `test_strength.py`, `compare_corner_strength.py` | Optional structural screening; not part of normal rebuilds |

OpenCascade solid operations in FreeCAD include boxes, cylinders, lofts, offset surfaces, fuses and cuts. Qhull computes the convex rear-chamber envelope. Actual PCB grip geometry remains rigid while the chamber connects it to the mounting frame.

Manual edits to generated Mount/Cover solids will be overwritten by the next rebuild. Implement persistent changes in the generator or its parameter inputs.

## Preserve a saved model from Python

Run this from the repository root using a Python compatible with FreeCAD. Choose a new destination; `export()` overwrites its named files.

```python
from pathlib import Path
import build_mount as m

source = m.ROOT / 'output/corner/apollo-mount.FCStd'
target = m.ROOT / 'output/study-corner'
assert not target.exists(), 'Choose a new output folder'
doc = m.App.openDocument(str(source))
p = m.read_parameters(doc)          # Preserve the saved settings, not defaults.
p.update(Yaw=-25., Pitch=8., RearChamberDepth=20.)
result = m.build(p)                 # Validate before replacing document geometry.
m.parameters(doc, p)
m.export(doc, p, result, target)
assert len(result['body'].Solids) == len(result['lid'].Solids) == 1
m.App.closeDocument(doc.Name)
```

The GUI macro already reloads `build_mount.py` on each execution. In a long-lived Python console, use `importlib.reload(build_mount)` after source edits to avoid testing stale code.

## Required verification

1. Record the source document and complete parameter set before editing.
2. Keep changes in the shared generator so CLI and GUI follow the same geometry rules.
3. Build the affected configuration into a separate folder. Never suppress a geometry error to force an export.
4. Run the relevant existing checks. For a CO₂ change, for example:

```python
import test_mount
# p and result come from the saved-document recipe above.
test_mount.check_co2_relief(p, result)
```

5. For wider generator changes, run `python test_mount.py`. Run `python test_lid_thickness.py` when the cover changes. For a small parameter adjustment, the generator/export checks and relevant fit checks are more useful than blindly running every historical simulation.
6. Inspect rendered views or the native FreeCAD model. Confirm clearances, connected material around cutouts, reinforcement and references. Verify both body and cover, plus the fit-ring slice.
7. Slice for the actual printer and orientation. Review the first unsupported layer under each large span, not just the final support silhouette.
8. Report what was changed, which tests passed, what was actually printed, and what remains provisional. A screenshot or low FEM stress alone is not evidence of a successful physical fit or long-term heat resistance.

Do not change another saved preset merely because it has different parameters. Do not replace a user's latest Orca arrangement with an older example or silently inherit old toolpaths. The geometry exports are separate from slicer projects.

## Structural screening

The FEM scripts use FreeCAD FEM, Gmsh and CalculiX. Binaries/solver environments and large result files are intentionally not distributed. `test_strength.py` currently expects `/usr/bin/gmsh`, FreeCAD FEM at `/usr/lib/freecad/Mod/Fem`, and CalculiX at `.tools/fem/bin/ccx`. On a compatible Linux installation with `ccx` already installed, the last path can be supplied with a local symlink:

```sh
mkdir -p .tools/fem/bin
ln -s "$(command -v ccx)" .tools/fem/bin/ccx
python test_strength.py --benchmark
```

Check that `command -v ccx` returns a path first. Other systems should adapt the explicit paths in the scripts. The benchmark compares a simple axial test with its analytical result. The flat-body fixture rejects corner or tilted models; do not bypass that guard.

```sh
python test_strength.py --case body-weight --source output/flat/apollo-mount.FCStd --size 2
python compare_corner_strength.py --variant ends --case side --size 2 --linear-edges
```

The corner script reads `output/Final-prints/entrance.FCStd` and requires Corner=Yes and CableEnabled=No. It compares end closures with an optional spine. Re-running it on a newly aimed entrance model is a **new experiment**, not reproduction of earlier numerical values. `ViewStrength.FCMacro` can show a resulting `strength.FCStd`; it is not an enclosure rebuild macro.

Assumptions include isotropic fully solid linear elasticity, an elastic-modulus proxy and fixed wall-screw bores. Sliced infill, layer anisotropy, wall compliance, screw preload, temperature and PETG creep are not modelled. Mesh failures must be reported, and stress peaks at sharp edges need mesh-sensitivity checks. Rebuilding CAD does not rerun FEM.
