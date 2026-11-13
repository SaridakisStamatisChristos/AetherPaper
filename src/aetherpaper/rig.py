"""Stateless articulated 2-D rigging for the offline Pillow renderer.

Uses the general hierarchical skeleton, two-bone IK and analytic spring response.
All motion is a pure function of scene time, so out-of-order snapshots match
sequential playback. Original Python implementation; no vendored upstream code.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping

Point = tuple[float, float]


@dataclass(frozen=True)
class Bone:
    name: str
    parent: str | None
    length: float
    angle: float = 0.0
    at: float = 1.0


class Skeleton:
    """Named parent-child bones, evaluated in parent-first order."""

    def __init__(self, bones: list[Bone]):
        self.bones = bones
        names: set[str] = set()
        for bone in bones:
            if bone.name in names:
                raise ValueError("duplicate bone: " + bone.name)
            if bone.parent is not None and bone.parent not in names:
                raise ValueError("parent must precede child: " + bone.name)
            if not (math.isfinite(bone.length) and bone.length > 0):
                raise ValueError("bone length must be positive and finite")
            if not (math.isfinite(bone.angle) and 0 <= bone.at <= 1):
                raise ValueError("invalid bone angle or attachment")
            names.add(bone.name)

    def solve(self, root: Point, scale: float = 1.0,
              angles: Mapping[str, float] | None = None) -> dict[str, tuple[Point, Point, float]]:
        """Return start, end and world angle for every jointed bone."""
        angles = angles or {}
        unknown = set(angles) - {b.name for b in self.bones}
        if unknown:
            raise ValueError("unknown bones: " + ", ".join(sorted(unknown)))
        out: dict[str, tuple[Point, Point, float]] = {}
        for bone in self.bones:
            if bone.parent is None:
                start, parent_angle = root, 0.0
            else:
                a, b, parent_angle = out[bone.parent]
                start = (a[0] + (b[0] - a[0]) * bone.at,
                         a[1] + (b[1] - a[1]) * bone.at)
            angle = parent_angle + angles.get(bone.name, bone.angle)
            end = (start[0] + math.cos(angle) * bone.length * scale,
                   start[1] + math.sin(angle) * bone.length * scale)
            out[bone.name] = (start, end, angle)
        return out


def two_bone_ik(root: Point, target: Point, upper: float, lower: float,
                bend: int = 1) -> tuple[Point, Point]:
    """Solve a rigid two-link chain; unreachable targets are clamped to reach."""
    if not (upper > 0 and lower > 0 and math.isfinite(upper) and math.isfinite(lower)):
        raise ValueError("IK link lengths must be finite and positive")
    if bend not in (-1, 1):
        raise ValueError("IK bend must be -1 or 1")
    dx, dy = target[0] - root[0], target[1] - root[1]
    distance = math.hypot(dx, dy)
    ux, uy = (dx / distance, dy / distance) if distance > 1e-12 else (1., 0.)
    d = max(abs(upper - lower) + 1e-9, min(distance, upper + lower - 1e-9))
    along = (upper * upper + d * d - lower * lower) / (2 * d)
    height = math.sqrt(max(0.0, upper * upper - along * along))
    elbow = (root[0] + ux * along - uy * height * bend,
             root[1] + uy * along + ux * height * bend)
    end = (root[0] + ux * d, root[1] + uy * d)
    return elbow, end


def spring_progress(elapsed: float, frequency: float = 3.0,
                    damping: float = 0.68) -> float:
    """Closed-form second-order unit-step response, no mutable simulation."""
    if elapsed <= 0:
        return 0.0
    if frequency <= 0 or not (0 < damping < 1):
        raise ValueError("frequency must be >0 and damping between 0 and 1")
    w = 2 * math.pi * frequency
    wd = w * math.sqrt(1 - damping * damping)
    return 1 - math.exp(-damping * w * elapsed) * (
        math.cos(wd * elapsed) + (damping * w / wd) * math.sin(wd * elapsed)
    )


def _ellipse(draw, p: Point, r: float, color: str, outline: str = "#57494A") -> None:
    draw.ellipse((round(p[0]-r), round(p[1]-r), round(p[0]+r), round(p[1]+r)),
                 fill=color, outline=outline, width=max(1, round(r*.11)))


def _line(draw, points: list[Point], color: str, w: float) -> None:
    draw.line([(round(x), round(y)) for x, y in points], fill=color,
              width=max(2, round(w)), joint="curve")


def _config(actor: dict, key: str, default: float) -> float:
    return actor.get("rig", {}).get(key, default)


def _body(actor: dict, pose, width: int, height: int, time: float):
    s = height * .42 * actor.get("scale", 1)
    x, y = pose.x * width, pose.y * height
    motion = abs(pose.walk) + abs(getattr(pose, "run", 0.0))
    bob = math.sin(time * 2.5) * .004 * s
    bob += min(1.0, motion) * abs(math.sin(time * 13)) * .018 * s
    root = (x, y - .38 * s + bob)
    head_tilt = 0.0
    if pose.look is not None:
        dx, dy = pose.look[0] * width-x, pose.look[1] * height-(y-.88*s)
        head_tilt = max(-.3, min(.3, math.atan2(dy, dx)*.18))
    head_tilt *= spring_progress(max(0, time), _config(actor,"spring",3.0))
    skel = Skeleton([
        Bone("pelvis",None,.05,-math.pi/2),
        Bone("torso","pelvis",_config(actor,"torso",.3),0),
        Bone("neck","torso",_config(actor,"neck",.12),head_tilt),
    ])
    return skel.solve(root,s), s, x, y


def advanced_hand(actor: dict, pose, width: int, height: int, time: float) -> Point:
    joints,s,x,y = _body(actor,pose,width,height,time)
    shoulder = joints["torso"][0]
    shoulder = (shoulder[0]+.155*s, shoulder[1]-.24*s)
    gesture = getattr(pose,"gesture",None)
    if pose.reach_prop and pose.pickup < .75:
        alpha = pose.pickup / .75
        target = (x+s*(.24+.32*alpha), y-s*(.52-.08*alpha))
    elif pose.holding:
        target = (x+.34*s,y-.54*s)
    elif pose.waving or gesture == "wave":
        target = (x+s*(.42+.07*math.sin(time*12)), y-s*(1.02+.04*math.sin(time*11)))
    elif gesture == "point":
        target = (x+.62*s,y-.77*s)
    elif gesture == "raise":
        target = (x+.16*s,y-1.12*s)
    else:
        swing = (pose.walk+getattr(pose,"run",0.0))*.13*s
        target = (x+.25*s-swing,y-.49*s)
    return two_bone_ik(shoulder,target,s*_config(actor,"upper_arm",.29),
                       s*_config(actor,"forearm",.28),bend=-1)[1]


def draw_character(draw, actor: dict, pose, width: int, height: int, time: float) -> None:
    """Render a reusable articulated paper puppet using actual joint coordinates."""
    joints,s,x,y = _body(actor,pose,width,height,time)
    skin = actor.get("skin","#DCA77F")
    shirt = actor.get("shirt","#B46C5A")
    pants = actor.get("pants","#53687C")
    hair = actor.get("hair","#51433F")
    dark = "#322E33"
    hip = joints["pelvis"][0]
    chest = joints["torso"][1]
    # Legs are independent two-bone chains with grounded animated foot targets.
    activity = min(1,abs(pose.walk)+abs(getattr(pose,"run",0)))
    running = abs(getattr(pose,"run",0)) > 0
    cycle = time*(15 if running else 10)
    for side in (-1,1):
        phase = cycle + (0 if side < 0 else math.pi)
        stride = math.sin(phase) * activity * (.27 if running else .17)*s
        lift = max(0,math.cos(phase)) * activity * (.19 if running else .095)*s
        start = (hip[0]+side*.09*s,hip[1])
        foot_target = (x+side*.105*s+stride, y-.015*s-lift)
        knee, foot = two_bone_ik(start,foot_target,
                                 s*_config(actor,"thigh",.23),s*_config(actor,"shin",.23),
                                 bend=side)
        _line(draw,[start,knee,foot],pants,.10*s)
        _ellipse(draw,foot,.057*s,dark)
    # Paper torso follows the solved bone hierarchy.
    torso_start = joints["torso"][0]
    draw.polygon([(round(torso_start[0]-.19*s),round(torso_start[1]+.035*s)),
                  (round(torso_start[0]+.19*s),round(torso_start[1]+.035*s)),
                  (round(chest[0]+.155*s),round(chest[1]-.01*s)),
                  (round(chest[0]-.155*s),round(chest[1]-.01*s))],
                 fill=shirt)
    _line(draw,[torso_start,chest],shirt,.22*s)
    for side in (-1,1):
        shoulder = (chest[0]+side*.155*s,chest[1]+.055*s)
        if side > 0:
            hand = advanced_hand(actor,pose,width,height,time)
        else:
            swing = (pose.walk+getattr(pose,"run",0.0))*.13*s
            hand_target = (x-.25*s+swing, y-.48*s)
            _,hand = two_bone_ik(shoulder,hand_target,
                                 s*_config(actor,"upper_arm",.29),
                                 s*_config(actor,"forearm",.28),bend=1)
        elbow,_ = two_bone_ik(shoulder,hand,
                              s*_config(actor,"upper_arm",.29),
                              s*_config(actor,"forearm",.28),bend=-side)
        _line(draw,[shoulder,elbow,hand],shirt,.085*s)
        _ellipse(draw,hand,.043*s,skin)
    head_base = joints["neck"][1]
    head = (head_base[0],head_base[1]-.055*s)
    radius = s*_config(actor,"head",.17)
    _ellipse(draw,(head[0]+3,head[1]+4),radius,"#988778",outline="#988778")
    _ellipse(draw,head,radius,skin)
    draw.pieslice((head[0]-radius,head[1]-radius*1.1,head[0]+radius,head[1]+radius*.4),
                  180,360,fill=hair)
    eyes_y = head[1]-.008*s
    gaze = 0
    if pose.look is not None:
        gaze = max(-.024*s,min(.024*s,(pose.look[0]*width-head[0])*.06))
    for side in (-1,1):
        _ellipse(draw,(head[0]+side*.065*s+gaze,eyes_y),.014*s,dark,outline=dark)
    expression = getattr(pose,"expression","neutral")
    openness = getattr(pose,"mouth",0.)
    if pose.talking and openness <= 0:
        openness = .24 + .7*abs(math.sin(time*math.pi*4.2))
    if openness > 0 or expression == "surprised":
        gape = (.015+.07*max(openness,.65 if expression=="surprised" else 0))*s
        draw.ellipse((head[0]-.04*s,head[1]+.055*s,
                      head[0]+.04*s,head[1]+.055*s+gape),fill=dark)
    elif expression == "sad":
        draw.arc((head[0]-.05*s,head[1]+.09*s,head[0]+.05*s,head[1]+.15*s),
                 175,355,fill=dark,width=max(1,round(.012*s)))
    else:
        draw.arc((head[0]-.05*s,head[1]+.045*s,head[0]+.05*s,head[1]+.11*s),
                 0,180,fill=dark,width=max(1,round(.012*s)))
