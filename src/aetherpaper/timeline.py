"""Stateless, deterministic timeline and actor/prop motion."""
from __future__ import annotations
from dataclasses import dataclass
import math
from .model import Project
from .choreography import evaluate


def clamp(v: float, a: float = 0, b: float = 1) -> float:
    return max(a, min(b, v))


def ease(v: float) -> float:
    v = clamp(v)
    return v * v * (3 - 2 * v)


def lerp(a: float, b: float, f: float) -> float:
    return a + (b - a) * f


def at_time(project: Project, time: float) -> tuple[dict, float]:
    if time < 0 or time >= project.duration:
        raise ValueError(f'time must be in [0, {project.duration})')
    offset = 0.0
    for scene in project.scenes:
        if time < offset + scene['duration'] - 1e-9:
            return scene, max(0, time - offset)
        offset += scene['duration']
    return project.scenes[-1], project.scenes[-1]['duration'] - 1/project.canvas['fps']


@dataclass(frozen=True)
class Pose:
    x: float
    y: float
    walk: float = 0
    talking: bool = False
    waving: bool = False
    pickup: float = 0
    holding: str | None = None
    reach_prop: str | None = None
    run: float = 0.0
    gesture: str | None = None
    look: tuple[float, float] | None = None
    expression: str = 'neutral'
    mouth: float = 0.0
    gesture_weight: float = 0.0
    bone_angles: dict | None = None
    pose_weight: float = 0.0
    hand_target: tuple[float,float] | None = None
    hand_weight: float = 0.0
    body_shift: tuple[float,float] = (0.,0.)
    foot_targets: dict | None = None
    gaze_weight: float = 1.0
    gait: float | None = None


def actor_pose(scene: dict, actor: dict, t: float) -> Pose:
    """Actions compose by timeline order; walk path is stable after completion."""
    x, y = actor['x'], actor['y']
    walk = 0.0
    talking = False
    waving = False
    pickup = 0.0
    holding = None
    reach_prop = None
    run = 0.0
    gesture = None
    look = None
    expression = 'neutral'
    mouth = 0.0
    gesture_weight = 0.0
    bone_angles = None
    pose_weight = 0.0
    hand_target = None
    hand_weight = 0.0
    body_shift = (0.,0.)
    foot_targets = None
    gaze_weight = 1.0
    gait = None
    for action in scene.get('actions', []):
        if action['target'] != actor['id']:
            continue
        start, end = action['start'], action['end']
        if action['type'] in ('walk', 'run'):
            if t >= start:
                progress = ease((min(t, end) - start) / (end - start))
                x, y = lerp(x, action['to'][0], progress), lerp(y, action['to'][1], progress)
                if t < end:
                    phase = math.sin((t-start) * 2*math.pi*(3.6 if action['type']=='run' else 2.1))
                    if action['type'] == 'run':
                        run = phase
                    else:
                        walk = phase * (0.7 + 0.3 * math.sin(math.pi*progress))
        elif action['type'] == 'speak':
            talking = talking or (start <= t < end)
            if start <= t < end and action.get('mouth_cues'):
                cues = action['mouth_cues']
                relative = t - start
                mouth = cues[0]['openness']
                for left, right in zip(cues, cues[1:]):
                    if relative >= right['at']:
                        mouth = right['openness']
                    elif left['at'] <= relative < right['at']:
                        f = (relative-left['at'])/(right['at']-left['at'])
                        mouth = lerp(left['openness'],right['openness'],f)
                        break
        elif action['type'] == 'look' and t >= start:
            look = tuple(action['to'])
        elif action['type'] == 'gesture' and start <= t < end:
            gesture = action['name']
            gesture_weight = ease(min(1,(t-start)/.15))*ease(min(1,(end-t)/.15))
        elif action['type'] == 'pose' and start <= t < end:
            bone_angles = action['angles']
            pose_weight = ease(min(1,(t-start)/.2))*ease(min(1,(end-t)/.2))
        elif action['type'] == 'expression' and start <= t < end:
            expression = action['state']
        elif action['type'] == 'wave':
            waving = waving or (start <= t < end)
            if start <= t < end:
                gesture_weight = max(gesture_weight,ease(min(1,(t-start)/.15))*ease(min(1,(end-t)/.15)))
        elif action['type'] == 'place' and t >= start:
            if t < end:
                hand_target = tuple(action['to'])
                hand_weight = ease((t-start)/(end-start))
            elif holding == action.get('prop'):
                holding = None
                reach_prop = None
                pickup = 0.0
        elif action['type'] == 'release' and t >= end:
            if holding == action.get('prop'):
                holding = None
                reach_prop = None
                pickup = 0.0
        elif action['type'] == 'pickup' and t >= start:
            holding = action['prop'] if t >= end else None
            pickup = ease((min(t, end)-start)/(end-start))
            reach_prop = action['prop']
            if 'hand_to' in action:
                if t < end:
                    hand_weight = pickup
                    hand_target = tuple(action['hand_to'])
                elif t < end + .45:
                    hand_weight = 1 - ease((t-end)/.45)
                    hand_target = tuple(action['hand_to'])
    # Performance clips overlay movement actions as a separate direction layer;
    # all values are evaluated from absolute scene time, without prior frames.
    for action in scene.get('actions',[]):
        if action['target']!=actor['id'] or action['type']!='performance' or t<action['start']:
            continue
        p=evaluate(action,t)
        if p.position is not None:x,y=p.position
        body_shift=p.body_shift
        if p.look is not None:look=p.look;gaze_weight=p.gaze_weight
        if p.hand_to is not None:
            hand_target=p.hand_to
            hand_weight=p.hand_weight
        if p.angles is not None:
            bone_angles={**(bone_angles or {}),**p.angles}
            pose_weight=1.0
        if p.feet is not None:foot_targets=p.feet
        if p.gait is not None:gait=p.gait
        if p.expression is not None:expression=p.expression
    return Pose(x, y, walk, talking, waving, pickup, holding, reach_prop, run, gesture, look,
                expression, mouth, gesture_weight, bone_angles, pose_weight, hand_target,
                hand_weight, body_shift, foot_targets, gaze_weight, gait)


def active_caption(scene: dict, t: float) -> str | None:
    for action in scene.get('actions', []):
        if action['type'] == 'speak' and action['start'] <= t < action['end']:
            return action['text']
    return None


def camera_state(scene: dict, t: float) -> tuple[float, float, float]:
    cx, cy, zoom = 0.5, 0.5, 1.0
    for action in scene.get('camera', []):
        if t >= action['start']:
            f = ease((min(t, action['end']) - action['start']) / (action['end']-action['start']))
            a = action.get('center_from', [cx, cy]); b = action.get('center_to', a)
            cx, cy = lerp(a[0], b[0], f), lerp(a[1], b[1], f)
            zoom = lerp(action.get('zoom_from', zoom), action.get('zoom_to', zoom), f)
            if 'track' in action:
                actor=next(a for a in scene.get('characters',[]) if a['id']==action['track'])
                tracked=actor_pose(scene,actor,t)
                cx,cy=tracked.x,tracked.y-.23*actor.get('scale',1)
    return cx, cy, zoom
