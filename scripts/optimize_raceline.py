"""Optimize a map-frame reference loop and export provenance plus a speed envelope."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
for name in ('core','navigation'):
    sys.path.insert(0,str(ROOT/'src'/('pinky_gp_'+name)))
from pinky_gp_navigation.raceline import optimize
from pinky_gp_navigation.vehicle_profile import load_profile
from pinky_gp_navigation.scan_race import Occupancy


def main():
    import yaml
    from PIL import Image
    p=argparse.ArgumentParser()
    p.add_argument('--map',required=True,type=Path)
    p.add_argument('--reference',required=True,type=Path)
    p.add_argument('--profile',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--offset',type=float,default=.18)
    a=p.parse_args()
    if a.output.exists():p.error('choose a new output path')
    cfg=yaml.safe_load(a.map.read_text())
    if cfg.get('mode','trinary')!='trinary' or abs(cfg['origin'][2])>1e-9:
        p.error('trinary axis-aligned map required')
    imgpath=a.map.parent/cfg['image']
    image=Image.open(imgpath).convert('L')
    data=[]
    for y in reversed(range(image.height)):
        for x in range(image.width):
            value=image.getpixel((x,y))/255
            probability=value if cfg.get('negate',0) else 1-value
            data.append(100 if probability>cfg['occupied_thresh'] else
                        0 if probability<cfg['free_thresh'] else -1)
    profile,radius=load_profile(a.profile)
    grid=Occupancy(image.width,image.height,cfg['resolution'],cfg['origin'][:2],data,radius)
    reference=json.loads(a.reference.read_text())
    if reference['frame_id']!='map':p.error('reference must use map coordinates')
    result=optimize(reference['points'],grid,profile,max_offset=a.offset)
    result['provenance']={key:hashlib.sha256(path.read_bytes()).hexdigest()
                          for key,path in [('map_yaml_sha256',a.map),('map_image_sha256',imgpath),
                                           ('reference_sha256',a.reference),('profile_sha256',a.profile)]}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result['optimization'],indent=2))


if __name__=='__main__':main()
