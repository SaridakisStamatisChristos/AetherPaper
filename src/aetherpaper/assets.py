"""Offline-only source asset inventory and safety checks."""
from __future__ import annotations
from pathlib import Path
from hashlib import sha256
from PIL import Image
from .model import SceneError


def audit_assets(project) -> list[dict]:
    root=project.source.parent.resolve()
    references=[]
    for i,scene in enumerate(project.scenes):
        for j,actor in enumerate(scene.get('characters',[])):
            if actor.get('visual',{}).get('type')=='sprites':
                for k,part in enumerate(actor['visual']['parts']):
                    references.append((f'scenes[{i}].characters[{j}].visual.parts[{k}].src',
                                       part['src'],'image'))
        for j,layer in enumerate(scene.get("layers",[])):
            if layer["type"]=="image":
                references.append((f"scenes[{i}].layers[{j}].src",layer["src"],"image"))
        for j,action in enumerate(scene.get("actions",[])):
            if action["type"]=="speak" and "audio" in action:
                references.append((f"scenes[{i}].actions[{j}].audio",action["audio"],"audio"))
    manifest=[]
    for ref,name,kind in references:
        if name.startswith(("http:","https:","data:","file:")):
            raise SceneError(f"{ref}: remote or URI-style sources are not permitted")
        location=(root/name).resolve()
        if not location.is_relative_to(root):
            raise SceneError(f"{ref}: path escapes project directory")
        if not location.is_file():
            raise SceneError(f"{ref}: asset file missing: {name}")
        if location.stat().st_size > 250*1024*1024:
            raise SceneError(f"{ref}: asset exceeds 250 MiB")
        if kind=="image":
            try:
                with Image.open(location) as img:
                    if img.width*img.height > 50_000_000:
                        raise SceneError(f"{ref}: image exceeds 50 megapixels")
                    img.verify()
            except (OSError,ValueError) as exc:
                raise SceneError(f"{ref}: image is unreadable") from exc
        if kind=="audio" and location.suffix.lower()!=".wav":
            raise SceneError(f"{ref}: narration must be a WAV file")
        manifest.append({"reference":ref,"kind":kind,"path":name,
                         "bytes":location.stat().st_size,
                         "sha256":sha256(location.read_bytes()).hexdigest()})
    return manifest


def production_manifest(project) -> dict:
    return {
        "format":"aetherpaper-manifest-0.2",
        "project":str(project.source),
        "version":project.data["version"],
        "canvas":dict(project.canvas),
        "duration_seconds":project.duration,
        "scene_count":len(project.scenes),
        "scenes":[{"id":s["id"],"duration":s["duration"],
                   "style":s.get("style",project.data.get("style","paper_cut")),
                   "action_types":sorted({a["type"] for a in s.get("actions",[])})}
                  for s in project.scenes],
        "assets":audit_assets(project),
        "network_required":False,
        "ai_runtime_required":False,
    }
