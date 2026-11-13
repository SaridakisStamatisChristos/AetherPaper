"""Illustrated, articulated 2D character preset for AetherPaper.

Original vector-like hand-authored geometry, drawn into Pillow. This intentionally
uses anatomical masses rather than stroke-only stick limbs. The same IK hand
coordinates drive both artwork and props; random scene effects do not enter
the character anatomy.
"""
from __future__ import annotations

import math
from PIL import Image, ImageDraw
from .rig import _body, advanced_hand, two_bone_ik


def _rgb(h: str) -> tuple[int, int, int]:
    return tuple(int(h[i:i+2], 16) for i in (1,3,5))


def _shade(h: str, delta: int) -> str:
    return "#" + "".join(f"{max(0,min(255,c+delta)):02x}" for c in _rgb(h))


def _shape(d, pts, fill, ink, outline):
    pts=[(round(x),round(y)) for x,y in pts]
    d.polygon(pts,fill=fill)
    if outline:
        d.line(pts+[pts[0]],fill=ink,width=outline,joint="curve")


def _cubic(a, b, c, e, count=14):
    out=[]
    for n in range(count+1):
        t=n/count
        u=1-t
        out.append((a[0]*u**3+3*b[0]*u*u*t+3*c[0]*u*t*t+e[0]*t**3,
                    a[1]*u**3+3*b[1]*u*u*t+3*c[1]*u*t*t+e[1]*t**3))
    return out


def _mass(d, a, b, radius_a, radius_b, fill, ink, edge):
    """Tapered illustrated upper/lower limb, with dark cut-edge and internal highlight."""
    dx,dy=b[0]-a[0],b[1]-a[1]
    dist=max(.001,math.hypot(dx,dy))
    nx,ny=-dy/dist,dx/dist
    corners=[(a[0]+nx*radius_a,a[1]+ny*radius_a),
             (b[0]+nx*radius_b,b[1]+ny*radius_b),
             (b[0]-nx*radius_b,b[1]-ny*radius_b),
             (a[0]-nx*radius_a,a[1]-ny*radius_a)]
    _shape(d,corners,fill,ink,edge)
    for center,radius in ((a,radius_a),(b,radius_b)):
        d.ellipse((center[0]-radius,center[1]-radius,
                   center[0]+radius,center[1]+radius),fill=fill)
    d.line([(round(a[0]-nx*radius_a*.35),round(a[1]-ny*radius_a*.35)),
            (round(b[0]-nx*radius_b*.35),round(b[1]-ny*radius_b*.35))],
           fill=_shade(fill,13),width=max(1,round(radius_b*.18)))


def draw_illustrated(image: Image.Image, actor: dict, pose, t: float) -> None:
    """Paint a coherent three-quarter-view puppet with a layered coat, scarf,
    tapered IK limbs, fitted boots, sculpted face, windswept hair and fabric folds.
    All geometry is derived from the same normalized actor pose as the timeline.
    """
    W,H=image.size
    joints,s,x,y=_body(actor,pose,W,H,t)
    visual=actor.get("visual",{})
    coat=visual.get("coat",actor.get("shirt","#346879"))
    lining=visual.get("lining","#D6A265")
    skin=actor.get("skin","#E1B28B")
    hair=actor.get("hair","#343C43")
    trousers=actor.get("pants","#3D5262")
    ink="#253340"
    d=ImageDraw.Draw(image)
    edge=max(1,round(s*.010))
    root=joints["pelvis"][0]
    chest=joints["torso"][1]
    neck=joints["neck"][1]
    activity=min(1.0,abs(pose.walk)+abs(pose.run))
    run=abs(pose.run)>.05
    wave=math.sin(t*(17 if run else 11))
    sway=wave*activity*.027*s
    breathe=math.sin(t*2.2)*.009*s

    # Back hair, a connected silhouette with shaped asymmetrical tips.
    head=(neck[0]+.012*s,neck[1]-.052*s)
    hr=s*.175
    backhair=_cubic((head[0]-.18*s,head[1]-.05*s),
        (head[0]-.28*s,head[1]-.23*s),(head[0]+.11*s,head[1]-.3*s),
        (head[0]+.22*s,head[1]-.02*s))
    backhair+=_cubic(backhair[-1],(head[0]+.25*s,head[1]+.07*s),
        (head[0]+.13*s+sway*.7,head[1]+.23*s),
        (head[0]+.07*s+sway,head[1]+.25*s))
    backhair+=_cubic(backhair[-1],(head[0]-.07*s,head[1]+.18*s),
        (head[0]-.22*s,head[1]+.27*s),
        (head[0]-.18*s,head[1]-.05*s))
    _shape(d,backhair,_shade(hair,-8),ink,edge)

    # The near/far boot and trousers are drawn independently with two-bone IK.
    for side in (-1,1):
        phase=t*(17 if run else 11)+(math.pi if side>0 else 0)
        step=math.sin(phase)*(.27 if run else .17)*activity*s
        lift=max(0,math.cos(phase))*(.19 if run else .095)*activity*s
        hip=(root[0]+side*.10*s,root[1]+.005*s)
        target=(x+side*.11*s+step,y-.022*s-lift)
        knee,foot=two_bone_ik(hip,target,.245*s,.258*s,bend=side)
        pants_fill=trousers if side>0 else _shade(trousers,-18)
        _mass(d,hip,knee,.073*s,.061*s,pants_fill,ink,edge)
        _mass(d,knee,foot,.061*s,.044*s,_shade(pants_fill,-5),ink,edge)
        # Curved sturdy boots, not point-feet.
        ankle=(foot[0],foot[1])
        toe=(ankle[0]+(side*.045+.08)*s,ankle[1]+.012*s)
        sole=[(ankle[0]-.06*s,ankle[1]-.023*s),
              (toe[0]+.04*s,toe[1]-.012*s),
              (toe[0]+.045*s,toe[1]+.046*s),
              (ankle[0]-.075*s,ankle[1]+.046*s)]
        _shape(d,sole,"#293640",ink,edge)
        d.line([(round(sole[0][0]),round(sole[0][1]+.032*s)),
                (round(sole[2][0]),round(sole[2][1]-.005*s))],
               fill="#9F907C",width=max(1,round(.011*s)))
        for n in range(2):
            ly=ankle[1]-(.008+n*.018)*s
            d.line((round(ankle[0]-.022*s),round(ly),
                    round(ankle[0]+.015*s),round(ly+.008*s)),
                    fill="#B5A58A",width=max(1,round(.008*s)))

    # Draped coat silhouette: broad shoulder, tapered waist and flowing hem.
    hem_y=y-.17*s
    coat_pts=_cubic((chest[0]-.145*s,chest[1]-.047*s),
                    (x-.27*s,y-.72*s),(x-.22*s+sway,y-.31*s),
                    (x-.28*s+sway,hem_y))
    coat_pts+=_cubic(coat_pts[-1],(x-.16*s+sway*.6,hem_y+.035*s),
                     (x+.05*s+sway,hem_y-.025*s),
                     (x+.28*s+sway*.75,hem_y+.008*s))
    coat_pts+=_cubic(coat_pts[-1],(x+.24*s,y-.38*s),
                     (x+.22*s,y-.66*s),
                     (chest[0]+.14*s,chest[1]-.047*s))
    _shape(d,coat_pts,coat,ink,edge+1)
    # Inner hem, lapels and stitched seams: color contrast reads even in preview.
    _shape(d,[(x-.11*s,y-.43*s),(x+.015*s,y-.71*s),
              (x+.075*s,y-.43*s),(x+.08*s,hem_y)],
           _shade(coat,-21),_shade(coat,-24),max(1,edge-1))
    _shape(d,[(chest[0]-.15*s,chest[1]),(x-.045*s,y-.59*s),
              (x+.015*s,y-.71*s),(chest[0]-.045*s,chest[1]-.055*s)],
           "#B7C0AD",ink,edge)
    _shape(d,[(chest[0]+.14*s,chest[1]),(x+.10*s,y-.59*s),
              (x+.015*s,y-.71*s),(chest[0]+.05*s,chest[1]-.055*s)],
           _shade(coat,20),ink,edge)
    for n in range(3):
        cy=y-(.52-.105*n)*s
        d.ellipse((x+.065*s,cy,x+.085*s,cy+.018*s),
                  fill="#E8BE82",outline=_shade(coat,-35),width=edge)
    d.line([(round(x-.16*s+sway*.7),round(hem_y-.004*s)),
            (round(x-.05*s+sway*.3),round(y-.25*s))],
           fill=_shade(coat,29),width=max(1,round(.014*s)))
    d.line([(round(x+.16*s),round(y-.30*s)),
            (round(x+.24*s+sway*.7),round(hem_y-.004*s))],
           fill=_shade(coat,-24),width=max(1,round(.011*s)))

    # Rear arm, foreground arm: both use consistent joint endpoints.
    for side in (-1,1):
        shoulder=(chest[0]+side*.15*s,chest[1]+.038*s)
        if side>0:
            hand=advanced_hand(actor,pose,W,H,t)
        else:
            neutral=(x-.24*s+sway,y-.49*s)
            hand=neutral
        elbow,actual=two_bone_ik(shoulder,hand,.29*s,.28*s,bend=-side)
        sleeve=coat if side>0 else _shade(coat,-22)
        _mass(d,shoulder,elbow,.083*s,.070*s,sleeve,ink,edge)
        _mass(d,elbow,actual,.070*s,.052*s,_shade(sleeve,6),ink,edge)
        _mass(d,(actual[0]-.013*s,actual[1]-.004*s),
              actual,.055*s,.052*s,lining,ink,edge)
        d.ellipse((actual[0]-.055*s,actual[1]-.062*s,
                   actual[0]+.063*s,actual[1]+.050*s),fill=skin,
                  outline=ink,width=edge)
        d.ellipse((actual[0]+.011*s,actual[1]-.046*s,
                   actual[0]+.05*s,actual[1]-.011*s),fill=_shade(skin,18))

    # Scarf has wind-following overlap and an asymmetrical trailing edge.
    _shape(d,[(x-.075*s,y-.73*s),(x+.09*s,y-.745*s),
              (x+.14*s,y-.68*s),(x-.06*s,y-.67*s)],
           lining,ink,edge)
    tail=_cubic((x-.073*s,y-.692*s),(x-.15*s+sway,y-.64*s),
                (x-.19*s+sway*1.6,y-.56*s),
                (x-.22*s+sway*1.6,y-.515*s))
    tail+=_cubic(tail[-1],(x-.10*s+sway,y-.535*s),
                 (x-.085*s,y-.62*s),
                 (x-.038*s,y-.682*s))
    _shape(d,tail,_shade(lining,-14),ink,edge)

    # Head volume: elongated face, eyelids, nose and cheek, no generic smiley.
    face=(head[0]-.147*s,head[1]-.17*s,
          head[0]+.15*s,head[1]+.19*s)
    d.ellipse((face[0]+.013*s,face[1]+.015*s,
               face[2]+.013*s,face[3]+.015*s),fill=_shade(hair,-16))
    d.ellipse(face,fill=skin,outline=ink,width=edge+1)
    d.ellipse((head[0]+.055*s,head[1]+.008*s,
               head[0]+.134*s,head[1]+.105*s),fill=_shade(skin,11))
    # Whimsical tapered nose and two eyes with slight gaze shift.
    gaze=0.0
    if pose.look is not None:
        gaze=max(-.018*s,min(.018*s,(pose.look[0]*W-head[0])*.055))
    for side in (-1,1):
        ex=head[0]+side*.068*s
        ey=head[1]-.01*s
        d.arc((ex-.047*s,ey-.024*s,ex+.044*s,ey+.02*s),
              195,347,fill=_shade(hair,-10),width=max(1,round(.014*s)))
        d.ellipse((ex-.021*s+gaze,ey-.008*s,
                   ex+.021*s+gaze,ey+.022*s),fill="#24333E")
        d.ellipse((ex-.007*s+gaze,ey-.004*s,
                   ex+.001*s+gaze,ey+.004*s),fill="#F2E9D8")
    d.line([(round(head[0]+.015*s),round(head[1]+.005*s)),
            (round(head[0]+.03*s),round(head[1]+.072*s)),
            (round(head[0]+.009*s),round(head[1]+.076*s))],
           fill=_shade(skin,-32),width=max(1,round(.008*s)),joint="curve")
    expression=pose.expression
    opening=pose.mouth if pose.mouth>0 else (.43*abs(math.sin(t*12)) if pose.talking else 0)
    if opening>0.08 or expression=="surprised":
        gape=max(opening,.8 if expression=="surprised" else 0)
        d.ellipse((head[0]-.033*s,head[1]+.095*s,
                   head[0]+.044*s,head[1]+(.111+.042*gape)*s),
                  fill="#6D3F46")
    else:
        if expression=="sad":
            d.arc((head[0]-.038*s,head[1]+.098*s,
                   head[0]+.045*s,head[1]+.15*s),
                  186,347,fill="#7A4546",width=max(1,round(.011*s)))
        else:
            d.arc((head[0]-.05*s,head[1]+.078*s,
                   head[0]+.06*s,head[1]+.145*s),
                  8,169,fill="#854C48",width=max(1,round(.011*s)))
    # Layered swept hair with individual strands & subtle reflected highlights.
    front=_cubic((head[0]-.154*s,head[1]-.065*s),
                 (head[0]-.18*s,head[1]-.255*s),
                 (head[0]+.15*s,head[1]-.27*s),
                 (head[0]+.157*s,head[1]-.07*s))
    front+=_cubic(front[-1],(head[0]+.095*s,head[1]-.095*s),
                  (head[0]+.06*s,head[1]-.15*s),
                  (head[0]+.025*s,head[1]-.12*s))
    front+=_cubic(front[-1],(head[0]-.07*s,head[1]-.01*s),
                  (head[0]-.12*s,head[1]-.01*s),
                  (head[0]-.154*s,head[1]-.065*s))
    _shape(d,front,hair,ink,edge)
    d.arc((head[0]-.12*s,head[1]-.18*s,head[0]+.11*s,head[1]-.055*s),
          204,334,fill=_shade(hair,38),width=max(1,round(.014*s)))
    for n in range(3):
        ox=.065*n*s
        d.arc((head[0]-.06*s+ox,head[1]-.11*s,
               head[0]+.025*s+ox,head[1]+.10*s),
              200,260,fill=_shade(hair,17),width=max(1,round(.009*s)))
