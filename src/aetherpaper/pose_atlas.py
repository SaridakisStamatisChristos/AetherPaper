"""Whole-pose illustrated actor renderer, v0.6.

A rigid-skeletal puppet is suitable for simple explanatory motion but is not
the sole route to rich character silhouettes. Artists may instead supply a
consistent transparent PNG pose atlas: one actor shown in different painted
poses. Draw the chosen cel as a coherent picture, anchored on the same ground
point during motion, without redrawing arms as disconnected strips.

Pose selection is a deterministic, seek-safe function of scene time. Optional
short crossfades are explicitly allowed but default to instant replacement to
avoid ghost limbs. The pose atlas has no network or model runtime dependencies.
"""
from __future__ import annotations
from functools import lru_cache
from pathlib import Path
from dataclasses import dataclass
from PIL import Image, ImageEnhance
from .timeline import actor_pose

@lru_cache(maxsize=32)
def _atlas(path:str) -> Image.Image:
    with Image.open(path) as im:
        if im.width*im.height>24_000_000:
            raise ValueError("pose atlas exceeds 24 million pixels")
        if im.mode not in ("RGBA","RGB","P"):
            raise ValueError("pose atlas must be a PNG/RGBA image")
        return im.convert("RGBA")


def _path(root:Path,name:str)->str:
    if name.startswith(("http:","https:","data:","file:")):
        raise ValueError("pose art cannot use remote URLs")
    base=root.resolve()
    result=(base/name).resolve()
    if not result.is_relative_to(base):
        raise ValueError("pose atlas path escapes project directory")
    if not result.is_file():
        raise FileNotFoundError("pose atlas not found: "+name)
    return str(result)


@dataclass(frozen=True)
class PoseFrame:
    name:str
    previous:str|None
    progress:float


def pose_frame(visual:dict,t:float)->PoseFrame:
    """Evaluate an artist's pose switch timeline, independent of prior frames."""
    events=visual["timeline"]
    chosen=events[0]
    previous=None
    for event in events[1:]:
        if t<event["at"]:
            break
        previous=chosen
        chosen=event
    progress=1.0
    if previous is not None:
        seconds=chosen.get("crossfade",0.0)
        if seconds>0:
            progress=min(1.0,max(0.0,(t-chosen["at"])/seconds))
    return PoseFrame(chosen["pose"],previous["pose"] if previous else None,progress)


def _cell(art:Image.Image,visual:dict,cell:int)->Image.Image:
    columns,rows=visual["columns"],visual["rows"]
    if art.width%columns or art.height%rows:
        raise ValueError("atlas width and height must divide exactly into columns/rows")
    cw,ch=art.width//columns,art.height//rows
    y,x=divmod(cell,columns)
    return art.crop((x*cw,y*ch,(x+1)*cw,(y+1)*ch))


def _geometry(image:Image.Image,actor:dict,pose,visual:dict,
              variant:dict)->tuple[tuple[int,int],tuple[int,int]]:
    W,H=image.size
    target_h=max(1,round(H*visual.get("height",.71)*actor.get("scale",1)))
    # Pixel density is preserved; real artwork is only resampled once per frame.
    art_h=target_h
    cw,ch=visual["_cell_size"]
    art_w=max(1,round(cw*target_h/ch))
    ax,ay=variant.get("anchor",visual.get("anchor",[.5,.96]))
    center=(pose.x*W,pose.y*H)
    return (round(center[0]-ax*art_w),round(center[1]-ay*art_h)),(art_w,art_h)


def draw_pose_atlas(image:Image.Image,root:Path,actor:dict,pose,t:float) -> None:
    visual=actor["visual"]
    atlas=_atlas(_path(root,visual["src"]))
    if atlas.width%visual["columns"] or atlas.height%visual["rows"]:
        raise ValueError("pose atlas grid is not divisible")
    frame=pose_frame(visual,t)
    variants=visual["poses"]
    size=(atlas.width//visual["columns"],atlas.height//visual["rows"])
    meta={**visual,"_cell_size":size}
    def draw_one(pose_name:str,opacity:float)->None:
        cfg=variants[pose_name]
        sprite=_cell(atlas,visual,cfg["cell"])
        origin,dims=_geometry(image,actor,pose,meta,cfg)
        sprite=sprite.resize(dims,Image.Resampling.LANCZOS)
        if opacity<1:
            a=sprite.getchannel("A").point(lambda v:round(v*opacity))
            sprite.putalpha(a)
        if image.mode=="RGBA":
            image.alpha_composite(sprite,origin)
        else:
            image.paste(sprite,origin,sprite)
    if frame.previous is not None and frame.progress<1:
        draw_one(frame.previous,1-frame.progress)
        draw_one(frame.name,frame.progress)
    else:
        draw_one(frame.name,1)


def pose_hand(actor:dict,pose,width:int,height:int,t:float)->tuple[float,float]:
    """Map the authored hand anchor into image space for prop attachment.

    If the actor uses a fully painted lantern in its pose artwork, omit the
    separate scene prop to avoid a duplicated visual lantern.
    """
    visual=actor["visual"]
    frame=pose_frame(visual,t)
    meta=visual["poses"][frame.name]
    hand=meta.get("hand")
    if hand is None:
        raise ValueError(f"pose {frame.name!r} requires a hand anchor for prop attachment")
    ah=height*visual.get("height",.71)*actor.get("scale",1)
    width_px=ah*visual["columns"]/visual["rows"]*visual.get("_aspect_ratio",1.)
    ax,ay=meta.get("anchor",visual.get("anchor",[.5,.96]))
    return (pose.x*width+(hand[0]-ax)*width_px,
            pose.y*height+(hand[1]-ay)*ah)
