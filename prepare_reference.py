"""Import Apollo's unmodified OBJ into FreeCAD and render inspection views.

Run on CachyOS: xvfb-run -a python prepare_reference.py
The OBJ is interpreted in millimetres; verify against the physical device.
"""

from pathlib import Path
import sys

sys.path.insert(0, "/usr/lib/freecad/lib")
import FreeCAD as App
import FreeCADGui as Gui
import Mesh
from PySide import QtCore

root = Path(__file__).resolve().parent
Gui.showMainWindow()
doc = App.newDocument("ApolloPCBReference")
doc.Label = "R PRO-1 main PCB - radar and CO2 boards missing"
Mesh.insert(str(root / "r-pro-1-pcb.obj"), doc.Name)
assert len(doc.Objects) == 368, "Source changed: recheck the imported assembly"
board = doc.Objects[0]
board.Label = "Main PCB (source mesh, millimetres assumed)"
board.addProperty("App::PropertyString", "MissingGeometry", "Reference")
board.MissingGeometry = "LD2450 radar, optional LD2412 radar, optional SCD40 daughterboard, Ethernet plug/cable"
bounds = board.Mesh.BoundBox
assert abs(bounds.XLength - 44.474687) < 0.01
assert abs(bounds.YLength - 56.974716) < 0.01
assert abs(bounds.ZLength - 1.586157) < 0.01
overall = App.BoundBox()
for obj in doc.Objects:
    assert obj.Mesh.CountFacets > 0
    overall.add(obj.Mesh.BoundBox)
    obj.ViewObject.ShapeColor = (0.72, 0.72, 0.75)
board.ViewObject.ShapeColor = (0.06, 0.36, 0.22)
doc.recompute()
view = Gui.activeDocument().activeView()
view.setAnimationEnabled(False)
for name, direction in (("front", "viewTop"), ("rear", "viewBottom"), ("iso", "viewAxonometric")):
    getattr(view, direction)()
    view.fitAll()
    Gui.updateGui()
    view.saveImage(str(root / f"pcb-reference-{name}.png"), 1200, 1000, "White")
doc.saveAs(str(root / "r-pro-1-pcb-reference.FCStd"))
print("Main PCB:", bounds, flush=True)
print("Complete source envelope:", overall, flush=True)
print("Saved r-pro-1-pcb-reference.FCStd and three inspection images", flush=True)
App.closeDocument(doc.Name)
Gui.getMainWindow().close()
QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.DeferredDelete)
QtCore.QCoreApplication.processEvents()
