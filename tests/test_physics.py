from pathlib import Path
import copy
import pytest
from aetherpaper.model import load_project, SceneError, validate_project
from aetherpaper.physics import falling, circles_touch, boxes_overlap, rope_points, prop_state
from aetherpaper.timeline import actor_pose
from aetherpaper.rig import advanced_hand
from aetherpaper.paint import render_frame

EXAMPLE=Path(__file__).resolve().parents[1]/"examples"/"interaction_demo.json"


def test_pickup_carry_and_place_are_seek_safe():
    p=load_project(EXAMPLE)
    scene=p.scenes[0]
    props={item["id"]:item for item in scene["props"]}
    chars={actor["id"]:actor for actor in scene["characters"]}
    def hand(aid,t):
        a=chars[aid]
        pos=actor_pose(scene,a,t)
        x,y=advanced_hand(a,pos,240,136,t)
        return x/240,y/136
    initial=prop_state(scene,props["book"],1.0,hand)
    carrying=prop_state(scene,props["book"],5.8,hand)
    final=prop_state(scene,props["book"],9.2,hand)
    assert initial.center == (.57,.62)
    assert carrying.foreground and carrying.owner=="ava"
    assert final.center == pytest.approx((.81,.63))
    assert final.owner is None
    assert prop_state(scene,props["book"],9.2,hand) == final


def test_gravity_collision_and_rope():
    assert falling((.5,.2),0) == (.5,.2)
    assert falling((.5,.2),5,ground=.78)[1] <= .78
    assert falling((.5,.2),5,ground=.78)[1] >= .2
    assert circles_touch((0,0),1,(1.9,0),1)
    assert not circles_touch((0,0),1,(3,0),1)
    assert boxes_overlap((0,0,1,1),(.9,.9,2,2))
    rope=rope_points((0,0),(1,0),.5,sag=.1,wind=.03)
    assert rope[0] == (0,0)
    assert rope[-1][0] == pytest.approx(1)
    assert rope[len(rope)//2][1] == pytest.approx(.1)


def test_interaction_video_changes_and_deterministic():
    p=load_project(EXAMPLE)
    s=p.scenes[0]
    a=render_frame(p,s,2.7,width=240,height=136)
    b=render_frame(p,s,2.7,width=240,height=136)
    c=render_frame(p,s,8.8,width=240,height=136)
    assert a.tobytes()==b.tobytes()
    assert a.tobytes()!=c.tobytes()


def test_cannot_release_unheld_object():
    p=copy.deepcopy(load_project(EXAMPLE).data)
    p["scenes"][0]["actions"].append(
      {"type":"release","target":"ava","prop":"ball","start":4,"end":4.3})
    with pytest.raises(SceneError,match="picked up"):
        validate_project(p)


def test_released_prop_falls():
    p=load_project(EXAMPLE)
    s=copy.deepcopy(p.scenes[0])
    s["actions"].append({"type":"pickup","target":"ava","prop":"ball","start":7.3,"end":8.0})
    s["actions"].append({"type":"release","target":"ava","prop":"ball","start":8.1,"end":8.3,"gravity":.9,"ground":.78})
    actors={a["id"]:a for a in s["characters"]}
    def hand(aid,t):
        pos=actor_pose(s,actors[aid],t)
        x,y=advanced_hand(actors[aid],pos,240,136,t)
        return x/240,y/136
    ball=next(p for p in s["props"] if p["id"]=="ball")
    released=prop_state(s,ball,8.2,hand)
    landed=prop_state(s,ball,9.9,hand)
    assert released.owner is None
    assert landed.center[1] <= .78
