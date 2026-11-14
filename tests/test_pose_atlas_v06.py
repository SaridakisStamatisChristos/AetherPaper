"""v0.6: Whole-pose illustrated animation and asset contract gates."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import pytest
from PIL import Image,ImageChops
from aetherpaper.model import load_project,validate_project,SceneError,Project
from aetherpaper.posekit import build_posekit
from aetherpaper.pose_atlas import pose_frame,pose_hand,draw_pose_atlas
from aetherpaper.timeline import actor_pose
from aetherpaper.paint import render_frame
from aetherpaper.assets import audit_assets
from aetherpaper.cli import main

ROOT=Path(__file__).resolve().parents[1]
EXAMPLE=ROOT/"examples"/"illustrated_poses_v06.json"
V05=ROOT/"examples"/"last_light_directed_v05.json"


@pytest.fixture(scope="module")
def art(tmp_path_factory):
    root=tmp_path_factory.mktemp("pose-art")
    result=build_posekit(root/"assets"/"pose_courier.png",V05)
    payload=json.loads(EXAMPLE.read_text(encoding="utf-8"))
    project=Project(root/"illustrated_poses_v06.json",payload)
    validate_project(payload)
    return result,project


def test_pose_generator_makes_real_editable_rgba_png(art):
    result,project=art
    assert result["columns"]==3 and result["rows"]==2
    assert set(result["poses"])=={"idle","step","reach","carry","place","gaze"}
    atlas=project.source.parent/"assets"/"pose_courier.png"
    with Image.open(atlas) as im:
        assert im.size==(1536,1024)
        assert im.mode=="RGBA"
        assert im.getextrema()[3]==(0,255)
        assert len(im.getcolors(maxcolors=10_000_000) or [])>300
    manifest=audit_assets(project)
    assert len(manifest)==1
    assert manifest[0]["kind"]=="image"


def test_pose_art_render_is_seek_safe_changes_across_events(art):
    _,project=art
    scene=project.scenes[0]
    a=render_frame(project,scene,1.5,width=320,height=180)
    b=render_frame(project,scene,1.5,width=320,height=180)
    c=render_frame(project,scene,5.5,width=320,height=180)
    d=render_frame(project,scene,11.5,width=320,height=180)
    assert a.tobytes()==b.tobytes()
    assert ImageChops.difference(a,c).getbbox() is not None
    assert ImageChops.difference(c,d).getbbox() is not None
    assert len(a.getcolors(maxcolors=1_000_000) or [])>250


def test_pose_timing_and_short_crossfade_exact(art):
    _,project=art
    visual=project.scenes[0]["characters"][0]["visual"]
    assert pose_frame(visual,.01).name=="idle"
    assert pose_frame(visual,.6).name=="step"
    assert pose_frame(visual,4.0).name=="reach"
    assert pose_frame(visual,5.3).name=="carry"
    assert pose_frame(visual,10.0).name=="place"
    assert pose_frame(visual,11.5).name=="gaze"
    switch=pose_frame(visual,5.28)
    assert switch.previous=="reach"
    assert 0<switch.progress<1
    assert pose_frame(visual,5.38).progress==1


def test_pose_anchor_and_prop_hand_metadata(art):
    result,project=art
    visual=project.scenes[0]["characters"][0]["visual"]
    for key,metadata in result["poses"].items():
        assert 0<=metadata["hand"][0]<=1
        assert 0<=metadata["hand"][1]<=1
        visual["poses"][key]["hand"]=metadata["hand"]
    pose=actor_pose(project.scenes[0],project.scenes[0]["characters"][0],5.5)
    x,y=pose_hand(project.scenes[0]["characters"][0],pose,640,360,5.5)
    assert 0<x<640
    assert 0<y<360
    validate_project(project.data)


def test_pose_atlas_never_overwrites_artist_modified_file(art):
    _,project=art
    path=project.source.parent/"assets"/"pose_courier.png"
    path.write_bytes(b"artist edited")
    with pytest.raises(FileExistsError,match="refusing"):
        build_posekit(path,V05)


def test_bad_pose_mapping_is_rejected():
    data=json.loads(EXAMPLE.read_text(encoding="utf-8"))
    visual=data["scenes"][0]["characters"][0]["visual"]
    visual["poses"]["gaze"]["cell"]=99
    with pytest.raises(SceneError,match="cell"):
        validate_project(data)
    data=json.loads(EXAMPLE.read_text(encoding="utf-8"))
    events=data["scenes"][0]["characters"][0]["visual"]["timeline"]
    events[2]["at"]=events[1]["at"]
    with pytest.raises(SceneError,match="strictly increasing"):
        validate_project(data)
    data=json.loads(EXAMPLE.read_text(encoding="utf-8"))
    data["scenes"][0]["characters"][0]["visual"]["src"]="../escape.png"
    with pytest.raises(SceneError,match="escapes"):
        audit_assets(Project(ROOT/"examples"/"fake.json",data))


def test_cli_posekit_generates_local_art(tmp_path,capsys):
    output=tmp_path/"pose.png"
    assert main(["posekit","--out",str(output),"--source",str(V05)])==0
    receipt=json.loads(capsys.readouterr().out)
    assert receipt["rows"]==2 and receipt["columns"]==3
    assert output.is_file()


def test_legacy_sprite_and_illustrated_scenes_still_validate():
    for path in (
        ROOT/"examples"/"last_light_directed_v05.json",
        ROOT/"examples"/"last_light_v04.json",
        ROOT/"examples"/"lantern_keeper_v03.json",
        ROOT/"examples"/"rig_demo.json",
    ):
        project=load_project(path)
        validate_project(project.data)
