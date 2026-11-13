"""Original expressive storybook portrait layers for the Studio Courier.

Art is painted upright on independent transparent RGBA canvases and rotated
90° clockwise into the engine's longitudinal +X sprite convention. The rig's
normal 90° counterclockwise head rotation restores each image's orientation.
No pretrained illustration or stock image is used: these vector-like forms
are authored in source and can be replaced by professional painted PNGs.
"""
from __future__ import annotations

import math
from PIL import Image, ImageDraw, ImageFilter

W,H=520,620
INK="#392F3B"
SKIN="#DCA47F"
SKIN_LIGHT="#F5CCAB"
SKIN_SHADE="#B97E6B"
BROWN="#523A3D"
HAIR="#49363A"
HAIR_LIGHT="#8A6257"
GOLD="#D9AB7F"


def _painter():
    return Image.new("RGBA",(W,H),(0,0,0,0))


def _curve(p0,p1,p2,p3,n=24):
    points=[]
    for i in range(n+1):
        t=i/n;u=1-t
        points.append((u**3*p0[0]+3*u*u*t*p1[0]+3*u*t*t*p2[0]+t**3*p3[0],
                       u**3*p0[1]+3*u*u*t*p1[1]+3*u*t*t*p2[1]+t**3*p3[1]))
    return points


def _shape(d,points,fill,stroke=INK,w=5):
    pts=[(round(x),round(y)) for x,y in points]
    d.polygon(pts,fill=fill)
    if w:d.line(pts+[pts[0]],fill=stroke,width=w,joint="curve")


def _brow(d,x,y,change):
    # Four subtle acting presets: neutral, smiling, concerned, astonished.
    if change=="happy":
        dy=-9
    elif change=="sad":
        dy=8
    elif change=="surprised":
        dy=-21
    else:dy=0
    d.arc((x-50,y-30+dy,x+50,y+20+dy),188 if change!="sad" else 12,
          330 if change!="sad" else 160,fill=INK,width=8)


def _eye(d,x,y,change):
    if change=="surprised":
        rx,ry=36,43
    elif change=="happy":
        rx,ry=37,20
    elif change=="sad":
        rx,ry=35,25
    else:rx,ry=36,30
    d.ellipse((x-rx,y-ry,x+rx,y+ry),fill="#F9E9D5",outline=INK,width=5)
    d.ellipse((x-17,y-19,x+18,y+22),fill="#A16C52",outline="#6A4C46",width=3)
    d.ellipse((x-10,y-12,x+11,y+14),fill="#332F3A")
    d.ellipse((x-8,y-10,x+2,y),fill="#FFF3E1")
    d.arc((x-rx-2,y-ry-5,x+rx+2,y+ry*.2),180,350,
          fill=INK,width=6)
    if change=="happy":
        d.arc((x-rx,y-ry*.8,x+rx,y+ry),0,168,fill=SKIN_SHADE,width=5)


def _head()->Image.Image:
    im=_painter();d=ImageDraw.Draw(im)
    # Narrow neck emerging from patterned collar.
    _shape(d,[(213,448),(307,447),(324,567),(210,568)],SKIN_SHADE,INK,7)
    _shape(d,[(225,452),(297,452),(302,559),(233,559)],SKIN,INK,3)
    # Ear volume, lobes and warm reflected highlights.
    for sx in (-1,1):
        x=132 if sx<0 else 389
        d.ellipse((x-38,291,x+28,396),fill=SKIN_SHADE,outline=INK,width=6)
        d.ellipse((x-25,308,x+11,368),fill=SKIN,outline=SKIN_LIGHT,width=3)
        d.ellipse((x-8,369,x+11,391),fill=GOLD,outline="#765044",width=4)
    # Sculpted silhouette: forehead -> temples -> cheekbones -> chin.
    outline=[]
    outline+=_curve((256,102),(143,84),(115,158),(119,292))
    outline+=_curve(outline[-1],(123,392),(191,489),(248,514))
    outline+=_curve(outline[-1],(299,519),(394,398),(398,287))
    outline+=_curve(outline[-1],(413,150),(362,104),(256,102))
    _shape(d,outline,SKIN,INK,9)
    # Side shadow, highlights and soft blush as properly clipped transparent art.
    shade=Image.new("RGBA",im.size,(0,0,0,0))
    sh=ImageDraw.Draw(shade)
    sh.ellipse((137,177,381,503),fill=(243,197,158,35))
    sh.ellipse((127,325,241,431),fill=(168,82,87,30))
    sh.ellipse((290,324,392,425),fill=(168,82,87,29))
    shade=shade.filter(ImageFilter.GaussianBlur(17))
    im=Image.alpha_composite(im,shade)
    d=ImageDraw.Draw(im)
    # Nose is a shaped wedge, with cream reflected light and darker nostril.
    path=_curve((255,291),(239,329),(238,344),(218,359))
    path+=_curve(path[-1],(228,382),(260,383),(275,365))
    d.line([(round(x),round(y)) for x,y in path],fill=SKIN_SHADE,width=7,joint="curve")
    d.arc((227,349,286,388),7,150,fill="#915F58",width=5)
    d.line((232,359,240,354),fill=SKIN_LIGHT,width=5)
    # Speckled freckles in two natural arcs, including some broken ink dots.
    for i in range(8):
        for side in (-1,1):
            x=260+side*(67+i*7)
            y=372+int(6*math.sin(i*.86+side))
            r=2+(i%3==0)
            d.ellipse((x-r,y-r,x+r,y+r),fill="#A76E62")
    d.arc((169,381,219,417),15,141,fill=SKIN_LIGHT,width=5)
    d.arc((312,381,361,417),16,139,fill=SKIN_LIGHT,width=5)
    return im.rotate(-90,expand=True)


def _face(expression:str)->Image.Image:
    im=_painter();d=ImageDraw.Draw(im)
    for x in (194,330):
        _brow(d,x,240,expression)
        _eye(d,x,294,expression)
    if expression=="happy":
        for x in (149,366):
            d.arc((x-28,362,x+28,410),20,174,
                  fill="#B66C67",width=5)
    if expression=="sad":
        d.line((171,255,207,246),fill=SKIN_SHADE,width=6)
        d.line((307,246,344,255),fill=SKIN_SHADE,width=6)
    if expression=="surprised":
        d.arc((231,369,291,412),179,351,fill=SKIN_SHADE,width=5)
    return im.rotate(-90,expand=True)


def _mouth(opened:bool)->Image.Image:
    im=_painter();d=ImageDraw.Draw(im)
    if opened:
        d.ellipse((211,406,298,461),fill="#7A414A",outline=INK,width=5)
        d.ellipse((226,435,281,453),fill="#D98281")
        d.arc((223,411,286,436),176,350,fill=SKIN_LIGHT,width=4)
    else:
        smile=_curve((203,422),(233,448),(272,452),(311,420))
        d.line([(round(x),round(y)) for x,y in smile],fill="#8D5357",width=7,joint="curve")
        d.arc((211,417,306,464),5,176,fill=SKIN_SHADE,width=3)
    return im.rotate(-90,expand=True)


def _fringe()->Image.Image:
    im=_painter();d=ImageDraw.Draw(im)
    # Hand-cut asymmetric layered auburn locks with visible paper fiber edges.
    crown=_curve((95,285),(75,150),(120,55),(269,57))
    crown+=_curve(crown[-1],(408,45),(449,110),(421,258))
    crown+=_curve(crown[-1],(373,224),(362,204),(351,172))
    crown+=_curve(crown[-1],(317,237),(255,208),(249,170))
    crown+=_curve(crown[-1],(198,244),(169,244),(159,189))
    crown+=_curve(crown[-1],(152,254),(120,279),(95,285))
    _shape(d,crown,HAIR,INK,9)
    # Three counter-directional locks vary in width and highlight.
    curls=[
        [(100,205),(64,266),(79,361),(119,393),(142,335),(125,262)],
        [(377,142),(422,202),(435,307),(400,365),(374,314),(381,226)],
        [(335,121),(358,162),(333,231),(293,244),(310,192),(286,153)]
    ]
    for n,curl in enumerate(curls):
        _shape(d,curl,"#60464B" if n!=1 else "#503A43",INK,5)
        d.arc((min(p[0] for p in curl)+10,min(p[1] for p in curl)+8,
               max(p[0] for p in curl)-4,max(p[1] for p in curl)-12),
              195,331,fill=HAIR_LIGHT,width=6)
    for i in range(7):
        x=148+i*36
        d.arc((x,79,x+113,177),205,324,
              fill="#977067" if i%2 else HAIR_LIGHT,width=5)
    # Tusks of loose strands silhouette (organic but not flyaway static).
    for x,y in ((102,320),(390,327),(135,235)):
        d.arc((x-30,y-65,x+44,y+83),185,276,fill="#98706A",width=7)
    return im.rotate(-90,expand=True)


def portrait_layers()->dict[str,Image.Image]:
    """Equivalent dimensions/alignment for all head-related sprite slots."""
    return {
        "head":_head(),
        "face_neutral":_face("neutral"),
        "face_happy":_face("happy"),
        "face_sad":_face("sad"),
        "face_surprised":_face("surprised"),
        "mouth_open":_mouth(True),
        "mouth_closed":_mouth(False),
        "hair_front":_fringe()
    }
