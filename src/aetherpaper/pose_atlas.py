"""Full-illustration pose atlas renderer and transparent-sheet importer.

v0.6 intentionally avoids making elaborate characters from primitive polygons.
A full-body, professionally painted character pose is a complete transparent
PNG: anatomy, hands, clothes and facial expression are preserved exactly.

This is deterministic cutout/flipbook animation. It is NOT automatic human
segmentation, AI inference, skeletal skinning, or frame interpolation.
"""
from __future__ import annotations

from functools import lru_cache
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import json
import math
import re

from PIL import Image, ImageOps

STATE_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,39}$")
MAX_SHEET_PIXELS = 24_000_000
MAX_FRAME_PIXELS = 8_000_000
MAX_FRAMES = 128


def safe_asset(root: Path, path: str) -> Path:
    """Restrict sprite references to local project files (including symlinks)."""
    if not isinstance(path, str) or not path or path.startswith(
        ("http:", "https:", "data:", "file:", "/", "\\")
    ) or "\\" in path:
        raise ValueError("sprite source must be a relative local path")
    root = Path(root).resolve()
    target = (root / path).resolve()
    if not target.is_relative_to(root):
        raise ValueError("sprite source escapes project directory")
    if not target.is_file():
        raise FileNotFoundError(f"missing illustrated pose PNG: {path}")
    if target.suffix.lower() != ".png":
        raise ValueError("illustrated poses must use transparent PNG")
    return target


def _read_png(path: str | Path, pixel_limit: int = MAX_FRAME_PIXELS) -> Image.Image:
    with Image.open(path) as source:
        if source.format != "PNG":
            raise ValueError("pose asset must be a real PNG")
        if source.width * source.height > pixel_limit:
            raise ValueError("pose asset exceeds image safety limit")
        if source.mode not in ("RGBA", "LA", "P"):
            raise ValueError("pose asset needs actual transparency; use RGBA PNG")
        rgba = source.convert("RGBA")
    alpha = rgba.getchannel("A")
    alpha_min, alpha_max = alpha.getextrema()
    if alpha_min == alpha_max:
        raise ValueError("pose asset must include transparent background and painted pixels")
    bounds = alpha.getbbox()
    if bounds is None:
        raise ValueError("pose asset has no visible painted artwork")
    if bounds[2] - bounds[0] < 3 or bounds[3] - bounds[1] < 3:
        raise ValueError("pose artwork is too small")
    return rgba


@lru_cache(maxsize=256)
def _pose_png(path: str, mtime_ns: int, file_size: int) -> Image.Image:
    # Cache the exact current content version. Updating the artist's PNG at
    # the same path cannot silently keep an obsolete illustration on screen.
    return _read_png(path)


def _current_pose(path: Path) -> Image.Image:
    info=path.stat()
    return _pose_png(str(path),info.st_mtime_ns,info.st_size)


def select_pose(visual: dict, pose, t: float) -> tuple[str, dict, int]:
    """Select the complete body illustration, without anatomy reconstruction."""
    available = visual["states"]
    explicit = getattr(pose, "sprite_state", None)
    if explicit is not None:
        if explicit not in available:
            raise ValueError(f"pose state not in this art pack: {explicit}")
        state = explicit
    else:
        candidates = [
            ("reach", getattr(pose, "reach_prop", None) and 0 < pose.pickup < 1),
            ("carry", pose.holding is not None),
            ("speak", pose.talking),
            ("walk", abs(pose.walk) + abs(pose.run) > .06),
        ]
        state = next((name for name,active in candidates if active and name in available),
                     visual.get("default", "idle"))
    frames = available[state]
    fps = float(visual.get("fps",8))
    index = min(len(frames)-1, int(max(0,t)*fps)) if visual.get("playback")=="once" else int(max(0,t)*fps) % len(frames)
    return state, frames[index], index


def frame_geometry(image_size: tuple[int,int], actor:dict, pose,
                   artwork:Image.Image, part:dict) -> tuple[int,int,int,int]:
    W,H = image_size
    settings=actor["visual"]
    h = max(1,round(H*float(settings.get("height",.56))*float(actor.get("scale",1))
                   *float(part.get("scale",1))))
    if h>H*3 or artwork.width*h/artwork.height>W*3:
        raise ValueError("illustrated figure exceeds safe canvas scale")
    w = max(1,round(artwork.width/artwork.height*h))
    foot=part.get("foot_anchor",settings.get("foot_anchor",[.5,.97]))
    anchor_x=1-float(foot[0]) if settings.get("mirror",False) else float(foot[0])
    center_x=(pose.x+getattr(pose,"body_shift",(0,0))[0])*W
    center_y=(pose.y+getattr(pose,"body_shift",(0,0))[1])*H
    return round(center_x-anchor_x*w),round(center_y-float(foot[1])*h),w,h


def draw_pose_atlas(canvas:Image.Image,source_root:Path,
                    actor:dict,pose,time:float)->tuple[str,int]:
    """Composite a whole painted body without separating or distorting limbs."""
    state,part,index=select_pose(actor["visual"],pose,time)
    path=safe_asset(source_root,part["src"])
    art=_current_pose(path)
    left,top,w,h=frame_geometry(canvas.size,actor,pose,art,part)
    if actor["visual"].get("mirror",False):
        art=ImageOps.mirror(art)
    art=art.resize((w,h),Image.Resampling.LANCZOS)
    if canvas.mode!="RGBA":
        # Mask-based pasting preserves transparency on RGB video frames.
        canvas.paste(art,(left,top),art)
    else:
        canvas.alpha_composite(art,(left,top))
    return state,index


def illustrated_hand(actor:dict,pose,time:float,W:int,H:int,source_root:Path)->tuple[float,float]:
    """Locate an authored hand contact on the *same* selected image frame.

    A missing hand anchor is an explicit contract failure, not guessed IK.
    """
    state,part,_ = select_pose(actor["visual"],pose,time)
    p = part.get("hand_anchor", actor["visual"].get("hand_anchor"))
    if p is None:
        raise ValueError(f"pose atlas state {state!r} has no hand_anchor for prop interaction")
    art=_current_pose(safe_asset(source_root,part["src"]))
    left,top,w,h=frame_geometry((W,H),actor,pose,art,part)
    x=float(p[0])
    if actor["visual"].get("mirror",False):
        x=1-x
    return (left+w*x, top+h*float(p[1]))


def _pair(value, label: str) -> tuple[float,float]:
    if not isinstance(value,list) or len(value)!=2 or any(
        isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) or x<0 or x>1 for x in value
    ):
        raise ValueError(f"{label} must be a normalized [x,y] pair")
    return float(value[0]),float(value[1])


def import_pose_sheet(sheet_path: str | Path, layout_path: str | Path,
                      output_dir: str | Path) -> dict:
    """Cut an already-transparent atlas into individual artist-owned poses.

    Layout JSON:
      {"columns":3,"rows":2,
       "frames":[{"state":"idle","cell":[0,0],"hand_anchor":[.8,.55]}, ...],
       "height":.55,"fps":8,"foot_anchor":[.5,.98]}

    This does not infer anatomy or strip arbitrary painted backgrounds.
    A poster or opaque illustration fails instead of producing fake cutouts.
    """
    path=Path(sheet_path)
    if not path.is_file():raise FileNotFoundError(f"missing source sheet: {path}")
    sheet=_read_png(path,MAX_SHEET_PIXELS)
    layout=json.loads(Path(layout_path).read_text(encoding="utf-8"))
    if not isinstance(layout,dict):
        raise ValueError("pose sheet layout must be a JSON object")
    columns,rows=layout.get("columns"),layout.get("rows")
    if not isinstance(columns,int) or isinstance(columns,bool) or not 1<=columns<=16:
        raise ValueError("columns must be an integer from 1 to 16")
    if not isinstance(rows,int) or isinstance(rows,bool) or not 1<=rows<=16:
        raise ValueError("rows must be an integer from 1 to 16")
    if sheet.width%columns or sheet.height%rows:
        raise ValueError("atlas dimensions must be divisible by columns and rows")
    frames=layout.get("frames")
    if not isinstance(frames,list) or not 1<=len(frames)<=MAX_FRAMES:
        raise ValueError("layout requires 1..128 frame records")
    cell_w,cell_h=sheet.width//columns,sheet.height//rows
    if cell_w*cell_h>MAX_FRAME_PIXELS:
        raise ValueError("individual pose cell is too large")
    default_anchor=_pair(layout.get("foot_anchor",[.5,.98]),"foot_anchor")
    if "hand_anchor" in layout:_pair(layout["hand_anchor"],"hand_anchor")
    rate=layout.get("fps",8)
    height=layout.get("height",.56)
    if isinstance(rate,bool) or not isinstance(rate,(int,float)) or not 1<=rate<=30:
        raise ValueError("pose atlas fps must be 1..30")
    if isinstance(height,bool) or not isinstance(height,(int,float)) or not .05<=height<=2:
        raise ValueError("pose atlas height must be between .05 and 2")
    states:dict[str,list[dict]]={}
    staged:list[tuple[str,bytes,dict]]=[]
    used=set()
    for i,record in enumerate(frames):
        if not isinstance(record,dict):
            raise ValueError(f"frame {i} must be a record")
        state=record.get("state")
        if not isinstance(state,str) or not STATE_NAME.fullmatch(state):
            raise ValueError(f"frame {i} has unsafe state name")
        cell=record.get("cell")
        if not isinstance(cell,list) or len(cell)!=2 or any(
            not isinstance(n,int) or isinstance(n,bool) for n in cell):
            raise ValueError(f"frame {i}: cell must be [column,row]")
        col,row=cell
        if not (0<=col<columns and 0<=row<rows) or (col,row) in used:
            raise ValueError(f"frame {i}: duplicated or out-of-bounds cell")
        used.add((col,row))
        cropped=sheet.crop((col*cell_w,row*cell_h,(col+1)*cell_w,(row+1)*cell_h))
        alpha=cropped.getchannel("A")
        visible=alpha.getbbox()
        if visible is None:
            raise ValueError(f"frame {i} is empty")
        opaque=sum(1 for a in alpha.getdata() if a>8)
        fraction=opaque/(cell_w*cell_h)
        if fraction<.015 or fraction>.92:
            raise ValueError(f"frame {i} lacks a clean transparent silhouette ({fraction:.1%} coverage)")
        part:dict={"src":"","foot_anchor":record.get("foot_anchor",list(default_anchor))}
        _pair(part["foot_anchor"],"frame foot_anchor")
        if "hand_anchor" in record:
            _pair(record["hand_anchor"],"frame hand_anchor")
            part["hand_anchor"]=record["hand_anchor"]
        if "scale" in record:
            v=record["scale"]
            if isinstance(v,bool) or not isinstance(v,(int,float)) or not .1<=v<=3:
                raise ValueError("frame scale must be .1..3")
            part["scale"]=v
        index=len(states.get(state,[]))
        filename=f"{state}_{index:03d}.png"
        part["src"]=filename
        buf=BytesIO()
        cropped.save(buf,format="PNG",optimize=True)
        staged.append((filename,buf.getvalue(),part))
        states.setdefault(state,[]).append(part)
    default=layout.get("default","idle" if "idle" in states else list(states)[0])
    if default not in states:
        raise ValueError("pose pack default is not among imported states")
    output=Path(output_dir).resolve()
    # Validate all writes before creating or changing any source-controlled files.
    for name,payload,_ in staged:
        target=output/name
        if target.exists() and target.read_bytes()!=payload:
            raise FileExistsError(f"refusing to overwrite hand-edited pose: {target}")
    visual={"type":"pose_atlas","states":states,"default":default,
            "foot_anchor":list(default_anchor),"height":height,
            "fps":rate,"playback":layout.get("playback","loop")}
    if visual["playback"] not in ("loop","once"):
        raise ValueError("playback must be loop or once")
    if "hand_anchor" in layout:visual["hand_anchor"]=layout["hand_anchor"]
    checksums={name:sha256(payload).hexdigest() for name,payload,_ in staged}
    result={"format":"aetherpaper-posepack-0.6",
            "source":str(path.resolve()),"frames":len(staged),
            "states":{name:len(frames) for name,frames in states.items()},
            "sha256":checksums,"visual":visual,
            "note":"Copy these visual paths relative to the scene JSON; no segmentation performed"}
    manifest=output/"posepack.json"
    data=json.dumps(result,indent=2)+"\n"
    if manifest.exists() and manifest.read_text(encoding="utf-8")!=data:
        # Manifests are reproducible from the supplied source and layout.
        raise FileExistsError(f"refusing to overwrite edited posepack receipt: {manifest}")
    # All errors are checked before the first file is created.
    output.mkdir(parents=True,exist_ok=True)
    for name,payload,_ in staged:
        dest=output/name
        if not dest.exists():dest.write_bytes(payload)
    manifest.write_text(data,encoding="utf-8")
    return result
