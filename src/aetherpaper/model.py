"""Versioned scene contract and strict, actionable validation."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json
import math
import re
from typing import Any

HEX_COLOR = re.compile(r'^#[0-9a-fA-F]{6}$')
SHAPES = {'rectangle', 'ellipse', 'polygon', 'text', 'image', 'room', 'rope'}
PROP_SHAPES = {'book', 'ball', 'cup', 'star', 'box', 'lantern'}
ACTION_TYPES = {'walk', 'run', 'pickup', 'speak', 'wave', 'look', 'gesture', 'expression', 'place', 'release', 'spring', 'pose'}

class SceneError(ValueError):
    """Invalid animation project."""


def _fail(path: str, message: str) -> None:
    raise SceneError(f'{path}: {message}')


def _object(value: Any, path: str) -> dict:
    if not isinstance(value, dict):
        _fail(path, 'expected object')
    return value


def _list(value: Any, path: str) -> list:
    if not isinstance(value, list):
        _fail(path, 'expected array')
    return value


def _string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        _fail(path, 'expected nonempty string')
    return value


def _number(value: Any, path: str, lo: float | None = None, hi: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        _fail(path, 'expected finite number')
    v = float(value)
    if lo is not None and v < lo or hi is not None and v > hi:
        _fail(path, f'out of range [{lo}, {hi}]')
    return v


def _color(value: Any, path: str) -> None:
    if not isinstance(value, str) or not HEX_COLOR.fullmatch(value):
        _fail(path, 'expected #RRGGBB color')


def _coord(value: Any, path: str) -> None:
    if not isinstance(value, list) or len(value) != 2:
        _fail(path, 'expected [x, y]')
    _number(value[0], f'{path}[0]', -2, 3)
    _number(value[1], f'{path}[1]', -2, 3)


@dataclass(frozen=True)
class Project:
    source: Path
    data: dict

    @property
    def canvas(self) -> dict:
        return self.data['canvas']

    @property
    def scenes(self) -> list[dict]:
        return self.data['scenes']

    @property
    def duration(self) -> float:
        return sum(scene['duration'] for scene in self.scenes)


def load_project(path: str | Path) -> Project:
    source = Path(path).resolve()
    try:
        data = json.loads(source.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as e:
        raise SceneError(f'{source}: unable to read JSON: {e}') from e
    validate_project(data)
    return Project(source, data)


def validate_project(data: Any) -> None:
    data = _object(data, '$')
    if data.get('version') not in ('0.1', '0.2', '0.3', '0.4'):
        _fail('$.version', 'expected version "0.1", "0.2", "0.3" or "0.4"')
    if data.get('style','paper_cut') not in ('paper_cut','scrapbook','storybook','cinematic_storybook'):
        _fail('$.style','unknown visual preset')
    canvas = _object(data.get('canvas'), '$.canvas')
    for key in ('width', 'height'):
        v = _number(canvas.get(key), f'$.canvas.{key}', 64, 4096)
        if int(v) != v or int(v) % 2:
            _fail(f'$.canvas.{key}', 'must be an even integer')
    fps = _number(canvas.get('fps'), '$.canvas.fps', 1, 60)
    if fps != int(fps):
        _fail('$.canvas.fps', 'must be an integer')
    scenes = _list(data.get('scenes'), '$.scenes')
    if not scenes:
        _fail('$.scenes', 'at least one scene is required')
    ids: set[str] = set()
    total_frames = 0
    for i, scene in enumerate(scenes):
        path = f'$.scenes[{i}]'
        scene = _object(scene, path)
        ident = _string(scene.get('id'), f'{path}.id')
        if ident in ids:
            _fail(f'{path}.id', 'duplicate scene id')
        ids.add(ident)
        dur = _number(scene.get('duration'), f'{path}.duration', 1/fps, 600)
        frames = round(dur * fps)
        if abs(frames / fps - dur) > 1e-6:
            _fail(f'{path}.duration', 'duration must be a multiple of 1/fps')
        total_frames += frames
        _color(scene.get('background', '#F5EAD6'), f'{path}.background')
        aa=_number(scene.get('supersample',1),f'{path}.supersample',1,3)
        if int(aa)!=aa:
            _fail(f'{path}.supersample','must be an integer')
        if scene.get('style',data.get('style','paper_cut')) not in ('paper_cut','scrapbook','storybook','cinematic_storybook'):
            _fail(f'{path}.style', 'unknown visual preset')
        if 'environment' in scene:
            env=_object(scene['environment'],f'{path}.environment')
            if env.get('type')!='moonlit_atelier':
                _fail(f'{path}.environment.type','unknown environment')
        if 'title_card' in scene:
            title=_object(scene['title_card'],f'{path}.title_card')
            _string(title.get('text'),f'{path}.title_card.text')
            a=_number(title.get('start',0),f'{path}.title_card.start',0,dur)
            b=_number(title.get('end',2.5),f'{path}.title_card.end',0,dur)
            if b<=a:
                _fail(f'{path}.title_card.end','must be later than start')
        if 'transition' in scene:
            tr = _object(scene['transition'],f'{path}.transition')
            if tr.get('type') not in ('fade','wipe'):
                _fail(f'{path}.transition.type', 'unsupported transition')
            _number(tr.get('duration',.4), f'{path}.transition.duration',.01,min(2,dur))
        for j, layer in enumerate(_list(scene.get('layers', []), f'{path}.layers')):
            lp = f'{path}.layers[{j}]'
            layer = _object(layer, lp)
            kind = _string(layer.get('type'), f'{lp}.type')
            if kind not in SHAPES:
                _fail(f'{lp}.type', f'unsupported shape {kind!r}')
            if kind == 'rope':
                _coord(layer.get('from'), f'{lp}.from')
                _coord(layer.get('to'), f'{lp}.to')
                _number(layer.get('sag',.12), f'{lp}.sag', 0, 1)
                _number(layer.get('wind',0), f'{lp}.wind', 0, .5)
            if kind not in ('room','rope'):
                for k in ('x', 'y', 'width', 'height'):
                    _number(layer.get(k), f'{lp}.{k}', -2, 3)
            if kind == 'text':
                _string(layer.get('text'), f'{lp}.text')
            if kind == 'image':
                _string(layer.get('src'), f'{lp}.src')
            if kind == 'polygon':
                pts = _list(layer.get('points'), f'{lp}.points')
                if len(pts) < 3:
                    _fail(f'{lp}.points', 'polygon needs at least three points')
                for k, pt in enumerate(pts):
                    _coord(pt, f'{lp}.points[{k}]')
            if 'color' in layer:
                _color(layer['color'], f'{lp}.color')
            if 'outline' in layer:
                _color(layer['outline'], f'{lp}.outline')
            if 'edge_width' in layer:
                _number(layer['edge_width'],f'{lp}.edge_width',0,.08)
            if 'depth' in layer:
                _number(layer['depth'],f'{lp}.depth',0,1)
            if 'enter' in layer:
                _number(layer['enter'], f'{lp}.enter', 0, dur)
        char_ids: set[str] = set()
        for j, actor in enumerate(_list(scene.get('characters', []), f'{path}.characters')):
            cp = f'{path}.characters[{j}]'
            actor = _object(actor, cp)
            aid = _string(actor.get('id'), f'{cp}.id')
            if aid in char_ids:
                _fail(f'{cp}.id', 'duplicate character id')
            char_ids.add(aid)
            for axis in ('x', 'y'):
                _number(actor.get(axis), f'{cp}.{axis}', -1, 2)
            _number(actor.get('scale', 1), f'{cp}.scale', 0.25, 3)
            for k in ('skin', 'shirt', 'pants', 'hair'):
                if k in actor:
                    _color(actor[k], f'{cp}.{k}')
            if 'visual' in actor:
                visual=_object(actor['visual'],f'{cp}.visual')
                if visual.get('type') not in ('illustrated','sprites'):
                    _fail(f'{cp}.visual.type','unsupported character visual')
                if 'rig' not in actor:
                    _fail(f'{cp}.rig','illustrated or sprite characters require a rig object')
                if visual['type']=='sprites':
                    rawrig=_object(actor['rig'],f'{cp}.rig')
                    available={b.get('name') for b in _list(rawrig.get('bones'),f'{cp}.rig.bones') if isinstance(b,dict)}
                    if not available:
                        _fail(f'{cp}.rig.bones','sprite characters need named bones')
                    parts=_list(visual.get('parts'),f'{cp}.visual.parts')
                    if not (1<=len(parts)<=64):
                        _fail(f'{cp}.visual.parts','requires 1..64 image parts')
                    for k,part in enumerate(parts):
                        sp=f'{cp}.visual.parts[{k}]'
                        part=_object(part,sp)
                        if part.get('bone') not in available:
                            _fail(f'{sp}.bone','unknown target bone')
                        _string(part.get('src'),f'{sp}.src')
                        pivot=part.get('pivot',[0,.5])
                        if not isinstance(pivot,list) or len(pivot)!=2:
                            _fail(f'{sp}.pivot','expected [x,y]')
                        for axis,value in enumerate(pivot):
                            _number(value,f'{sp}.pivot[{axis}]',0,1)
                        _number(part.get('scale',1),f'{sp}.scale',.1,4)
                        _number(part.get('z',0),f'{sp}.z',-100,100)
                        if 'expression' in part and part['expression'] not in ('neutral','happy','sad','surprised'):
                            _fail(f'{sp}.expression','unknown expression state')
                        if 'mouth_state' in part and part['mouth_state'] not in ('open','closed'):
                            _fail(f'{sp}.mouth_state','must be open or closed')
                        if set(part)-{'bone','src','pivot','scale','z','expression','mouth_state'}:
                            _fail(sp,'unsupported sprite part fields')
                for key,val in visual.items():
                    if key in ('coat','lining') and visual['type']=='illustrated':
                        _color(val,f'{cp}.visual.{key}')
                    elif key not in ({'type','coat','lining'} if visual['type']=='illustrated' else {'type','parts'}):
                        _fail(f'{cp}.visual.{key}','unknown visual field')
            if 'rig' in actor:
                rig = _object(actor['rig'], f'{cp}.rig')
                lengths = {'torso', 'neck', 'upper_arm', 'forearm', 'thigh', 'shin', 'head'}
                for key, value in rig.items():
                    if key == 'bones':
                        bones = _list(value,f'{cp}.rig.bones')
                        seen: set[str] = set()
                        for n, bone in enumerate(bones):
                            bp=f'{cp}.rig.bones[{n}]'
                            bone = _object(bone,bp)
                            name=_string(bone.get('name'),f'{bp}.name')
                            if name in seen:
                                _fail(f'{bp}.name','duplicate bone')
                            parent=bone.get('parent')
                            if parent is not None and parent not in seen:
                                _fail(f'{bp}.parent','parent must precede child')
                            _number(bone.get('length'),f'{bp}.length',.02,1)
                            _number(bone.get('angle',0),f'{bp}.angle',-math.pi,math.pi)
                            _number(bone.get('at',1),f'{bp}.at',0,1)
                            if 'offset' in bone:
                                offset=bone['offset']
                                if not isinstance(offset,list) or len(offset)!=2:
                                    _fail(f'{bp}.offset','expected [x,y]')
                                for k,axis in enumerate(offset):
                                    _number(axis,f'{bp}.offset[{k}]',-1,1)
                            seen.add(name)
                        if not {'pelvis','torso','neck'} <= seen:
                            _fail(f'{cp}.rig.bones','must contain pelvis, torso and neck bones')
                    elif key in lengths | {'spring'}:
                        _number(value, f'{cp}.rig.{key}', 0.02 if key != 'spring' else 0.1, 1 if key != 'spring' else 12)
                    else:
                        _fail(f'{cp}.rig.{key}', 'unknown rig property')
        prop_ids: set[str] = set()
        for j, prop in enumerate(_list(scene.get('props', []), f'{path}.props')):
            pp = f'{path}.props[{j}]'
            prop = _object(prop, pp)
            pid = _string(prop.get('id'), f'{pp}.id')
            if pid in prop_ids:
                _fail(f'{pp}.id', 'duplicate prop id')
            prop_ids.add(pid)
            shape = _string(prop.get('shape'), f'{pp}.shape')
            if shape not in PROP_SHAPES:
                _fail(f'{pp}.shape', f'unsupported prop shape {shape}')
            for k in ('x', 'y'):
                _number(prop.get(k), f'{pp}.{k}', -2, 3)
            _number(prop.get('size', 0.1), f'{pp}.size', 0.01, 1)
            if 'color' in prop:
                _color(prop['color'], f'{pp}.color')
        for j, action in enumerate(_list(scene.get('actions', []), f'{path}.actions')):
            ap = f'{path}.actions[{j}]'
            action = _object(action, ap)
            typ = _string(action.get('type'), f'{ap}.type')
            if typ not in ACTION_TYPES:
                _fail(f'{ap}.type', f'unsupported action {typ!r}')
            target = _string(action.get('target'), f'{ap}.target')
            if target not in char_ids:
                _fail(f'{ap}.target', f'unknown character {target}')
            start = _number(action.get('start'), f'{ap}.start', 0, dur)
            end = _number(action.get('end'), f'{ap}.end', 0, dur)
            if end <= start:
                _fail(f'{ap}.end', 'must be later than start')
            if typ in ('walk', 'run', 'look'):
                _coord(action.get('to'), f'{ap}.to')
            if typ == 'gesture' and action.get('name') not in ('wave', 'point', 'raise'):
                _fail(f'{ap}.name', 'unknown gesture')
            if typ == 'expression' and action.get('state') not in ('neutral', 'happy', 'sad', 'surprised'):
                _fail(f'{ap}.state', 'unknown expression')
            if typ == 'pose':
                angles=_object(action.get('angles'),f'{ap}.angles')
                if not angles:
                    _fail(f'{ap}.angles','at least one bone angle required')
                actor=next(a for a in scene['characters'] if a['id']==target)
                named={b['name'] for b in actor.get('rig',{}).get('bones',[])} if actor.get('rig',{}).get('bones') else {'pelvis','torso','neck'}
                for name,value in angles.items():
                    if name not in named:
                        _fail(f'{ap}.angles.{name}','unknown bone')
                    _number(value,f'{ap}.angles.{name}',-math.pi,math.pi)
            if typ in ('pickup','place','release','spring'):
                if action.get('prop') not in prop_ids:
                    _fail(f'{ap}.prop', 'unknown prop')
            if typ=='pickup' and 'hand_to' in action:
                _coord(action['hand_to'],f'{ap}.hand_to')
            if typ in ('place','spring'):
                _coord(action.get('to'), f'{ap}.to')
            if typ == 'release':
                _number(action.get('gravity',.9), f'{ap}.gravity', .01, 3)
                _number(action.get('ground',.78), f'{ap}.ground', 0, 2)
                _number(action.get('bounce',.28), f'{ap}.bounce', 0, 1)
                _number(action.get('velocity_x',0), f'{ap}.velocity_x', -2, 2)
            if typ == 'spring':
                _number(action.get('frequency',2.2), f'{ap}.frequency', .1, 12)
                _number(action.get('damping',.68), f'{ap}.damping', .01, .99)
            if typ == 'speak':
                _string(action.get('text'), f'{ap}.text')
                if 'audio' in action:
                    _string(action['audio'], f'{ap}.audio')
                if 'mouth_cues' in action:
                    cues = _list(action['mouth_cues'], f'{ap}.mouth_cues')
                    if not cues:
                        _fail(f'{ap}.mouth_cues', 'requires at least one cue')
                    previous = -1.0
                    for k, cue in enumerate(cues):
                        cue = _object(cue, f'{ap}.mouth_cues[{k}]')
                        stamp = _number(cue.get('at'), f'{ap}.mouth_cues[{k}].at', 0, end-start)
                        if stamp <= previous:
                            _fail(f'{ap}.mouth_cues[{k}].at', 'cues must be strictly increasing')
                        previous = stamp
                        _number(cue.get('openness'), f'{ap}.mouth_cues[{k}].openness', 0, 1)
        # Release and placement must follow a pickup by the same character.
        owned: dict[str,str] = {}
        interactions = sorted(enumerate(scene.get('actions',[])),key=lambda p:p[1]['start'])
        for index, action in interactions:
            if action['type'] == 'pickup':
                if action['prop'] in owned:
                    _fail(f'{path}.actions[{index}]', 'prop already held')
                owned[action['prop']] = action['target']
            elif action['type'] in ('place','release'):
                if owned.get(action['prop']) != action['target']:
                    _fail(f'{path}.actions[{index}]', 'prop must be picked up by this character first')
                owned.pop(action['prop'])
        for j, cam in enumerate(_list(scene.get('camera', []), f'{path}.camera')):
            cp = f'{path}.camera[{j}]'
            cam = _object(cam, cp)
            a = _number(cam.get('start'), f'{cp}.start', 0, dur)
            b = _number(cam.get('end'), f'{cp}.end', 0, dur)
            if b <= a:
                _fail(f'{cp}.end', 'must be later than start')
            if 'track' in cam and cam['track'] not in char_ids:
                _fail(f'{cp}.track','unknown camera tracking character')
            for k in ('zoom_from', 'zoom_to'):
                _number(cam.get(k, 1), f'{cp}.{k}', 1, 2.5)
            for k in ('center_from', 'center_to'):
                if k in cam:
                    _coord(cam[k], f'{cp}.{k}')
    if total_frames > 120_000:
        _fail('$.scenes', 'project exceeds 120,000 frames')
