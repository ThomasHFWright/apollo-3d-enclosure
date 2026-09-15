# Working on this enclosure

Read README.md, docs/PARAMETERS.md and docs/AI-WORKFLOW.md before modifying geometry.

- For routine user parameter changes, lead with editing Parameters → Data in FreeCAD and executing Rebuild.FCMacro through FreeCAD's Macro menu. Reserve CLI/Python recipes for source changes or requested automation.
- For generator development, use FreeCAD's Python API through build_mount.py. No MCP service is required.
- Read all settings from the user's specified saved document with read_parameters(); CLI starts from defaults.
- Preserve unrelated saved settings, especially Corner, Yaw, Pitch, RearChamberDepth, CableEnabled and fit/hardware clearances.
- Treat Mount/Cover as generated solids. Persistent changes belong in the shared generator, not manual edits of exported meshes.
- Preserve rigid PCB rails, module and PoE clearances, vent-edge reinforcement and screw bearing surfaces. Cable is a reference and intersection cut, never a standalone printed tube.
- Build to a new named folder during development. Rebuild.FCMacro always writes output/custom; it does not update slicer projects or thumbnails.
- Run affected existing checks and add one regression check for nontrivial new geometry logic. Report invalid geometry or solver failures instead of bypassing validation.
- Check both body and lid, valid connected solids, closed meshes, fit-ring isolation and bed placement. Numeric parameter bounds are not proof of physical fit.
- Do not claim FEM predicts PETG thermal creep or that simplified module envelopes are detailed component CAD.
- Keep documentation in sync with PARAMETERS, including calculated read-only fields.
- Do not publish printer credentials, local application settings, private photographs, backups or solver caches. Do not send/start a print unless explicitly requested.
- Preserve Apollo attribution and CC BY-NC-SA 4.0 terms.
