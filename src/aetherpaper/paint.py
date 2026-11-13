"""Deterministic hand-cut paper illustrations and procedural puppets.

All geometry uses normalized scene coordinates. The procedural renderer
creates actual frame-to-frame animation, not a slideshow or iframe.
"""
from __future__ import annotations
from functools import lru_cache
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from hashlib import sha256
import math
import random
from .model import Project
from .timeline import actor_pose, active_caption, camera_state, lerp
from .rig import advanced_hand, draw_character as draw_rig_character
from .physics import rope_points, prop_state

INK = '#312D34'
OUTLINE = '#5D4B49'


def _rgb(value: str):
    return tuple(int(value[i:i+2], 16) for i in (1, 3, 5))


def _shade(value: str, delta: int = -20) -> tuple[int, int, int]:
    return tuple(max(0, min(255, c+delta)) for c in _rgb(value))


def _font(size: int, bold: bool = False):
    locations = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf',
        '/Library/Fonts/Arial.ttf', 'C:/Windows/Fonts/arial.ttf',
    ]
    for p in locations:
        if Path(p).exists():
            return ImageFont.truetype(p, max(7, size))
    return ImageFont.load_default()


def _ellipse(d: ImageDraw.ImageDraw, bounds, fill, outline=OUTLINE, line=2):
    d.ellipse(tuple(int(round(x)) for x in bounds), fill=fill, outline=outline, width=max(1, int(line)))


def _poly(d: ImageDraw.ImageDraw, points, color, stroke=OUTLINE, w=2, shadow=True):
    pts = [(int(round(x)), int(round(y))) for x, y in points]
    if shadow:
        d.polygon([(x+3, y+4) for x, y in pts], fill='#968474')
    d.polygon(pts, fill=color)
    d.line(pts + pts[:1], fill=stroke, width=max(1, int(w)), joint='curve')


@lru_cache(maxsize=40)
def _background(width: int, height: int, color: str, seed: int) -> Image.Image:
    base = Image.new('RGB', (width, height), _rgb(color))
    d = ImageDraw.Draw(base)
    r = random.Random(seed)
    # Subtle fiber freckles are deterministic, constant across frames (no flicker).
    for _ in range(max(60, (width * height) // 460)):
        x = r.randrange(width); y = r.randrange(height)
        delta = r.choice((-19, -12, -8, 8, 11, 15))
        shade = _shade(color, delta)
        d.ellipse((x, y, x+r.choice((1, 1, 2)), y+1), fill=shade)
    return base


def _paper_rectangle(d, box, color, outline=OUTLINE, width=2):
    x0, y0, x1, y1 = box
    p = [(x0+3, y0), (x1-3, y0+2), (x1, y1-3), (x0+1, y1)]
    _poly(d, p, color, outline, width)


def _draw_room(img: Image.Image, scene: dict) -> None:
    W, H = img.size
    d = ImageDraw.Draw(img)
    wall = scene.get('wall', '#EBD9BA')
    floor = scene.get('floor', '#AD7658')
    d.rectangle((0, 0, W, H*.78), fill=wall)
    d.polygon([(0, H*.78), (W, H*.78), (W, H), (0, H)], fill=floor)
    d.line((0, H*.78, W, H*.78), fill='#71584B', width=max(2, H//120))
    # Paper window, layered window frame and outdoor sky.
    x0, y0, x1, y1 = int(.08*W), int(.17*H), int(.36*W), int(.58*H)
    _paper_rectangle(d, (x0-8,y0-8,x1+8,y1+8), '#F8EACC')
    _paper_rectangle(d, (x0,y0,x1,y1), '#B8D9D8')
    d.ellipse((x0+15,y0+15,x0+45,y0+45), fill='#F9E9B7')
    d.line((x0+(x1-x0)//2,y0,x0+(x1-x0)//2,y1),fill='#F7E3C3',width=7)
    d.line((x0,y0+(y1-y0)//2,x1,y0+(y1-y0)//2),fill='#F7E3C3',width=7)
    _paper_rectangle(d, (W*.56, H*.66, W*.83, H*.70), '#9A6F53')
    _paper_rectangle(d, (W*.59, H*.69, W*.62, H*.86), '#754F3B')
    _paper_rectangle(d, (W*.78, H*.69, W*.81, H*.86), '#754F3B')
    _paper_rectangle(d, (W*.93, H*.47, W*.94, H*.82), '#547E61')
    d.ellipse((W*.87,H*.37,W*.99,H*.59),fill='#7B9870',outline='#516D4B',width=3)


def _draw_layer(img: Image.Image, layer: dict, source: Path, t: float) -> None:
    W,H = img.size
    if t < layer.get('enter', 0):
        return
    kind = layer['type']
    if kind == 'room':
        _draw_room(img, layer)
        return
    if kind == 'rope':
        points=rope_points(tuple(layer['from']),tuple(layer['to']),t,
                           layer.get('sag',.12),layer.get('wind',0))
        d=ImageDraw.Draw(img)
        d.line([(round(x*W),round(y*H)) for x,y in points],
               fill=layer.get('color','#8C7059'),width=max(1,round(H*.012)),joint='curve')
        return
    x,y,w,h = (layer[k] for k in ('x','y','width','height'))
    x0,y0,x1,y1 = x*W,y*H,(x+w)*W,(y+h)*H
    d = ImageDraw.Draw(img)
    c = layer.get('color', '#E8BB85')
    if kind == 'rectangle':
        _paper_rectangle(d, (x0,y0,x1,y1), c, width=max(1,H//280))
    elif kind == 'ellipse':
        _ellipse(d, (x0+3,y0+4,x1+3,y1+4), '#968474', outline=None)
        _ellipse(d,(x0,y0,x1,y1),c, line=max(1,H//240))
    elif kind == 'polygon':
        _poly(d, [(x0+a*w*W, y0+b*h*H) for a,b in layer['points']], c)
    elif kind == 'text':
        d.text((int(x0),int(y0)),layer['text'],font=_font(int(layer.get('font_size',.04)*H),bold=bool(layer.get('bold',True))),fill=c)
    elif kind == 'image':
        path = (source.parent / layer['src']).resolve()
        if not path.is_relative_to(source.parent.resolve()):
            raise ValueError('image path must stay within the project directory')
        with Image.open(path) as asset:
            paper = asset.convert('RGBA')
        size = (max(1,round(w*W)),max(1,round(h*H)))
        paper = paper.resize(size, Image.Resampling.LANCZOS)
        img.paste(paper, (round(x0),round(y0)),paper)


def _draw_prop(d, prop: dict, W:int, H:int, cx:float, cy:float, scale:float=1.0):
    s = H * prop.get('size',.1) * scale
    x,y = cx*W,cy*H
    c = prop.get('color','#BC6B4D')
    shape=prop['shape']
    if shape == 'book':
        _poly(d,[(x-s*.63,y-s*.36),(x+s*.4,y-s*.47),(x+s*.65,y+s*.32),(x-s*.36,y+s*.43)],'#F6E7CC')
        _poly(d,[(x-s*.63,y-s*.44),(x+s*.35,y-s*.54),(x+s*.58,y+s*.23),(x-s*.40,y+s*.34)],c)
        d.line([(x-s*.44,y-s*.44),(x-s*.2,y+s*.32)],fill=_shade(c,-45),width=max(1,round(s*.07)))
    elif shape == 'ball':
        _ellipse(d,(x-s*.5,y-s*.5,x+s*.5,y+s*.5),c,line=2)
        d.arc((x-s*.35,y-s*.35,x+s*.35,y+s*.35),45,240,fill='#F8E2BB',width=max(1,round(s*.07)))
    elif shape == 'cup':
        _poly(d,[(x-s*.38,y-s*.4),(x+s*.37,y-s*.4),(x+s*.27,y+s*.47),(x-s*.28,y+s*.47)],c)
        d.arc((x+s*.15,y-s*.22,x+s*.66,y+s*.27),-80,95,fill=INK,width=max(2,round(s*.12)))
    elif shape == 'box':
        _paper_rectangle(d,(x-s*.5,y-s*.4,x+s*.5,y+s*.45),c)
        d.line((x-s*.48,y-s*.03,x+s*.48,y-s*.03),fill='#E4BA80',width=max(1,round(s*.06)))
    elif shape == 'star':
        pts=[]
        for i in range(10):
            r = s*(.52 if i%2==0 else .23)
            a = -math.pi/2+i*math.pi/5
            pts.append((x+math.cos(a)*r,y+math.sin(a)*r))
        _poly(d,pts,c)


def _hand(actor:dict, pose, W:int, H:int, t:float):
    if 'rig' in actor:
        return advanced_hand(actor,pose,W,H,t)
    s=H*.42*actor.get('scale',1)
    x,y=pose.x*W,pose.y*H
    right_shoulder=(x+s*.14,y-s*.68)
    if pose.reach_prop and pose.pickup < .75:
        # A deliberate reach toward a nearby prop.
        f=pose.pickup/.75
        return x+s*(.25+.37*math.sin(math.pi*f/2)), y-s*(.57-.08*f)
    if pose.holding:
        return x+s*.36, y-s*.53
    if pose.waving:
        return x+s*(.27+0.06*math.sin(t*12)),y-s*.98
    return right_shoulder[0]+s*.14, right_shoulder[1]+s*.22


def _draw_character(d, actor:dict, pose, W:int,H:int,t:float):
    if 'rig' in actor:
        draw_rig_character(d,actor,pose,W,H,t)
        return
    s=H*.42*actor.get('scale',1)
    x,y=pose.x*W,pose.y*H
    shirt=actor.get('shirt','#B46C5A')
    pants=actor.get('pants','#53687C')
    skin=actor.get('skin','#DCA77F')
    hair=actor.get('hair','#51433F')
    line=max(1,round(s*.015))
    shoulder=(x,y-s*.7)
    hip=(x,y-s*.39)
    stride=pose.walk*s*.20
    # Feet, jointed pants and shoes. Animated feet alternate during walking.
    for side in (-1,1):
        knee=(x+side*s*.09+side*stride,y-s*.19)
        foot=(x+side*s*.095+side*stride*1.45,y-s*.012+abs(stride)*(.08 if side<0 else -.08))
        _poly(d,[(hip[0]+side*s*.075,hip[1]),(knee[0]-s*.055,knee[1]),(knee[0]+s*.06,knee[1]),(hip[0]+side*s*.12,hip[1])],pants)
        d.line((knee[0],knee[1],foot[0],foot[1]),fill=_shade(pants,-20),width=max(3,round(s*.105)))
        _ellipse(d,(foot[0]-s*.06,foot[1]-s*.025,foot[0]+s*.11,foot[1]+s*.045),'#38363B',line=line)
    # Torso: paper shirt, shadow and collar.
    _poly(d,[(x-s*.16,y-s*.73),(x+s*.16,y-s*.73),(x+s*.19,y-s*.38),(x-s*.19,y-s*.38)],shirt,w=line)
    _poly(d,[(x-s*.072,y-s*.72),(x+s*.075,y-s*.72),(x,y-s*.64)],'#E5D0AD',w=line,shadow=False)
    # Rear/left arm and mitten.
    d.line((x-s*.145,y-s*.675,x-s*.24,y-s*.52,x-s*.16-stride*.2,y-s*.42),fill=_shade(shirt,-26),width=max(4,round(s*.096)),joint='curve')
    _ellipse(d,(x-s*.20-stride*.2,y-s*.46,x-s*.105-stride*.2,y-s*.39),skin,line=line)
    # Right arm: reach, wave, or hold.
    hx,hy=_hand(actor,pose,W,H,t)
    elbow=((x+s*.14+hx)/2+s*.05,(y-s*.70+hy)/2+s*.025)
    d.line((x+s*.14,y-s*.68,elbow[0],elbow[1],hx,hy),fill=_shade(shirt,-12),width=max(4,round(s*.089)),joint='curve')
    _ellipse(d,(hx-s*.045,hy-s*.045,hx+s*.045,hy+s*.045),skin,line=line)
    # Head and hair cap; cut-paper face is intentionally stylized.
    cx,cy=x,y-s*.86
    rad=s*.17
    _ellipse(d,(cx-rad+3,cy-rad+4,cx+rad+3,cy+rad+4),'#968474',outline=None)
    _ellipse(d,(cx-rad,cy-rad,cx+rad,cy+rad),skin,line=line)
    _ellipse(d,(cx-rad,cy-rad-s*.018,cx+rad,cy-rad+s*.155),hair,line=line)
    _ellipse(d,(cx-rad*.35,cy-s*.016,cx-rad*.20,cy+s*.048),INK,outline=None)
    _ellipse(d,(cx+rad*.20,cy-s*.016,cx+rad*.35,cy+s*.048),INK,outline=None)
    # Mouth opens rhythmically for speech, stays closed otherwise.
    if pose.talking:
        gape = .025 + .075*abs(math.sin(t*math.pi*4.2))
        _ellipse(d,(cx-s*.043,cy+s*.075,cx+s*.043,cy+s*(.075+gape)),INK,outline=None)
    else:
        d.arc((cx-s*.048,cy+s*.055,cx+s*.049,cy+s*.116),0,180,fill=INK,width=line)


def _caption(img, text):
    W,H=img.size
    d=ImageDraw.Draw(img)
    fs=max(11,round(H*.045))
    font=_font(fs,True)
    # Word-wrap based on actual font metrics rather than character count.
    words=text.split(); lines=[]; line=''
    for word in words:
        candidate=(line+' '+word).strip()
        if d.textbbox((0,0),candidate,font=font)[2] > W*.85 and line:
            lines.append(line); line=word
        else:
            line=candidate
    if line: lines.append(line)
    lines=lines[-3:]
    spacing=max(4,round(fs*.25))
    block=len(lines)*(fs+spacing)+fs*.4
    y=H-max(10,H*.04)-block
    d.rounded_rectangle((W*.065,y-fs*.24,W*.935,H-H*.025),radius=fs*.32,fill='#302A2A',outline='#E4C89F',width=max(1,round(H*.003)))
    for line in lines:
        box=d.textbbox((0,0),line,font=font)
        lw=box[2]-box[0]
        d.text(((W-lw)/2,y),line,fill='#FFF5DE',font=font,stroke_width=max(0,round(H*.001)),stroke_fill='#FFF5DE')
        y+=fs+spacing


def render_frame(project:Project, scene:dict, t:float, *, width:int|None=None, height:int|None=None)->Image.Image:
    W=width or project.canvas['width']; H=height or project.canvas['height']
    if W%2 or H%2 or W<64 or H<64:
        raise ValueError('output width and height must be even and >=64')
    seed=int.from_bytes(sha256(scene['id'].encode()).digest()[:4], 'big')
    canvas=_background(W,H,scene.get('background','#F5EAD6'),seed).copy()
    for layer in scene.get('layers',[]):
        _draw_layer(canvas,layer,project.source,t)
    d=ImageDraw.Draw(canvas)
    actors={a['id']:a for a in scene.get('characters',[])}
    poses={aid:actor_pose(scene,a,t) for aid,a in actors.items()}
    def hand_at(aid,when):
        a=actors[aid]
        hp=actor_pose(scene,a,when)
        hx,hy=_hand(a,hp,W,H,when)
        return (hx/W,hy/H)
    states={p['id']:prop_state(scene,p,t,hand_at) for p in scene.get('props',[])}
    for prop in scene.get('props',[]):
        state=states[prop['id']]
        if not state.foreground:
            _draw_prop(d,prop,W,H,*state.center)
    # Draw back-to-front by canvas y.
    for actor in sorted(scene.get('characters',[]),key=lambda a:poses[a['id']].y):
        _draw_character(d,actor,poses[actor['id']],W,H,t)
    for prop in scene.get('props',[]):
        state=states[prop['id']]
        if state.foreground:
            _draw_prop(d,prop,W,H,*state.center,.8 if state.owner else 1)
    cx,cy,zoom=camera_state(scene,t)
    if zoom>1.00001 or abs(cx-.5)>.00001 or abs(cy-.5)>.00001:
        cropW=W/zoom; cropH=H/zoom
        left=max(0,min(W-cropW,cx*W-cropW/2)); top=max(0,min(H-cropH,cy*H-cropH/2))
        canvas=canvas.crop((round(left),round(top),round(left+cropW),round(top+cropH))).resize((W,H),Image.Resampling.BICUBIC)
    caption=active_caption(scene,t)
    if caption:
        _caption(canvas,caption)
    return canvas
