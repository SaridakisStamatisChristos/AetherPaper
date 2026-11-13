"""v0.3 visual gate: deterministic illustrated movement and cinematic assets."""
from pathlib import Path
import copy
import pytest
from PIL import ImageChops, ImageStat

from aetherpaper.model import SceneError,load_project,validate_project
from aetherpaper.paint import render_frame
from aetherpaper.timeline import actor_pose
from aetherpaper.physics import prop_state
from aetherpaper.rig import advanced_hand

EXAMPLE=Path(__file__).resolve().parents[1]/"examples"/"lantern_keeper_v03.json"


def test_v03_contract_and_legacy_examples():
    project=load_project(EXAMPLE)
    assert project.data["version"]=="0.3"
    assert project.duration==10
    assert project.scenes[0]["style"] if "style" in project.scenes[0] else project.data["style"]=="cinematic_storybook"
    assert load_project(EXAMPLE.parent/"rig_demo.json").data["version"]=="0.2"
    assert load_project(EXAMPLE.parent/"room_pickup.json").data["version"]=="0.1"


def test_illustrated_puppet_renders_and_changes_without_random_flicker():
    p=load_project(EXAMPLE)
    scene=p.scenes[0]
    early=render_frame(p,scene,1.2,width=480,height=270)
    same=render_frame(p,scene,1.2,width=480,height=270)
    lifted=render_frame(p,scene,4.0,width=480,height=270)
    placed=render_frame(p,scene,8.5,width=480,height=270)
    assert early.tobytes()==same.tobytes()
    assert ImageChops.difference(early,lifted).getbbox()
    assert ImageChops.difference(lifted,placed).getbbox()
    assert len(set(early.getdata()))>300
    assert ImageStat.Stat(early.convert("L")).stddev[0]>15


def test_prop_light_follows_carried_actor_hand_and_ends_on_table():
    project=load_project(EXAMPLE)
    scene=project.scenes[0]
    actor=scene["characters"][0]
    prop=scene["props"][0]
    def hand(aid,t):
        assert aid==actor["id"]
        pose=actor_pose(scene,actor,t)
        px,py=advanced_hand(actor,pose,480,270,t)
        return (px/480,py/270)
    initial=prop_state(scene,prop,.1,hand)
    carried=prop_state(scene,prop,5.5,hand)
    final=prop_state(scene,prop,9.1,hand)
    assert initial.center == (.585,.648)
    assert carried.owner=="keeper"
    assert carried.center != initial.center
    assert final.owner is None
    assert final.center==pytest.approx((.8,.636))


def test_bad_new_style_visual_and_title_rejected():
    baseline=load_project(EXAMPLE).data
    wrong=copy.deepcopy(baseline)
    wrong["scenes"][0]["characters"][0]["visual"]["type"]="unknown"
    with pytest.raises(SceneError,match="visual"):
        validate_project(wrong)
    wrong=copy.deepcopy(baseline)
    wrong["scenes"][0]["environment"]["type"]="unknown"
    with pytest.raises(SceneError,match="environment"):
        validate_project(wrong)
    wrong=copy.deepcopy(baseline)
    wrong["scenes"][0]["title_card"]["end"]=-1
    with pytest.raises(SceneError,match="title_card"):
        validate_project(wrong)
    wrong=copy.deepcopy(baseline)
    wrong["scenes"][0]["props"][0]["shape"]="explosive"
    with pytest.raises(SceneError,match="shape"):
        validate_project(wrong)


def test_illustrated_actors_require_valid_rig_and_colors():
    baseline=load_project(EXAMPLE).data
    wrong=copy.deepcopy(baseline)
    del wrong["scenes"][0]["characters"][0]["rig"]
    with pytest.raises(SceneError,match="rig"):
        validate_project(wrong)
    wrong=copy.deepcopy(baseline)
    wrong["scenes"][0]["characters"][0]["visual"]["coat"]="red"
    with pytest.raises(SceneError,match="RRGGBB"):
        validate_project(wrong)
