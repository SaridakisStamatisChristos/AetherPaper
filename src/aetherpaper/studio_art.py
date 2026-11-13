"""Original illustrated 'Studio Courier' art treatment for v0.5.

The prior v0.4 atlas supplied separate parts but flat fills dominated.
This edition transforms the original paintings with consistent warm palette,
collaged paper grain, edge-ink, radial highlights and glancing ambient shadow.
Every texture is deterministic, stored in PNG once, never re-generated per
video frame. The output remains replaceable human-editable transparent art.
"""
from __future__ import annotations

from hashlib import sha256
from io import BytesIO
from pathlib import Path
import math
import random

from PIL import Image, ImageChops, ImageFilter, ImageDraw, ImageEnhance
from . import artkit


STUDIO_COLORS = {
    "outline":"#332F39",
    "coat":"#405B75", "coat_light":"#688398", "coat_dark":"#303F59",
    "gold":"#B98654", "gold_light":"#E2C08A",
    "wine":"#9F4E50", "skin":"#DDA27B", "skin_light":"#F2C4A0",
    "skin_shadow":"#AE7163", "hair":"#4B3435","hair_light":"#80645B",
    "trousers":"#4B5369", "trousers_light":"#737C8B",
    "boot":"#303340", "boot_light":"#77716B", "ivory":"#F5E5CC"
}


def _paper_noise(width:int,height:int,seed:int)->Image.Image:
    rng=random.Random(seed)
    small=Image.new("L",(max(3,width//24),max(3,height//24)))
    small.putdata([rng.randrange(150,254) for _ in range(small.width*small.height)])
    return small.resize((width,height),Image.Resampling.BICUBIC)


def _treat(original:Image.Image,name:str,seed:int)->Image.Image:
    """Layer-safe painterly surface applied only where original alpha exists."""
    img=original.convert("RGBA")
    w,h=img.size
    alpha=img.getchannel("A")
    rng=random.Random(seed)
    coarse=_paper_noise(w,h,seed)
    # Real large-area pigment density variation, not merely scattered dots.
    # Multiplication by a softened noise map gives subtle watercolor pooling.
    density=coarse.point(lambda p:max(0,min(255,round(244+(p-202)*.17))))
    pigment=Image.merge("RGB",(density,density,density))
    rgb=ImageChops.multiply(img.convert("RGB"),pigment)
    img=Image.merge("RGBA",(*rgb.split(),alpha))
    # Translucent watercolor mottling: contrast stays readable after 2x shrink.
    tone=Image.new("RGBA",img.size,(0,0,0,0))
    td=ImageDraw.Draw(tone)
    for i in range(110):
        x=rng.randrange(w)
        y=rng.randrange(h)
        r=rng.randrange(8,64)
        tint=(231,184,137,rng.randrange(2,14)) if i%2 else (34,40,63,rng.randrange(2,12))
        td.ellipse((x-r,y-r*.55,x+r,y+r*.55),fill=tint)
    tone=tone.filter(ImageFilter.GaussianBlur(3))
    wash=Image.alpha_composite(img,tone)
    # Quiet fibers and fine engraved pencil lines, clipped to original alpha.
    ink=Image.new("RGBA",img.size,(0,0,0,0))
    d=ImageDraw.Draw(ink)
    for i in range(max(230,w*h//930)):
        x=rng.randrange(w)
        y=rng.randrange(h)
        length=rng.randrange(2,18)
        d.line((x,y,x+length,y+rng.choice((-2,-1,0,1,2))),
               fill=(241,223,192,14) if i%2 else (21,35,48,17),
               width=1)
    # More expressive hatching near the sleeve seams and folds.
    if name in ("torso","cape","scarf","thigh_l","thigh_r","arm_l","arm_r"):
        for i in range(45):
            x=rng.uniform(w*.15,w*.88)
            y=rng.uniform(h*.2,h*.75)
            d.arc((x-18,y-12,x+20,y+16),15,68,fill=(21,32,44,32),width=2)
    surface=Image.alpha_composite(wash,ink)
    # Stronger shadow on one side provides dimensional paper-edge weight.
    edge_base=alpha.filter(ImageFilter.MaxFilter(11))
    edge_inside=alpha.filter(ImageFilter.MinFilter(11))
    border=ImageChops.subtract(edge_base,edge_inside)
    border=ImageChops.multiply(border,Image.new("L",img.size,65))
    contour=Image.new("RGBA",img.size,(40,44,55,0))
    contour.putalpha(border)
    surface=Image.alpha_composite(contour,surface)
    # Preserve the original punched out silhouette even after blurred wash.
    surface.putalpha(alpha)
    return surface


def generate_studio_kit(root:str|Path) -> dict:
    """Generate 20 original enhanced PNG parts, never overwrite edited art."""
    destination=Path(root).resolve()
    destination.mkdir(parents=True,exist_ok=True)
    original_palette=dict(artkit.PALETTE)
    images={}
    try:
        artkit.PALETTE.update(STUDIO_COLORS)
        for name,builder in artkit.BUILDERS.items():
            images[name]=builder()
    finally:
        artkit.PALETTE.clear()
        artkit.PALETTE.update(original_palette)
    digests={}
    for name,base in images.items():
        seed=int.from_bytes(sha256(name.encode("utf-8")).digest()[:4],"big")
        upgraded=_treat(base,name,seed)
        # Keep exact RGBA and full-resolution editable source pieces.
        stream=BytesIO()
        upgraded.save(stream,format="PNG",optimize=True)
        buf=stream.getvalue()
        path=destination/(name+".png")
        if path.exists() and path.read_bytes()!=buf:
            raise FileExistsError(f"refusing to overwrite modified v0.5 character art: {path}")
        if not path.exists():
            path.write_bytes(buf)
        digests[path.name]=sha256(buf).hexdigest()
    return {"name":"studio-courier-v0.5","directory":str(destination),
            "parts":len(digests),"sha256":digests,
            "art_direction":"textured watercolor paper, sunset-rimmed indigo coat and russet scarf",
            "reproducible":True,"network_required":False}
