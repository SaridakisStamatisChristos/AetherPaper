"""Artist sprite rig tests use local PNG parts, never mock a render."""
from pathlib import Path
import copy
import pytest
from PIL import Image, ImageDraw

from aetherpaper.assets import audit_assets
from aetherpaper.model import Project,SceneError,load_project,validate_project
from aetherpaper.sprite_rig import attach_sprite,draw_sprite_character
from aetherpaper.timeline import actor_pose


def _sprite_project(tmp_path):
    for name,color in (("coat","#437889"),("head","#E2AE88")):
        img=Image.new("RGBA",(100,46),(0,0,0,0))
        d=ImageDraw.Draw(img)
        d.rounded_rectangle((1,6,97,40),radius=14,fill=color,outline="#263542",width=3)
        img.save(tmp_path/(name+".png"))
    data=copy.deepcopy(load_project(Path(__file__).resolve().parents[1]/
                                   "examples"/"lantern_keeper_v03.json").data)
    scene=data["scenes"][0]
    scene["props"]=[]
    scene["actions"]=[{"type":"pose","target":"artist","start":.1,"end":2.5,
                      "angles":{"torso":.6}}]
    scene["characters"]=[{
       "id":"artist","x":.5,"y":.83,"scale":1.4,
       "rig":{"bones":[
          {"name":"pelvis","parent":None,"length":.05,"angle":-1.5707963268},
          {"name":"torso","parent":"pelvis","length":.3,"angle":0},
          {"name":"neck","parent":"torso","length":.15,"angle":0}
       ]},
       "visual":{"type":"sprites","parts":[
          {"bone":"torso","src":"coat.png","pivot":[0,.5],"scale":1.1,"z":0},
          {"bone":"neck","src":"head.png","pivot":[0,.5],"scale":1.3,"z":1}
       ]}
    }]
    validate_project(data)
    return Project(tmp_path/"sprite_scene.json",data)


def test_rigid_pivot_affine_rotation_has_distinct_geometry():
    art=Image.new("RGBA",(80,22),(230,130,63,255))
    a=Image.new("RGB",(180,180),"#142832")
    b=a.copy()
    attach_sprite(a,art,(70,70),(126,70))
    attach_sprite(b,art,(70,70),(70,126))
    assert a.tobytes()!=b.tobytes()
    assert a.getpixel((120,70)) != b.getpixel((120,70))


def test_sprite_parts_follow_bone_pose_and_repeat_exactly(tmp_path):
    p=_sprite_project(tmp_path)
    scene=p.scenes[0]
    artist=scene["characters"][0]
    def frame(t):
        img=Image.new("RGB",(320,180),"#193641")
        draw_sprite_character(img,tmp_path,artist,actor_pose(scene,artist,t),t)
        return img
    assert frame(.5).tobytes()==frame(.5).tobytes()
    assert frame(.5).tobytes()!=frame(1.9).tobytes()
    entries=audit_assets(p)
    assert len(entries)==2 and all(item["kind"]=="image" for item in entries)


def test_sprite_schema_and_paths_reject_bad_art(tmp_path):
    p=_sprite_project(tmp_path)
    bad=copy.deepcopy(p.data)
    bad["scenes"][0]["characters"][0]["visual"]["parts"][0]["pivot"]=[2,.5]
    with pytest.raises(SceneError,match="pivot"):
        validate_project(bad)
    bad=copy.deepcopy(p.data)
    bad["scenes"][0]["characters"][0]["visual"]["parts"][0]["bone"]="missing"
    with pytest.raises(SceneError,match="bone"):
        validate_project(bad)
    bad=copy.deepcopy(p.data)
    bad["scenes"][0]["characters"][0]["visual"]["parts"][0]["src"]="../escape.png"
    with pytest.raises(SceneError,match="escapes"):
        audit_assets(Project(tmp_path/"scene.json",bad))
    bad=copy.deepcopy(p.data)
    bad["scenes"][0]["characters"][0]["visual"]["parts"][0]["src"]="absent.png"
    with pytest.raises(SceneError,match="missing"):
        audit_assets(Project(tmp_path/"scene.json",bad))
