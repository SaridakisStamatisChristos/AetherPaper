"""v0.6 image-led characters: transparent atlases, safe imports, real rendering."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from PIL import Image, ImageDraw, ImageChops

from aetherpaper.model import load_project,validate_project,SceneError,Project
from aetherpaper.timeline import actor_pose
from aetherpaper.pose_demo import make_demo
from aetherpaper.pose_atlas import (
    import_pose_sheet,select_pose,safe_asset,illustrated_hand,draw_pose_atlas
)
from aetherpaper.paint import render_frame
from aetherpaper.assets import audit_assets
from aetherpaper.cli import main

SOURCE=Path(__file__).resolve().parents[1]/"examples"/"last_light_directed_v05.json"


@pytest.fixture(scope="module")
def art_demo(tmp_path_factory):
    dest=tmp_path_factory.mktemp("atlas")
    generated=make_demo(SOURCE,dest)
    project=load_project(generated["scene"])
    return project,generated


def test_illustrated_demo_is_real_rgba_and_has_distinct_poses(art_demo):
    project,meta=art_demo
    assert project.data["version"]=="0.6"
    assert meta["generated_frames"]==6
    assert set(meta["states"])=={"walk","idle","reach","carry","speak"}
    assert len(audit_assets(project))==6
    atlas=project.source.parent/"assets"/"pose_atlas_demo"/"demo_sheet.png"
    with Image.open(atlas) as image:
        assert image.mode=="RGBA"
        assert image.size==(768,640)
        lo,hi=image.getchannel("A").getextrema()
        assert lo==0 and hi>0
    for state,frames in project.scenes[0]["characters"][0]["visual"]["states"].items():
        for f in frames:
            p=project.source.parent/f["src"]
            with Image.open(p) as picture:
                assert picture.mode=="RGBA" and picture.size==(256,320)
                assert picture.getchannel("A").getextrema()[0]==0


def test_director_selects_full_painted_poses_without_animation_state(art_demo):
    project,_=art_demo
    s=project.scenes[0]
    actor=s["characters"][0]
    checks=((.3,"walk"),(1.9,"idle"),(2.4,"reach"),(3.2,"carry"),(4.3,"speak"))
    for t,state in checks:
        pose=actor_pose(s,actor,t)
        chosen,part,_=select_pose(actor["visual"],pose,t)
        assert chosen==state
        assert part["src"].endswith(".png")
    # Random-access samples are identical even after querying another time.
    assert select_pose(actor["visual"],actor_pose(s,actor,.3),.3)==select_pose(
        actor["visual"],actor_pose(s,actor,.3),.3)


def test_actual_illustrated_frames_differ_and_repeat_exactly(art_demo):
    project,_=art_demo
    s=project.scenes[0]
    a=render_frame(project,s,.9,width=320,height=180)
    b=render_frame(project,s,.9,width=320,height=180)
    c=render_frame(project,s,3.2,width=320,height=180)
    assert a.tobytes()==b.tobytes()
    assert a.size==c.size
    assert ImageChops.difference(a,c).getbbox() is not None
    assert len(a.getcolors(maxcolors=1_000_000) or [])>100


def test_frame_anchor_drives_precise_hand_location(art_demo):
    project,_=art_demo
    s=project.scenes[0]
    actor=s["characters"][0]
    pose=actor_pose(s,actor,3.3)
    x,y=illustrated_hand(actor,pose,3.3,640,360,project.source.parent)
    assert 0<x<640 and 0<y<360
    visual=actor["visual"]
    state,part,_=select_pose(visual,pose,3.3)
    assert state=="carry"
    assert part["hand_anchor"][0]>=0
    # The selected frame's hand marker follows actor world motion.
    moved=copy.copy(actor)
    moved["x"]=actor["x"]+.1
    from dataclasses import replace
    shifted=replace(pose,x=pose.x+.1)
    x2,y2=illustrated_hand(actor,shifted,3.3,640,360,project.source.parent)
    assert x2-x==pytest.approx(64,abs=2)
    assert y2==pytest.approx(y,abs=1)


def test_scene_validation_rejects_invalid_state_and_stale_art(art_demo):
    project,_=art_demo
    invalid=copy.deepcopy(project.data)
    p=next(a for a in invalid["scenes"][0]["actions"] if a["type"]=="performance")
    p["keyframes"][2]["sprite_state"]="unknown_pose"
    with pytest.raises(SceneError,match="sprite_state"):
        validate_project(invalid)
    invalid=copy.deepcopy(project.data)
    invalid["scenes"][0]["characters"][0]["visual"]["height"]=1000
    with pytest.raises(SceneError,match="height"):
        validate_project(invalid)
    invalid=copy.deepcopy(project.data)
    invalid["scenes"][0]["characters"][0]["visual"]["states"]["walk"][0]["src"]="../outside.png"
    with pytest.raises(SceneError,match="escapes"):
        audit_assets(Project(project.source,invalid))
    with pytest.raises(ValueError,match="escapes"):
        safe_asset(project.source.parent,"../secret.png")


def test_reject_nontransparent_poster_and_bad_layout(tmp_path):
    opaque=Image.new("RGB",(120,80),"white")
    src=tmp_path/"poster.png";opaque.save(src)
    layout={"columns":1,"rows":1,"frames":[{"state":"idle","cell":[0,0]}]}
    path=tmp_path/"layout.json";path.write_text(json.dumps(layout))
    with pytest.raises(ValueError,match="transparen"):
        import_pose_sheet(src,path,tmp_path/"poses")
    transparent=Image.new("RGBA",(120,80),(0,0,0,0))
    d=ImageDraw.Draw(transparent)
    d.ellipse((20,15,90,70),fill=(70,130,190,255))
    transparent.save(src)
    layout["frames"].append({"state":"idle","cell":[0,0]})
    path.write_text(json.dumps(layout))
    with pytest.raises(ValueError,match="duplicated"):
        import_pose_sheet(src,path,tmp_path/"poses")
    layout["frames"]=[{"state":"../unsafe","cell":[0,0]}]
    path.write_text(json.dumps(layout))
    with pytest.raises(ValueError,match="unsafe"):
        import_pose_sheet(src,path,tmp_path/"poses")


def test_importer_never_overwrites_replaced_artist_pose(tmp_path):
    src=tmp_path/"src.png"
    picture=Image.new("RGBA",(80,100),(0,0,0,0))
    ImageDraw.Draw(picture).ellipse((10,5,70,93),fill=(133,80,93,255))
    picture.save(src)
    layout=tmp_path/"layout.json"
    layout.write_text(json.dumps({"columns":1,"rows":1,
       "frames":[{"state":"idle","cell":[0,0]}]}))
    result=import_pose_sheet(src,layout,tmp_path/"out")
    assert result["frames"]==1
    assert import_pose_sheet(src,layout,tmp_path/"out")["sha256"]==result["sha256"]
    (tmp_path/"out"/"idle_000.png").write_bytes(b"artist edition")
    with pytest.raises(FileExistsError,match="hand-edited"):
        import_pose_sheet(src,layout,tmp_path/"out")


def test_cli_pose_demo_writes_valid_project(tmp_path,capsys):
    assert main(["pose-demo","--source",str(SOURCE),"--out",str(tmp_path)])==0
    data=json.loads(capsys.readouterr().out)
    project=load_project(data["scene"])
    assert project.duration==5
    assert len(audit_assets(project))==6


def test_legacy_v05_remains_loadable():
    assert load_project(SOURCE).data["version"]=="0.5"
