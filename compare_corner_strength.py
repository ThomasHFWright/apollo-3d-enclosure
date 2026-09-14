"""Compare end closures with a continuous corner spine using the existing FEM solver.

Run: python compare_corner_strength.py --variant ends --case pull --size 2
Repeat with --variant spine. Saved geometry is built from the user's entrance CAD.
"""
import argparse
import json
import hashlib
from pathlib import Path
import build_mount as m
import test_strength as fem


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--variant',choices=['ends','spine'],required=True)
    ap.add_argument('--case',choices=['pull','side','weight'],default='pull')
    ap.add_argument('--size',type=float,default=2.)
    ap.add_argument('--linear-edges',action='store_true',help='Keep quadratic midside nodes on straight mesh edges to avoid folded curved elements')
    args=ap.parse_args()
    root=m.ROOT/'output/strength/corner-comparison'
    root.mkdir(parents=True,exist_ok=True)
    source=m.ROOT/'output/Final-prints/entrance.FCStd'
    doc=m.App.openDocument(str(source))
    p=m.read_parameters(doc)
    assert p['Corner'] and not p['CableEnabled'], 'Comparison currently requires corner with cable disabled'
    p['CornerSpine']=args.variant=='spine'
    m.App.closeDocument(doc.Name)
    cache=root/(args.variant+'.brep')
    settings=root/(args.variant+'.json')
    signature=dict(parameters=p,generator_sha256=hashlib.sha256((m.ROOT/'build_mount.py').read_bytes()).hexdigest())
    if cache.exists() and settings.exists() and json.loads(settings.read_text())==signature:
        shape=m.Part.Shape();shape.read(str(cache))
    else:
        result=m.build(p)
        shape=result['body']
        assert shape.common(m.box(-500,500,-500,500,-500,p['CornerSetback'])).Volume<.001
        shape.exportBrep(str(cache))
        settings.write_text(json.dumps(signature,indent=2))
        pose=result['pose']
        (root/(args.variant+'-pose.json')).write_text(json.dumps(dict(base=list(pose.Base),rotation=pose.Rotation.Q)))
    saved=json.loads((root/(args.variant+'-pose.json')).read_text())
    pose=m.App.Placement(m.V(*saved['base']),m.App.Rotation(*saved['rotation']))
    fixed=fem.select_faces(shape,lambda f:isinstance(f.Surface,m.Part.Cylinder)
        and abs(f.Surface.Radius-2.3)<1e-5 and abs(f.Surface.Axis.y)<1e-5
        and abs(f.CenterOfMass.y)>45)
    assert len(fixed)==4, fixed
    inverse=pose.inverse()
    def rear_rail(face):
        if not isinstance(face.Surface,m.Part.Plane):return False
        local=m.moved(face,inverse)
        return local.BoundBox.ZLength<1e-5 and abs(local.CenterOfMass.z)<1e-5
    loaded=fem.select_faces(shape,rear_rail)
    assert len(loaded)>=4 and not set(loaded)&set(fixed),loaded
    direction,force={'pull':((0,0,1),10.),'side':((1,0,0),10.),'weight':((0,-1,0),1.)}[args.case]
    m.App.ParamGet('User parameter:BaseApp/Preferences/Mod/Fem/Gmsh').SetString('gmshBinaryPath','/usr/bin/gmsh')
    metadata=dict(case='corner-'+args.case,variant=args.variant,parameters=p,force_N=force,direction=direction,
        mesh_max_mm=args.size,linear_element_edges=args.linear_edges,youngs_modulus_proxy_MPa=1072.,poisson_ratio_assumed=.35,
        limitations='Isotropic solid linear-elastic comparison; four wall screw bores fixed. Total force distributed over identical PCB rear ledges, bonded load proxy. No infill, layer anisotropy, PCB/contact, anchor flexibility, thermal effects or PETG creep. Peak stresses at sharp edges are mesh dependent. Not a lifetime or strength certification.')
    folder=root/(f'{args.variant}-{args.case}-h{args.size:g}'+('-straight' if args.linear_edges else ''))
    folder.mkdir(exist_ok=True)
    status=folder/'status.json'
    status.write_text(json.dumps(dict(status='RUNNING',settings=metadata),indent=2))
    try:
        fem.solve(shape,fixed,loaded,direction,force,args.size,1072.,folder,metadata,linear_edges=args.linear_edges)
    except BaseException as error:
        status.write_text(json.dumps(dict(status='FAILED',error=str(error)),indent=2))
        raise
    status.write_text(json.dumps(dict(status='PASS - comparative numerical screening only')))


if __name__=='__main__':
    main()
