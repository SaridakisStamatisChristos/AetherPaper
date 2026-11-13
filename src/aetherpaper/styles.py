"""Visual presets and lightweight layered paper effects, without external assets."""
from __future__ import annotations
from PIL import Image, ImageDraw, ImageFilter
import math
import random

PRESETS = {"paper_cut", "scrapbook", "storybook"}


def styled_background(base: Image.Image, style: str, seed: int) -> Image.Image:
    if style not in PRESETS:
        raise ValueError("unknown style preset: " + style)
    if style == "paper_cut":
        return base
    w,h=base.size
    d=ImageDraw.Draw(base)
    if style == "scrapbook":
        spacing=max(14,round(h*.09))
        for x in range(0,w,spacing):
            d.line((x,0,x,h),fill="#D9CFC1",width=1)
        for y in range(0,h,spacing):
            d.line((0,y,w,y),fill="#D9CFC1",width=1)
        r=random.Random(seed)
        for _ in range(max(8,(w*h)//15000)):
            x=r.randrange(w); y=r.randrange(h)
            length=r.randrange(3,12)
            d.line((x,y,x+length,y+length*.2),fill="#C9B29C",width=1)
        d.polygon([(0,0),(w*.28,0),(w*.24,h*.04),(0,h*.05)],fill="#F5EBCD")
    else:
        # Soft broad daylight and an illustrated paper theatre border.
        overlay=Image.new("RGBA",(w,h),(0,0,0,0))
        od=ImageDraw.Draw(overlay)
        for y in range(h):
            alpha=round(24*(1-y/max(1,h-1)))
            od.line((0,y,w,y),fill=(250,222,170,alpha))
        overlay=overlay.filter(ImageFilter.GaussianBlur(max(2,round(h*.04))))
        base=Image.alpha_composite(base.convert("RGBA"),overlay).convert("RGB")
        d=ImageDraw.Draw(base)
        line=max(1,round(h*.004))
        d.rounded_rectangle((w*.018,h*.018,w*.982,h*.982),
                            radius=max(5,round(h*.02)),outline="#C2A985",width=line)
    return base


def shadows(base: Image.Image, feet: list[tuple[float,float,float]]) -> Image.Image:
    """Soft contact shadows underneath puppet feet."""
    if not feet:
        return base
    w,h=base.size
    mask=Image.new("L",(w,h),0)
    d=ImageDraw.Draw(mask)
    for x,y,s in feet:
        rx=max(3,round(.22*s))
        ry=max(2,round(.038*s))
        d.ellipse((round(x-rx),round(y-ry),round(x+rx),round(y+ry)),fill=75)
    mask=mask.filter(ImageFilter.GaussianBlur(max(1,round(h*.008))))
    ink=Image.new("RGB",(w,h),"#504133")
    return Image.composite(ink,base,mask)


def finish_style(base: Image.Image, style: str, time: float) -> Image.Image:
    if style == "paper_cut":
        return base
    w,h=base.size
    d=ImageDraw.Draw(base)
    if style == "scrapbook":
        # Hand-cut off-white inner border and two small translucent tape labels.
        k=max(1,round(h*.006))
        d.line([(w*.03,h*.035),(w*.975,h*.027)],fill="#F6EDDA",width=k)
        d.line([(w*.03,h*.97),(w*.97,h*.978)],fill="#F6EDDA",width=k)
        d.polygon([(w*.075,h*.045),(w*.21,h*.044),(w*.225,h*.095),(w*.08,h*.105)],
                  fill="#F2DEB3")
    elif style == "storybook":
        # Stable vignette; no animated texture flicker.
        overlay=Image.new("RGBA",(w,h),(0,0,0,0))
        od=ImageDraw.Draw(overlay)
        k=max(1,round(min(w,h)*.006))
        od.rounded_rectangle((k,k,w-k,h-k),radius=max(4,k*4),
                             outline=(112,72,56,95),width=k)
        base=Image.alpha_composite(base.convert("RGBA"),overlay).convert("RGB")
    return base


def transition_frame(frame: Image.Image, transition: dict, t: float) -> Image.Image:
    duration=transition.get("duration",.4)
    if duration <= 0 or t >= duration:
        return frame
    u=max(0.0,min(1.0,t/duration))
    eased=u*u*(3-2*u)
    mode=transition["type"]
    if mode=="fade":
        return Image.blend(Image.new("RGB",frame.size,"#F9F1E1"),frame,eased)
    if mode=="wipe":
        w,h=frame.size
        mask=Image.new("L",(w,h),0)
        md=ImageDraw.Draw(mask)
        md.rectangle((0,0,round(w*eased),h),fill=255)
        return Image.composite(frame,Image.new("RGB",frame.size,"#F9F1E1"),mask)
    raise ValueError("unsupported transition")
