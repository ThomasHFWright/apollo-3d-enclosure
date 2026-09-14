"""FreeCAD/CalculiX screening, not a printed-PETG lifetime certification.

python test_strength.py --benchmark
python test_strength.py --case body-weight --size 2
Run each case again at --size 1 for a mesh-sensitivity check.
"""
import argparse
import hashlib
import json
import math
import os
import re
from pathlib import Path
import subprocess
import sys

sys.path[:0] = ['/usr/lib/freecad/lib', '/usr/lib/freecad/Mod/Fem']
import FreeCAD as App
import Part
import ObjectsFem
from femmesh.gmshtools import GmshTools
from femtools.ccxtools import FemToolsCcx
from PySide import QtCore

ROOT = Path(__file__).resolve().parent
V = App.Vector
CASES = {'body-weight': ('Mount', (0, -1, 0), 1.),
         'body-pull': ('Mount', (0, 0, -1), 10.),
         'cover-pull': ('Cover', (0, 0, 1), 10.)}


def select_faces(shape, predicate):
    return [f'Face{i}' for i, face in enumerate(shape.Faces, 1) if predicate(face)]


def boundaries(source, case):
    """Geometric selection, never hardcoded topology indexes; flat preset only."""
    p = source.Parameters
    if p.Corner or abs(p.Yaw) > 1e-6 or abs(p.Pitch) > 1e-6:
        raise ValueError('This screening fixture supports flat, untilted models only')
    shape = source.getObject(CASES[case][0]).Shape.copy()
    z = 4 + p.BoardDistance
    radius = getattr(p, 'ScrewHoleDiameter', 3.4)/2 if case == 'cover-pull' else 2.3
    fixed = select_faces(shape, lambda f: isinstance(f.Surface, Part.Cylinder)
                         and abs(f.Surface.Radius-radius) < 1e-5
                         and abs(f.Surface.Axis.z) > .999)
    assert len(fixed) == 4, f'Expected four screw bores, got {fixed}'
    if case == 'body-weight':
        loaded = select_faces(shape, lambda f: isinstance(f.Surface, Part.Plane)
                              and abs(f.CenterOfMass.y + 56.974716/2 + p.RegistrationGap) < 1e-5
                              and f.normalAt(0, 0).y > .99)
        assert loaded, 'No lower PCB registration surfaces found'
    else:
        height = z if case == 'body-pull' else z + 1.586157 + p.BoardSlotGap
        loaded = select_faces(shape, lambda f: isinstance(f.Surface, Part.Plane)
                              and f.BoundBox.ZLength < 1e-5
                              and abs(f.CenterOfMass.z-height) < 1e-5)
        assert len(loaded) >= 3, loaded  # Segmented rails on all four PCB edges.
    assert not set(fixed) & set(loaded)
    return shape, fixed, loaded


def execute(command, folder, name):
    with (folder/name).open('w') as log:
        done = subprocess.run(command, cwd=folder, stdout=log, stderr=subprocess.STDOUT,
                              env=dict(os.environ, OMP_NUM_THREADS='4', OPENBLAS_NUM_THREADS='4'),
                              timeout=1800)
    if done.returncode:
        raise RuntimeError(f'{command[0]} exited {done.returncode}; see {folder/name}')


def solve(shape, fixed_faces, loaded_faces, direction, force, size, modulus, folder, metadata, linear_edges=False):
    folder.mkdir(parents=True, exist_ok=True)
    doc = App.newDocument('StrengthScreening')
    geom = doc.addObject('Part::Feature', 'TestPart')
    geom.Shape = shape
    assert shape.isValid() and len(shape.Solids) == 1
    notes = doc.addObject('App::TextDocument', 'Assumptions')
    notes.Text = json.dumps(metadata, indent=2)
    analysis = ObjectsFem.makeAnalysis(doc, 'Analysis')
    material = ObjectsFem.makeMaterialSolid(doc, 'PETG')
    material.Material = {'Name': 'ELEGOO Rapid PETG - isotropic screening proxy',
                         'YoungsModulus': f'{modulus} MPa', 'PoissonRatio': '0.35',
                         'Density': '1260 kg/m^3'}
    analysis.addObject(material)
    fixed = ObjectsFem.makeConstraintFixed(doc, 'ScrewBoresFixed')
    fixed.References = [(geom, fixed_faces)]
    analysis.addObject(fixed)
    load = ObjectsFem.makeConstraintForce(doc, 'DistributedLoad')
    load.References = [(geom, loaded_faces)]
    load.Force = f'{force} N'
    axis = doc.addObject('Part::Feature', 'LoadDirection')
    axis.Shape = Part.makeLine(V(), V(*direction))
    load.Direction = (axis, ['Edge1'])
    load.Reversed = False
    analysis.addObject(load)
    mesh = ObjectsFem.makeMeshGmsh(doc, 'Mesh')
    mesh.Shape = geom
    mesh.ElementOrder = '2nd'
    mesh.SecondOrderLinear = linear_edges
    mesh.CharacteristicLengthMin = min(.3, size)
    mesh.CharacteristicLengthMax = size
    mesh.HighOrderOptimize = 'Optimization'
    analysis.addObject(mesh)
    doc.recompute()
    assert (load.DirectionVector-V(*direction)).Length < 1e-6
    assert abs(load.Force.getValueAs('N').Value-force) < 1e-6
    gm = GmshTools(mesh)
    gm.load_properties()
    gm.update_mesh_data()
    gm.get_tmp_file_paths(str(folder))
    gm.get_gmsh_command()
    gm.write_gmsh_input_files()
    print(f'Meshing {folder.name}', flush=True)
    execute([gm.gmsh_bin, '-v', '4', '-nt', '4', '-', gm.temp_file_geo], folder, 'gmsh.log')
    gm.update_properties()
    assert mesh.FemMesh.VolumeCount > 0
    solver = ObjectsFem.makeSolverCalculiXCcxTools(doc, 'CalculiX')
    solver.SplitInputWriter = False
    solver.AnalysisType = 'static'
    solver.GeometricalNonlinearity = 'linear'
    solver.MatrixSolverType = 'default'
    solver.WorkingDir = str(folder)
    analysis.addObject(solver)
    doc.recompute()
    ft = FemToolsCcx(analysis, solver)
    ft.update_objects()
    ft.setup_working_dir(str(folder))
    error = ft.check_prerequisites()
    if error:
        raise RuntimeError(error)
    ft.write_inp_file()
    assert ft.inp_file_name and Path(ft.inp_file_name).is_file()
    print(f'Solving {folder.name}: {mesh.FemMesh.NodeCount} nodes, {mesh.FemMesh.VolumeCount} elements', flush=True)
    execute([str(ROOT/'.tools/fem/bin/ccx'), '-i', str(Path(ft.inp_file_name).with_suffix(''))], folder, 'ccx.log')
    solver_log = (folder/'ccx.log').read_text()
    assert 'Job finished' in solver_log and '*ERROR' not in solver_log
    ft.load_results()
    dat = Path(ft.inp_file_name).with_suffix('.dat').read_text()
    match = re.search(r'total force .*?for set SCREWBORESFIXED[^\n]*\n\s*([-+\d.Ee]+)\s+([-+\d.Ee]+)\s+([-+\d.Ee]+)', dat)
    assert match, 'Missing support reaction output'
    reaction = V(*(float(v) for v in match.groups()))
    assert (reaction+V(*direction)*force).Length < max(1e-5, force*.001), reaction
    results = [o for o in doc.Objects if o.isDerivedFrom('Fem::FemResultObject')]
    assert len(results) == 1 and results[0].vonMises
    result = results[0]
    stresses, displacements = result.vonMises, result.DisplacementLengths
    assert all(math.isfinite(v) for v in stresses + displacements)
    peak = max(range(len(stresses)), key=stresses.__getitem__)
    report = dict(metadata, reaction_N=list(reaction), nodes=mesh.FemMesh.NodeCount, elements=mesh.FemMesh.VolumeCount,
                  volume_mm3=shape.Volume, fixed_faces=fixed_faces, loaded_faces=loaded_faces,
                  load_area_mm2=sum(shape.getElement(f).Area for f in loaded_faces),
                  max_displacement_mm=max(displacements),
                  max_von_mises_MPa=max(stresses),
                  peak_stress_position_mm=list(mesh.FemMesh.getNodeById(result.NodeNumbers[peak])))
    if metadata['case'] == 'benchmark':
        end_nodes = mesh.FemMesh.getNodesByFace(shape.getElement(loaded_faces[0]))
        displacements = dict(zip(result.NodeNumbers, result.DisplacementVectors))
        actual = sum(displacements[n].x for n in end_nodes)/len(end_nodes)
        expected = force*100/(modulus*4)
        assert abs(actual/expected-1) < .02, (actual, expected)
        report['axial_displacement_mm'] = actual
        report['analytical_displacement_mm'] = expected
    doc.recompute()
    doc.saveAs(str(folder/'strength.FCStd'))
    (folder/'summary.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2), flush=True)
    App.closeDocument(doc.Name)
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--benchmark', action='store_true')
    ap.add_argument('--case', choices=CASES, default='body-weight')
    ap.add_argument('--source', type=Path, default=ROOT/'output/flat/apollo-mount.FCStd')
    ap.add_argument('--size', type=float, default=2.)
    ap.add_argument('--modulus', type=float, default=1072.)
    ap.add_argument('--force', type=float)
    args = ap.parse_args()
    if not all(math.isfinite(v) and v > 0 for v in (args.size, args.modulus, args.force if args.force is not None else 1.)):
        ap.error('Mesh size, modulus and force must be finite and positive')
    App.ParamGet('User parameter:BaseApp/Preferences/Mod/Fem/Gmsh').SetString('gmshBinaryPath', '/usr/bin/gmsh')
    App.ParamGet('User parameter:BaseApp/Preferences/Mod/Fem/Ccx').SetString('ccxBinaryPath', str(ROOT/'.tools/fem/bin/ccx'))
    case = 'benchmark' if args.benchmark else args.case
    meta = {'case': case, 'mesh_max_mm': args.size, 'matrix_solver': 'default (SPOOLES)', 'youngs_modulus_proxy_MPa': args.modulus,
            'poisson_ratio_assumed': .35, 'material_source': 'https://www.elegoo.com/products/rapid-petg-filament-1-75mm-colored-1kg',
            'limitations': 'Solid isotropic linear elastic screening. E uses 1072 MPa flexural modulus as a proxy; Poisson ratio assumed. No infill, layer anisotropy, creep, temperature law, PCB/contact model, screw preload or wall-anchor failure. Fixed screw bores are idealized. Sharp-edge/constraint peak stresses may be mesh-dependent; not a safety factor.'}
    if args.benchmark:
        shape = Part.makeBox(100, 2, 2)
        fixed = select_faces(shape, lambda f: f.CenterOfMass.x < 1e-6)
        loaded = select_faces(shape, lambda f: f.CenterOfMass.x > 99.999)
        direction, force = (1, 0, 0), 10.
    else:
        source = App.openDocument(str(args.source.resolve()))
        shape, fixed, loaded = boundaries(source, case)
        _, direction, force = CASES[case]
        meta.update(source=str(args.source.resolve()), source_sha256=hashlib.sha256(args.source.read_bytes()).hexdigest(),
                    rear_chamber_mm=source.Parameters.RearChamberDepth)
        App.closeDocument(source.Name)
    force = args.force if args.force is not None else force
    meta.update(force_N=force, direction=direction)
    folder = ROOT/'output/strength'/f'{case}-h{args.size:g}-E{args.modulus:g}-F{force:g}'
    folder.mkdir(parents=True, exist_ok=True)
    status = folder/'status.json'
    status.write_text(json.dumps({'status': 'RUNNING', 'settings': meta}, indent=2))
    try:
        solve(shape, fixed, loaded, direction, force, args.size, args.modulus, folder, meta)
    except BaseException as error:
        status.write_text(json.dumps({'status': 'FAILED - do not use old results', 'error': str(error)}, indent=2))
        raise
    status.write_text(json.dumps({'status': 'PASS - numerical screening only'}, indent=2))


def show_results(doc, folder=None):
    """Attach native GUI editors to headless results and show an undeformed stress map."""
    import FreeCADGui as Gui
    import FemGui
    from femviewprovider.view_material_common import VPMaterialCommon
    from femviewprovider.view_mesh_gmsh import VPMeshGmsh
    from femviewprovider.view_solver_ccxtools import VPSolverCcxTools
    from femviewprovider.view_result_mechanical import VPResultMechanical
    result = next(o for o in doc.Objects if o.isDerivedFrom('Fem::FemResultObject'))
    for obj, provider in ((doc.PETG, VPMaterialCommon), (doc.Mesh, VPMeshGmsh),
                          (doc.CalculiX, VPSolverCcxTools), (result, VPResultMechanical)):
        if not obj.ViewObject.Proxy:
            provider(obj.ViewObject)
    for obj in doc.Objects:
        obj.ViewObject.Visibility = False
    FemGui.setActiveAnalysis(doc.Analysis)
    pipeline = doc.getObject('Pipeline_CCX_Results')
    if pipeline is None:
        pipeline = ObjectsFem.makePostVtkResult(doc, [result], 'CCX_Results')
        doc.Analysis.addObject(pipeline)
    else:
        pipeline.load(result)
    pipeline.recompute()
    pipeline.ViewObject.DisplayMode = 'Surface'
    pipeline.ViewObject.Field = 'von Mises Stress'
    pipeline.ViewObject.Visibility = True
    pipeline.ViewObject.updateColorBars()
    view = Gui.activeDocument().activeView()
    view.setAnimationEnabled(False)
    view.setCameraOrientation(App.Rotation(V(), V(0, 1, 0), V(1, .6, 1), 'ZYX').Q)
    view.fitAll()
    view.getCameraNode().height = view.getCameraNode().height.getValue()*1.3
    Gui.Selection.clearSelection()
    Gui.updateGui()
    if folder:
        width, height = view.getSize()
        view.saveImage(str(folder/'stress.png'), width, height, 'White')
        pipeline.ViewObject.Field = 'Displacement Magnitude'
        pipeline.ViewObject.updateColorBars()
        Gui.updateGui()
        view.saveImage(str(folder/'displacement.png'), width, height, 'White')
        pipeline.ViewObject.Field = 'von Mises Stress'
        pipeline.ViewObject.updateColorBars()
        # Cover inside shows the keeper rails, absent from a front exterior view.
        if json.loads(doc.Assumptions.Text)['case'] == 'cover-pull':
            view.setCameraOrientation(App.Rotation(V(), V(0, 1, 0), V(-1, .6, -1), 'ZYX').Q)
            view.fitAll()
            view.getCameraNode().height = view.getCameraNode().height.getValue()*1.3
            Gui.updateGui()
            view.saveImage(str(folder/'stress-inside.png'), width, height, 'White')
        doc.save()


if __name__ == '__main__':
    app = QtCore.QCoreApplication.instance() or QtCore.QCoreApplication([])
    main()
