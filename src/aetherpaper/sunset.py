"""Original cinematic sunset-cliff paper-diorama environment.

Painted directly in Pillow from hand-authored geometry. The relief hierarchy,
sea, headland, village and lighthouse have stable deterministic textures and
color palettes. Nothing is loaded from the Internet at render time.
"""
from __future__ import annotations

from functools import lru_cache
from hashlib import sha256
import math
import random
from PIL import Image,ImageDraw,ImageFilter


def _p(w,h,coords):
    return [(round(x*w),round(y*h)) for x,y in coords]


def _smooth(points,iterations=2):
    points=list(points)
    for _ in range(iterations):
        out=[points[0]]
        for a,b in zip(points,points[1:]):
            out.append((.75*a[0]+.25*b[0],.75*a[1]+.25*b[1]))
            out.append((.25*a[0]+.75*b[0],.25*a[1]+.75*b[1]))
        out.append(points[-1])
        points=out
    return points


def _mountain(d,w,h,outline,fill,back=1):
    silhouette=[(0,1),*outline, (1,1)]
    d.polygon(_p(w,h,silhouette),fill=fill)
    d.line(_p(w,h,outline),fill="#9C8390" if back else "#5B586D",
           width=max(1,round(h*.003)),joint="curve")


def _house(d,w,h,x,y,size,seed):
    r=random.Random(seed)
    width=size*w; height=size*.76*h
    x0=x*w;y0=y*h
    wall=r.choice(["#CFB7AD","#D9C8B6","#C1A6AA","#B8A59B"])
    d.polygon([(x0-width*.5,y0),(x0+width*.5,y0),
               (x0+width*.5,y0-height),(x0-width*.5,y0-height)],fill=wall)
    d.polygon([(x0-width*.56,y0-height),(x0,y0-height*.99-width*.21),
               (x0+width*.57,y0-height)],fill="#796A6C")
    for j in range(2):
        d.rounded_rectangle((x0-width*(.30-j*.30),y0-height*.55,
                             x0-width*(.18-j*.30),y0-height*.23),
                            radius=max(1,round(width*.025)),fill="#F1BD6D")


@lru_cache(maxsize=24)
def _base(w:int,h:int,seed:int)->Image.Image:
    rng=random.Random(seed)
    image=Image.new("RGB",(w,h))
    d=ImageDraw.Draw(image)
    # Multi-band sunset gradient: mauve upper sky through apricot horizon.
    stops=[(0,(92,80,112)),(.34,(169,112,137)),(.67,(233,158,137)),(.84,(255,194,141)),(1,(251,218,170))]
    for y in range(h):
        v=y/h
        for (a,ca),(b,cb) in zip(stops,stops[1:]):
            if a<=v<=b:
                s=(v-a)/(b-a)
                col=tuple(round(ca[i]*(1-s)+cb[i]*s) for i in range(3))
                break
        else:col=stops[-1][1]
        d.line((0,y,w,y),fill=col)
    # Broad feathered cloud bands: fixed shapes, with dark undersides.
    for i in range(13):
        cx=rng.uniform(-.1,1.13)
        cy=rng.uniform(.08,.57)
        length=rng.uniform(.085,.29)
        alpha=70 if i%3 else 125
        d.arc((round((cx-length)*w),round((cy-.05)*h),
               round((cx+length)*w),round((cy+.04)*h)),
              189,332,fill="#E6A7B2" if i%2 else "#C889A6",
              width=max(2,round(h*.012)))
    # Atmosphere behind sun, backed by translucent radial wash.
    halo=Image.new("RGBA",(w,h),(0,0,0,0))
    hd=ImageDraw.Draw(halo)
    sx,sy=.755*w,.425*h
    for i in range(22,0,-1):
        radius=i*h*.012
        strength=round(11+(22-i)*.18)
        hd.ellipse((sx-radius,sy-radius,sx+radius,sy+radius),
                   fill=(255,217,167,strength))
    halo=halo.filter(ImageFilter.GaussianBlur(max(2,round(h*.014))))
    image=Image.alpha_composite(image.convert("RGBA"),halo).convert("RGB")
    d=ImageDraw.Draw(image)
    sun_r=h*.102
    d.ellipse((sx-sun_r,sy-sun_r,sx+sun_r,sy+sun_r),fill="#FFE5AD")
    # Distant ridges in 4 atmospheric depth bands.
    ridges=[
        ([(0,.7),(.09,.61),(.19,.63),(.27,.52),(.37,.65),(.44,.56),
          (.53,.69),(.62,.61),(.72,.67),(.83,.52),(1,.59)],"#B49EAE"),
        ([(0,.735),(.12,.64),(.23,.705),(.34,.58),(.46,.72),(.62,.65),
          (.74,.72),(.85,.63),(1,.68)],"#8F869D"),
        ([(0,.78),(.14,.69),(.27,.76),(.39,.63),(.48,.76),(.56,.70),
          (.74,.81),(.82,.67),(1,.72)],"#626B83"),
    ]
    for outline,color in ridges:
        _mountain(d,w,h,_smooth(outline),color)
    # Sea with winding horizontal pools, distant coastline and broken light.
    d.polygon(_p(w,h,[(0,.77),(.50,.73),(.68,.78),(1,.742),(1,1),(0,1)]),
              fill="#53798C")
    for i in range(130):
        x=rng.uniform(0,1)
        y=rng.uniform(.765,.97)
        length=rng.uniform(.006,.052)*w
        tint=rng.choice(["#9CA2A9","#BDB6B1","#D7BEAD","#8291A0"])
        d.line((round(x*w),round(y*h),round(x*w+length),round(y*h)),
               fill=tint,width=1 if i%3 else 2)
    # Cliff silhouette and painterly contour / geological strata.
    cliff=[(.685,1),(.7,.83),(.748,.735),(.806,.704),(.851,.62),
           (.935,.584),(1,.56),(1,1)]
    d.polygon(_p(w,h,cliff),fill="#505666")
    d.polygon(_p(w,h,[(.74,1),(.77,.816),(.83,.744),(.91,.672),
                      (1,.648),(1,1)]),fill="#71707A")
    d.polygon(_p(w,h,[(.80,.963),(.87,.839),(.91,.729),
                      (.97,.691),(1,.70),(1,1)]),fill="#99817C")
    for i in range(19):
        x=rng.uniform(.76,1.02)
        y=rng.uniform(.65,.98)
        d.line((round(x*w),round(y*h),round((x-.034)*w),round((y+.035)*h)),
               fill="#AD9991" if i%2 else "#4F5866",width=2)
    # Clustered lantern-lit houses perched along the headland.
    for i,(x,y,size) in enumerate([
        (.86,.719,.026),(.887,.685,.028),(.921,.648,.035),
        (.956,.618,.033),(.986,.598,.033),(.905,.738,.025),
        (.948,.694,.024),(.982,.674,.029),(.84,.748,.021)
    ]):
        _house(d,w,h,x,y,size,seed+i+43)
    # Lighthouse on the far ridge: clear recognisable story destination.
    tower_x=.953*w
    d.polygon([(tower_x-13*h*.027,.51*h),
               (tower_x+13*h*.027,.51*h),
               (tower_x+8*h*.027,.34*h),
               (tower_x-8*h*.027,.34*h)],fill="#E4D4C5")
    d.polygon(_p(w,h,[(.932,.358),(.974,.358),(.964,.321),(.943,.321)]),
              fill="#594A57")
    d.rounded_rectangle((round(.947*w),round(.282*h),round(.963*w),round(.336*h)),
                        radius=2,fill="#F8DA9A")
    d.polygon(_p(w,h,[(.941,.288),(.968,.288),(.955,.269)]),
              fill="#554755")
    d.rectangle((round(.951*w),round(.472*h),round(.959*w),round(.493*h)),
                fill="#BD917F")
    # Foreground terrace provides solid ground for planted character feet.
    d.polygon(_p(w,h,[(0,.89),(.19,.867),(.35,.866),(.53,.875),
                     (.75,.88),(.87,.915),(.92,1),(0,1)]),fill="#534F5B")
    d.line(_p(w,h,[(0,.887),(.2,.864),(.39,.866),(.62,.872),(.75,.878)]),
           fill="#BD9879",width=max(3,round(h*.011)),joint="curve")
    d.polygon(_p(w,h,[(0,.955),(.22,.926),(.42,.949),
                     (.62,.931),(.85,.98),(.92,1),(0,1)]),fill="#6B5861")
    for i in range(160):
        xx=rng.uniform(0,.84)*w
        yy=rng.uniform(.885,1)*h
        radius=rng.randrange(1,4)
        d.ellipse((xx-radius,yy-radius,xx+radius,yy+radius),
                  fill="#9C8878" if i%2 else "#4A4A58")
    # Silhouetted red-leaf tree on far left, receding behind actor.
    d.line(_p(w,h,[(.015,.94),(.041,.65),(.067,.52),(.039,.42)]),
           fill="#393F4B",width=max(3,round(.029*h)),joint="curve")
    branches=[
        [(.052,.65),(.008,.59),(-.01,.49)],
        [(.06,.57),(.135,.49),(.158,.42)],
        [(.038,.56),(.094,.34),(.153,.28)]
    ]
    for pts in branches:
        d.line(_p(w,h,pts),fill="#414251",width=max(2,round(h*.011)))
    for i in range(49):
        ax=rng.uniform(-.05,.19)
        ay=rng.uniform(.24,.61)
        rx=rng.uniform(.007,.023)*w
        ry=rng.uniform(.006,.017)*h
        color=rng.choice(["#6A4B59","#955867","#B76F69","#C98975","#614A59"])
        d.ellipse((ax*w-rx,ay*h-ry,ax*w+rx,ay*h+ry),fill=color)
    # Grain is stable across all frames; smaller than designed linework.
    for i in range(max(120,w*h//1150)):
        px=rng.randrange(w);py=rng.randrange(h)
        d.point((px,py),fill=rng.choice(("#BCA5AA","#BFAEA0","#766F80")))
    return image


def sunset_background(scene:dict,w:int,h:int,t:float)->Image.Image:
    seed=int.from_bytes(sha256(scene["id"].encode()).digest()[:4],"big")
    background=_base(w,h,seed).copy()
    # Moving but sparse floating pollen; deterministic & seek-safe.
    dr=ImageDraw.Draw(background)
    r=random.Random(seed+2201)
    for i in range(21):
        nx=r.random()
        ny=r.uniform(.16,.87)
        x=(nx+t*(.002+.0006*(i%4)))%1
        y=(ny+t*.001*(i%2))%1
        radius=max(1,round(h*(.0013+.0008*(i%3))))
        dr.ellipse((round(x*w-radius),round(y*h-radius),
                    round(x*w+radius),round(y*h+radius)),fill="#EFD9B8")
    return background


def sunset_foreground(image:Image.Image,t:float)->Image.Image:
    w,h=image.size
    d=ImageDraw.Draw(image)
    rng=random.Random(3411)
    # Near-camera leaf fronds have their own slow sway and fixed seed.
    for side in (-1,1):
        origin=(0 if side<0 else w,h)
        for i in range(9):
            x=origin[0]+side*(-.027*w+.006*w*math.sin(t*.7+i))
            y=h*(.94+.01*i)
            xx=x+side*(-.018-i*.001)*w
            yy=y-h*(.027+i*.005)
            d.line((round(x),round(y),round(xx),round(yy)),
                   fill="#353E48",width=max(2,round(h*.004)))
            rx=h*(.008+.001*(i%3))
            d.ellipse((xx-rx,yy-rx*.6,xx+rx,yy+rx*.6),
                      fill="#566458" if i%2 else "#6D6B58")
    return image
