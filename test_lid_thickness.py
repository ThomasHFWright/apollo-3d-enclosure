"""Check our radar window against the supplied official textured front panel."""
import build_mount as m


def main():
    source=next(m.ROOT.glob('*model_files/r_pro-1_case.step'))
    official=m.Part.read(str(source))
    # Apollo's case contains the front; its separate lid has rear port cutouts.
    inside=max((f for f in official.Faces if isinstance(f.Surface,m.Part.Plane)
                and f.normalAt(0,0).z>.999 and f.BoundBox.ZLength<1e-6),key=lambda f:f.Area)
    ceiling=inside.CenterOfMass.z
    assert abs(ceiling-1.75)<1e-6
    relief=[f for f in official.Faces if f.BoundBox.ZMax<ceiling-1e-6
            and f.BoundBox.ZMin>=-1e-6
            and inside.isInside(m.V(f.CenterOfMass.x,f.CenterOfMass.y,ceiling),1e-6,True)]
    # BREP bounds of the recessed texture give its deepest exterior surface.
    minimum=ceiling-max(f.BoundBox.ZMax for f in relief)
    assert abs(minimum-1.25)<1e-4,minimum
    for x,y in ((0,0),(5,5),(10,10),(-10,0),(0,20)):
        cut=official.common(m.Part.makeLine(m.V(x,y,-1),m.V(x,y,ceiling)))
        assert len(cut.Edges)==1 and abs(cut.Edges[0].Length-1.25)<1e-5
    for path in sorted((m.ROOT/'output').glob('*/apollo-mount.FCStd'))+list((m.ROOT/'output/Final-prints').glob('*.FCStd')):
        if path.parent.name.startswith(('corner-setback-','corner-end-closures-')):continue
        doc=m.App.openDocument(str(path))
        skin=doc.Parameters.FrontSkin
        assert skin<=minimum+1e-6,(path,skin,minimum)
        pose=doc.SourcePCB.Placement.multiply(m.App.Placement(m.SOURCE_CENTRE,m.App.Rotation()))
        lid=m.moved(doc.Cover.Shape,pose.inverse())
        z=m.PCB_T+doc.Parameters.FrontHeight+doc.Parameters.FrontClearance
        for x,y in ((0,0),(-10,0),(10,0),(0,-15),(0,15)):
            cut=lid.common(m.Part.makeLine(m.V(x,y,z-.1),m.V(x,y,z+skin+.1)))
            assert len(cut.Edges)==1 and abs(cut.Edges[0].Length-skin)<1e-5,(path,x,y)
        print(f'PASS {path.relative_to(m.ROOT)}: front {skin:g} mm <= official minimum {minimum:.2f} mm')
        m.App.closeDocument(doc.Name)


if __name__=='__main__':
    main()
