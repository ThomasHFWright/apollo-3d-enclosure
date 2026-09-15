"""Runnable geometry checks: python test_mount.py (uses installed FreeCAD)."""
import build_mount as m
from pathlib import Path
from tempfile import TemporaryDirectory


def rejected(**changes):
    try:
        m.build(m.defaults(**changes))
    except ValueError as error:
        print("PASS rejected:",error,flush=True)
    else:
        raise AssertionError(f"Unsafe parameters accepted: {changes}")


def check_corner_setback():
    for changes in (dict(Corner=True,Pitch=15.),
                    dict(Corner=True,Yaw=-20.,Pitch=15.,RearChamberDepth=1.,CableEnabled=False),
                    dict(Corner=True,CornerAngle=110.,CableEnabled=False)):
        original=m.build(m.defaults(**changes,CornerSetback=0.))
        trimmed=m.build(m.defaults(**changes,CornerSetback=10.))
        cut=m.box(-500,500,-500,500,-500,10.)
        assert original['body'].common(cut).Volume>100, 'Probe must include original tip'
        assert trimmed['body'].common(cut).Volume<.001, 'Rear tip still occupies plaster clearance'
        expected=original['body'].cut(cut)
        assert expected.cut(trimmed['body']).Volume<.01, 'Lost material outside requested cut'
        # End closures cover both gaps without filling the central air path.
        for y in (-53.9,40.1):
            web=m.box(-1,1,y,y+13.8,10.01,13.99).cut(trimmed['cable_cut'])
            assert web.cut(trimmed['body']).Volume<.01, 'Missing flat end closure'
        added=trimmed['body'].cut(expected)
        assert added.cut(m.box(-100,100,-100,100,10.,14.)).Volume<.01, 'Material added outside central web'
        assert original['pose'].toMatrix()==trimmed['pose'].toMatrix(), 'PCB moved'
        assert abs(original['lid'].Volume-trimmed['lid'].Volume)<1e-6
        assert len(trimmed['body'].Solids)==1
        assert m.closed_mesh(trimmed['body']).isSolid()
        print('PASS corner setback: precise tip removal, unchanged PCB/cover, connected closed mesh',changes,flush=True)
    rejected(Corner=True,CornerSetback=-1.)
    rejected(Corner=True,CornerSetback=25.)
    rejected(CO2ReliefSize=10.)
    rejected(CO2ReliefClearance=3.)


def check_nut_hoods(p, result):
    # Check the actual vent tools against the protection zone; re-cutting a
    # separately intersected curved shell can produce invalid OCC fragments.
    assert result['nut_vent_keepout'].Volume>1
    assert result['nut_vent_keepout'].common(result['vent_tools']).Volume<.01, 'Vents enter finger-hole reinforcement'
    # At steep angles a pocket can lie entirely inside the chamber, where no
    # protruding hood is needed. The zero-yaw cases have four exposed hoods.
    if p['Yaw']!=0:return
    # Probe actual material outside each pocket, not just the empty cut. These
    # points were missing when the outer taper was smaller than its own cutter.
    wall=p['WallThickness']
    grip_back=result['seam']-6.6
    depth=p['NutAccessDepth']
    t=(depth-3)/(depth+.2)
    inner_radius=(1-t)*p['NutAccessDiameter']/2+t*3.5
    sx=m.W/2+p['SideOverhang']+p['SideClearance']+wall+3
    for sign in (-1,1):
        for y in (p['LowerContactY'],p['UpperContactY']):
            centre=m.V(sign*(sx-depth*(1-t)+inner_radius+wall/2),y,grip_back-3)
            probe=m.Part.makeSphere(.4,result['pose'].multVec(centre))
            assert probe.cut(result['body']).Volume<.001, 'Missing wall around finger pocket'
            blend=wall-1.
            shoulder=m.V(sign*(sx+4.5+blend*.1),y,grip_back+.3+blend*.5)
            probe=m.Part.makeSphere(.03,result['pose'].multVec(shoulder))
            assert probe.cut(result['body']).Volume<.000001, 'Missing tapered screw-boss shoulder'


def check_cable_rim(result):
    assert result['cable_vent_keepout'].common(result['vent_tools']).Volume<.01, 'Vents enter cable/plug reinforcement'
    assert result['rim'].cut(result['body']).Volume<.01, 'Missing material around cable/plug opening'
    assert result['body'].common(result['cable_cut']).Volume<.01, 'Activated cable opening is blocked'
    assert result['body'].common(result['cable_preview']).Volume<.01, 'Actual cable intersects model'


def check_end_rails(result):
    for face in ('rear','front'):
        for sign in (-1,1):
            spans=[(a,b) for f,s,a,b in result['end_contacts'] if (f,s)==(face,sign)]
            assert sum(b-a for a,b in spans)>18, (face,sign,spans)
            shape=result['body' if face=='rear' else 'lid']
            for a,b in spans:
                point=m.V((a+b)/2,sign*(m.H/2-.4),-1 if face=='rear' else m.PCB_T+.4)
                assert shape.isInside(result['pose'].multVec(point),.00001,True), 'End rail missing from printed part'
    doc=m.App.openDocument(str(m.ROOT/'r-pro-1-pcb-reference.FCStd'))
    try:
        for obj in doc.Objects[1:]:
            bb=obj.Mesh.BoundBox
            for rail in result['retention']:
                a=rail.BoundBox
                overlap=(min(a.XMax+m.SOURCE_CENTRE.x,bb.XMax)>max(a.XMin+m.SOURCE_CENTRE.x,bb.XMin)+.001 and
                         min(a.YMax+m.SOURCE_CENTRE.y,bb.YMax)>max(a.YMin+m.SOURCE_CENTRE.y,bb.YMin)+.001 and
                         min(a.ZMax,bb.ZMax)>max(a.ZMin,bb.ZMin)+.001)
                assert not overlap, f'Inspect component at PCB keeper: {obj.Name}'
    finally:
        m.App.closeDocument(doc.Name)


def check_co2_relief(p,result):
    ix=m.W/2+p['SideOverhang']+p['SideClearance']
    notch=result['co2_cut']
    assert notch.common(result['body']).Volume<1e-5, 'CO2 notch blocked'
    local=m.moved(notch,result['pose'].inverse())
    half=p['CO2ReliefSize']/2+p['CO2ReliefClearance']
    assert abs(local.BoundBox.YLength-2*half)<1e-6
    assert abs(local.BoundBox.XMin-(m.CO2_CENTRE.x-half))<1e-6
    assert abs(local.CenterOfMass.y-m.CO2_CENTRE.y)<1e-6
    assert abs(local.BoundBox.XMax-ix)<1e-6, 'CO2 notch stops short of inner wall'
    a,b=local.BoundBox.YMin,local.BoundBox.YMax
    wall=m.box(ix+.1,ix+p['WallThickness']-.1,
               a,b,-1.,1.)
    assert m.moved(wall,result['pose']).cut(result['body']).Volume<.001, 'CO2 relief removed outer wall'
    # No thin strip may remain between the original square and the wall.
    border=m.box(m.CO2_CENTRE.x+half+.01,ix-.01,a+.01,b-.01,-1.9,-.1)
    assert m.moved(border,result['pose']).common(result['body']).Volume<.001


def check_custom_rails_and_hoods():
    for bite in (.8,1.2):
        p=m.defaults(Corner=True,Yaw=-20.,Pitch=15.,RearChamberDepth=1.,CableEnabled=False,EdgeBite=bite)
        result=m.build(p)
        check_end_rails(result)
        check_co2_relief(p,result)
        for sign in (-1,1):
            blob=m.Part.makeSphere(.15,result['pose'].multVec(m.V(sign*18.,33.2,-15.5)))
            assert blob.common(result['body']).Volume<.00001, 'Nut hood protrudes through top wall'
            ceiling=m.Part.makeSphere(.15,result['pose'].multVec(m.V(sign*18.,31.5,-15.5)))
            assert ceiling.cut(result['body']).Volume<.00001, 'Finger pocket removes top wall'
        check_nut_hoods(p,result)
        print('PASS custom flush hoods and four-edge rails, bite',bite,flush=True)


def check_head_recesses(p,result):
    diameter,depth=m.head_recess_dimensions(p)
    if not depth:return
    lid=m.moved(result['lid'],result['pose'].inverse())
    sx=m.W/2+p['SideOverhang']+p['SideClearance']+p['WallThickness']+3
    seat=result['seam']+3.2
    for sign in (-1,1):
        for y in (p['LowerContactY'],p['UpperContactY']):
            head=m.Part.makeCylinder(diameter/2-.001,depth,m.V(sign*sx,y,seat+.001))
            assert head.common(lid).Volume<1e-5, 'Head recess undersized or blocked'
            # Bearing surface and outer rim must remain real connected material.
            for z in (result['seam']+.1,seat-.1,seat+depth-.1):
                probe=m.Part.makeSphere(.05,m.V(sign*(sx+4.2),y,z))
                assert probe.cut(lid).Volume<1e-6, 'Missing screw-seat floor or head rim'
            shaft=m.moved(m.Part.makeCylinder(m.FASTENERS[p['FastenerSize']][0]/2,12,
                                            m.V(sign*sx,y,seat-12)),result['pose'])
            assert shaft.common(result['body']).Volume<1e-5, '12 mm screw hits body'
            assert shaft.common(result['lid']).Volume<1e-5, '12 mm screw hits lid'


def check_head_options():
    off=m.build(m.defaults(CableEnabled=False,ScrewHeadDepth=0.))
    p=m.defaults(CableEnabled=False)
    on=m.build(p)
    check_head_recesses(p,on)
    assert on['pose']==off['pose']
    assert abs(on['body'].Volume-off['body'].Volume)<.001
    assert off['lid'].cut(on['lid']).Volume<.001, 'Head recess removes original screw seat'
    assert on['lid'].Volume>off['lid'].Volume
    p=m.defaults(CableEnabled=False,FastenerSize='M2',ScrewHeadDiameter=4.,ScrewHeadDepth=2.)
    check_head_recesses(p,m.build(p))
    for changes in (dict(ScrewHeadDiameter=7.),dict(ScrewHeadDiameter=4.),dict(ScrewHeadDepth=-1.),dict(ScrewHeadClearance=-.1)):
        rejected(**changes)
    print('PASS head recesses: M3 measured size, configurable M2, disabled, unchanged screw seats and 12 mm shaft clearance',flush=True)


def check_contact_only_openings():
    empty=m.Part.makeCompound([])
    wire=m.Part.makeCylinder(3,30,m.V(0,0,-15))
    clearance=m.box(-10,10,-11,11,-15,15)
    guard=m.box(-13,13,-14,14,-18,18)
    crossed=m.box(-20,20,-20,20,-1,1)
    nearby=m.box(5,7,-20,20,5,9)
    # Nearby geometry, tangent-only contact, and a cable already inside a vent
    # must not acquire a connector-sized hole or reinforcement.
    for stock,vents in ((nearby,empty),(m.box(3,5,-20,20,5,9),empty),
                        (crossed,m.box(-4,4,-4,4,-2,2))):
        cut,rim=m.cable_openings(stock,wire,clearance,guard,vents,empty)
        assert cut.Volume<1e-5 and rim.Volume<1e-5
    stock=m.Part.makeCompound([crossed,nearby])
    cut,rim=m.cable_openings(stock,wire,clearance,guard,empty,empty)
    assert abs(cut.Volume-20*22*2)<.001, 'Crossing must get the full connector opening'
    assert cut.common(nearby).Volume<1e-5, 'One crossing enabled a nearby-only cut'
    assert rim.Volume>cut.Volume
    assert stock.cut(cut).common(wire).Volume<1e-5
    print('PASS cable contact: near miss, tangency, existing vent, full opening, independent walls',flush=True)


def check_cable_disabled():
    p=m.defaults()
    assert p["CableEnabled"] is False
    assert p["RearChamberDepth"] == 10.
    off=m.build(p)
    bad=m.defaults(CableEnabled=False,AutoCableRoute=False,MinBendRadius=1e6,
                   CableHoleWidth=-1.,CableHoleHeight=0.,CableHoleRadius=100.,
                   CableDiameter=-5.,PlugLength=0.,PlugWidth=-3.,PlugHeight=0.,
                   CableTangentLength=0.,CableRimWidth=-1.,CableClearance=-1.,
                   CableEntryX=10000.,CableEntryY=-10000.,CableElevation=1000.)
    ignored=m.build(bad)
    for key in ('body','lid'):
        assert off[key].cut(ignored[key]).Volume<.01 and ignored[key].cut(off[key]).Volume<.01
        m.closed_mesh(off[key])
    assert off['pose']==ignored['pose']
    for key in ('plug','path','passage','cable_preview','cable_cut','cable_vent_keepout','rim'):
        assert not off[key].Vertexes and not ignored[key].Vertexes, key
    assert off['actual_entry_depth']==off['actual_tangent_length']==off['radius']==0.
    check_nut_hoods(p,off)
    with TemporaryDirectory(prefix='apollo-disabled-export-') as folder:
        doc=m.App.newDocument('DisabledExportCheck')
        m.parameters(doc,p)
        # Rebuilding must clear a previously displayed cable, not leave stale geometry.
        doc.addObject('Part::Feature','CablePreview').Shape=m.Part.makeCylinder(3,20)
        m.export(doc,p,off,Path(folder))
        assert not doc.CablePreview.Shape.Vertexes
        m.App.closeDocument(doc.Name)
        doc=m.App.openDocument(str(Path(folder)/'apollo-mount.FCStd'))
        assert not m.read_parameters(doc)['CableEnabled']
        assert not doc.CablePreview.Shape.Vertexes and not doc.PlugClearance.Shape.Vertexes
        m.App.closeDocument(doc.Name)
    rejected(CableEnabled=False,WallThickness=1.)
    rejected(CableEnabled=True,CableHoleWidth=-1.)
    print('PASS cable disabled: all cable inputs ignored, unchanged pose, empty guides/cuts/rim, saved exports, structural checks retained',flush=True)


def check_fasteners():
    for size in m.FASTENERS:
        p=m.defaults(FastenerSize=size,Corner=True,Pitch=15.)
        r=m.build(p)
        flats,depth,hole=m.fastener_dimensions(p)
        assert abs(flats-({'M2':4.4,'M3':5.9}[size]))<1e-8
        for key in ('body','lid'):
            m.closed_mesh(r[key])
        local=m.moved(r['body'],r['pose'].inverse())
        sx=m.W/2+p['SideOverhang']+p['SideClearance']+p['WallThickness']+3
        for sign in (-1,1):
            for y in (p['LowerContactY'],p['UpperContactY']):
                # Gauge the complete nominal pocket, and probe its flat wall
                # beyond the entrance where the finger-access tool ends.
                radius=(flats-.002)/m.math.sqrt(3)
                pts=[m.V(sign*sx+radius*m.math.cos(i*m.math.pi/3),y+radius*m.math.sin(i*m.math.pi/3),r['seam']-6.6+.01) for i in range(7)]
                gauge=m.Part.Face(m.Part.makePolygon(pts)).extrude(m.V(0,0,depth-.02))
                assert gauge.common(local).Volume<1e-5, 'Nut pocket smaller than requested'
                probe=m.V(sign*sx,y+flats/2+.03,r['seam']-6.6+depth/2)
                assert local.isInside(probe,1e-6,True), 'Missing flat nut-pocket wall'
                shaft=m.moved(m.Part.makeCylinder(hole/2-.001,12,m.V(sign*sx,y,r['seam']-7)),r['pose'])
                assert shaft.common(r['body']).Volume<1e-5
                assert shaft.common(r['lid']).Volume<1e-5
        with TemporaryDirectory(prefix='apollo-fastener-test-') as folder:
            doc=m.App.newDocument('FastenerCheck')
            m.parameters(doc,p)
            assert doc.Parameters.getEnumerationsOfProperty('FastenerSize')==['M2','M3']
            m.export(doc,p,r,Path(folder))
            m.App.closeDocument(doc.Name)
            doc=m.App.openDocument(str(Path(folder)/'apollo-mount.FCStd'))
            assert m.read_parameters(doc)==p
            assert abs(doc.Parameters.NutPocketAcrossFlats-flats)<1e-8
            # Migrating a pre-dropdown file preserves all its existing inputs.
            for name in ('FastenerSize','NutClearance','ScrewClearance',
                         'ScrewHeadDiameter','ScrewHeadDepth','ScrewHeadClearance'):
                doc.Parameters.removeProperty(name)
            migrated=m.read_parameters(doc)
            assert migrated==dict(p,FastenerSize='M3',NutClearance=.4,ScrewClearance=.4)
            m.parameters(doc,migrated)
            doc.Parameters.FastenerSize=size
            assert m.read_parameters(doc)['FastenerSize']==size
            m.App.closeDocument(doc.Name)
        print('PASS fastener:',size,'pocket',flats,'depth',depth,'hole',hole,'geometry, dropdown, round-trip, migration',flush=True)
    for changes in (dict(FastenerSize='M4'),dict(FastenerSize='M5'),dict(NutClearance=.7),
                    dict(NutClearance=-.1),dict(NutClearance=float('nan')),dict(ScrewClearance=3.),
                    dict(FastenerSize='M2',NutClearance=.7)):
        rejected(**changes)


if __name__ == "__main__":
    check_corner_setback()
    check_head_options()
    check_custom_rails_and_hoods()
    check_fasteners()
    check_cable_disabled()
    check_contact_only_openings()
    # Routing regressions explicitly enable the now optional cable.
    standard=m.build(m.defaults(CableEnabled=True))
    # The old finger guard left a triangular tab across this top-panel vent,
    # even though no finger pocket intersects this panel.
    tab=m.Part.makeSphere(.08,standard['pose'].multVec(m.V(10.,33.9,-19.5)))
    assert tab.common(standard['body']).Volume<.00001, 'Stray finger-guard tab in flat top vent'
    check_cable_rim(standard)
    print('PASS flat neighbouring vent has no stray pocket tab',flush=True)
    flat=m.build(m.defaults(CableEnabled=True,RearChamberDepth=67.3))
    assert m.defaults()["PlugLength"] == 15.
    start=flat["pose"].inverse().multVec(flat["path"].Vertexes[0].Point)
    assert abs(start.z + m.defaults()["RearHeight"] + 15.) < .001
    no_guide=m.build(m.defaults(CableEnabled=True,RearChamberDepth=67.3,CableGuide=False))
    assert abs(flat["body"].Volume-no_guide["body"].Volume) < .001
    assert "CableGuide" not in m.defaults(CableGuide=True)
    assert flat["cable_preview"].isValid()
    assert flat["cable_preview"].cut(flat["passage"]).Volume < .01
    p=m.defaults()
    aperture=m.Part.Face(m.rectangle(-p['CableHoleWidth']/2,p['CableHoleWidth']/2,
                                    -p['CableHoleHeight']/2,p['CableHoleHeight']/2,0,p['CableHoleRadius']))
    plug_face=m.Part.Face(m.rectangle(-p['PlugWidth']/2,p['PlugWidth']/2,
                                     -p['PlugHeight']/2,p['PlugHeight']/2,0))
    assert plug_face.cut(aperture).Area < .001
    assert sum(isinstance(e.Curve,m.Part.Circle) for e in aperture.Edges)==4
    assert abs(aperture.BoundBox.XLength-20.)<.001
    assert abs(aperture.BoundBox.YLength-22.)<.001
    print('PASS rounded 20 x 22 mm hole clears 17 x 18 mm plug envelope',flush=True)
    check_cable_rim(no_guide)
    check_cable_rim(flat)
    assert flat["rim"].Volume > 0 and no_guide["rim"].Volume > 0
    assert flat["rim"].cut(flat["body"]).Volume < .01
    sharp=m.build(m.defaults(CableEnabled=True,RearChamberDepth=67.3,CornerRadius=0.))
    assert sharp["body"].isValid()
    assert sharp["lid"].Volume > flat["lid"].Volume
    assert any(isinstance(e.Curve,m.Part.Circle) and abs(e.Curve.Radius-2.5)<.001 for e in flat["lid"].Edges)
    assert abs(flat["radius"]-no_guide["radius"]) < .001
    print("PASS display-only cable, legacy guide flag ignored, unobstructed passage",flush=True)
    short=m.build(m.defaults(CableEnabled=True,BoardDistance=30.))
    assert short["actual_entry_depth"] < 0
    assert short["body"].Volume > 0
    for changes in ({},{"RearHeight":20.},{"Pitch":15.},{"Yaw":20.,"Pitch":10.},{"Yaw":20.,"Pitch":20.}):
        p=m.defaults(RearChamberDepth=30.,**changes)
        r=m.build(p)
        neck=-(p["RearHeight"]+p["RearClearance"]+p["WallThickness"])
        assert abs(r["pose"].multVec(m.V(0,0,neck)).z-r["rear_front"]-30.) < .001
    print("PASS 30 mm chamber stays 30 despite module heights/angles",flush=True)
    for corner in (False,True):
        angled=m.build(m.defaults(CableEnabled=True,Yaw=30.,Pitch=30.,MinBendRadius=9.,Corner=corner))
        angled["body"].check(True)
        angled["lid"].check(True)
        assert max(angled['hood_end_exposure'])<.001
        assert angled['body'].common(angled['nut_access']).Volume < .01
        assert angled["contacts"] == flat["contacts"]
        for original,tilted in zip(flat["retention"],angled["retention"]):
            assert original.cut(tilted).Volume < .001
            assert tilted.cut(original).Volume < .001
        check_cable_rim(angled)
        assert angled["rim"].cut(angled["body"]).Volume < .01
        with TemporaryDirectory(prefix="apollo-export-test-") as folder:
            doc=m.App.newDocument("ExportCheck")
            m.parameters(doc,m.defaults(CableEnabled=True,Yaw=30.,Pitch=30.,MinBendRadius=9.,Corner=corner))
            m.export(doc,m.read_parameters(doc),angled,Path(folder))
            assert {f.name for f in Path(folder).iterdir()} == {
                'body.stl', 'lid.stl', 'body.step', 'lid.step',
                'assembly.step', 'apollo-mount.FCStd'}
            exported=m.Part.read(str(Path(folder)/"assembly.step"))
            assert len(exported.Solids)==2
            expected=angled["body"].Volume+angled["lid"].Volume
            assert abs(exported.Volume-expected)<expected*1e-6  # STEP spline round-trip tolerance.
            assert doc.getObject("CablePreview") is not None
            m.App.closeDocument(doc.Name)
    print("PASS 30/30 flat and corner: deformed bay, unchanged PCB holders, clear cable route",flush=True)
    for changes in (
        dict(BoardDistance=80.,CableTangentLength=28.,CableEntryDepth=6.),
        dict(CableEntryDepth=-30.),
        dict(CableEntryY=-8.907,CableEntryDepth=-30.),
        dict(Corner=True,Pitch=15.),
        dict(Corner=True,Pitch=15.,BoardDistance=100.),
        dict(Corner=True,Pitch=20.,Yaw=20.,RearChamberDepth=30.),
        dict(Pitch=30.,Yaw=30.,RearChamberDepth=30.),
        dict(Pitch=0.,Yaw=40.,RearChamberDepth=30.,MinBendRadius=9.),
        dict(Pitch=10.,Yaw=40.,RearChamberDepth=30.),
        dict(Pitch=-10.,Yaw=-40.,RearChamberDepth=30.),
        dict(Yaw=90.,RearChamberDepth=30.),
        dict(Yaw=-90.,RearChamberDepth=30.),
        dict(Corner=True,Pitch=30.,Yaw=30.,RearChamberDepth=30.),
        dict(Yaw=20.,Pitch=10.,BoardDistance=115.,CableGuide=True),
        dict(CableAzimuth=0.,CableEntryX=68.,CableEntryY=-8.907,BoardDistance=100.,CableTangentLength=40.),
        dict(Corner=True,CornerAngle=110.,CableGuide=False),
        dict(CableEntryX=10.,CableEntryY=-70.,CableEntryDepth=25.,CableElevation=-10.,BoardDistance=120.,CableTangentLength=40.),
    ):
        result=m.build(m.defaults(CableEnabled=True,**changes))
        check_head_recesses(m.defaults(CableEnabled=True,**changes),result)
        check_nut_hoods(m.defaults(CableEnabled=True,**changes),result)
        check_cable_rim(result)
        if changes==dict(CableEntryY=-8.907,CableEntryDepth=-30.):
            assert result['cable_cut'].Volume<.001 and result['rim'].Volume<.001, 'Clear rear exit must not create a hole or rim'
        assert abs(result['wall_width']-70.)<.001
        assert abs(result['wall_height']+20.-108.)<.001
        assert min(result['support_lengths'])>=m.defaults(CableEnabled=True,**changes)['NutAccessDepth']
        assert max(result['hood_end_exposure'])<.001
        if changes.get("Yaw") in (20.,30.,40.,90.,-90.):
            result["body"].check(True)
            result["lid"].check(True)
        assert result["radius"] >= m.defaults(CableEnabled=True,**changes)["MinBendRadius"]
        assert result["body"].common(result["cable_cut"]).Volume < .01
        assert result["rim"].cut(result["body"]).Volume < .01
        assert abs(result['pose'].Base.x-m.W/2*m.math.sin(m.math.radians(changes.get('Yaw',0))))<.001
        assert result['body'].common(result['nut_access']).Volume < .01
        mesh=m.MeshPart.meshFromShape(Shape=result['body'],LinearDeflection=.12,AngularDeflection=.15,Relative=False)
        assert mesh.isSolid(),f'Open STL: {changes}'
        print("PASS variant:",changes,flush=True)
    assert sum(b-a for face,side,a,b in flat["contacts"] if face=="rear") > 64  # CO2 square removes 14.6 mm of one rail.
    assert sum(b-a for face,side,a,b in flat["contacts"] if face=="front") > 71
    check_end_rails(flat)
    print("PASS extended rails clear of all supplied component bounds",flush=True)
    doc=m.App.newDocument("LegacyParameterCheck")
    m.parameters(doc,m.defaults(BoardDistance=90.,Pitch=15.))
    doc.Parameters.addProperty("App::PropertyBool","CableGuide")
    doc.Parameters.removeProperty("RearChamberDepth")
    migrated=m.read_parameters(doc)
    assert abs(m.board_distance(migrated)-90.) < .001
    m.parameters(doc,migrated)
    assert "CableGuide" not in doc.Parameters.PropertiesList
    doc.Parameters.RearChamberDepth=30.
    assert abs(m.board_distance(m.read_parameters(doc))-(30+22.7*m.math.cos(m.math.radians(15)))) < .001
    m.App.closeDocument(doc.Name)
    print("PASS legacy file distance migration and new single depth input",flush=True)
    rejected(CableEnabled=True,MinBendRadius=200.)
    rejected(CableEnabled=True,BoardDistance=20.)
    rejected(EdgeBite=4.)
    rejected(RegistrationGap=1.)
    # Depth drives the shape; automatic wall clearance can make even this short
    # requested chamber valid. Do not reintroduce the old arbitrary rejection.
    tiny=m.build(m.defaults(RearChamberDepth=1.,Yaw=40.))
    assert tiny['pose'].Base.z-tiny['rear_front']>m.board_distance(m.defaults(RearChamberDepth=1.,Yaw=40.))
    assert tiny['body'].common(tiny['reserved']).Volume<.01
    print('PASS short chamber uses automatic wall clearance',flush=True)
    rejected(CableEnabled=True,RearChamberDepth=30.,AutoCableRoute=False)
    rejected(CornerRadius=5.)
    rejected(SideVentOffset=-1.)
    rejected(BlackReliefStartY=10.,BlackReliefEndY=5.)
    rejected(CableEnabled=True,CableHoleWidth=12.)
    rejected(CableEnabled=True,CableHoleRadius=10.)
    rejected(CableEnabled=True,CableHoleWidth=17.,CableHoleHeight=18.,CableHoleRadius=3.)
