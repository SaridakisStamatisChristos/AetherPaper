"""Deterministic prop lifecycle, grounded gravity, contact tests and rope motion.

No mutable state is stored across frames: arbitrary time queries produce the same
result. Interactions are calculated from sorted, validated scene events.
"""
from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Callable
from .rig import spring_progress

Point = tuple[float, float]


@dataclass(frozen=True)
class PropState:
    center: Point
    foreground: bool = False
    owner: str | None = None


def circles_touch(a: Point, radius_a: float, b: Point, radius_b: float) -> bool:
    if min(radius_a,radius_b) < 0:
        raise ValueError("negative collision radius")
    return math.dist(a,b) <= radius_a + radius_b


def boxes_overlap(a: tuple[float,float,float,float],
                  b: tuple[float,float,float,float]) -> bool:
    return a[0] <= b[2] and a[2] >= b[0] and a[1] <= b[3] and a[3] >= b[1]


def falling(initial: Point, elapsed: float, gravity: float = 0.9,
            ground: float = .78, bounce: float = .28,
            velocity_x: float = 0.0) -> Point:
    """Analytic vertical motion with repeated damped rebounds and ground clamp."""
    if not (gravity > 0 and 0 <= bounce <= 1):
        raise ValueError("invalid gravity or bounce")
    elapsed = max(0.0,elapsed)
    x = initial[0]+velocity_x*elapsed
    y0 = min(initial[1],ground)
    if elapsed == 0:
        return (x,y0)
    drop = max(0,ground-y0)
    impact = math.sqrt(2*drop/gravity)
    if elapsed <= impact:
        return (x,min(ground,y0+.5*gravity*elapsed*elapsed))
    dt = elapsed-impact
    v = gravity*impact*bounce
    if bounce >= 1 and v > 0:
        flight = 2*v/gravity
        dt %= flight
        return (x,min(ground,ground-v*dt+.5*gravity*dt*dt))
    for _ in range(120):
        if v < 0.0001:
            break
        flight = 2*v/gravity
        if dt < flight:
            return (x,min(ground,ground-v*dt+.5*gravity*dt*dt))
        dt -= flight
        v *= bounce
    return (x,ground)


def rope_points(start: Point, end: Point, time: float,
                sag: float = .12, wind: float = .0,
                segments: int = 24) -> list[Point]:
    """Parabolic sag and damped sinusoidal sway in normalized scene coordinates."""
    if segments < 2 or segments > 256 or not (0 <= sag <= 1 and 0 <= wind <= .5):
        raise ValueError("invalid rope parameters")
    out=[]
    for i in range(segments+1):
        u=i/segments
        x=start[0]+(end[0]-start[0])*u
        y=start[1]+(end[1]-start[1])*u+4*sag*u*(1-u)
        x+=math.sin(time*2.5+u*math.pi)*wind*math.sin(math.pi*u)
        out.append((x,y))
    return out


def prop_state(scene: dict, prop: dict, time: float,
               hand_at: Callable[[str,float],Point]) -> PropState:
    """Evaluate pickup -> carry -> place/release/spring, including follow-on events.

    hand_at(actor_id,time) returns normalized hand coordinates. Actions are
    processed chronologically; source JSON order breaks same-time ties.
    """
    position = (prop['x'], prop['y'])
    owner = None
    freefall = None
    actions = sorted(
        (a for a in scene.get('actions',[])
         if a['type'] in ('pickup','place','release','spring')
         and a.get('prop') == prop['id']),
        key=lambda a:a['start']
    )
    for action in actions:
        start,end=action['start'],action['end']
        if time < start:
            break
        if freefall is not None:
            initial, started, gravity, ground, bounce, vx = freefall
            position=falling(initial,start-started,gravity,ground,bounce,vx)
            freefall=None
        kind=action['type']
        if kind == 'pickup':
            if time < end:
                f=max(0,min(1,(time-start)/(end-start)))
                f=f*f*(3-2*f)
                hand=hand_at(action['target'],time)
                return PropState((position[0]+(hand[0]-position[0])*f,
                                  position[1]+(hand[1]-position[1])*f),True)
            owner=action['target']
        elif kind == 'place':
            destination=tuple(action['to'])
            if time < end:
                f=max(0,min(1,(time-start)/(end-start)))
                f=f*f*(3-2*f)
                hand=hand_at(action['target'],time)
                return PropState((hand[0]+(destination[0]-hand[0])*f,
                                  hand[1]+(destination[1]-hand[1])*f),True,owner)
            position=destination
            owner=None
        elif kind == 'release':
            initial=hand_at(action['target'],start) if owner else position
            freefall=(initial,start,action.get('gravity',.9),
                      action.get('ground',.78),action.get('bounce',.28),
                      action.get('velocity_x',0.0))
            owner=None
        elif kind == 'spring':
            destination=tuple(action['to'])
            if time < end:
                f=spring_progress((time-start),action.get('frequency',2.2),
                                  action.get('damping',.68))
                return PropState((position[0]+(destination[0]-position[0])*f,
                                  position[1]+(destination[1]-position[1])*f))
            position=destination
            owner=None
    if freefall is not None:
        initial, started, gravity,ground,bounce,vx=freefall
        return PropState(falling(initial,time-started,gravity,ground,bounce,vx))
    if owner is not None:
        return PropState(hand_at(owner,time),True,owner)
    return PropState(position)
