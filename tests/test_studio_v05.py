"""v0.5 art direction: procedural original paintings and hand-directed performance."""
from __future__ import annotations
import copy
import json
import math
from pathlib import Path

import pytest
from PIL import Image, ImageChops

from aetherpaper.choreography import evaluate
from aetherpaper.artkit import PALETTE
from aetherpaper.studio_art import generate_studio_kit
from aetherpaper.model import Project,SceneError,validate_project
from aetherpaper.paint import render_frame
from aetherpaper.timeline import actor_pose
from aetherpaper.sprite_rig import posed_sprite_joints,sprite_hand
from aetherpaper.physics import prop_state
from aetherpaper.assets import audit_assets
from aetherpaper.cli import main

SAMPLE=Path(__file__).resolve().parents[1]/"examples"/"last_light_directed_v05.json"


@pytest.fixture(scope="module")
def studio_project(tmp_path_factory):
    root=tmp_path_factory.mktemp("studio")
    kit=generate_studio_kit(root/"assets"/"studio_courier")
    assert kit["parts"]==20
    data=json.loads(SAMPLE.read_text(encoding="utf-8"))
    validate_project(data)
    path=root/"director.json"
    path.write_text(json.dumps(data),encoding="utf-8")
    return Project(path,data)


def test_artkit_is_real_editable_transparent_png_and_palette_is_restored(studio_project):
    root=studio_project.source.parent/"assets"/"studio_courier"
    names=sorted(root.glob("*.png"))
    assert len(names)==20
    assert len(audit_assets(studio_project))==20
    for name in ("head.png","torso.png","scarf.png","arm_r.png","face_happy.png"):
        with Image.open(root/name) as image:
            assert image.mode=="RGBA"
            assert image.getextrema()[3]==(0,255)
            assert len(image.getcolors(maxcolors=1_000_000) or [])>20
    assert PALETTE["coat"]=="#2A7781"


def test_generator_never_overwrites_artist_authored_replacement(tmp_path):
    # Use a dedicated kit; corrupting the shared module fixture makes later
    # render tests fail for an unrelated, intentionally malformed PNG.
    root=tmp_path/"artist_edited_kit"
    generate_studio_kit(root)
    again=generate_studio_kit(root)
    assert again["parts"]==20
    modified=root/"head.png"
    modified.write_bytes(b"custom artist illustration")
    with pytest.raises(FileExistsError,match="refusing"):
        generate_studio_kit(root)


def test_director_interpolates_positions_without_overstepping_segment(studio_project):
    scene=studio_project.scenes[0]
    perf=next(a for a in scene["actions"] if a["type"]=="performance")
    first=evaluate(perf,0)
    middle=evaluate(perf,1.4)
    last=evaluate(perf,14)
    assert first.position==pytest.approx((.145,.884))
    assert .22<middle.position[0]<.31
    assert last.position==pytest.approx((.63,.883))
    assert last.expression=="happy"
    assert first.feet_world["l"]==pytest.approx((.112,.877))
    # The left shoe is planted for first half step, not oscillating in place.
    assert evaluate(perf,.1).feet_world["l"]==pytest.approx((.112,.877))
    assert evaluate(perf,.3).feet_world["l"]==pytest.approx((.112,.877))
    assert evaluate(perf,.3).feet_world["r"][0] > first.feet_world["r"][0]


def test_director_clip_controls_real_pose_and_bone_angles(studio_project):
    scene=studio_project.scenes[0];actor=scene["characters"][0]
    early=actor_pose(scene,actor,.1)
    late=actor_pose(scene,actor,12.4)
    assert early.x<late.x
    assert early.foot_world is not None
    assert late.expression=="happy"
    assert late.bone_angles["head"]>0
    body=posed_sprite_joints(actor,late,480,270,12.4)
    assert body["head"][0]!=body["head"][1]
    assert body["thigh_l"][1]==pytest.approx(body["shin_l"][0])


def test_v05_renders_deterministic_real_film_frames(studio_project):
    scene=studio_project.scenes[0]
    a=render_frame(studio_project,scene,2.1,width=320,height=180)
    b=render_frame(studio_project,scene,2.1,width=320,height=180)
    c=render_frame(studio_project,scene,9.7,width=320,height=180)
    assert a.size==(320,180)
    assert a.tobytes()==b.tobytes()
    assert ImageChops.difference(a,c).getbbox() is not None
    assert len(a.getcolors(maxcolors=1_000_000) or [])>500


def test_studio_hero_physically_carries_prop_on_sprite_hand(studio_project):
    scene=studio_project.scenes[0];actor=scene["characters"][0];prop=scene["props"][0]
    def hand(aid,t):
        assert aid=="courier"
        pose=actor_pose(scene,actor,t)
        x,y=sprite_hand(actor,pose,640,360,t)
        return (x/640,y/360)
    for t in (5.3,6.9,7.9,8.9):
        state=prop_state(scene,prop,t,hand)
        assert state.owner=="courier"
        assert state.center==pytest.approx(hand("courier",t))
    placed=prop_state(scene,prop,11.2,hand)
    assert placed.owner is None
    assert placed.center==pytest.approx((.747,.665))


def test_v05_rejects_invalid_foot_and_time_choreography(studio_project):
    data=studio_project.data
    modified=copy.deepcopy(data)
    a=next(x for x in modified["scenes"][0]["actions"] if x["type"]=="performance")
    a["keyframes"][1]["at"]=0
    with pytest.raises(SceneError,match="strictly"):
        validate_project(modified)
    modified=copy.deepcopy(data)
    a=next(x for x in modified["scenes"][0]["actions"] if x["type"]=="performance")
    a["keyframes"][0]["feet_world"]["l"]=[float("nan"),.877]
    with pytest.raises(SceneError,match="finite"):
        validate_project(modified)
    modified=copy.deepcopy(data)
    a=next(x for x in modified["scenes"][0]["actions"] if x["type"]=="performance")
    a["keyframes"][0]["angles"]["wrong"]=-.2
    with pytest.raises(SceneError,match="unknown bone"):
        validate_project(modified)
    modified=copy.deepcopy(data)
    a=next(x for x in modified["scenes"][0]["actions"] if x["type"]=="performance")
    a["keyframes"][0]["interpolation"]="quantum"
    with pytest.raises(SceneError,match="interpolation"):
        validate_project(modified)


def test_hermite_continuous_at_keyframes_and_hold_is_exact():
    action={"type":"performance","start":1,"end":5,"keyframes":[
        {"at":0,"position":[.1,.8],"interpolation":"smooth"},
        {"at":1,"position":[.3,.8],"interpolation":"hold"},
        {"at":2,"position":[.3,.7],"interpolation":"smooth"},
        {"at":4,"position":[.5,.7]}]}
    assert evaluate(action,1).position==pytest.approx((.1,.8))
    assert evaluate(action,2.5).position==pytest.approx((.3,.8))
    assert evaluate(action,3).position==pytest.approx((.3,.7))
    assert evaluate(action,5).position==pytest.approx((.5,.7))
    for t in [1+i*.05 for i in range(81)]:
        x,y=evaluate(action,t).position
        assert .1<=x<=.5
        assert .7<=y<=.8


def test_cli_studio_artkit_smoke(tmp_path,capsys):
    result=main(["artkit","--edition","studio","--out",str(tmp_path/"art")])
    assert result==0
    data=json.loads(capsys.readouterr().out)
    assert data["parts"]==20
    assert len(list((tmp_path/"art").glob("*.png")))==20
