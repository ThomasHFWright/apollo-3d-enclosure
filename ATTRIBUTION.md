# Attribution and reuse

## Apollo Automation references

The original R PRO-1 PCB mesh and official case reference are by **Apollo Automation**:

- [R PRO-1 product](https://apolloautomation.com/products/r-pro-1)
- [Official Printables model, ID 1349017](https://www.printables.com/model/1349017-apollo-automation-r-pro-1-dual-mmwave-multisensor)
- [Apollo source/CAD links](https://wiki.apolloautomation.com/homey/products/general/links/)
- [Apollo R_PRO-1 repository and license](https://github.com/ApolloAutomation/R_PRO-1)

The downloaded Printables model description, dated 6 April 2026, lists `r-pro-1-pcb.obj` and specifies **Creative Commons Attribution–NonCommercial–ShareAlike 4.0 International**. The same license text is published in Apollo's R_PRO-1 repository. That text is included as LICENSE.md.

Files retained here:

- `r-pro-1-pcb.obj.gz`: losslessly compressed original OBJ; decompress to restore it. No geometry edits.
- `r-pro-1-pcb-reference.FCStd`: imported and coloured reference assembly made from that mesh. It does not add detailed geometry for the missing daughterboards.
- `SourcePCB` within the enclosure `.FCStd` documents: the same reference mesh, repositioned to match each generated enclosure.
- `apollo-automation-r-pro-1-dual-mmwave-multisensor-with-optional-co2-addon-model_files/r_pro-1_case.step`: official front-case reference used by the thickness check.

## Community enclosure

**Thomas H. F. Wright / ThomasHFWright**, with AI-assisted FreeCAD/Python development, created the configurable fixed-angle wall/corner enclosure and accompanying generator, tests and guides.

Changes relative to the reference product include a fixed printed mount, configurable yaw/pitch and corner setback, ventilated connecting chamber, extended PCB rails and component notches, bolted cover and recessed hardware, and conditional reinforced cable openings. This is a community design, not Apollo's original enclosure, an official release or a claim of Apollo endorsement.

This repository is shared under **CC BY-NC-SA 4.0**. Credit Apollo for its references and ThomasHFWright for the enclosure/generator; identify modifications, keep reuse noncommercial and distribute adaptations under the same terms. The authoritative terms are in [LICENSE.md](LICENSE.md), with a [plain-language summary from Creative Commons](https://creativecommons.org/licenses/by-nc-sa/4.0/). Third-party trademarks remain with their owners.

FreeCAD, OpenCascade, Qhull, Gmsh, CalculiX and OrcaSlicer are separate dependencies under their respective licenses. Their binaries are not bundled here.
