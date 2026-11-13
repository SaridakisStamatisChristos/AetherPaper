"""Shot-independent animation direction for hand-authored character performance.

The earlier v0.4 rig derives most motion from generic sines. v0.5 lets a
director write reusable, precise performance keyframes in scene JSON: body
location, lean, individual bone angles, gaze, planted foot offsets and hand
targets. This module is deterministic for random-access rendering.

Interpolation uses cubic Hermite with time-aware finite-difference tangents.
All numerical overshoots are limited to each segment's endpoint range. A
'hold' keyframe creates a dramatic deliberate stillness before the next beat.
"""
from __future__ import annotations
from dataclasses import dataclass
from math import isfinite


def _ease(u:float)->float:
    u=max(0.,min(1.,u))
    return u*u*(3-2*u)


def _field(keyframes:list[dict],name:str,t:float,default=None):
    entries=[(k["at"],k[name],k.get("interpolation","smooth")) for k in keyframes if name in k]
    if not entries: return default
    if t<=entries[0][0]:return entries[0][1]
    if t>=entries[-1][0]:return entries[-1][1]
    for i in range(len(entries)-1):
        a,va,mode=entries[i]
        b,vb,_=entries[i+1]
        if a<=t<=b:
            if mode=="hold":return va if t<b else vb
            f=(t-a)/(b-a)
            if mode=="linear":return _mix(va,vb,f)
            if isinstance(va,(list,tuple)):
                return [ _hermite(entries,i,t,index=j) for j in range(len(va))]
            return _hermite(entries,i,t,index=None)
    return entries[-1][1]


def _mix(a,b,t):
    if isinstance(a,(list,tuple)):
        return [float(x)+(float(y)-float(x))*t for x,y in zip(a,b)]
    return float(a)+(float(b)-float(a))*t


def _hermite(entries:list[tuple],i:int,t:float,index:int|None=None)->float:
    def scalar(value):
        return float(value[index]) if index is not None else float(value)
    a,va,_=entries[i]
    b,vb,_=entries[i+1]
    y0,y1=scalar(va),scalar(vb)
    d=b-a
    t=(t-a)/d
    p=entries[i-1] if i>0 else None
    n=entries[i+2] if i+2<len(entries) else None
    if p is not None:
        m0=(y1-scalar(p[1]))/(b-p[0])
    else:
        m0=(y1-y0)/d
    if n is not None:
        m1=(scalar(n[1])-y0)/(n[0]-a)
    else:
        m1=(y1-y0)/d
    # Disallow wiggles/overshoots between equal or reversing values.
    slope=(y1-y0)/d
    if abs(slope)<1e-12:
        m0=m1=0.
    else:
        if m0*slope<0:m0=0.
        if m1*slope<0:m1=0.
        m0=max(-3*abs(slope),min(3*abs(slope),m0))
        m1=max(-3*abs(slope),min(3*abs(slope),m1))
    h00=2*t*t*t-3*t*t+1
    h10=t*t*t-2*t*t+t
    h01=-2*t*t*t+3*t*t
    h11=t*t*t-t*t
    value=h00*y0+h10*d*m0+h01*y1+h11*d*m1
    return max(min(y0,y1),min(max(y0,y1),value))


@dataclass(frozen=True)
class Performance:
    position:tuple[float,float]|None=None
    body_shift:tuple[float,float]=(0.,0.)
    look:tuple[float,float]|None=None
    hand_to:tuple[float,float]|None=None
    hand_weight:float=0.
    gaze_weight:float=0.
    gait:float|None=None
    feet:dict[str,tuple[float,float]]|None=None
    angles:dict[str,float]|None=None
    expression:str|None=None


def evaluate(action:dict,t:float)->Performance:
    """Sample a director-authored performance at scene time t."""
    local=max(0.,min(action["end"]-action["start"],t-action["start"]))
    keyframes=action["keyframes"]
    def take(name,default=None):return _field(keyframes,name,local,default)
    def vec(name,default=None):
        v=take(name,default)
        return tuple(v) if v is not None else None
    positions=vec("position")
    shift=vec("body_shift",(0.,0.))
    look=vec("look")
    hand=vec("hand_to")
    hand_weight=float(take("hand_weight",0.0))
    gaze_weight=float(take("gaze_weight",1.0 if look else 0.0))
    gait=take("gait")
    angles={}
    bone_names={name for k in keyframes for name in k.get("angles",{})}
    for name in bone_names:
        # Keys may omit one bone: interpolate only across events specifying it.
        track=[{"at":k["at"],"value":k["angles"][name],
                "interpolation":k.get("interpolation","smooth")}
               for k in keyframes if name in k.get("angles",{})]
        angles[name]=_field(track,"value",local)
    feet={}
    for side in ("l","r"):
        track=[{"at":k["at"],"value":k["feet"][side],
                "interpolation":k.get("interpolation","smooth")}
               for k in keyframes if side in k.get("feet",{})]
        if track:feet[side]=tuple(_field(track,"value",local))
    expression=None
    for key in keyframes:
        if key["at"]<=local and "expression" in key:
            expression=key["expression"]
    return Performance(positions,shift,look,hand,max(0.,min(1.,hand_weight)),
                       max(0.,min(1.,gaze_weight)),gait,
                       feet or None,angles or None,expression)
