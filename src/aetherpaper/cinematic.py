"""Handcrafted cinematic paper-diorama environment.

AetherPaper v0.3's new look is an original built-in 'moonlit_atelier' set.
No external assets, fonts, browser or AI inference are required. The set and
vignette are cached and per-frame atmospheric movement is a pure function of t.
"""
from __future__ import annotations

from functools import lru_cache
from hashlib import sha256
import math
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont


def _font(size: int, serif: bool = True):
    names=(["/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSerif-Regular.ttf"] if serif else
           ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"])
    for name in names:
        if Path(name).is_file():
            return ImageFont.truetype(name,max(9,size))
    return ImageFont.load_default()


def _box(w,h,normalized):
    return tuple(round(v*(w if i%2==0 else h)) for i,v in enumerate(normalized))


@lru_cache(maxsize=24)
def atelier_background(w: int, h: int, seed: int) -> Image.Image:
    """Construct a richly layered night interior once per dimension/seed."""
    img=Image.new("RGB",(w,h))
    draw=ImageDraw.Draw(img)
    for iy in range(h):
        u=iy/max(1,h-1)
        draw.line((0,iy,w,iy),fill=(round(22+28*u),round(45+26*u),round(60+22*u)))
    rng=random.Random(seed)
    # Tall moonlit arched window with painted mountain landscape.
    aperture=_box(w,h,(.087,.11,.475,.705))
    draw.rounded_rectangle(_box(w,h,(.07,.077,.49,.73)),radius=round(.047*h),
                           fill="#594D4B",outline="#BB9D80",width=max(2,round(.014*h)))
    draw.rounded_rectangle(aperture,radius=round(.044*h),fill="#7999A0")
    # Sky glow, moon, fine stars.
    moon=(.322,.235,.385,.347)
    draw.ellipse(_box(w,h,moon),fill="#F4E6BC")
    draw.ellipse(_box(w,h,(.33,.242,.39,.34)),outline="#DBD7B8",width=1)
    for i in range(24):
        px=rng.uniform(.108,.454); py=rng.uniform(.145,.49)
        r=1 if i%3 else 2
        draw.ellipse((px*w-r,py*h-r,px*w+r,py*h+r),fill="#D3D9C4")
    draw.polygon([(round(.095*w),round(.61*h)),(round(.19*w),round(.46*h)),
                  (round(.29*w),round(.62*h)),(round(.392*w),round(.47*h)),
                  (round(.475*w),round(.615*h))],fill="#4B6D76")
    draw.polygon([(round(.095*w),round(.65*h)),(round(.21*w),round(.53*h)),
                  (round(.31*w),round(.654*h)),(round(.404*w),round(.55*h)),
                  (round(.48*w),round(.66*h))],fill="#345963")
    draw.rectangle(_box(w,h,(.093,.652,.481,.705)),fill="#2B4B50")
    # Glazed mullions and bevelled sill.
    mull=max(2,round(h*.012))
    draw.line(_box(w,h,(.282,.108,.282,.702)),fill="#D0B597",width=mull)
    draw.line(_box(w,h,(.092,.448,.485,.448)),fill="#D0B597",width=mull)
    draw.rectangle(_box(w,h,(.056,.7,.507,.744)),fill="#B89875",outline="#403E43",width=2)
    draw.rectangle(_box(w,h,(.06,.725,.506,.748)),fill="#795C4C")
    # Warm-to-cool wall panelling and vertical architecture.
    for x in (.028,.521,.957):
        draw.rectangle(_box(w,h,(x,.02,x+.014,.81)),fill="#294550")
        draw.line(_box(w,h,(x+.018,.07,x+.018,.792)),fill="#947A64",width=1)
    draw.line(_box(w,h,(0,.075,1,.075)),fill="#9E8270",width=max(2,round(.008*h)))
    draw.line(_box(w,h,(0,.797,1,.797)),fill="#BB956E",width=max(3,round(.014*h)))
    # Antique walnut bookshelf, cut-paper compartments, distinct colored book spines.
    draw.rounded_rectangle(_box(w,h,(.605,.106,.937,.695)),radius=max(4,round(.012*h)),
                           fill="#362E31",outline="#A17D5C",width=max(2,round(.012*h)))
    shelves=[(.175,.342),(.369,.529),(.557,.678)]
    spine_colors=["#C18B60","#728A80","#B66F68","#DDD1A3","#567A87",
                  "#91718B","#8E9972","#D7A674","#C7B69C"]
    for lo,hi in shelves:
        draw.rectangle(_box(w,h,(.63,lo,.915,hi)),fill="#243F46")
        cursor=.641
        while cursor<.907:
            bw=rng.uniform(.013,.024)
            tilt=rng.uniform(-.006,.005)
            bh=rng.uniform(.11,.15)
            bottom=hi-.011
            x0=cursor*w
            draw.polygon([(x0,(bottom-bh)*h),(x0+bw*w,(bottom-bh+tilt)*h),
                          (x0+bw*w,bottom*h),(x0,bottom*h)],
                         fill=rng.choice(spine_colors))
            draw.line((round(x0+3),round((bottom-bh+.028)*h),
                       round(x0+3),round((bottom-.016)*h)),
                      fill="#DFC398",width=1)
            cursor+=bw+rng.uniform(.003,.006)
        draw.rectangle(_box(w,h,(.605,hi,.937,hi+.019)),
                       fill="#B08B69",outline="#45383A",width=1)
    # Ground has angled bands to suggest physical depth and floorboards.
    draw.polygon([(0,round(h*.798)),(w,round(h*.798)),(w,h),(0,h)],fill="#6C6259")
    for i in range(12):
        yy=.804+i*.022
        draw.line(_box(w,h,(0,yy,1,yy)),fill="#807265",width=1)
    for x in (.02,.25,.55,.78):
        draw.line(_box(w,h,(x,.81,x+(.5-x)*.2,1)),fill="#504D49",width=1)
    # Table with tapered legs and a beveled top, placed between shelf and character.
    draw.polygon([(.495*w,.687*h),(.87*w,.687*h),(.89*w,.727*h),(.478*w,.727*h)],
                 fill="#C1A07B")
    draw.polygon([(.489*w,.722*h),(.886*w,.722*h),(.864*w,.751*h),(.505*w,.75*h)],
                 fill="#715B4D")
    for x0 in (.536,.815):
        draw.polygon([(x0*w,.742*h),((x0+.033)*w,.742*h),
                      ((x0+.026)*w,.845*h),((x0-.012)*w,.846*h)],
                     fill="#443D3C")
    # Warm books and scrolls on the tabletop.
    draw.polygon([(.72*w,.68*h),(.831*w,.676*h),(.842*w,.699*h),(.723*w,.704*h)],
                 fill="#CDB88A")
    draw.line(_box(w,h,(.732,.688,.828,.685)),fill="#F0DBB3",width=max(1,round(.009*h)))
    # Potted plant on far edge with asymmetrical leaf silhouettes.
    draw.polygon([(.923*w,.74*h),(.96*w,.74*h),(.957*w,.807*h),(.927*w,.807*h)],
                 fill="#A77564")
    draw.line(_box(w,h,(.944,.732,.946,.534)),fill="#587466",width=max(2,round(.009*h)))
    for k in range(9):
        ax=.943+.035*math.sin(k*1.9)
        ay=.67-k*.019
        leaf=(round((ax-.025)*w),round((ay-.025)*h),
              round((ax+.024)*w),round((ay+.024)*h))
        draw.ellipse(leaf,fill="#507C72" if k%2 else "#76917D")
    # Stable fiber grain that remains fixed between frames.
    for i in range(max(140,w*h//850)):
        px=rng.randrange(w);py=rng.randrange(h)
        tone=rng.choice(("#BEB2A1","#657A77","#D1BC9A"))
        if i%5:
            draw.point((px,py),fill=tone)
    return img


@lru_cache(maxsize=16)
def _vignette(w: int,h: int) -> Image.Image:
    """Alpha mask with a stable radial exposure falloff, calculated once."""
    rgba=Image.new("RGBA",(w,h))
    pixels=[]
    for y in range(h):
        ny=(y+.5-h*.49)/(h*.72)
        for x in range(w):
            nx=(x+.5-w*.5)/(w*.73)
            r=math.sqrt(nx*nx+ny*ny)
            strength=max(0,min(.38,(r-.36)*.42))
            pixels.append((4,13,20,round(strength*255)))
    rgba.putdata(pixels)
    return rgba


def render_atelier_background(scene: dict, w: int, h: int,t:float) -> Image.Image:
    seed=int.from_bytes(sha256(scene["id"].encode()).digest()[:4],"big")
    img=atelier_background(w,h,seed).copy()
    # A slow moonbeam, translucent shafts and particulate depth.
    veil=Image.new("RGBA",(w,h),(0,0,0,0))
    d=ImageDraw.Draw(veil)
    d.polygon([(round(.095*w),round(.12*h)),(round(.43*w),round(.115*h)),
               (round(.74*w),round(.98*h)),(round(.21*w),round(.99*h))],
              fill=(209,224,216,15))
    rng=random.Random(seed+243)
    for i in range(max(18,round(w*h/15500))):
        sx=rng.uniform(.08,.79)*w
        sy=((rng.uniform(0,1)+t*(.006+(i%4)*.002))%1)*h
        rad=max(1,round(h*(.0013+(i%3)*.001)))
        d.ellipse((sx-rad,sy-rad,sx+rad,sy+rad),
                  fill=(241,225,190,45+(i%3)*20))
    return Image.alpha_composite(img.convert("RGBA"),veil).convert("RGB")


def add_prop_light(image:Image.Image, props:list[dict],states:dict,time:float) -> Image.Image:
    w,h=image.size
    lanterns=[(p,states[p["id"]]) for p in props if p["shape"]=="lantern"]
    if not lanterns:
        return image
    light=Image.new("RGBA",(w,h),(0,0,0,0))
    draw=ImageDraw.Draw(light)
    for p,state in lanterns:
        x,y=state.center[0]*w,state.center[1]*h
        pulse=1+.08*math.sin(time*3.6+1.4)
        r=h*.23*pulse
        for n in range(12,0,-1):
            frac=n/12
            draw.ellipse((x-r*frac,y-r*frac,x+r*frac,y+r*frac),
                         fill=(244,162,69,round(4+13*(1-frac)**2)))
    light=light.filter(ImageFilter.GaussianBlur(max(1,round(h*.035))))
    return Image.alpha_composite(image.convert("RGBA"),light).convert("RGB")


def foreground_and_grade(image:Image.Image,scene:dict,t:float) -> Image.Image:
    w,h=image.size
    # Decorative branches cross in front of the camera, creating true depth.
    foreground=ImageDraw.Draw(image)
    for side in (-1,1):
        start=w*(0 if side<0 else 1)
        drift=math.sin(t*.43+side)*w*.004
        path=[(start,h*.1),(start+side*(-w*.035)+drift,h*.19),
              (start+side*(-w*.10)+drift,h*.29)]
        foreground.line([(round(x),round(y)) for x,y in path],
                        fill="#1A343E",width=max(2,round(h*.014)),joint="curve")
        for i in range(5):
            px=path[1][0]+side*(-.022*w)*i
            py=h*(.15+i*.029)
            rad=h*(.014+.004*(i%2))
            foreground.ellipse((px-rad*1.4,py-rad*.8,px+rad*1.4,py+rad*.8),
                               fill="#2B5657")
    overlay=_vignette(w,h)
    return Image.alpha_composite(image.convert("RGBA"),overlay).convert("RGB")


def cinematic_caption(image:Image.Image,text:str) -> None:
    """Quiet, letterspaced subtitle on a small translucent bottom plaque."""
    w,h=image.size
    font=_font(round(.034*h),serif=True)
    d=ImageDraw.Draw(image)
    text=text.strip()
    limit=w*.69
    while len(text)>3 and d.textbbox((0,0),text,font=font)[2]>limit:
        text=text[:-2].rstrip()+"…"
    bbox=d.textbbox((0,0),text,font=font)
    tw=bbox[2]-bbox[0]
    pad=round(.028*w)
    y=h*.882
    box=(round((w-tw)/2-pad),round(y-h*.012),
         round((w+tw)/2+pad),round(y+h*.075))
    d.rounded_rectangle(box,radius=max(4,round(h*.011)),
                        fill="#23363D",outline="#B99F7E",
                        width=max(1,round(h*.002)))
    d.text(((w-tw)/2,y),text,font=font,fill="#F4E6CC")


def title_overlay(image:Image.Image, scene:dict, t:float) -> None:
    title=scene.get("title_card")
    if not title:
        return
    start,end=title.get("start",0),title.get("end",2.5)
    if not start<=t<end:
        return
    w,h=image.size
    d=ImageDraw.Draw(image)
    fade=min(1,(t-start)/.55,(end-t)/.55)
    font=_font(round(h*.056),serif=True)
    text=title["text"]
    width=d.textbbox((0,0),text,font=font)[2]
    x=w*.5-width*.5
    y=h*.104-(1-fade)*h*.025
    overlay=Image.new("RGBA",image.size,(0,0,0,0))
    od=ImageDraw.Draw(overlay)
    od.text((round(x),round(y)),text,font=font,
            fill=(250,229,192,round(240*fade)),
            stroke_width=max(0,round(h*.002)),stroke_fill=(24,48,55,round(170*fade)))
    image.paste(Image.alpha_composite(image.convert("RGBA"),overlay).convert("RGB"))
