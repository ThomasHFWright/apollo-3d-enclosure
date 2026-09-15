"""Corner nesting regression: python test_compact_corner.py (FreeCAD required)."""
import build_mount as m
from test_mount import check_co2_relief, check_end_rails, check_cable_rim


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
                    dict(Yaw=0.,Pitch=15.,CableEnabled=False),
                    dict(Yaw=-70.,Pitch=10.,CableEnabled=False),
                    dict(Yaw=-39.,Pitch=4.,CornerAngle=110.,CableEnabled=False)):
        p=dict(saved,**changes);p['CompactCorner']=True
        r=m.build(p)
        assert r['corner_depth_saving']>0
        lid=m.moved(r['lid'],r['pose'].inverse())
        assert lid.cut(old_lid).Volume<.001 and old_lid.cut(lid).Volume<.001
        assert r['contacts']==base['contacts'] and r['end_contacts']==base['end_contacts']
        for a,b in zip(base['retention'],r['retention']):
            assert a.cut(b).Volume<.001 and b.cut(a).Volume<.001
        check_co2_relief(p,r)
        check_end_rails(r)
        for shape in (r['body'],r['lid']):
            shape.check(True)
            assert len(shape.Solids)==1 and m.closed_mesh(shape).isSolid()
        # Four original wall-screw bores must still be present and unobstructed.
        angle=90-p['CornerAngle']/2
        length=r['wall_width']/2/m.math.cos(m.math.radians(angle))
        for sign in (-1,1):
            rotation=m.App.Rotation(m.V(0,1,0),-sign*angle)
            for y in (-r['wall_height']/2-5,r['wall_height']/2+5):
                bore=m.moved(m.Part.makeCylinder(2.29,6,m.V(sign*length*.65,y,-1)),m.App.Placement(m.V(),rotation))
                assert bore.common(r['body']).Volume<.001
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


if __name__=='__main__':
    check()
    check_extra_depth()
