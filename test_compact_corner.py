"""Corner nesting regression: python test_compact_corner.py (FreeCAD required)."""
import build_mount as m
from test_mount import check_co2_relief, check_end_rails, check_cable_rim, check_nut_hoods


def check():
    doc=m.App.openDocument(str(m.ROOT/'output/Final-prints/entrance.FCStd'))
    saved=m.read_parameters(doc)
    old_pose=doc.SourcePCB.Placement.multiply(m.App.Placement(m.SOURCE_CENTRE,m.App.Rotation()))
    old_lid=m.moved(doc.Cover.Shape,old_pose.inverse())
    base=m.build(saved)
    assert base['body'].cut(doc.Mount.Shape).Volume<.001
    assert doc.Mount.Shape.cut(base['body']).Volume<.001
    m.App.closeDocument(doc.Name)
    assert not saved['CompactCorner']
    for changes in (dict(Yaw=-39.,Pitch=4.,CableEnabled=True),
                    dict(Yaw=39.,Pitch=4.,CableEnabled=True),
                    dict(Yaw=39.,Pitch=15.,CableEnabled=False),
                    dict(Yaw=-39.,Pitch=15.,CableEnabled=False),
                    dict(Yaw=0.,Pitch=15.,CableEnabled=False),
                    dict(Yaw=-70.,Pitch=10.,CableEnabled=False),
                    dict(Yaw=-90.,Pitch=0.,CableEnabled=False),
                    dict(Yaw=90.,Pitch=0.,CableEnabled=False),
                    dict(Yaw=-39.,Pitch=4.,CornerAngle=110.,CableEnabled=False)):
        p=dict(saved,**changes);p['CompactCorner']=True
        r=m.build(p)
        assert r['corner_depth_saving']>0
        if p['Yaw']==0 and p['Pitch']==15:
            assert r['corner_depth_saving']>13, 'Empty rectangular rear bay still sets stand-off'
        # Nesting must not add a panel across the open back of the corner frame.
        # Stay near the setback: at 90 degrees the PCB rim legitimately reaches
        # into the front of the corner cavity and must remain supported there.
        rear=m.box(-1,1,-5,5,p['CornerSetback']+4.1,p['CornerSetback']+6.)
        assert rear.common(r['body']).Volume<.001
        lid=m.moved(r['lid'],r['pose'].inverse())
        assert lid.cut(old_lid).Volume<.001 and old_lid.cut(lid).Volume<.001
        assert r['contacts']==base['contacts'] and r['end_contacts']==base['end_contacts']
        for a,b in zip(base['retention'],r['retention']):
            assert a.cut(b).Volume<.001 and b.cut(a).Volume<.001
        check_co2_relief(p,r)
        check_end_rails(r)
        check_nut_hoods(p,r)
        for shape in (r['body'],r['lid']):
            shape.check(True)
            assert len(shape.Solids)==1 and m.closed_mesh(shape).isSolid()
        above=m.moved(m.box(-500,500,-500,500,r['seam'],500),r['pose'])
        frame=m.Part.makeCompound([r['mount_frame'],r['frame_bridges']])
        assert r['body'].cut(frame).common(above).Volume<.001, 'Chamber rises around lid'
        if abs(p['Yaw'])==39 and p['Pitch']==15:
            # Inside the previously open triangular frame/chamber junction.
            probe=m.Part.makeSphere(.2,m.V(31.1 if p['Yaw']>0 else -31.1,-28.3,37.8))
            assert probe.cut(r['body']).Volume<1e-6, 'Gap beside wall-contact frame'
        # Four original wall-screw bores must still be present and unobstructed.
        angle=90-p['CornerAngle']/2
        length=r['wall_width']/2/m.math.cos(m.math.radians(angle))
        for sign in (-1,1):
            rotation=m.App.Rotation(m.V(0,1,0),-sign*angle)
            placement=m.App.Placement(m.V(),rotation)
            x0,x1=sorted((0,sign*length))
            frame=m.box(x0,x1,-r['wall_height']/2-10,r['wall_height']/2+10,0,4)
            frame=frame.cut(m.box(x0+8,x1-8,-r['wall_height']/2+6,r['wall_height']/2-6,-1,5))
            for y in (-r['wall_height']/2-5,r['wall_height']/2+5):
                x=sign*length*.65
                frame=frame.cut(m.Part.makeCylinder(2.3,6,m.V(x,y,-1)))
                frame=frame.cut(m.Part.makeCone(2.3,4.5,2.2,m.V(x,y,1.9)))
                bore=m.moved(m.Part.makeCylinder(2.29,6,m.V(sign*length*.65,y,-1)),m.App.Placement(m.V(),rotation))
                assert bore.common(r['body']).Volume<.001
            frame=m.moved(frame,placement).cut(m.box(-500,500,-500,500,-500,p['CornerSetback']))
            assert frame.cut(r['cable_cut']).cut(r['body']).Volume<.01, 'Wall-contact frame cut away'
        if p['CableEnabled']:
            assert r['plug'].Volume>0 and r['cable_preview'].Volume>0
            assert r['body'].common(r['plug']).Volume<.01
            assert r['body'].common(r['cable_preview']).Volume<.01
            check_cable_rim(r)
        print('PASS compact',changes,'depth saving',round(r['corner_depth_saving'],2),flush=True)
    # The option has no effect on flat-wall presets.
    doc=m.App.openDocument(str(m.ROOT/'output/flat/apollo-mount.FCStd'))
    p=m.read_parameters(doc);p['CompactCorner']=True
    r=m.build(p)
    assert r['corner_depth_saving']==0
    assert r['body'].cut(doc.Mount.Shape).Volume<.001 and doc.Mount.Shape.cut(r['body']).Volume<.001
    m.App.closeDocument(doc.Name)
    print('PASS standard corner and flat-wall behaviour unchanged',flush=True)


def check_extra_depth():
    doc=m.App.openDocument(str(m.ROOT/'output/compact-corner-poe/apollo-mount.FCStd'))
    p=m.read_parameters(doc)
    before=doc.SourcePCB.Placement.multiply(m.App.Placement(m.SOURCE_CENTRE,m.App.Rotation()))
    p['RearChamberDepth']+=5.
    r=m.build(p)
    assert abs(r['pose'].Base.z-before.Base.z-5.)<1e-6
    assert abs(r['pose'].Base.x-before.Base.x)<1e-6
    assert r['body'].common(r['plug']).Volume<.01
    assert m.closed_mesh(r['body']).isSolid()
    m.App.closeDocument(doc.Name)
    print('PASS depth adjustment: +5 mm input adds exactly 5 mm forward clearance',flush=True)


def check_saved_outputs():
    from pathlib import Path
    from tempfile import TemporaryDirectory
    for name in ('flat/apollo-mount','corner/apollo-mount','custom/apollo-mount',
                 'yaw90/apollo-mount','yaw_minus90/apollo-mount','Final-prints/entrance',
                 'compact-corner-poe/apollo-mount','compact-pitch15/apollo-mount'):
        doc=m.App.openDocument(str(m.ROOT/'output'/(name+'.FCStd')))
        p=m.read_parameters(doc)
        r=m.build(p)
        previous=doc.SourcePCB.Placement.multiply(m.App.Placement(m.SOURCE_CENTRE,m.App.Rotation()))
        assert (r['pose'].Base-previous.Base).Length<1e-6, 'PCB placement changed: '+name
        if not p['CompactCorner']:
            for old,new in ((doc.Mount.Shape,r['body']),(doc.Cover.Shape,r['lid'])):
                assert old.cut(new).Volume<.001 and new.cut(old).Volume<.001, name
        check_co2_relief(p,r)
        check_end_rails(r)
        check_nut_hoods(p,r)
        check_cable_rim(r)
        with TemporaryDirectory() as folder:
            m.parameters(doc,p)
            m.export(doc,p,r,Path(folder))  # Both meshes, bed placement and A1 bounds.
        assert m.read_parameters(doc)==p
        m.App.closeDocument(doc.Name)
        print('PASS saved output',name,flush=True)


if __name__=='__main__':
    check()
    check_extra_depth()
    check_saved_outputs()
