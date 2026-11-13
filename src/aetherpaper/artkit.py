"""Generate the original AetherPaper Atelier Courier cutout art pack.

All transparent parts are authored with Pillow primitives and hand-laid shapes.
This is a freely reproducible proof-of-pipeline asset kit: it is not a substitute
for a professional artist's original layered illustrations.

Each PNG is drawn along its positive local X bone axis (pivot at [0, .5]).
Its height is set independently to control the part's physical cross section.
"""
from __future__ import annotations

from pathlib import Path
import math
import random
from PIL import Image, ImageDraw

PALETTE = {
    "outline":"#25333D", "coat":"#2A7781", "coat_light":"#538E91",
    "coat_dark":"#1F5662", "gold":"#D9A96B", "gold_light":"#F3D09B",
    "wine":"#A25857", "skin":"#DDB089", "skin_light":"#F1CBA4",
    "skin_shadow":"#BA886D", "hair":"#33434E", "hair_light":"#62707B",
    "trousers":"#41566B", "trousers_light":"#708198", "boot":"#283840",
    "boot_light":"#5C5C5C", "ivory":"#F5E5C8"
}


def _part(w:int=640,h:int=340):
    return Image.new("RGBA",(w,h),(0,0,0,0))


def _poly(draw,points,color,outline="#25333D",edge=7):
    pts=[(round(x),round(y)) for x,y in points]
    draw.polygon(pts,fill=color)
    if edge:
        draw.line(pts+[pts[0]],fill=outline,width=edge,joint="curve")


def _curve(a,b,c,d,n=18):
    result=[]
    for i in range(n+1):
        t=i/n
        u=1-t
        result.append((u**3*a[0]+3*u*u*t*b[0]+3*u*t*t*c[0]+t**3*d[0],
                       u**3*a[1]+3*u*u*t*b[1]+3*u*t*t*c[1]+t**3*d[1]))
    return result


def _fabric(img:Image.Image,seed:int=0,amount:int=320)->None:
    # Texture is fixed at art generation time, no per-frame random grain flicker.
    r=random.Random(seed)
    d=ImageDraw.Draw(img)
    for i in range(amount):
        x=r.randrange(img.width);y=r.randrange(img.height)
        if img.getpixel((x,y))[3]<200:
            continue
        color=(240,225,203,33) if i%2 else (17,32,39,35)
        d.line((x,y,x+r.randint(2,6),y+1),fill=color,width=1)


def _torso():
    img=_part(640,690);d=ImageDraw.Draw(img)
    # Hips at x=0, shoulders at x=540. Cutout mass is asymmetrically tailored.
    coat=[(10,256),(130,210),(350,187),(510,142),(619,210),
          (620,515),(515,577),(350,506),(145,493),(3,449)]
    _poly(d,coat,PALETTE["coat"])
    _poly(d,[(0,366),(160,325),(425,310),(594,328),
             (590,393),(430,389),(161,414)],PALETTE["coat_dark"],edge=0)
    _poly(d,[(30,260),(330,201),(580,170),(565,238),(326,278),
             (57,345)],PALETTE["coat_light"],edge=0)
    # Waist darts and button fly.
    d.line((130,235,157,487),fill="#A4B5AC",width=5)
    d.line((408,198,405,503),fill="#1C505D",width=6)
    for x,y in [(167,331),(284,319),(393,312),(510,314)]:
        d.ellipse((x-10,y-10,x+10,y+10),fill=PALETTE["gold_light"],
                  outline="#625346",width=3)
    # Central open lapels and shirt panel.
    _poly(d,[(406,259),(588,260),(562,392),(420,385)],PALETTE["ivory"],edge=3)
    _poly(d,[(470,219),(630,218),(568,306),(507,292)],PALETTE["coat_dark"])
    _poly(d,[(475,480),(625,473),(561,392),(492,406)],PALETTE["coat_light"])
    d.line((38,442,140,452,245,444),fill="#172C3A",width=8,joint="curve")
    d.line((80,255,315,218),fill="#A6C1BA",width=4)
    _fabric(img,101)
    return img


def _cape():
    img=_part(640,490);d=ImageDraw.Draw(img)
    cape=_curve((0,235),(130,145),(260,90),(512,90))
    cape+=_curve(cape[-1],(559,123),(600,195),(615,275))
    cape+=_curve(cape[-1],(540,360),(410,397),(316,377))
    cape+=_curve(cape[-1],(190,335),(75,315),(0,305))
    _poly(d,cape,PALETTE["wine"],edge=7)
    ribbon=_curve((14,240),(260,200),(470,155),(592,277))
    d.line([(round(x),round(y)) for x,y in ribbon],
           fill="#D98A75",width=12,joint="curve")
    d.line((75,310,314,352,470,336),fill="#693B47",width=8,joint="curve")
    for x in range(130,590,55):
        d.line((x,364,x-15,385),fill="#DBA778",width=3)
    _fabric(img,307,260)
    return img


def _upper_arm(far:bool=False):
    img=_part(640,360);d=ImageDraw.Draw(img)
    color=PALETTE["coat_dark"] if far else PALETTE["coat"]
    _poly(d,[(0,67),(195,84),(480,108),(625,127),
             (632,243),(465,265),(206,290),(1,302)],color)
    _poly(d,[(16,90),(185,104),(508,137),(550,170),
             (271,188),(17,183)],PALETTE["coat_light"] if not far else PALETTE["coat"],edge=0)
    d.line((476,115,490,258),fill=PALETTE["gold"],width=9)
    for x in (190,234):
        d.line((x,85,x+17,286),fill=PALETTE["coat_dark"],width=3)
    _fabric(img,440+far,210)
    return img


def _forearm(far:bool=False):
    img=_part(640,330);d=ImageDraw.Draw(img)
    color=PALETTE["coat_dark"] if far else PALETTE["coat"]
    _poly(d,[(0,80),(400,100),(542,124),(540,237),
             (400,246),(0,258)],color)
    _poly(d,[(45,99),(390,117),(528,137),(430,160),(72,149)],
          PALETTE["coat_light"] if not far else PALETTE["coat"],edge=0)
    d.line((398,100,408,249),fill=PALETTE["gold"],width=8)
    # Deliberately integrated hand/glove at the end of the wrist.
    d.ellipse((493,104,639,250),fill=PALETTE["skin"],outline=PALETTE["outline"],width=7)
    d.ellipse((541,114,615,145),fill=PALETTE["skin_light"])
    d.arc((520,153,620,245),200,325,fill=PALETTE["skin_shadow"],width=5)
    _fabric(img,520+far,180)
    return img


def _thigh(side:int):
    img=_part(640,390);d=ImageDraw.Draw(img)
    _poly(d,[(0,62),(210,60),(529,108),(635,130),
             (632,274),(534,290),(220,324),(0,317)],
          PALETTE["trousers"])
    _poly(d,[(16,100),(325,113),(560,146),(543,177),(201,182),
             (20,166)],PALETTE["trousers_light"],edge=0)
    d.line((72,309,576,261),fill="#293D54",width=5)
    d.line((130,60,128,316),fill=PALETTE["gold"],width=5)
    _fabric(img,692+side,190)
    return img


def _shin(side:int):
    img=_part(640,390);d=ImageDraw.Draw(img)
    _poly(d,[(0,105),(365,110),(456,89),(589,91),
             (625,143),(637,271),(563,297),(425,261),(0,266)],
          PALETTE["trousers"])
    _poly(d,[(350,100),(634,102),(639,288),(455,319),(339,272)],
          PALETTE["boot"])
    d.line((390,133,625,144),fill=PALETTE["boot_light"],width=12)
    # Toe cap and hard leather sole.
    _poly(d,[(485,240),(636,244),(639,304),(551,338),(423,293)],
          "#24333C")
    d.line((455,290,564,333,633,296),fill=PALETTE["gold"],width=11,joint="curve")
    for i in range(3):
        d.line((440+i*45,159,450+i*40,230),fill="#B9A48E",width=6)
    _fabric(img,834+side,170)
    return img


def _head():
    img=_part(640,760);d=ImageDraw.Draw(img)
    # Longitudinal face bone: jaw near 8% and crown at 96%.
    d.ellipse((20,84,629,669),fill=PALETTE["skin"],
              outline=PALETTE["outline"],width=10)
    d.ellipse((76,112,563,455),fill=PALETTE["skin_light"])
    d.arc((27,132,613,676),235,322,fill=PALETTE["skin_shadow"],width=13)
    d.ellipse((205,610,334,721),fill=PALETTE["skin_shadow"])
    d.ellipse((214,600,326,694),fill=PALETTE["skin"])
    d.line((48,415,96,450,168,461),fill=PALETTE["skin_shadow"],width=8,joint="curve")
    return img


def _face(expression:str):
    img=_part(640,760);d=ImageDraw.Draw(img)
    # This entire facial painting is aligned to the head sprite's bone.
    for y in (266,492):
        # Eyes become two rows because local +X rotates to vertical on screen.
        d.arc((320,y-38,540,y+43),178,350,fill=PALETTE["hair"],width=10)
        d.ellipse((407,y-24,449,y+19),fill=PALETTE["hair"])
        d.ellipse((417,y-20,427,y-10),fill="#FDF3DE")
    # Highlights and angular nose.
    d.line((279,361,248,378,270,391),fill=PALETTE["skin_shadow"],width=8,
           joint="curve")
    if expression=="happy":
        d.arc((167,327,264,448),10,165,fill="#9D504E",width=12)
    elif expression=="sad":
        d.arc((170,327,259,448),198,340,fill="#9D504E",width=12)
        d.line((332,229,378,213),fill=PALETTE["hair"],width=8)
    elif expression=="surprised":
        d.ellipse((195,365,257,422),fill="#87484E")
    else:
        d.arc((182,348,248,423),5,154,fill="#985E53",width=9)
    return img


def _mouth(is_open:bool):
    img=_part(640,760);d=ImageDraw.Draw(img)
    if is_open:
        d.ellipse((179,359,267,427),fill="#6D3744")
        d.arc((183,365,264,422),193,350,fill="#F5C5AA",width=8)
    else:
        d.arc((180,346,258,424),6,154,fill="#985E53",width=9)
    return img


def _hair_front():
    img=_part(640,760);d=ImageDraw.Draw(img)
    fringe=_curve((264,91),(388,-24),(545,40),(621,145))
    fringe+=_curve(fringe[-1],(660,320),(560,324),(515,260))
    fringe+=_curve(fringe[-1],(475,218),(394,216),(362,266))
    fringe+=_curve(fringe[-1],(292,312),(255,282),(212,245))
    fringe+=_curve(fringe[-1],(171,170),(205,106),(264,91))
    _poly(d,fringe,PALETTE["hair"])
    d.arc((298,54,606,297),201,345,fill=PALETTE["hair_light"],width=16)
    for i in range(4):
        d.arc((270+i*52,120,480+i*42,345),180,267,
              fill="#50616A",width=6)
    return img


def _hair_back():
    img=_part(640,520);d=ImageDraw.Draw(img)
    wisp=_curve((12,257),(114,96),(259,81),(384,132))
    wisp+=_curve(wisp[-1],(472,173),(574,135),(637,224))
    wisp+=_curve(wisp[-1],(531,387),(414,341),(345,348))
    wisp+=_curve(wisp[-1],(247,411),(119,420),(12,257))
    _poly(d,wisp,PALETTE["hair"])
    d.arc((90,154,563,395),203,330,fill=PALETTE["hair_light"],width=12)
    return img


def _scarf():
    img=_part(640,670);d=ImageDraw.Draw(img)
    _poly(d,[(13,100),(185,92),(431,111),(607,194),
             (637,301),(538,346),(381,323),(141,308),(8,292)],
          PALETTE["wine"])
    _poly(d,[(152,123),(557,146),(615,255),(376,250),(134,215)],
          "#C87968",edge=0)
    d.line((10,300,440,325,603,289),fill=PALETTE["gold"],width=12,joint="curve")
    for n in range(5):
        x=490+n*25
        d.line((x,313,x+6,365),fill=PALETTE["gold_light"],width=6)
    return img


BUILDERS = {
    "cape":_cape,
    "thigh_l":lambda:_thigh(-1),"shin_l":lambda:_shin(-1),
    "thigh_r":lambda:_thigh(1),"shin_r":lambda:_shin(1),
    "arm_l":lambda:_upper_arm(True),"forearm_l":lambda:_forearm(True),
    "torso":_torso,"arm_r":lambda:_upper_arm(False),
    "forearm_r":lambda:_forearm(False),
    "head":_head,"hair_back":_hair_back,"hair_front":_hair_front,
    "scarf":_scarf,
    **{"face_"+e:(lambda e=e:_face(e)) for e in ("neutral","happy","sad","surprised")},
    "mouth_open":lambda:_mouth(True),
    "mouth_closed":lambda:_mouth(False)
}


def build_artkit(output:str|Path)->dict:
    """Write a complete editable transparent-PNG character kit.

    Original sample assets only. Existing files are never replaced if a user
    has modified them: generated assets have deterministic SHA-256 identities,
    and this command refuses to overwrite divergent existing art.
    """
    from hashlib import sha256
    root=Path(output).resolve()
    root.mkdir(parents=True,exist_ok=True)
    files={}
    import io
    for name,builder in BUILDERS.items():
        sprite=builder()
        temp=io.BytesIO()
        sprite.save(temp,format="PNG",optimize=True)
        payload=temp.getvalue()
        dest=root/(name+".png")
        if dest.exists() and dest.read_bytes()!=payload:
            raise FileExistsError("refusing to replace modified artwork: "+str(dest))
        if not dest.exists():
            dest.write_bytes(payload)
        files[name+".png"]=sha256(payload).hexdigest()
    return {"artkit":"atelier-courier-v0.4","directory":str(root),
            "parts":len(files),"sha256":files,
            "license":"original AetherPaper source-generated assets (MIT)"}
