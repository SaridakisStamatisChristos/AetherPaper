"""Artist-provided cutout-sprite rendering on named skeleton bones.

Each independent transparent PNG is authored with its long dimension along +X
and a declared pivot. It is rigidly attached to a world-space bone and rotated
around that pivot. This supports replaceable artwork without regenerating code.
"""
from __future__ import annotations
from functools import lru_cache
from pathlib import Path
import math

from PIL import Image
from .rig import _body


@lru_cache(maxsize=96)
def _sprite(path: str) -> Image.Image:
    with Image.open(path) as loaded:
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


def attach_sprite(image: Image.Image, sprite: Image.Image, start: tuple[float,float],
                  end: tuple[float,float], pivot: tuple[float,float] = (0,.5),
                  scale: float = 1.0) -> None:
    """Affine rotate and scale one transparent image about its declared bone pivot.

    Source art is drawn horizontally, with the bone starting at the chosen
    normalized pivot; image intrinsic width corresponds to one bone length.
    """
    dx,dy=end[0]-start[0],end[1]-start[1]
    length=math.hypot(dx,dy)
    if length<1e-6:
        return
    target_width=max(1,round(length*scale))
    target_height=max(1,round(sprite.height*target_width/sprite.width))
    # Keep memory bounded even for malformed artistic input.
    if target_width>8192 or target_height>8192:
        raise ValueError("sprite rasterized dimensions exceed 8192")
    art=sprite.resize((target_width,target_height),Image.Resampling.LANCZOS)
    anchor=(round(pivot[0]*target_width),round(pivot[1]*target_height))
    radius=math.ceil(math.hypot(target_width,target_height))+3
    if radius>2048:
        raise ValueError('sprite rotated canvas exceeds 4096 pixels')
    # A centered pivot avoids rotation/expand offset ambiguities.
    square=Image.new("RGBA",(2*radius,2*radius))
    square.alpha_composite(art,(radius-anchor[0],radius-anchor[1]))
    angle=-math.degrees(math.atan2(dy,dx))
    rotated=square.rotate(angle,Image.Resampling.BICUBIC,expand=False)
    box=(round(start[0]-radius),round(start[1]-radius))
    image.paste(rotated,box,rotated)


def draw_sprite_character(image: Image.Image, source_root: Path,
                          actor: dict, pose, time: float) -> None:
    art=actor["visual"]
    joints,_,_,_=_body(actor,pose,*image.size,time)
    # Z ordering is explicit and stable. The character's entire cast remains
    # assembled by the same joint transforms regardless of video timestamp.
    for part in sorted(art["parts"],key=lambda p:p.get("z",0)):
        start,end,_=joints[part["bone"]]
        sprite=_sprite(str(_resolved(source_root,part["src"])))
        attach_sprite(image,sprite,start,end,tuple(part.get("pivot",[0,.5])),
                      part.get("scale",1.0))
