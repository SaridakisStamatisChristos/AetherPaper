"""Create reproducible six-pose PNG illustration fallback from the existing rig.

This is a compatibility fixture, not the final art direction. It demonstrates
that a single transparent 3x2 pose atlas can be generated from existing local
artwork, edited externally, or entirely replaced with commissioned artwork.

Original studio PNGs and the 0.5 performance JSON remain authoritative; this
command does not overwrite artwork if the source bytes were artist-edited.
"""
from __future__ import annotations
from dataclasses import replace
from pathlib import Path
from hashlib import sha256
from io import BytesIO
import json
import math
from PIL import Image,ImageDraw
from .studio_art import generate_studio_kit
from .model import load_project
from .timeline import actor_pose
from .sprite_rig import draw_sprite_character,sprite_hand

SLOTS = (("idle",.1),("step",1.35),("reach",4.7),
         ("carry",7.45),("place",10.1),("gaze",12.6))


def _lantern(img:Image.Image,point:tuple[float,float])->None:
    d=ImageDraw.Draw(img)
    x,y=point
    sz=28
    d.rounded_rectangle((x-sz*.57,y-sz*.45,x+sz*.57,y+sz*.57),radius=5,
                        fill="#9B684C",outline="#493944",width=3)
    d.rounded_rectangle((x-sz*.39,y-sz*.31,x+sz*.39,y+sz*.41),radius=3,
                        fill="#F7C976",outline="#E6B167",width=2)
    d.arc((x-sz*.33,y-sz*.94,x+sz*.33,y-sz*.42),
          165,15,fill="#C69A69",width=4)
    d.line((x-sz*.22,y-sz*.28,x+sz*.23,y+sz*.38),
           fill="#805A50",width=3)
    d.line((x+sz*.22,y-sz*.28,x-sz*.23,y+sz*.38),
           fill="#805A50",width=3)


def build_posekit(out:str|Path,project:str|Path)->dict:
    source=load_project(project)
    scene=source.scenes[0]
    actor=scene["characters"][0]
    root=source.source.parent
    # Preserve any existing edited studio art rather than regenerating it.
    artroot=root/"assets"/"studio_courier"
    if not artroot.exists():
        generate_studio_kit(artroot)
    width=512;height=512
    atlas=Image.new("RGBA",(width*3,height*2))
    poses={}
    for index,(name,t) in enumerate(SLOTS):
        state=actor_pose(scene,actor,t)
        # Bake the original rig's coherent silhouette in a single illustrated
        # image; the finished film never rotates individual rectangular limbs.
        state=replace(state,x=.50,y=.875,foot_world=None,foot_targets=None)
        frame=Image.new("RGBA",(width,height))
        draw_sprite_character(frame,root,actor,state,t)
        hx,hy=sprite_hand(actor,state,width,height,t)
        if name in ("reach","carry","place"):
            _lantern(frame,(hx,hy))
        atlas.alpha_composite(frame,((index%3)*width,(index//3)*height))
        poses[name]={"cell":index,"anchor":[.50,.875],
                     "hand":[max(0,min(1,hx/width)),max(0,min(1,hy/height))]}
    stream=BytesIO()
    atlas.save(stream,format="PNG",optimize=True)
    payload=stream.getvalue()
    target=Path(out).resolve()
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists() and target.read_bytes()!=payload:
        raise FileExistsError("refusing to overwrite user-modified pose art: "+str(target))
    if not target.exists():
        target.write_bytes(payload)
    return {"format":"aetherpaper-pose-atlas-0.6",
            "path":str(target),"columns":3,"rows":2,
            "width":atlas.width,"height":atlas.height,
            "source":"local original studio courier rig",
            "poses":poses,"sha256":sha256(payload).hexdigest(),
            "reproducible":True,"network_required":False}
