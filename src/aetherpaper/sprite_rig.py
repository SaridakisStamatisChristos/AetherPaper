"""Layered articulated sprite renderer, v0.4.

Characters are made from replaceable transparent PNG pieces, articulated
through a named bone rig. Optional two-link IK solves arms and legs against
concrete world-space targets. All animation remains a pure function of time.

Asset convention: source art points along +X; its declared normalized pivot
maps to the bone start. Layers are explicitly z-ordered. This is rigid-part
puppetry, not weighted mesh deformation.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import math
from PIL import Image
from .rig import _body, two_bone_ik

Point = tuple[float, float]
Joint = tuple[Point, Point, float]


@lru_cache(maxsize=128)
def _sprite(path: str) -> Image.Image:
    with Image.open(path) as loaded:
        if loaded.width * loaded.height > 10_000_000:
            raise ValueError("sprite exceeds 10 megapixel in-memory limit")
        return loaded.convert("RGBA")


def _resolved(root: Path, path: str) -> Path:
    base=root.resolve()
    if path.startswith(("http:", "https:", "data:", "file:")):
        raise ValueError("sprite images must be local files")
    candidate=(base/path).resolve()
    if not candidate.is_relative_to(base):
        raise ValueError("sprite asset escapes project directory")
    if not candidate.is_file():
        raise FileNotFoundError("missing sprite asset: " + path)
    return candidate


def attach_sprite(image: Image.Image, sprite: Image.Image, start: Point,
                  end: Point, pivot: Point = (0,.5),
                  scale: float = 1.0) -> None:
    """Draw one layered image rotated around its authored joint pivot."""
    dx,dy=end[0]-start[0],end[1]-start[1]
    length=math.hypot(dx,dy)
    if length<1e-6:
        return
    target_width=max(1,round(length*scale))
    target_height=max(1,round(sprite.height*target_width/sprite.width))
    if target_width>8192 or target_height>8192:
        raise ValueError("sprite rasterized dimensions exceed 8192")
    art=sprite.resize((target_width,target_height),Image.Resampling.LANCZOS)
    anchor=(round(pivot[0]*target_width),round(pivot[1]*target_height))
    radius=math.ceil(math.hypot(target_width,target_height))+3
    if radius>2048:
        raise ValueError("sprite rotated canvas exceeds 4096 pixels")
    square=Image.new("RGBA",(2*radius,2*radius))
    square.alpha_composite(art,(radius-anchor[0],radius-anchor[1]))
    angle=-math.degrees(math.atan2(dy,dx))
    rotated=square.rotate(angle,Image.Resampling.BICUBIC,expand=False)
    image.paste(rotated,(round(start[0]-radius),round(start[1]-radius)),rotated)


def _target(actor:dict, pose, side:int, t:float, x:float,y:float,s:float)->Point:
    """Return reachable target in world pixels, blending gestures into the hand."""
    neutral=(x+side*.21*s,y-.315*s)
    if side<0:
        return (neutral[0]+pose.walk*.07*s,neutral[1])
    target=(x+.21*s-pose.walk*.045*s,y-.315*s)
    if pose.holding:
        target=(x+.30*s,y-.47*s)
    if pose.waving or pose.gesture=="wave":
        target=(x+.22*s+math.sin(t*11)*.036*s,y-.98*s)
    elif pose.gesture=="raise":
        target=(x+.19*s,y-1.025*s)
    elif pose.gesture=="point":
        target=(x+.61*s,y-.68*s)
    if pose.waving or pose.gesture:
        weight=max(0,min(1,pose.gesture_weight))
        target=(neutral[0]+(target[0]-neutral[0])*weight,
                neutral[1]+(target[1]-neutral[1])*weight)
    if pose.hand_target is not None:
        dest=(pose.hand_target[0]*actor["_width"],pose.hand_target[1]*actor["_height"])
        f=max(0,min(1,pose.hand_weight))
        target=(target[0]+(dest[0]-target[0])*f,
                target[1]+(dest[1]-target[1])*f)
    return target


def _update_limb(joints:dict[str,Joint],upper_name:str,lower_name:str,
                 target:Point,bend:int) -> None:
    if upper_name not in joints or lower_name not in joints:
        return
    base,end,_=joints[upper_name]
    downstream,end2,_=joints[lower_name]
    upper=math.dist(base,end)
    lower=math.dist(downstream,end2)
    hinge,tip=two_bone_ik(base,target,upper,lower,bend=bend)
    joints[upper_name]=(base,hinge,math.atan2(hinge[1]-base[1],hinge[0]-base[0]))
    joints[lower_name]=(hinge,tip,math.atan2(tip[1]-hinge[1],tip[0]-hinge[0]))


def posed_sprite_joints(actor:dict,pose,width:int,height:int,time:float) -> dict[str,Joint]:
    """Solve the shared rig and retarget standard named arm/leg pairs with IK.

    Expected pairs:
        arm_l/forearm_l, arm_r/forearm_r, thigh_l/shin_l, thigh_r/shin_r
    These are optional: arbitrary custom bones and older sprite kits remain valid.
    """
    joints,s,x,y=_body(actor,pose,width,height,time)
    # Avoid writing ephemeral runtime keys into caller's JSON actor object.
    actor_data={**actor,"_width":width,"_height":height}
    for side,suffix in ((-1,"l"),(1,"r")):
        upper,lower="arm_"+suffix,"forearm_"+suffix
        dest=_target(actor_data,pose,side,time,x,y,s)
        if not (pose.bone_angles and (upper in pose.bone_angles or lower in pose.bone_angles)):
            _update_limb(joints,upper,lower,dest,-side)
    walking=max(abs(pose.walk),abs(pose.run),abs(pose.gait or 0.))
    for side,suffix in ((-1,"l"),(1,"r")):
        upper,lower="thigh_"+suffix,"shin_"+suffix
        if upper not in joints:
            continue
        cycle=pose.gait if pose.gait is not None else pose.walk+pose.run
        stride=cycle*(.105 if abs(pose.run)<.1 else .17)*s*side
        lift=max(0,cycle*side)*walking*.09*s
        dest=(x+side*.119*s+stride,y-.017*s-lift)
        if pose.foot_targets is not None and suffix in pose.foot_targets:
            dx,dy=pose.foot_targets[suffix]
            dest=(x+dx*s,y+dy*s)
        if pose.foot_world is not None and suffix in pose.foot_world:
            fx,fy=pose.foot_world[suffix]
            dest=(fx*width,fy*height)
        if not (pose.bone_angles and (upper in pose.bone_angles or lower in pose.bone_angles)):
            _update_limb(joints,upper,lower,dest,-side)
    if "cape" in joints:
        a,b,_=joints["cape"]
        length=math.dist(a,b)
        # Damped sway is constant and deterministic at any render timestamp.
        sway=(.05*math.sin(time*2.5)+pose.walk*.10)*s
        tip=(a[0]-sway,a[1]+length*.97)
        joints["cape"]=(a,tip,math.atan2(tip[1]-a[1],tip[0]-a[0]))
    if "hair_back" in joints:
        a,b,_=joints["hair_back"]
        length=math.dist(a,b)
        drift=.09*math.sin(time*2.1+.8)*s
        tip=(a[0]+drift,a[1]+length)
        joints["hair_back"]=(a,tip,math.atan2(tip[1]-a[1],tip[0]-a[0]))
    return joints


def sprite_hand(actor:dict,pose,width:int,height:int,time:float)->Point:
    """Use the actual visible sprite forearm endpoint for held-prop alignment."""
    joints=posed_sprite_joints(actor,pose,width,height,time)
    if "forearm_r" in joints:
        return joints["forearm_r"][1]
    # Custom artist rigs need not use the canonical limb labels.
    from .rig import advanced_hand
    return advanced_hand(actor,pose,width,height,time)


def _selected(part:dict,pose,time:float)->bool:
    condition=part.get("expression")
    if condition is not None and condition!=pose.expression:
        return False
    state=part.get("mouth_state")
    if state is not None:
        opening=pose.mouth if pose.mouth>0 else (
            .7*abs(math.sin(time*12)) if pose.talking else 0)
        is_open=pose.talking and opening>=.25
        return (state=="open")==is_open
    return True


def draw_sprite_character(image:Image.Image,source_root:Path,
                          actor:dict,pose,time:float)->None:
    art=actor["visual"]
    joints=posed_sprite_joints(actor,pose,*image.size,time)
    for part in sorted(art["parts"],key=lambda p:p.get("z",0)):
        if not _selected(part,pose,time):
            continue
        start,end,_=joints[part["bone"]]
        sprite=_sprite(str(_resolved(source_root,part["src"])))
        attach_sprite(image,sprite,start,end,tuple(part.get("pivot",[0,.5])),
                      part.get("scale",1.0))
