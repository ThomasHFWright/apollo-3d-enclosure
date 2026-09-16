"""Independent corner movement: python test_wall_offsets.py [saved.FCStd]."""
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import build_mount as m


def check(source):
    doc=m.App.openDocument(str(source))
    saved=m.read_parameters(doc)
    assert saved['Corner'], 'Use a corner document'
    for corner_angle,compact in ((saved['CornerAngle'],True),
                                 (110.,True),
                                 (saved['CornerAngle'],False)):
        p=dict(saved,CornerAngle=corner_angle,CompactCorner=compact)
        base=m.build(p)
        angle=m.math.radians(90-corner_angle/2)
        normals=(m.V(m.math.sin(angle),0,m.math.cos(angle)),
                 m.V(-m.math.sin(angle),0,m.math.cos(angle)))
        for left,right in (((5.,0.),(0.,5.),(5.,5.)) if compact else ((3.,4.),)):
            changed=dict(p,LeftWallOffset=p['LeftWallOffset']+left,
                         RightWallOffset=p['RightWallOffset']+right)
            result=m.build(changed)
            delta=result['pose'].Base-base['pose'].Base
            for normal,expected in zip(normals,(left,right)):
                assert abs(normal.dot(delta)-expected)<1e-6, 'Other-wall clearance changed'
            assert abs(delta.y)<1e-6
            assert result['pose'].Rotation.inverted().multiply(base['pose'].Rotation).Angle<1e-8
            assert abs(result['corner_depth_saving']-base['corner_depth_saving'])<1e-6
            assert result['mount_frame'].cut(base['mount_frame']).Volume<.001
            assert base['mount_frame'].cut(result['mount_frame']).Volume<.001
            old_lid=m.moved(base['lid'],base['pose'].inverse())
            new_lid=m.moved(result['lid'],result['pose'].inverse())
            assert old_lid.cut(new_lid).Volume<.001 and new_lid.cut(old_lid).Volume<.001
            with TemporaryDirectory() as folder:
                m.parameters(doc,changed)
                m.export(doc,changed,result,Path(folder))
                assert m.read_parameters(doc)==changed
            print('PASS independent wall offsets',corner_angle,compact,left,right,flush=True)
    m.App.closeDocument(doc.Name)
    # Flat walls retain their single RearChamberDepth control.
    doc=m.App.openDocument(str(m.ROOT/'output/flat/apollo-mount.FCStd'))
    p=m.read_parameters(doc)
    result=m.build(dict(p,LeftWallOffset=5.,RightWallOffset=7.))
    assert result['body'].cut(doc.Mount.Shape).Volume<.001
    assert doc.Mount.Shape.cut(result['body']).Volume<.001
    assert result['wall_offset'].Length==0
    m.App.closeDocument(doc.Name)
    for key in ('LeftWallOffset','RightWallOffset'):
        for value in (-1.,float('nan'),float('inf')):
            try:m.build(dict(saved,**{key:value}))
            except ValueError:pass
            else:raise AssertionError(f'Accepted invalid {key}: {value}')
    print('PASS flat-wall behaviour and offset validation',flush=True)


if __name__=='__main__':
    check(Path(sys.argv[1]) if len(sys.argv)>1 else m.ROOT/'output/Final-prints/entrance.FCStd')
