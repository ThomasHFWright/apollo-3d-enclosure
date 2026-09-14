# Publication checks — 15 September 2026

Environment: FreeCAD 1.1.3, Qhull, system Python, CachyOS/Linux.

The selected repository files were copied to a fresh temporary directory to check that local caches and untracked model files were not needed for the documented workflow.

- All 58 editable source parameters occur exactly once in the parameter-reference tables. Twelve calculated properties are documented separately.
- Relative Markdown file links resolve to included files. Native CAD ZIP containers pass integrity checks. Selected files are below GitHub's per-file limit.
- Compressed PCB reference decompresses successfully; a fresh CLI build of the corridor example passes the generator/export checks: valid connected body/lid, no reserved-module/wall/cover collision, closed printable meshes and bed bounds.
- `python test_lid_thickness.py` passes for all six supplied CAD documents: 1.20 mm front skin versus the official reference's 1.25 mm minimum.
- The actual `Rebuild.FCMacro` is tested in FreeCAD's GUI on a virtual display: load the corner preset, change yaw/pitch/depth/cable settings, regenerate, verify the complete parameter set is preserved except for those requested changes, and check the CO₂ relief.

This publication does not introduce enclosure geometry changes. The full historical geometry suite and FEM comparisons were not rerun for the documentation/publication task. No print was started. These checks do not establish physical fit, RF performance or lifetime under PoE heat.
