"""Stateless, deterministic timeline and actor/prop motion."""
from __future__ import annotations
from dataclasses import dataclass
import math
from .model import Project


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


def actor_pose(scene: dict, actor: dict, t: float) -> Pose:
    """Actions compose by timeline order; walk path is stable after completion."""
    x, y = actor['x'], actor['y']
    walk = 0.0
    talking = False
    waving = False
    pickup = 0.0
    holding = None
    reach_prop = None
    for action in scene.get('actions', []):
        if action['target'] != actor['id']:
            continue
        start, end = action['start'], action['end']
        if action['type'] == 'walk':
            if t >= start:
                progress = ease((min(t, end) - start) / (end - start))
                x, y = lerp(x, action['to'][0], progress), lerp(y, action['to'][1], progress)
                if t < end:
                    walk = math.sin((t-start) * 2*math.pi*2.1) * (0.7 + 0.3 * math.sin(math.pi*progress))
        elif action['type'] == 'speak':
            talking = talking or (start <= t < end)
        elif action['type'] == 'wave':
            waving = waving or (start <= t < end)
        elif action['type'] == 'pickup' and t >= start:
            holding = action['prop'] if t >= end else None
            pickup = ease((min(t, end)-start)/(end-start))
            reach_prop = action['prop']
    return Pose(x, y, walk, talking, waving, pickup, holding, reach_prop)


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
    return cx, cy, zoom
