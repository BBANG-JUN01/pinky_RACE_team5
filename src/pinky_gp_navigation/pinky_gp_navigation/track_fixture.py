"""One geometry definition for the registered simulation map, world and scoring."""
import json
import math
from pathlib import Path
from xml.etree import ElementTree as ET

# Box centres and full extents in metres. +x is the start-line heading.
WALLS = ((0, -.46, 3.66, .06), (0, 1.90, 3.66, .06),
         (-1.80, .72, .06, 2.36), (1.80, .72, .06, 2.36),
         (0, .72, 1.72, .55), (-.57, 1.835, .27, .105))
EVENT_BOXES = {'cone': (.64, 0., .09, .09), 'barrier': (.64, 0., .09, .91)}
ORIGIN = (-2.04, -.66)
RES = .03
WIDTH, HEIGHT = 136, 94


def wall_distance(x, y, boxes=WALLS):
    return min(math.hypot(max(abs(x - bx) - w/2, 0),
                          max(abs(y - by) - h/2, 0)) for bx, by, w, h in boxes)


def centerline():
    pts = [(0., 0.)]
    def straight(end):
        x, y = pts[-1]
        n = math.ceil(math.dist((x, y), end) / .075)
        pts.extend((x + (end[0]-x)*i/n, y + (end[1]-y)*i/n) for i in range(1, n+1))
    def arc(cx, cy, a):
        for i in range(1, 13):
            angle = a + math.pi*i/24
            pts.append((cx+.48*math.cos(angle), cy+.48*math.sin(angle)))
    straight((.84, 0.))
    arc(.84, .48, -math.pi/2)
    straight((1.32, .96))
    arc(.84, .96, 0)
    straight((-.84, 1.44))
    arc(-.84, .96, math.pi/2)
    straight((-1.32, .48))
    arc(-.84, .48, math.pi)
    straight((0., 0.))
    return pts[:-1]


def occupancy():
    return [100 if wall_distance(ORIGIN[0]+(i % WIDTH+.5)*RES,
                                 ORIGIN[1]+(i // WIDTH+.5)*RES) <= RES*.71 else 0
            for i in range(WIDTH*HEIGHT)]


def box_model(name, box, height=.32, z=None):
    x, y, width, depth = box
    model = ET.Element('model', name=name)
    ET.SubElement(model, 'static').text = 'true'
    ET.SubElement(model, 'pose').text = f'{x} {y} {height/2 if z is None else z} 0 0 0'
    link = ET.SubElement(model, 'link', name='link')
    for role in ('collision', 'visual'):
        element = ET.SubElement(link, role, name=role)
        shape = ET.SubElement(ET.SubElement(element, 'geometry'), 'box')
        ET.SubElement(shape, 'size').text = f'{width} {depth} {height}'
    return model


def event_sdf(event):
    root = ET.Element('sdf', version='1.9')
    root.append(box_model(event, EVENT_BOXES[event]))
    return ET.tostring(root, encoding='unicode')


def write_track(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    if any((directory/name).exists() for name in ('map.pgm','map.yaml','path.json','track.sdf')):
        raise FileExistsError('generated track already exists; use a fresh track_dir')
    cells = occupancy()
    pixels = bytes(0 if cells[y*WIDTH+x] else 254
                   for y in reversed(range(HEIGHT)) for x in range(WIDTH))
    (directory/'map.pgm').write_bytes(f'P5\n{WIDTH} {HEIGHT}\n255\n'.encode()+pixels)
    (directory/'map.yaml').write_text(
        f'image: map.pgm\nmode: trinary\nresolution: {RES}\norigin: [{ORIGIN[0]}, {ORIGIN[1]}, 0.0]\n'
        'negate: 0\noccupied_thresh: 0.65\nfree_thresh: 0.196\n')
    (directory/'path.json').write_text(json.dumps({'frame_id':'map','points':centerline()}))
    root = ET.Element('sdf', version='1.9')
    world = ET.SubElement(root, 'world', name='pinky_gp')
    for library, system in [('physics','Physics'), ('user-commands','UserCommands'),
                            ('scene-broadcaster','SceneBroadcaster'), ('sensors','Sensors')]:
        plugin = ET.SubElement(world, 'plugin', filename=f'gz-sim-{library}-system',
                               name=f'gz::sim::systems::{system}')
        if system == 'Sensors':
            ET.SubElement(plugin, 'render_engine').text = 'ogre2'
    light = ET.SubElement(world, 'light', type='directional', name='sun')
    ET.SubElement(light, 'direction').text = '-0.3 0.2 -1'
    ET.SubElement(light, 'diffuse').text = '0.9 0.9 0.9 1'
    world.append(box_model('ground', (0, .72, 12, 12), .1, -.05))
    for i, box in enumerate(WALLS):
        world.append(box_model('wall_'+str(i), box))
    ET.ElementTree(root).write(directory/'track.sdf', encoding='utf-8', xml_declaration=True)


def ray(x,y,a,boxes):
    ux,uy=math.cos(a),math.sin(a)
    near=math.inf
    for bx,by,w,h in boxes:
        entry,exit_=0.,12.
        for p,d,c,size in ((x,ux,bx,w),(y,uy,by,h)):
            if abs(d)<1e-10:
                if abs(p-c)>size/2: exit_=-1
                continue
            lo,hi=(c-size/2-p)/d,(c+size/2-p)/d
            entry=max(entry,min(lo,hi));exit_=min(exit_,max(lo,hi))
        if entry<=exit_: near=min(near,entry)
    return near
