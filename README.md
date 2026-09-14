# Apollo R PRO-1 fixed-angle wall and corner enclosure

A community enclosure for the **Apollo Automation R PRO-1**, designed with FreeCAD and Python. Print the direction you need: the mount has no ball joint or friction-fit backplate to slip under cable load. A bolted lid retains the main PCB on segmented rails, with space and ventilation for PoE and the optional radar/CO₂ modules.

![Corner preset](docs/images/corner.png)

*Corner preset; the blue cable is a reference preview, not a printed tube.*

**Two assembly parts:** body and lid. An optional fit ring lets you check the PCB and hardware before committing to a full body print. The front sensor window is 1.2 mm thick; actual radar performance and long-term PETG behaviour still need checking in your installation.

This is an independent community project, not an official Apollo product. Thanks to [Apollo Automation](https://apolloautomation.com/products/r-pro-1) for providing the PCB and case references. See [attribution and reuse terms](ATTRIBUTION.md).

## Start here

- **Print an existing version:** download body and lid STLs from the table below, then slice for your printer.
- **Change the angle or fit:** follow the [FreeCAD guide](docs/FREECAD.md).
- **Look up a setting:** [every editable and calculated parameter](docs/PARAMETERS.md).
- **Ask an AI to modify the design:** [AI workflow and copyable prompts](docs/AI-WORKFLOW.md).
- **Print and assemble:** [PETG, support settings, hardware and fit checks](docs/PRINTING.md).

Download the complete project with GitHub's **Code → Download ZIP**, then extract it, or:

```sh
git clone https://github.com/ThomasHFWright/apollo-3d-enclosure.git
cd apollo-3d-enclosure
```

Keep `Rebuild.FCMacro` beside `build_mount.py`. A downloaded STL alone cannot expose the design parameters.

## Included models

These values were read from each saved CAD document for this publication. Defaults in the parameter reference describe new CLI builds; saved models can have different settings.

| Version | Mount | Yaw / pitch | Requested rear chamber | Cable | Files |
|---|---|---|---|---|---|
| Flat | Flat wall | 0° / 0° | 30 mm | On | [CAD](output/flat/apollo-mount.FCStd) · [body](output/flat/body.stl) · [lid](output/flat/lid.stl) · [fit ring](output/flat/fit-ring.stl) |
| Corner | 90° inside corner | 0° / 15° | 30 mm | On | [CAD](output/corner/apollo-mount.FCStd) · [body](output/corner/body.stl) · [lid](output/corner/lid.stl) · [fit ring](output/corner/fit-ring.stl) |
| Right-facing | Flat wall | +90° / 0° | 30 mm | On | [CAD](output/yaw90/apollo-mount.FCStd) · [body](output/yaw90/body.stl) · [lid](output/yaw90/lid.stl) |
| Left-facing | Flat wall | −90° / 0° | 30 mm | On | [CAD](output/yaw_minus90/apollo-mount.FCStd) · [body](output/yaw_minus90/body.stl) · [lid](output/yaw_minus90/lid.stl) |
| Custom corridor | 90° inside corner | −39° / +4° | 1 mm | Off | [CAD](output/custom/apollo-mount.FCStd) · [body](output/custom/body.stl) · [lid](output/custom/lid.stl) · [fit ring](output/custom/fit-ring.stl) |
| Entrance snapshot | 90° inside corner | −39° / +4° | 1 mm | Off | [CAD](output/Final-prints/entrance.FCStd) · [body](output/Final-prints/entrance.stl) · [lid](output/Final-prints/lid.stl) |

The five preset folders also contain individual STEP solids and `assembly.step`. All corner examples have a 10 mm corner-tip setback and top/bottom closures; their middle remains open. A requested 1 mm chamber does **not** mean the PCB is 1 mm from the wall: electronics space and any additional wall clearance are separate.

`output/custom` is also the macro's working export folder and is overwritten on a successful rebuild. Copy an example you want to keep before experimenting. The entrance snapshot is kept separately as an example of that workflow.

The STLs contain printable parts only. Native `.FCStd` documents include the original PCB as a visible guide. Orange clearance objects are simplified space reservations, not detailed models of the missing modules.

## How it works

`build_mount.py` calls FreeCAD's native Python geometry API: create solids, join them, subtract vents and clearances, then validate and export. Qhull's `qconvex` constructs the rear chamber envelope. No FreeCAD MCP server is required.

The model is **parametric through the generator**, not through a conventional sketch/Pad/Pocket feature history. Editing the `Parameters` object changes inputs; running `Rebuild.FCMacro` regenerates the shapes. Editing a value or pressing Recompute alone does not regenerate them.

## Requirements and command-line builds

Developed with FreeCAD **1.1.3** on CachyOS/Linux. FreeCAD GUI builds use FreeCAD's own Python. Terminal builds require a Python interpreter compatible with the installed FreeCAD modules, plus `qconvex` on `PATH`. The scripts currently add `/usr/lib/freecad/lib` (and `/usr/lib/freecad/Mod/Fem` for FEM); other installation layouts may require adapting those paths. No pip package replaces the FreeCAD installation.

For a new CLI build or PCB-reference import, first decompress the unchanged upstream mesh:

```sh
gzip -dk r-pro-1-pcb.obj.gz
python -c 'import build_mount; print(build_mount.App.Version())'
qconvex -V
python build_mount.py --corner --set Yaw=-39 --set Pitch=4 --set RearChamberDepth=1 --set CableEnabled=false --name my-corridor
```

This creates `output/my-corridor/` with CAD, STL and STEP files. `--set` can be repeated for any editable parameter. Booleans are `true`/`false`; `--name` should be a simple new folder name. CLI builds start from **source defaults**, not the currently open or saved custom model. To preserve a saved model's settings, use the GUI guide or the saved-document Python recipe in the AI guide.

Existing CAD files already contain the PCB mesh, so reopening/rebuilding those normally does not need the decompressed OBJ. Download/extract it before creating a new document. The compressed OBJ is about 13 MB, expands to about 89 MB, and requires no Git LFS.

## Validation and limitations

The generator checks connected valid solids, reserved-component and wall collisions, body/lid overlap, closed STL meshes and the A1's 256 mm build-volume limit. These checks do not verify every physical module, print orientation, support choice or cable insertion manoeuvre.

```sh
python test_mount.py
python test_lid_thickness.py
```

The full geometry suite can take several minutes. It uses the included PCB reference document and official case STEP. Optional historical FEM scripts are included; see [AI workflow / structural screening](docs/AI-WORKFLOW.md#structural-screening). They are comparative solid-material calculations, not a prediction of heat-induced creep or printed PETG service life.

The supplied PCB mesh omits the plugged-in LD2450, optional LD2412 and CO₂ daughterboards. Front height 13.9 mm, rear height 16.9 mm and side overhang 1.4 mm came from physical measurements. Verify your revision with the fit ring, lid, actual nuts and Ethernet connector before printing a batch.

## Contribute

Share your printer/material, parameter values, a photo of the problem and a small reproducible example in an issue or pull request. Keep PCB grips, fastener seats, vent reinforcement and cable clearances intact when changing the chamber. Please distinguish geometric validation from actual fit and sustained-PoE testing.

## License

Shared under [CC BY-NC-SA 4.0](LICENSE.md): attribute the creators, use noncommercially, and share adaptations under the same terms. See [ATTRIBUTION.md](ATTRIBUTION.md) for Apollo's original files and the changes made here. Apollo names and logos remain their owners' marks; this project is not endorsed by Apollo.
