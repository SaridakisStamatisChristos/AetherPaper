"""Small transparent full-pose demo sourced from the existing v0.5 sprite rig.

This fixture is deliberately NOT claimed to be new or professional artwork.
It demonstrates the new pose-atlas engine with real, inspectable pose PNGs and
allows regression testing without an external image-generation model.
A professionally illustrated pose sheet can replace it without code changes.
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import json

from PIL import Image
from .model import load_project,validate_project
from .timeline import actor_pose
from .sprite_rig import draw_sprite_character,sprite_hand
from .pose_atlas import import_pose_sheet


SAMPLES=[
    ("walk",.75),
    ("walk",1.40),
    ("idle",3.18),
    ("reach",4.67),
    ("carry",6.35),
    ("speak",12.55),
]


def make_demo(source:str|Path,output_root:str|Path)->dict:
    baseline=load_project(source)
    scene=baseline.scenes[0]
    actor=scene["characters"][0]
    if actor["visual"]["type"]!="sprites":
        raise ValueError("pose demonstration source must have a layered sprite rig")
    root=Path(output_root).resolve()
    root.mkdir(parents=True,exist_ok=True)
    assets=root/"assets"/"pose_atlas_demo"
    assets.mkdir(parents=True,exist_ok=True)
    cell=(256,320)
    sheet=Image.new("RGBA",(cell[0]*3,cell[1]*2))
    entries=[]
    for i,(state,t) in enumerate(SAMPLES):
        pose=actor_pose(scene,actor,t)
        # Place the complete existing character at the same baseline in each
        # atlas cell. Reproduction is independent of the previous frame.
        pose=replace(pose,x=.5,y=.89,body_shift=(0.,0.))
        cell_image=Image.new("RGBA",cell)
        draw_sprite_character(cell_image,baseline.source.parent,actor,pose,t)
        sheet.alpha_composite(cell_image,((i%3)*cell[0],(i//3)*cell[1]))
        hx,hy=sprite_hand(actor,pose,*cell,t)
        entries.append({"state":state,"cell":[i%3,i//3],
                        "hand_anchor":[max(0,min(1,hx/cell[0])),
                                       max(0,min(1,hy/cell[1]))]})
    sheet_path=assets/"demo_sheet.png"
    sheet.save(sheet_path)
    layout={"columns":3,"rows":2,"fps":6,"height":.64,
            "foot_anchor":[.5,.89],"frames":entries}
    layout_path=assets/"demo_layout.json"
    layout_path.write_text(json.dumps(layout,indent=2)+"\n",encoding="utf-8")
    imported=import_pose_sheet(sheet_path,layout_path,assets/"poses")
    visual=imported["visual"]
    # Each src from pose importer is relative to poses/; write scene-relative
    # paths while preserving artist-authored hand and foot anchors.
    for frames in visual["states"].values():
        for frame in frames:
            frame["src"]="assets/pose_atlas_demo/poses/"+frame["src"]
    project={
      "version":"0.6",
      "title":"Pose Atlas Pipeline Acceptance — Source Art Baseline",
      "style":"cinematic_storybook",
      "canvas":{"width":640,"height":360,"fps":12},
      "scenes":[{
        "id":"atlas-demo","duration":5.0,"style":"cinematic_storybook",
        "environment":{"type":"sunset_cliff"},"supersample":1,
        "characters":[{
          "id":"courier","x":.25,"y":.89,"scale":1.0,"visual":visual
        }],
        "props":[],"layers":[],
        "actions":[{
          "type":"performance","target":"courier","start":0,"end":5,
          "keyframes":[
            {"at":0,"position":[.25,.89],"sprite_state":"walk"},
            {"at":.60,"position":[.33,.89],"sprite_state":"walk"},
            {"at":1.20,"position":[.42,.89],"sprite_state":"walk"},
            {"at":1.7,"position":[.50,.89],"sprite_state":"idle"},
            {"at":2.1,"position":[.52,.89],"sprite_state":"reach"},
            {"at":3.0,"position":[.52,.89],"sprite_state":"carry"},
            {"at":4.0,"position":[.52,.89],"sprite_state":"speak","expression":"happy"},
            {"at":5.0,"position":[.52,.89],"sprite_state":"idle"}
          ]
        }],
        "camera":[{"start":0,"end":5,"zoom_from":1,"zoom_to":1.08,
                    "center_from":[.5,.5],"center_to":[.53,.5]}]
      }]
    }
    validate_project(project)
    target=root/"pose_atlas_demo_v06.json"
    target.write_text(json.dumps(project,indent=2)+"\n",encoding="utf-8")
    return {"scene":str(target),"source_sheet":str(sheet_path),
            "generated_frames":sum(len(f) for f in visual["states"].values()),
            "states":list(visual["states"]),
            "source_quality":"legacy generated v0.5 artwork; not professional",
            "run":"aetherpaper render "+str(target)+" --out output/pose_demo_v06.mp4"}
