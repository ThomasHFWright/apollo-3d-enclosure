# Printing, fit and assembly

## Printer and filament

The working setup is a Bambu Lab A1 with a 0.4 mm nozzle and white ELEGOO Rapid/Fast PETG. Start from the appropriate manufacturer/system filament profile in your slicer. The tested OrcaSlicer 2.4.2 setup used its bundled **Elegoo Rapid PETG @System** profile (250°C nozzle, 70°C bed) and these process settings:

| Setting | Working value |
|---|---|
| Layer height / first layer | 0.24 / 0.20 mm |
| Walls | 4 |
| Top / bottom layers | 5 / 5 |
| Sparse infill | 25% gyroid |
| Outer / inner wall speed | 60 / 100 mm/s |
| First layer / first-layer infill | 25 / 40 mm/s |
| Body supports | Tree auto, allowed on the model as well as the bed |
| Support top / bottom gap | 0.2 / 0.2 mm |
| Support top interface layers | 3 |
| Support XY gap | 0.35 mm |
| Brim | 5 mm when needed for adhesion |

These are starting settings for that setup, not a universal PETG profile. Calibrate and dry according to your actual filament/printer guidance. A different print orientation or larger angle can substantially change support needs.

## Orientation and exports

The generator orients the body with the PCB rim toward the bed when possible; at steep angles it switches to a wall-contact face to keep all material above the bed. The lid is exported exterior face down. The fit ring is a separate optional coupon. Check the first layer and support access in the slicer rather than assuming exported orientation is always the most economical.

Import `body.stl` and `lid.stl` as separate printable parts at 100% scale, in millimetres. Do not slice `SourcePCB`, the cable preview or orange clearance envelopes. Native CAD and `assembly.step` show assembled positions; individual STL/STEP exports are oriented for printing. The automated bed check is for a 256 mm cube; smaller printers need their own check.

## Hardware

- Four standard M3 hex nuts by default; pockets are 5.9 mm across flats and 2.9 mm deep.
- Four matching M3 bolts. M3×12 mm was checked for the developed corner arrangement; verify engagement and protrusion for your variant. M3×8 mm provided only about 1.1 mm engagement in the checked arrangement and was too short.
- Head recesses default to 5.7 mm diameter × 3.0 mm depth, based on measured heads of 5.3 × 2.8 mm plus clearance.
- Four wall screws/anchors suitable for your wall. The printed wall holes are 4.6 mm with countersunk entrances; wall hardware is separate from the M3 cover bolts.

M2 is available in the FastenerSize dropdown; change both body and lid together and measure the matching heads. Ordinary hex nuts are assumed, not nyloc. Fastener clearance is a print-tolerance allowance, not guaranteed fit for every machine.

## Fit and assembly

1. Print the chosen preset's **fit ring and lid** first. The fit ring is a coupon, not a third assembly part.
2. With the device unpowered, check the main PCB seats freely, all daughterboards/pins clear the plastic, and the CO₂ notch reaches the inner wall without interference. Only the main PCB edges should be retained.
3. Test nuts, bolt holes and head recesses. Adjust the relevant clearance parameters and rebuild if required; do not clamp a bent PCB into place.
4. Print the body and remove supports. The shallow fit ring cannot check the complete finger-access pockets or cable route.
5. Place nuts into the rear-facing pockets through the chamber before installing the PCB. Confirm access with fingers or tweezers.
6. Check your Ethernet male connector and boot pass through the opening and can negotiate the route. A cross-section clearance check alone does not prove a rigid connector can move around every bend. Arrange cable insertion and wall fastening while the PCB is accessible.
7. Attach the body to the wall, seat the PCB on its ledges, and gently tighten the lid until its flanges seat. Check bolt tips and heads clear the electronics.
8. Keep ventilation open around the PoE hardware and CO₂ sensor. Check operation, radar coverage, physical fit and retention during sustained use before printing a batch.

The 1.2 mm front skin measured thinner than the supplied official front's minimum 1.25 mm. This is a geometry comparison, not an RF attenuation measurement. White unfilled PETG was the intended material; other colours/fillers and sensor revisions may behave differently.
