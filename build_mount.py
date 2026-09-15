"""Two-part Apollo R PRO-1 enclosure. Run with system Python or Rebuild.FCMacro.

FreeCAD files contain native solids and editable parameters. Rerun the macro
after editing Parameters; exported STL files are oriented for printing.
"""
import argparse
import math
import subprocess
from pathlib import Path
import sys

sys.path.insert(0, "/usr/lib/freecad/lib")
import FreeCAD as App
import Part
import Mesh
import MeshPart

ROOT = Path(__file__).resolve().parent
V = App.Vector
W, H, PCB_T = 44.474688, 56.974716, 1.586157
SOURCE_CENTRE = V(0.025, 23.062045, 0)
# Centre of the CO2 connector body in the supplied PCB mesh (r_pro_1_pcb157).
CO2_CENTRE = V(15.786532, -6.861016, 0)
# DIN 934 ordinary hex nuts: thread diameter, across flats, thickness (mm).
# Larger nuts do not leave sufficient material in the existing 9 mm bosses.
FASTENERS = {"M2": (2., 4., 1.6), "M3": (3., 5.5, 2.4)}
# Edge-intersecting component Y bounds from the supplied component mesh.
EDGE_BANDS = {("rear",-1):[(.79,20.28)], ("rear",1):[],
              ("front",-1):[], ("front",1):[(-11.69,-2.69),(1.88,17.28)]}
# X intervals near the bottom (-1) and top (+1) edges, including parts that
# intersect the maximum allowed 1.2 mm edge bite. Source mesh omits modules.
END_EDGE_BANDS = {("rear",-1):[(-6.025,5.975),(12.602,13.002)],
                  ("rear",1):[(-14.033,-12.433),(-7.975,-4.775)],
                  ("front",-1):[(-6.025,5.975),(11.552,14.053)],
                  ("front",1):[(11.928,13.929)]}
# Values are mm/degrees. Front/rear heights are user measurements; cable and
# cable dimensions are explicitly adjustable starting assumptions.
PARAMETERS = [
    ("Corner", False, "Mount", "Inside-corner base instead of flat wall"),
    ("CompactCorner", False, "Mount", "Experimental: nest the electronics bay into the corner; RearChamberDepth adds forward stand-off"),
    ("CornerAngle", 90., "Mount", "Included angle between the two walls"),
    ("CornerSetback", 10., "Mount", "Trim corner tip forward along the wall-angle bisector to clear rounded plaster; 0 restores the tip; ignored for flat walls"),
    ("CornerSpine", False, "Mount", "Extend flat corner closure continuously from top to bottom; No closes only the end gaps"),
    ("Yaw", 0., "Mount", "Facing angle: positive turns the sensor toward the right"),
    ("Pitch", 0., "Mount", "Positive tilts the sensor downward"),
    ("RearChamberDepth", 10., "Mount", "Mounting-frame front plane to centre of electronics-bay rear rim; excludes the PCB/modules bay"),
    ("FrontHeight", 13.9, "Clearances", "PCB front face to tallest module including pins"),
    ("RearHeight", 16.9, "Clearances", "PCB rear face to PoE socket opening"),
    ("SideOverhang", 1.4, "Clearances", "Reserve measured black-part overhang on both sides"),
    ("TopOverhang", .5, "Clearances", "User reports no top-edge overhang, or less than 0.5 mm"),
    ("SideClearance", 1., "Clearances", "Air/fit gap outside the component outline"),
    ("FrontClearance", 1.5, "Clearances", "Gap above tallest module/pins"),
    ("RearClearance", 3., "Clearances", "Air gap behind rear component envelope"),
    ("BoardSlotGap", .3, "Retention", "Vertical free play above the main PCB; do not preload the board"),
    ("RegistrationGap", .3, "Retention", "Side/end stop clearance; must remain smaller than EdgeBite"),
    ("EdgeBite", .8, "Retention", "How far each keeper overlaps a clear PCB edge"),
    ("EdgeReliefMargin", .8, "Retention", "Extra rail clearance around edge components"),
    ("BlackReliefStartY", 0., "Retention", "Start of additional rear-left rail gap for the black overhang, PCB-centred Y"),
    ("BlackReliefEndY", 21., "Retention", "End of additional rear-left rail gap for the black overhang, PCB-centred Y"),
    ("CO2ReliefSize", 13., "Retention", "Square centred on the CO2 connector; 13 mm reaches the PCB edge; daughterboard size provisional"),
    ("CO2ReliefClearance", .8, "Retention", "Extra space on EACH side of the square CO2 holder notch"),
    ("LowerContactY", -20.062, "Retention", "Lower cover screw pair relative to board centre"),
    ("UpperContactY", 21.938, "Retention", "Upper cover screw pair relative to board centre"),
    ("FastenerSize", "M3", "Retention", "Matched bolt holes and ordinary hex nuts; M4/M5 do not fit the existing housings"),
    ("NutClearance", .4, "Retention", "TOTAL extra nut-pocket width across flats, not per side; M3 + 0.4 = 5.9 mm"),
    ("ScrewClearance", .4, "Retention", "TOTAL extra diameter of the unthreaded bolt holes"),
    ("ScrewHeadDiameter", 5.3, "Retention", "Measured bolt-head diameter; independent of FastenerSize"),
    ("ScrewHeadDepth", 2.8, "Retention", "Measured bolt-head height; 0 disables head recesses"),
    ("ScrewHeadClearance", .4, "Retention", "TOTAL added head-hole diameter; half this value is added to recess depth"),
    ("NutAccessDiameter", 18., "Retention", "Nominal finger space; flattened at top/bottom to preserve wall thickness; insert nuts before PCB"),
    ("NutAccessDepth", 12., "Retention", "Depth of the inward-sloping finger pocket behind each nut seat"),
    ("WallThickness", 2.8, "Printing", "Structural cage/perimeter wall thickness"),
    ("FrontSkin", 1.2, "Printing", "Uniform radar-facing cover thickness; RF performance requires testing"),
    ("CornerRadius", 2.5, "Printing", "Rounded outer corners on body and cover; 0 disables, maximum WallThickness"),
    ("VentSlot", 6., "Printing", "Width of ventilation slots, separated by structural ribs"),
    ("VentRib", 3., "Printing", "Material between ventilation slots"),
    ("SideVentOffset", 4., "Printing", "Move side-wall slots upward to strengthen the lower edge"),
    ("CableEnabled", False, "Cable", "Enable cable preview, routing checks, connector cutouts and reinforcement; No skips all cable processing"),
    ("PortX", -.025, "Cable", "Socket aperture centre, from source mesh cross-section"),
    ("PortY", -8.907, "Cable", "Socket aperture centre, from source mesh cross-section"),
    ("PlugWidth", 17., "Cable", "PROVISIONAL plug/boot clearance width"),
    ("PlugHeight", 18., "Cable", "PROVISIONAL plug/boot/latch clearance height"),
    ("PlugLength", 15., "Cable", "Socket opening to start of flexible cable; include actual plug/boot protrusion"),
    ("CableDiameter", 6., "Cable", "Actual cable outside diameter"),
    ("CableClearance", .8, "Cable", "Radial free clearance around cable"),
    ("CableHoleWidth", 20., "Cable", "Clear width of rounded rectangular plug-through passage; include boot and print clearance"),
    ("CableHoleHeight", 22., "Cable", "Clear height of plug-through passage; include latch/boot and print clearance"),
    ("CableHoleRadius", 3., "Cable", "Corner radius of plug-through passage"),
    ("CableEntryX", 0., "Cable", "Cable entry X in fixed mounting-frame coordinates"),
    ("CableEntryY", -68., "Cable", "Cable entry Y in fixed mounting-frame coordinates"),
    ("CableEntryDepth", 8., "Cable", "Preferred entry depth ahead of rear frame; AutoCableRoute may move it backward"),
    ("AutoCableRoute", True, "Cable", "Move cable entry rearward and extend tangent if needed, preserving entry X/Y and direction"),
    ("CableAzimuth", -90., "Cable", "Outgoing direction toward cable entry: 0 right, 90 up, -90 down"),
    ("CableElevation", 0., "Cable", "Outgoing direction: 0 parallel to wall, positive toward room"),
    ("CableTangentLength", 34., "Cable", "Bezier handle length; increase space if bend-radius check fails"),
    ("MinBendRadius", 20., "Cable", "Minimum cable centreline bend radius; use cable maker's requirement"),
    ("CableRimWidth", 3., "Cable", "Solid margin around cable cuts, including across ventilation slots"),
]


def defaults(**changes):
    p=dict([(name, value) for name, value, _, _ in PARAMETERS], **changes)
    # Preserve callers using the previous PCB-distance input; new UI has one driver.
    if "BoardDistance" in changes:
        if "RearChamberDepth" in changes:
            raise ValueError("Specify RearChamberDepth, not both distance inputs")
        p["RearChamberDepth"] += p.pop("BoardDistance")-board_distance(p)
    if "CornerChamfer" in changes:
        p["CornerRadius"]=p.pop("CornerChamfer")
    p.pop("CableGuide",None)  # Legacy files/callers: the cable is now reference-only.
    return p


def board_distance(p):
    bay=p["RearHeight"]+p["RearClearance"]+p["WallThickness"]
    return p["RearChamberDepth"]+bay*math.cos(math.radians(p["Yaw"]))*math.cos(math.radians(p["Pitch"]))


def fastener_dimensions(p):
    size=p.get("FastenerSize", "M3")
    if size not in FASTENERS:
        raise ValueError("FastenerSize must be M2 or M3; M4/M5 need larger screw housings")
    diameter,flats,thickness=FASTENERS[size]
    clearance=p.get("NutClearance", .4)
    screw_clearance=p.get("ScrewClearance", .4)
    if not math.isfinite(clearance) or clearance < 0 or not math.isfinite(screw_clearance) or screw_clearance < .1:
        raise ValueError("NutClearance must be nonnegative and ScrewClearance at least 0.1 mm")
    pocket=flats+clearance
    hole=diameter+screw_clearance
    # Keep at least 1 mm outside the hex vertices and 0.8 mm of nut bearing
    # land per side; the nut must also fit through the 7 mm access throat.
    if pocket >= 2*flats/math.sqrt(3):
        raise ValueError("NutClearance is too large to stop the hex nut turning")
    if pocket/math.sqrt(3) > 3.5 or hole > flats-1.6:
        raise ValueError("Fastener clearance leaves insufficient boss wall or nut bearing surface")
    return pocket, thickness+.5, hole


def read_parameters(doc):
    p={name:getattr(doc.Parameters,name,default) for name,default,_,_ in PARAMETERS}
    if "RearChamberDepth" not in doc.Parameters.PropertiesList:
        p["RearChamberDepth"] += doc.Parameters.BoardDistance-board_distance(p)
    if "CornerRadius" not in doc.Parameters.PropertiesList and "CornerChamfer" in doc.Parameters.PropertiesList:
        p["CornerRadius"]=doc.Parameters.CornerChamfer
    return p


def head_recess_dimensions(p):
    diameter,depth,clearance=(p[name] for name in ('ScrewHeadDiameter','ScrewHeadDepth','ScrewHeadClearance'))
    if not all(math.isfinite(v) for v in (diameter,depth,clearance)) or depth<0 or clearance<0:
        raise ValueError('Screw head dimensions must be finite; depth and clearance must be nonnegative')
    if depth==0:return 0.,0.
    hole=fastener_dimensions(p)[2]
    if diameter<hole+1.6 or diameter+clearance>6.6:
        raise ValueError('Screw head must leave 0.8 mm bearing land and 1.2 mm wall in the 9 mm boss; adjust head diameter/clearance')
    return diameter+clearance,depth+clearance/2


def box(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1-x0, y1-y0, z1-z0, V(x0, y0, z0))


def rectangle(x0, x1, y0, y1, z, radius=0):
    if radius:
        r=radius
        arcs=[Part.ArcOfCircle(Part.Circle(V(x,y,z),V(0,0,1),r),a,a+math.pi/2).toShape()
              for x,y,a in ((x1-r,y0+r,-math.pi/2),(x1-r,y1-r,0),
                            (x0+r,y1-r,math.pi/2),(x0+r,y0+r,math.pi))]
        edges=[]
        for i,arc in enumerate(arcs):
            edges.extend([Part.makeLine(arcs[i-1].Vertexes[-1].Point,arc.Vertexes[0].Point),arc])
        return Part.Wire(edges)
    return Part.makePolygon([V(x0,y0,z), V(x1,y0,z), V(x1,y1,z), V(x0,y1,z), V(x0,y0,z)])


def solid_loft(wires):
    """Planar wall triangles avoid twisted-face failures; corners retain true arcs."""
    bottom=Part.Face(wires[0])
    bottom.reverse()
    faces=[bottom,Part.Face(wires[-1])]
    for lower,upper in zip(wires,wires[1:]):
        for a,b in zip(lower.OrderedEdges,upper.OrderedEdges):
            if isinstance(a.Curve,Part.Line):
                x,y=a.Vertexes[0].Point,a.Vertexes[-1].Point
                z,w=b.Vertexes[0].Point,b.Vertexes[-1].Point
                faces.extend([Part.Face(Part.makePolygon([x,y,w,x])),Part.Face(Part.makePolygon([x,w,z,x]))])
            else:
                faces.extend(Part.makeRuledSurface(a,b).Faces)
    solid=Part.makeSolid(Part.makeShell(faces))
    if solid.Volume<0:
        solid.reverse()
    return solid


def circle(radius,centre):
    return Part.Wire([Part.makeCircle(radius,centre)])


def convex_envelope(points):
    """Smallest convex chamber around the mounting rim and module clearances."""
    data='3\n'+str(len(points))+'\n'+'\n'.join(f'{v.x} {v.y} {v.z}' for v in points)
    facets=subprocess.run(['qconvex','Qt','i'],input=data,text=True,capture_output=True,check=True).stdout.splitlines()[1:]
    centre=sum(points,V())/len(points)
    faces=[]
    for facet in facets:
        a,b,c=[points[int(i)] for i in facet.split()]
        if (b-a).cross(c-a).dot(a-centre)<0:b,c=c,b
        faces.append(Part.Face(Part.makePolygon([a,b,c,a])))
    return Part.makeSolid(Part.makeShell(faces)).removeSplitter()


def closed_mesh(shape):
    mesh=MeshPart.meshFromShape(Shape=shape,LinearDeflection=.12,AngularDeflection=.15,Relative=False)
    if not mesh.isSolid():raise ValueError('Shape cannot produce a closed STL')
    return mesh


def moved(shape, placement):
    result = shape.copy()
    result.Placement = placement.multiply(result.Placement)
    return result


def fuse(shapes):
    return shapes[0].multiFuse(shapes[1:]) if len(shapes)>1 else shapes[0]


def valid(shape, label):
    if not shape.isValid() or len(shape.Solids) != 1 or shape.Volume <= 0:
        raise ValueError(f"{label}: expected one valid connected solid (valid={shape.isValid()}, solid volumes={[round(s.Volume,3) for s in shape.Solids]})")


def rail_spans(p,face,sign,axis="y"):
    length=H if axis=="y" else W
    low,high=-length/2+3,length/2-3  # Stay off the PCB's rounded corners.
    blocked=list((EDGE_BANDS if axis=="y" else END_EDGE_BANDS)[face,sign])
    # Wider edge bites also reach these components on the existing side rails.
    if axis=="y":
        nearby={('front',1):[(21.094,20.72,26.12)],
                ('front',-1):[(21.144,20.72,26.12),(21.139,-16.363,-7.663)],
                ('rear',-1):[(21.265,-12.425,-.425),(21.357,-24.705,-23.705),(21.282,-14.239,-13.239)]}
        blocked.extend((a,b) for x,a,b in nearby.get((face,sign),[]) if W/2-p['EdgeBite']<x+.001)
    if axis=="y" and (face,sign)==("rear",-1):
        blocked.append((p["BlackReliefStartY"],p["BlackReliefEndY"]))
    spans=[]
    for a,b in sorted(blocked):
        a=max(-length/2+3,a-p["EdgeReliefMargin"])
        b=min(high,b+p["EdgeReliefMargin"])
        if a-low >= 3:
            spans.append((low,min(a,high)))
        low=max(low,b)
    if high-low >= 3:
        spans.append((low,high))
    return spans


def cable_openings(stock, wire, clearance, guard, vents, other_cuts):
    """Only enlarge openings where the actual cable hits remaining material."""
    hits=wire.common(stock).cut(vents).cut(other_cuts)
    openings=[s for s in clearance.common(stock).Solids if s.common(hits).Volume>1e-5]
    cut=Part.makeCompound(openings)
    # Gate each disconnected intersection, not the whole route: a real crossing
    # of one wall must not enable a proximity-only cut in another wall.
    rings=[s for s in guard.common(stock).Solids if s.common(cut).Volume>1e-5] if openings else []
    return cut,Part.makeCompound(rings)


def build(p):
    nut_flats,nut_depth,screw_hole=fastener_dimensions(p)
    head_diameter,head_depth=head_recess_dimensions(p)
    cable_enabled=p.get('CableEnabled',False)
    ignored={name for name,_,group,_ in PARAMETERS if group=='Cable'} if not cable_enabled else set()
    for key, value in p.items():
        if key not in ignored and key != "FastenerSize" and not isinstance(value, bool) and not math.isfinite(value):
            raise ValueError(f"{key} must be finite")
    for key in ("RearChamberDepth", "FrontHeight", "RearHeight", "SideClearance", "FrontClearance",
                "RearClearance", "BoardSlotGap", "RegistrationGap", "EdgeReliefMargin", "WallThickness", "FrontSkin",
                "VentSlot", "VentRib", "PlugWidth", "PlugHeight", "PlugLength", "CableDiameter",
                "CableClearance", "CableTangentLength", "MinBendRadius", "CableRimWidth",
                "CableHoleWidth", "CableHoleHeight", "NutAccessDiameter", "NutAccessDepth"):
        if key not in ignored and p[key] <= 0:
            raise ValueError(f"{key} must be positive")
    if not 60 <= p["CornerAngle"] <= 150 or abs(p["Yaw"]) > 90 or abs(p["Pitch"]) > 40:
        raise ValueError("Supported geometry: corner angle 60..150 degrees, yaw -90..90, pitch -40..40")
    if not 0 < p["EdgeBite"] <= 1.2 or p["TopOverhang"] < 0 or p["SideOverhang"] < 0:
        raise ValueError("EdgeBite must be 0..1.2 mm; overhangs cannot be negative")
    if p["RegistrationGap"] >= p["EdgeBite"]:
        raise ValueError("RegistrationGap must be smaller than EdgeBite so the board cannot slide off its ledges")
    if not -H/2 <= p["BlackReliefStartY"] < p["BlackReliefEndY"] <= H/2:
        raise ValueError("Black-part rail relief must be an ordered interval within the PCB height")
    if p["WallThickness"] < 2.4 or p["VentRib"] < 2.4 or p["FrontSkin"] < .8:
        raise ValueError("Minimum walls/ribs 2.4 mm; minimum front skin 0.8 mm")
    if not 0 <= p["CornerRadius"] <= p["WallThickness"]:
        raise ValueError("CornerRadius must be between 0 and WallThickness")
    if not 0 <= p["SideVentOffset"] <= 10:
        raise ValueError("SideVentOffset must be between 0 and 10 mm")
    if cable_enabled:
        hw,hh=p["CableHoleWidth"]/2,p["CableHoleHeight"]/2
        hr=p["CableHoleRadius"]
        if not 0 <= hr < min(hw,hh):
            raise ValueError("CableHoleRadius must be nonnegative and smaller than half the hole width/height")
        if min(hw,hh) < p["CableDiameter"]/2+p["CableClearance"]:
            raise ValueError("Cable hole must contain the cable and its clearance")
        # Rounded corners must also clear the full provisional rectangular boot.
        x,y=p["PlugWidth"]/2,p["PlugHeight"]/2
        if x>hw or y>hh or (max(0,x-hw+hr)**2+max(0,y-hh+hr)**2 > hr**2+.000001):
            raise ValueError("Cable hole rounded corners clip PlugWidth/PlugHeight; enlarge the hole or reduce its corner radius")
    c, wall = p["SideClearance"], p["WallThickness"]
    ix = W/2 + p["SideOverhang"] + c
    iy0, iy1 = -H/2-c, H/2+p["TopOverhang"]+c
    ox, oy0, oy1 = ix+wall, iy0-wall, iy1+wall
    seam = PCB_T + 1.
    grip_back=seam-6.6  # Rigid PCB holder: ledges, stops and all four screw bosses.
    half=p['CO2ReliefSize']/2+p['CO2ReliefClearance']
    if p['CO2ReliefSize']<2*(W/2-CO2_CENTRE.x) or p['CO2ReliefClearance']<0:
        raise ValueError('CO2ReliefSize must reach the PCB edge (at least 12.902 mm); clearance cannot be negative')
    if CO2_CENTRE.x+half>ix or abs(CO2_CENTRE.y)+half>H/2-3:
        raise ValueError('CO2 square clearance would remove the outer wall or a PCB corner; reduce its size/clearance')
    # Extend the connector-centred square through the rail to the inner wall.
    co2_local=box(CO2_CENTRE.x-half,ix,
                  CO2_CENTRE.y-half,CO2_CENTRE.y+half,grip_back-.01,seam+.01)
    ceiling = PCB_T+p["FrontHeight"]+p["FrontClearance"]
    bw, bh, plate = max(70., 2*ox+12), max(88., oy1-oy0+12), 4.
    angle = 90-p["CornerAngle"]/2 if p["Corner"] else 0.
    rotation = App.Rotation(V(0,1,0), p['Yaw']).multiply(App.Rotation(V(1,0,0), p["Pitch"]))
    neck = -p["RearHeight"]-p["RearClearance"]-wall
    wall_normals=[App.Rotation(V(0,1,0),a).multVec(V(0,0,1)) for a in (-angle,angle)]
    wall_voids=[moved(box(-500,500,-500,500,-500,0),App.Placement(V(),App.Rotation(V(0,1,0),a)))
                for a in sorted(set((-angle,angle)))]
    # Include the screw bosses outside the PCB outline, not empty chamber space.
    rigid_points=[rotation.multVec(V(x,y,z)) for x in (-ox-7.5,ox+7.5)
                  for y in (oy0,oy1) for z in (neck,max(ceiling+p['FrontSkin'],seam+3.2+head_depth))]
    nut_access=[]
    for sign in (-1,1):
        for y in (p['LowerContactY'],p['UpperContactY']):
            sx=sign*(ox+3)
            pocket=Part.makeLoft([circle(p['NutAccessDiameter']/2,V(sx-sign*p['NutAccessDepth'],y,grip_back-p['NutAccessDepth'])),
                                 circle(3.5,V(sx,y,grip_back+.2))],True,True)
            # Keep the top/bottom panel thickness when the circular pocket
            # approaches an enclosure edge; do not require an external bulge.
            nut_access.append(pocket.common(box(-500,500,iy0,iy1,-500,500)))
    # The plate never grows with angle. The convex chamber is free to overhang
    # it, just like the PCB and cover; only actual wall clearance moves the PCB.
    rear_z=bw/2*math.tan(math.radians(angle)) if p['Corner'] else 0.
    if p['Corner']:
        # Retain a full wall thickness behind each wall-screw countersink.
        limit=rear_z*.65-(4.5+wall)*math.sin(math.radians(angle))
        if not 0 <= p['CornerSetback'] <= limit:
            raise ValueError(f"CornerSetback must be 0..{limit:.2f} mm to retain material around wall screws")
    rear_front=rear_z+plate
    centre=V(W/2*math.sin(math.radians(p['Yaw'])),0,rear_front+board_distance(p))
    for n in wall_normals:
        centre.z+=max(0.,max(plate+wall-n.dot(centre+q) for q in rigid_points)/n.z)
    original_centre=V(centre)
    compact=p['Corner'] and p.get('CompactCorner',False)
    if compact:
        # Separate the shallow screw housings from the taller cover and rear bay.
        envelope=[box(-ox,ox,oy0,oy1,neck,ceiling+p['FrontSkin'])]
        envelope += [Part.makeCylinder(4.5,6.5+3.2+head_depth,V(sign*(ox+3),y,seam-6.5))
                     for sign in (-1,1) for y in (p['LowerContactY'],p['UpperContactY'])]
        # Cable-off retains its existing meaning: no plug/routing constraints.
        if cable_enabled:
            envelope.append(box(p['PortX']-p['PlugWidth']/2,p['PortX']+p['PlugWidth']/2,
                                p['PortY']-p['PlugHeight']/2,p['PortY']+p['PlugHeight']/2,
                                -p['RearHeight']-p['PlugLength'], -p['RearHeight']))
        # Project exact cylinder/box bounds in each wall-normal direction.
        limits=[]
        for n in wall_normals:
            projection=App.Placement(V(),App.Rotation(n,V(0,0,1)).multiply(rotation))
            low=min(moved(shape,projection).BoundBox.ZMin for shape in envelope)
            limits.append(plate+wall-low)
        a,b=wall_normals
        centre.x=(limits[0]-limits[1])/(a.x-b.x)
        centre.z=(limits[0]-a.x*centre.x)/a.z+p['RearChamberDepth']
    pose=App.Placement(centre,rotation)
    local=lambda s:moved(s,pose)
    points=[V(x,y,rear_z-1) for x in (-bw/2+plate,bw/2-plate) for y in (-bh/2+plate,bh/2-plate)]
    points += [pose.multVec(V(x,y,z)) for x in (-ix,ix) for y in (iy0,iy1)
               for z in (-p['RearHeight']-p['RearClearance'],seam+1)]
    if compact:
        # Use the hollow corner behind the old flat mounting-frame plane.
        back=max(p['CornerSetback']+plate+wall,(plate+wall)/wall_normals[0].z+.1)
        reach=(back-(plate+wall)/wall_normals[0].z)/math.tan(math.radians(angle))
        points += [V(x,y,back) for x in (-reach,reach) for y in (-bh/2+plate,bh/2-plate)]
        if cable_enabled:
            points += [pose.multVec(v.Point) for v in envelope[-1].Vertexes]
    inner=convex_envelope(points)
    # Offset planar walls, then round the outside. This keeps real circular
    # corners without forcing all chamber sections to have matching rectangles.
    radius=p['CornerRadius']
    padding=wall-radius
    outer=convex_envelope([v.Point+V(x,y,z) for v in inner.Vertexes
                          for x in (-padding,padding) for y in (-padding,padding) for z in (-padding,padding)]) if padding else inner.copy()
    # Shallow hull joints (e.g. yaw 40 / pitch 10) collapse at 0.001 mm
    # approximation tolerance. Preserve their small arcs at kernel precision.
    if radius:outer=outer.makeOffsetShape(radius,1e-7,join=0)
    front_cut=local(box(-500,500,-500,500,seam,500))
    def rear_clip(shape):
        if compact:
            return shape.cut(Part.makeCompound(wall_voids)).common(box(-500,500,-500,500,p['CornerSetback'],500))
        return shape.common(box(-500,500,-500,500,rear_z,500))
    outer=rear_clip(outer.cut(front_cut))
    mount_y = bh/2+10  # Exposed mounting ears keep wall-screw access outside the cage.
    chamber_faces=inner.Faces
    hoods=[]
    hood_guards=[]
    support_lengths=[]
    hood_end_exposure=[]
    for sign in (-1,1):
        for y in (p['LowerContactY'],p['UpperContactY']):
            sx=sign*(ox+3)
            length=p['NutAccessDepth']
            radius=p['NutAccessDiameter']/2+wall
            slope=(radius-3.5-wall)/(length+.3)
            # Roll the foot inward until its end is buried in the enclosure,
            # rather than leaving a raised circular cap at the finger depth.
            for extension in range(61):
                end=circle(max(1.,radius-extension),
                           V(sx-sign*length*(1+extension/(length+.3)),y,grip_back-length-extension))
                cap=local(Part.Face(end))
                if cap.cut(outer).Area<.001:break
            else:
                raise ValueError('Nut hood cannot meet enclosure within 60 mm; adjust nut access size/depth')
            support_lengths.append(length+extension)
            hood_end_exposure.append(cap.cut(outer).Area)
            # Follow the finger cutter with a real wall; a smaller outer taper
            # is consumed by the pocket and leaves bare holes through the vents.
            blend=wall-1.
            profiles=[circle(radius,V(sx-sign*length,y,grip_back-length)),
                      circle(3.5+wall,V(sx,y,grip_back+.3)),
                      circle(4.5,V(sx,y,grip_back+.3+blend))]
            hood=Part.makeLoft(profiles,True,True)
            if extension:
                # Curve only the short foot, not the whole hood: a global
                # smooth loft through a nearby third ring balloons the body.
                tail=[]
                for t in (1.,2/3,1/3,0.):
                    r=(2*t**3-3*t**2+1)*radius+(t**3-2*t**2+t)*extension*slope
                    r+=(-2*t**3+3*t**2)*max(1.,radius-extension)
                    tail.append(circle(r,V(sx-sign*length*(1+t*extension/(length+.3)),y,grip_back-length-t*extension)))
                hood=hood.fuse(Part.makeLoft(tail,True,False))
            # Broad circular hood bases used to poke through the neighbouring
            # top panel as two oval bumps. Match the pocket's flat end limits.
            hood=local(hood.common(box(-500,500,oy0,oy1,-500,500)))
            hoods.append(rear_clip(hood).cut(Part.makeCompound(wall_voids)))
            # Extend only the vent keep-out behind the access mouth, leaving
            # a rim in the chamber wall rather than a slot touching its edge.
            guard_extension=extension+wall
            guard=Part.makeLoft([
                circle(radius+slope*guard_extension,V(sx-sign*length*(1+guard_extension/(length+.3)),y,grip_back-length-guard_extension)),
                profiles[1],profiles[2]],True,True)
            hood_guards.append(local(guard))
    outer=outer.multiFuse(hoods)
    nut_access_shape=local(Part.makeCompound(nut_access))
    # At steep angles the convex cavity can be wider than the PCB rim. Close
    # that excess locally so the unchanged holder joins a full collar, rather
    # than touching the chamber at isolated edges.
    inner=inner.cut(local(box(-500,500,-500,500,grip_back,500)))
    inner=inner.fuse(local(box(-ix,ix,iy0,iy1,grip_back-.1,seam+1)))
    body = outer.cut(inner)
    body.check(True)
    holder=Part.Face(rectangle(-ox,ox,oy0,oy1,grip_back,p['CornerRadius'])).extrude(V(0,0,seam-grip_back))
    holder=holder.cut(box(-ix,ix,iy0,iy1,grip_back-1,seam+1))
    # A pocket's enlarged guard must not leave tabs on neighbouring panels
    # that the pocket never pierces. Vents only cut within these panel slabs.
    pocket_panels=[]
    for guard,access in zip(hood_guards,nut_access):
        panels=[]
        for face in chamber_faces:
            panel=face.extrude(face.normalAt(0,0)*(wall+2))
            if panel.common(local(access)).Volume>.001:
                panels.append(panel)
        if panels:pocket_panels.append(guard.common(Part.makeCompound(panels)))
    vent_protected=Part.makeCompound(pocket_panels+[local(holder)])
    # Inset each actual chamber face, then cut parallel slots through that face
    # only. The same margins work on trapezoids and the short end panels at 90°.
    vents=[]
    for face in chamber_faces:
        if all(abs(v.Point.z-rear_z+1)<1e-5 for v in face.Vertexes):continue
        if all(abs(pose.inverse().multVec(v.Point).z-seam-1)<1e-5 for v in face.Vertexes):continue
        normal=face.normalAt(0,0)
        vertical=V(0,1,0) if abs(normal.y)<.8 else V(1,0,0)
        vertical=(vertical-normal*normal.dot(vertical)).normalize()
        horizontal=vertical.cross(normal).normalize()
        placement=App.Placement(face.CenterOfMass,App.Rotation(horizontal,vertical,normal,'ZXY'))
        flat=moved(face,placement.inverse())
        try:
            inset=flat.makeOffset2D(-8)
            if not inset.Faces or inset.Area< p['VentSlot']*p['VentRib']:continue
        except Exception:continue  # A panel too small to inset remains solid.
        region=inset.extrude(V(0,0,wall+2))
        bounds=inset.BoundBox
        y=bounds.YMin+(p['SideVentOffset'] if abs(normal.y)<.8 else 0)
        while y+p['VentSlot']<=bounds.YMax:
            tool=region.common(box(bounds.XMin-1,bounds.XMax+1,y,y+p['VentSlot'],-1,wall+3))
            if tool.Volume>1:
                vents.append(moved(tool,placement))
            y+=p['VentSlot']+p['VentRib']
    rear_vents=bool(vents)
    all_vents=Part.makeCompound(vents).cut(vent_protected)

    screws = []
    if p["Corner"]:
        bases = []
        length = bw/2/math.cos(math.radians(angle))
        for sign in (-1,1):
            transform = App.Placement(V(),App.Rotation(V(0,1,0),-sign*angle))
            x0,x1 = sorted((0,sign*length))
            slab = box(x0,x1,-mount_y,mount_y,0,plate)
            opening = box(x0+8,x1-8,-bh/2+6,bh/2-6,-1,plate+1)
            bases.append(moved(slab.cut(opening),transform))
            for y in (-mount_y+5,mount_y-5):
                x=sign*length*.65
                screws.append(moved(Part.makeCylinder(2.3,plate+2,V(x,y,-1)),transform))
                screws.append(moved(Part.makeCone(2.3,4.5,2.2,V(x,y,plate-2.1)),transform))
        for y in (-bh/2,bh/2-plate):
            triangle=Part.makePolygon([V(-bw/2,y,rear_z),V(0,y,0),V(bw/2,y,rear_z),V(-bw/2,y,rear_z)])
            bases.append(Part.Face(triangle).extrude(V(0,plate,0)))
        base=fuse(bases)
        if p['CornerSetback']:
            base=base.cut(box(-500,500,-500,500,-500,p['CornerSetback']))
            # Close the trimmed V at its ends, optionally along the full height.
            # Clip its ends to the original wall planes so clearance is retained.
            depth=p['CornerSetback']
            reach=(depth+plate)/math.tan(math.radians(angle))
            spine=box(-reach,reach,-mount_y,mount_y,depth,depth+plate)
            spine=spine.cut(Part.makeCompound(wall_voids))
            if not p['CornerSpine']:
                spine=spine.cut(box(-500,500,-bh/2+plate,bh/2-plate,-500,500))
            base=base.fuse(spine)
    else:
        base=box(-bw/2,bw/2,-mount_y,mount_y,0,plate).cut(box(-bw/2+8,bw/2-8,-bh/2+6,bh/2-6,-1,plate+1))
        for x in (-bw/2+5,bw/2-5):
            for y in (-mount_y+5,mount_y-5):
                screws += [Part.makeCylinder(2.3,6,V(x,y,-1)),Part.makeCone(2.3,4.5,2.2,V(x,y,1.9))]
    body=fuse([body,base]).cut(fuse(screws))
    if local(holder).cut(nut_access_shape).cut(body).Volume>.01:
        raise ValueError('Chamber does not fully support the rigid PCB rim')

    # Thin front skin, vented skirt, and long PCB keeper rails on the cover.
    lid=Part.Face(rectangle(-ox,ox,oy0,oy1,seam,p["CornerRadius"])).extrude(V(0,0,ceiling+p["FrontSkin"]-seam))
    lid=lid.cut(box(-ix,ix,iy0,iy1,seam-1,ceiling))
    lidvents=[]
    y=iy0+6
    while y+4 < iy1-6:
        lidvents.append(box(-ox-1,ox+1,y,y+4,seam+3,ceiling-3))
        y+=8
    x=-ix+6
    while x+4 < ix-6:
        lidvents.append(box(x,x+4,oy0-1,oy1+1,seam+3,ceiling-3))
        x+=8
    lid=lid.cut(Part.makeCompound(lidvents))
    feet, keepers, reliefs, body_bosses, lid_bosses, holes, nutcuts = [],[],[],[],[],[],[]
    headcuts=[]
    contacts=[]
    end_contacts=[]
    for sign in (-1,1):
        a,b=sorted((sign*(W/2-p["EdgeBite"]),sign*(ox+.1)))
        tip_a,tip_b=sorted((sign*(W/2-p["EdgeBite"]),sign*(W/2+.1)))
        stop_a,stop_b=sorted((sign*(W/2+p["RegistrationGap"]),sign*(ox+.1)))
        for y0,y1 in rail_spans(p,"rear",sign):
            feet.extend([box(a,b,y0,y1,-2.,0.),box(stop_a,stop_b,y0,y1,-2.,seam)])
            reliefs.extend([box(a,b,y0-.1,y1+.1,-3,.01),box(stop_a,stop_b,y0-.1,y1+.1,-3,seam+.1)])
            spans=[(y0,y1)] if sign<0 else [(y0,min(y1,CO2_CENTRE.y-half)),(max(y0,CO2_CENTRE.y+half),y1)]
            contacts.extend(("rear",sign,a,b) for a,b in spans if b>a)
        for y0,y1 in rail_spans(p,"front",sign):
            keepers.extend([box(a,b,y0,y1,seam,seam+wall),box(tip_a,tip_b,y0,y1,PCB_T+p["BoardSlotGap"],seam+.1)])
            reliefs.append(box(a,b,y0-.1,y1+.1,PCB_T+p["BoardSlotGap"]-.01,seam+wall+.1))
            contacts.append(("front",sign,y0,y1))
    for sign in (-1,1):
        outside=oy0-.1 if sign<0 else oy1+.1
        a,b=sorted((sign*(H/2-p["EdgeBite"]),outside))
        tip_a,tip_b=sorted((sign*(H/2-p["EdgeBite"]),sign*(H/2+.1)))
        stop_a,stop_b=sorted((sign*(H/2+p["RegistrationGap"]),outside))
        for x0,x1 in rail_spans(p,"rear",sign,axis="x"):
            feet.extend([box(x0,x1,a,b,-2.,0.),box(x0,x1,stop_a,stop_b,-2.,seam)])
            reliefs.extend([box(x0-.1,x1+.1,a,b,-3,.01),box(x0-.1,x1+.1,stop_a,stop_b,-3,seam+.1)])
            end_contacts.append(("rear",sign,x0,x1))
        for x0,x1 in rail_spans(p,"front",sign,axis="x"):
            keepers.extend([box(x0,x1,a,b,seam,seam+wall),box(x0,x1,tip_a,tip_b,PCB_T+p["BoardSlotGap"],seam+.1)])
            reliefs.append(box(x0-.1,x1+.1,a,b,PCB_T+p["BoardSlotGap"]-.01,seam+wall+.1))
            end_contacts.append(("front",sign,x0,x1))
    for y in (p["LowerContactY"],p["UpperContactY"]):
        if not -H/2+5 < y < H/2-5:
            raise ValueError("Contact locations must avoid rounded PCB corners")
        for sign in (-1,1):
            sx=sign*(ox+3)
            body_bosses.append(Part.makeCylinder(4.5,6.5,V(sx,y,seam-6.5)))
            # Preserve the original 3.2 mm seat and bolt grip length. Add the
            # head-hiding rim above it instead of counterboring a thin floor.
            lid_bosses.append(Part.makeCylinder(4.5,3.2+head_depth,V(sx,y,seam)))
            if head_depth:
                headcuts.append(Part.makeCylinder(head_diameter/2,head_depth+.1,V(sx,y,seam+3.2)))
            holes.append(Part.makeCylinder(screw_hole/2,12,V(sx,y,seam-7)))
            radius=nut_flats/math.sqrt(3)
            pts=[V(sx+radius*math.cos(i*math.pi/3),y+radius*math.sin(i*math.pi/3),seam-6.6) for i in range(7)]
            nutcuts.append(Part.Face(Part.makePolygon(pts)).extrude(V(0,0,nut_depth)))
    feet=[cut for foot in feet if not (cut:=foot.cut(co2_local)).isNull() and cut.Volume>1e-6]
    body=fuse([body]+[local(s) for s in feet+body_bosses])
    lid=local(fuse([lid]+keepers+lid_bosses).cut(Part.makeCompound(holes+headcuts)))
    body=body.cut(local(fuse(holes+nutcuts)))

    # Reserve broad component envelopes, omitting only inspected clear edge pads.
    front_envelope=box(-W/2-p["SideOverhang"],W/2+p["SideOverhang"],-H/2,H/2+p["TopOverhang"],PCB_T+.05,PCB_T+p["FrontHeight"]+.05)
    rear_envelope=box(-W/2-p["SideOverhang"],W/2+p["SideOverhang"],-H/2,H/2,-p["RearHeight"]-p["RearClearance"],-.05)
    reserved=local(fuse([front_envelope,rear_envelope,box(-W/2,W/2,-H/2+5,H/2-5,.01,PCB_T-.01)]).cut(Part.makeCompound(reliefs)))

    plug=path=passage=cable_preview=cable_guard=cable_cut=Part.makeCompound([])
    radius=handle=0.
    end=V(0,0,rear_front)
    if cable_enabled:
        px,py=p["PortX"],p["PortY"]
        plug=local(box(px-p["PlugWidth"]/2,px+p["PlugWidth"]/2,py-p["PlugHeight"]/2,py+p["PlugHeight"]/2,
                       -p["RearHeight"]-p["PlugLength"],-p["RearHeight"]+.1))
        start=pose.multVec(V(px,py,-p["RearHeight"]-p["PlugLength"]))
        tangent=rotation.multVec(V(0,0,-1))
        az,el=math.radians(p["CableAzimuth"]),math.radians(p["CableElevation"])
        direction=V(math.cos(az)*math.cos(el),math.sin(az)*math.cos(el),math.sin(el))
        end=V(p["CableEntryX"],p["CableEntryY"],rear_front+p["CableEntryDepth"])
        curve=Part.BezierCurve()
        handle=p["CableTangentLength"]
        requested_z=end.z
        # Keep the larger hole and its reinforcement sweep from folding through
        # themselves. This constrains the route, never the chamber-depth setting.
        route_min=max(p["MinBendRadius"],math.hypot(hw,hh)+p["CableRimWidth"]+1.)
        # ponytail: rearward search in 5 mm steps, up to 200 mm; use a path solver if
        # routing later needs obstacles beyond the checked wall/module envelopes.
        for scale in ((1.,1.5,2.) if p["AutoCableRoute"] else (1.,)):
            handle=p["CableTangentLength"]*scale
            for retreat in (range(0,201,5) if p["AutoCableRoute"] else (0,)):
                end.z=requested_z-retreat
                curve.setPoles([start,start+tangent*handle,end-direction*handle,end])
                # ponytail: sampled curvature bound; use analytic extrema for tighter routing.
                curvatures=[abs(curve.curvature(i/200)) for i in range(201)]
                radius=1/max(curvatures) if max(curvatures)>1e-9 else math.inf
                if radius >= route_min:
                    break
            if radius >= route_min:
                break
        else:
            action="Adjust cable entry X/Y, direction or tangent length" if p["AutoCableRoute"] else "Enable AutoCableRoute or adjust cable entry/tangent length"
            raise ValueError(f"Cable bend radius {radius:.1f} mm < required {route_min:.1f} mm for cable/hole. {action}; the chamber length has not been changed")
        path=Part.Wire([curve.toShape()])
        profile_pose=App.Placement(start,rotation.multiply(App.Rotation(V(1,0,0),180)))
        profile=moved(rectangle(-hw,hw,-hh,hh,0,hr),profile_pose)
        passage=path.makePipeShell([profile],True,False)
        cable_preview=path.makePipeShell([Part.Wire([Part.makeCircle(p["CableDiameter"]/2,start,tangent)])],True,False)
        valid(passage,"Cable passage")
        if cable_preview.common(reserved).Volume > .01:
            raise ValueError("Cable route intersects installed-module clearance")
        margin=p["CableRimWidth"]
        rim_profile=moved(rectangle(-hw-margin,hw+margin,-hh-margin,hh+margin,0,hr+margin),profile_pose)
        rim_sweep=path.makePipeShell([rim_profile],True,False)
        # Protect the complete cut, including the straight plug clearance and both
        # finite sweep ends; otherwise the plug leaves a C-rim and loose vent ends.
        end_guards=[]
        for point,outward in ((start,-tangent),(end,direction)):
            cap=next(f for f in rim_sweep.Faces if (f.CenterOfMass-point).Length<.001)
            end_guards.append(cap.extrude(outward*margin))
        plug_guard=local(Part.Face(rectangle(px-p['PlugWidth']/2-margin,px+p['PlugWidth']/2+margin,
                           py-p['PlugHeight']/2-margin,py+p['PlugHeight']/2+margin,
                           -p['RearHeight']-p['PlugLength']-margin,margin)).extrude(V(0,0,p['PlugLength']+.1+2*margin)))
        cable_guard=fuse([rim_sweep,plug_guard]+end_guards)
    vent_protected=Part.makeCompound([vent_protected,local(Part.makeCompound(feet+body_bosses))])
    all_vents=all_vents.cut(vent_protected)
    if cable_enabled:
        cable_cut,cable_guard=cable_openings(body,cable_preview,fuse([plug,passage]),
                                             cable_guard,all_vents,nut_access_shape)
    # Leave the cable rim solid when cutting vents, instead of adding coincident
    # shell fragments back afterwards. This avoids non-manifold oblique unions.
    rim=cable_guard
    vent_protected=Part.makeCompound([vent_protected,cable_guard])
    all_vents=all_vents.cut(vent_protected)
    try:
        candidate=body.copy().cut(all_vents) if not all_vents.isNull() else body.copy()
        candidate.check(True)
        closed_mesh(candidate)
        body=candidate
    except (ValueError,Part.OCCError):
        accepted=[]
        for vent in vents:
            tool=vent.cut(vent_protected)
            if tool.isNull() or tool.Volume<.001:continue
            try:
                candidate=body.copy().cut(tool)
                candidate.check(True)
                closed_mesh(candidate)
            except (ValueError,Part.OCCError):continue
            body=candidate
            accepted.append(tool)
        all_vents=Part.makeCompound(accepted)
        rear_vents=bool(accepted)
    body=body.cut(Part.makeCompound([cable_cut,nut_access_shape,local(co2_local)]))
    # Intersecting finger pockets can leave tiny, completely detached slivers.
    # Trim only these cut-off scraps; never discard a second structural piece.
    structural=[s for s in body.Solids if s.Volume>wall**3]
    scraps=[s for s in body.Solids if s.Volume<=wall**3]
    protected=local(Part.makeCompound(feet+body_bosses))
    if (len(structural)==1 and sum(s.Volume for s in scraps)<2*wall**3
        and all(s.common(protected).Volume<.0001 and s.common(base).Volume<.0001 for s in scraps)):
        body=structural[0]
    # Keep split faces: refining the circular hoods can corrupt later boolean
    # slices even when OCC still reports a valid solid and a closed mesh.
    # Plain collar and wall-to-base transitions: no added fillet strips.
    for shape,label in ((body,"Mount"),(lid,"Cover")):
        valid(shape,label)
        shape.check(True)
        if shape.common(reserved).Volume > .01:
            raise ValueError(f"{label} intrudes into module clearance; change angle/distance")
        for wall_void in wall_voids:
            if shape.common(wall_void).Volume > .01:
                raise ValueError(f"{label} enters wall; change angle/distance")
    if compact:
        # Reusing corner space must not bury electronics or the connector in
        # the wall/plate. Existing final body checks also catch closed end caps.
        for wall_void in wall_voids:
            if reserved.common(wall_void).Volume > .01:
                raise ValueError("Compact corner module envelope enters wall")
        if cable_enabled:
            for obstacle in [body,lid]+wall_voids:
                if plug.common(obstacle).Volume > .01:
                    raise ValueError("Compact corner plug clearance is obstructed; increase chamber depth or adjust route")
    if body.common(lid).Volume > .01:
        raise ValueError("Cover and body overlap")
    if cable_enabled and body.common(cable_preview).Volume > .01:
        raise ValueError("Cable route still intersects material after vent/cut processing; adjust the route")
    return dict(corner_depth_saving=original_centre.z-centre.z,body=body,lid=lid,reserved=reserved,plug=plug,path=path,passage=passage,cable_preview=cable_preview,pose=pose,seam=seam,
                ceiling=ceiling+p["FrontSkin"],radius=radius,contacts=contacts,end_contacts=end_contacts,retention=feet+keepers,
                rear_vents=rear_vents,actual_entry_depth=end.z-rear_front,actual_tangent_length=handle,
                rear_front=rear_front,wall_width=bw,wall_height=bh,vent_tools=all_vents,
                nut_access=nut_access_shape,co2_cut=local(co2_local),
                nut_vent_keepout=Part.makeCompound(pocket_panels),
                cable_vent_keepout=cable_guard,
                cable_cut=cable_cut,
                support_lengths=support_lengths,
                hood_end_exposure=hood_end_exposure,
                rim=rim.cut(Part.makeCompound([cable_cut,nut_access_shape])))


def parameters(doc, values):
    obj=doc.getObject("Parameters") or doc.addObject("App::FeaturePython","Parameters")
    obj.Label="Parameters - edit, then run Rebuild.FCMacro"
    for old in ("CornerChamfer","ContactLength","CableGuide"):
        if old in obj.PropertiesList:
            obj.removeProperty(old)
    for name,default,group,description in PARAMETERS:
        if name not in obj.PropertiesList:
            kind="App::PropertyEnumeration" if isinstance(default,str) else "App::PropertyBool" if isinstance(default,bool) else "App::PropertyFloat"
            obj.addProperty(kind,name,group,description)
        if name == "FastenerSize":
            setattr(obj,name,list(FASTENERS))
        setattr(obj,name,values[name])
    for name,value in zip(("NutPocketAcrossFlats","NutPocketDepth","ScrewHoleDiameter"),fastener_dimensions(values)):
        if name not in obj.PropertiesList:
            obj.addProperty("App::PropertyFloat",name,"Retention","Calculated fastener dimension in mm")
        setattr(obj,name,value)
        obj.setEditorMode(name,1)
    for name,value in zip(('ScrewHeadRecessDiameter','ScrewHeadRecessDepth'),head_recess_dimensions(values)):
        if name not in obj.PropertiesList:
            obj.addProperty('App::PropertyFloat',name,'Retention','Calculated head recess including print clearance, in mm')
        setattr(obj,name,value)
        obj.setEditorMode(name,1)
    if "BoardDistance" not in obj.PropertiesList:
        obj.addProperty("App::PropertyFloat","BoardDistance","Mount","Calculated PCB distance; edit RearChamberDepth")
    obj.BoardDistance=board_distance(values)
    obj.setEditorMode("BoardDistance",1)
    return obj


def export(doc,p,result,folder,gui=False,preview=False):
    folder.mkdir(parents=True,exist_ok=True)
    doc.Parameters.BoardDistance=result['pose'].Base.z-result['rear_front']
    for name,value,description in (
        ('PCBOffsetX',result['pose'].Base.x,'PCB centre X in mounting frame; compact corners balance the two wall clearances'),
        ('CornerDepthSaving',result['corner_depth_saving'],'Forward-depth reduction versus standard placement at the same parameters; positive is closer to corner'),
        ('AdditionalWallClearance',0. if p['Corner'] and p.get('CompactCorner',False) else doc.Parameters.BoardDistance-board_distance(p),'Standard-placement extra stand-off; zero in compact mode, which calculates placement directly'),
        ('WallPlateWidth',result['wall_width'],'Nominal wall-plate width; does not grow with yaw or pitch'),
        ('WallPlateHeight',result['wall_height']+20,'Calculated wall-plate height including screw ears')):
        if name not in doc.Parameters.PropertiesList:
            doc.Parameters.addProperty('App::PropertyFloat',name,'Mount',description)
        setattr(doc.Parameters,name,value)
        doc.Parameters.setEditorMode(name,1)
    if "ActualCableEntryDepth" not in doc.Parameters.PropertiesList:
        doc.Parameters.addProperty("App::PropertyFloat","ActualCableEntryDepth","Cable","Calculated cable entry depth after automatic route adjustment")
    doc.Parameters.ActualCableEntryDepth=result["actual_entry_depth"]
    doc.Parameters.setEditorMode("ActualCableEntryDepth",1)
    if "ActualCableTangentLength" not in doc.Parameters.PropertiesList:
        doc.Parameters.addProperty("App::PropertyFloat","ActualCableTangentLength","Cable","Calculated tangent length after automatic route adjustment")
    doc.Parameters.ActualCableTangentLength=result["actual_tangent_length"]
    doc.Parameters.setEditorMode("ActualCableTangentLength",1)
    for name,label,shape in (("Mount","Structural mount - one printed part",result["body"]),
                             ("Cover","Front cover and PCB keepers",result["lid"]),
                             ("ModuleClearance","Measured/provisional module envelope (NOT component CAD)",result["reserved"]),
                             ("PlugClearance","Provisional plug and boot space",result["plug"]),
                             ("CablePreview","Cable route preview - reference only, NOT printed",result["cable_preview"]),
                             ("CableCentreline","Cable route centreline",result["path"])):
        obj=doc.getObject(name) or doc.addObject("Part::Feature",name)
        obj.Label=label
        obj.Shape=shape
        if gui:
            obj.ViewObject.ShapeColor=(.76,.82,.86) if name=="Mount" else (.92,.92,.90)
            obj.ViewObject.Visibility=name in ("Mount","Cover") or (name=="CablePreview" and p.get('CableEnabled',False))
            if name=="CablePreview":
                obj.ViewObject.ShapeColor=(.15,.65,1.)
                obj.ViewObject.Transparency=35
            if name=="ModuleClearance":
                obj.ViewObject.ShapeColor=(1.,.6,.1)
                obj.ViewObject.Transparency=70
    source=doc.getObject("SourcePCB")
    if source is None:
        source=doc.addObject("Mesh::Feature","SourcePCB")
        source.Label="Original PCB mesh - radar and CO2 boards absent"
        source.Mesh=Mesh.Mesh(str(ROOT/"r-pro-1-pcb.obj"))
    source.Placement=result["pose"].multiply(App.Placement(-SOURCE_CENTRE,App.Rotation()))
    if gui:
        source.ViewObject.ShapeColor=(.12,.4,.27)
        source.ViewObject.Visibility=False
    doc.recompute()
    print_shapes=dict(body=result["body"],lid=result["lid"])
    for key,shape in print_shapes.items():
        top=result["ceiling"] if key=="lid" else result["seam"]
        orient=App.Placement(V(0,0,top),App.Rotation(V(1,0,0),180)).multiply(result["pose"].inverse())
        printable=moved(shape,orient)
        # Tessellate once in the validated model coordinates. Re-tessellating
        # after rotation can split near-coincident curved-face vertices in OCC.
        source_mesh=closed_mesh(shape)
        mesh=source_mesh.copy()
        mesh.transform(orient.toMatrix())
        if key=="body" and mesh.BoundBox.ZMin < -.01:
            # At steep angles, a mounting ear can project past the PCB rim.
            # Put a wall-contact face on the bed instead of burying the ear.
            angle=90-p["CornerAngle"]/2 if p["Corner"] else 0.
            orient=App.Placement(V(),App.Rotation(V(0,1,0),angle))
            printable=moved(shape,orient)
            mesh=source_mesh.copy()
            mesh.transform(orient.toMatrix())
        if not mesh.isSolid() or mesh.BoundBox.ZMin < -.01:
            raise ValueError(f"{key}: STL must be closed and above print bed (closed={mesh.isSolid()}, lowest Z={mesh.BoundBox.ZMin:.6f} mm)")
        if max(mesh.BoundBox.XLength,mesh.BoundBox.YLength,mesh.BoundBox.ZLength) > 256:
            raise ValueError(f"{key}: exceeds the Bambu A1 256 mm build volume")
        mesh.write(str(folder/f"{key}.stl"))
        printable.exportStep(str(folder/f"{key}.step"))
    Part.export([doc.Mount,doc.Cover],str(folder/"assembly.step"))
    if gui:
        source.Visibility=True
        doc.Cover.ViewObject.Transparency=70
    # Persist CAD before optional offscreen rendering. saveImage can crash native
    # Wayland/OpenGL contexts; normal interactive rebuilds never need PNG exports.
    doc.saveAs(str(folder/"apollo-mount.FCStd"))
    if gui and preview:
        import FreeCADGui as Gui
        source.Visibility=False
        doc.Cover.ViewObject.Transparency=0
        view=Gui.activeDocument().activeView()
        view.setAnimationEnabled(False)
        front_view=App.Rotation(V(),V(0,1,0),V(1,.6,1),"ZYX")
        view.setCameraOrientation(front_view.Q)
        view.fitAll()
        Gui.updateGui()
        view.saveImage(str(folder/"assembled.png"),1400,1100,"White")
        doc.Cover.Visibility=False
        source.Visibility=True
        doc.ModuleClearance.Visibility=True
        view.fitAll()
        Gui.updateGui()
        view.saveImage(str(folder/"clearances.png"),1400,1100,"White")
        doc.ModuleClearance.Visibility=False
        source.Visibility=False
        doc.Cover.Visibility=True
        view.setCameraOrientation(App.Rotation(V(),V(0,1,0),V(-1,.4,-1),"ZYX").Q)
        view.fitAll()
        Gui.updateGui()
        view.saveImage(str(folder/"rear.png"),1400,1100,"White")
        view.setCameraOrientation(front_view.Q)
        view.fitAll()
        source.Visibility=True
        doc.Cover.ViewObject.Transparency=70
        Gui.updateGui()
        doc.save()
    cable_status=f"cable radius {result['radius']:.1f} mm" if p.get('CableEnabled',False) else 'cable disabled'
    print(f"PASS {folder.name}: two valid solids; no module/wall/cover collision; closed printable meshes; {cable_status}",flush=True)


def main():
    macro=bool(App.GuiUp)
    if macro:
        doc=App.ActiveDocument
        if doc is None or doc.getObject("Parameters") is None:
            raise ValueError("Activate the Apollo model tab containing Parameters, then run Rebuild again")
        p=read_parameters(doc)
        folder=ROOT/"output"/"custom"
        gui=True
    else:
        parser=argparse.ArgumentParser(description=__doc__)
        parser.add_argument("--corner",action="store_true")
        parser.add_argument("--preview",action="store_true")
        parser.add_argument("--set",action="append",default=[],metavar="NAME=VALUE")
        parser.add_argument("--name",default=None)
        args=parser.parse_args()
        p=defaults()
        p["Corner"]=args.corner
        for item in args.set:
            key,value=item.split("=",1)
            if key not in p:
                parser.error(f"Unknown parameter {key}")
            if isinstance(p[key],bool):
                if value.lower() not in ("true","false"):
                    parser.error(f"{key} expects true or false")
                p[key]=value.lower()=="true"
            elif isinstance(p[key],str):
                p[key]=value
            else:
                p[key]=float(value)
        gui=args.preview
        if gui:
            import FreeCADGui as Gui
            Gui.showMainWindow()
        doc=App.newDocument("ApolloMount")
        folder=ROOT/"output"/(args.name or ("corner" if p["Corner"] else "flat"))
    parameters(doc,p)
    result=build(p)
    export(doc,p,result,folder,gui,preview=gui and not macro)
    if not macro:
        App.closeDocument(doc.Name)
        if gui:
            from PySide import QtCore
            Gui.getMainWindow().close()
            QtCore.QCoreApplication.sendPostedEvents(None,QtCore.QEvent.DeferredDelete)
            QtCore.QCoreApplication.processEvents()


if __name__=="__main__":
    main()
