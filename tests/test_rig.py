"""Acceptance tests for v0.2 articulated rig and JSON controls."""
import copy
import math
from pathlib import Path

import pytest
from PIL import ImageChops

from aetherpaper.model import load_project, validate_project, SceneError
from aetherpaper.rig import Bone, Skeleton, two_bone_ik, spring_progress, advanced_hand
from aetherpaper.paint import render_frame
from aetherpaper.timeline import actor_pose

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "rig_demo.json"


def test_skeleton_hierarchy_and_attachment():
    rig = Skeleton([Bone("root", None, 2, 0), Bone("child", "root", 1, math.pi / 2, .5)])
    points = rig.solve((3, 4))
    assert points["root"][1] == pytest.approx((5, 4))
    assert points["child"][0] == pytest.approx((4, 4))
    assert points["child"][1] == pytest.approx((4, 5))


def test_skeleton_rejects_invalid_chains():
    with pytest.raises(ValueError, match="parent"):
        Skeleton([Bone("child", "missing", 1)])
    with pytest.raises(ValueError, match="length"):
        Skeleton([Bone("root", None, 0)])
    with pytest.raises(ValueError, match="duplicate"):
        Skeleton([Bone("root", None, 1), Bone("root", None, 2)])


@pytest.mark.parametrize("target", [(1, 1), (10, 0), (0, 0)])
def test_ik_maintains_lengths(target):
    elbow, hand = two_bone_ik((0, 0), target, 2.0, 1.5, bend=1)
    assert math.dist((0, 0), elbow) == pytest.approx(2.0, abs=1e-7)
    assert math.dist(elbow, hand) == pytest.approx(1.5, abs=1e-7)
    assert math.dist((0, 0), hand) <= 3.5


def test_spring_deterministic_and_bounded_settle():
    assert spring_progress(0) == 0
    assert spring_progress(2) == pytest.approx(1, abs=.01)
    assert spring_progress(.3) == spring_progress(.3)


def test_v02_scene_has_genuine_motion_and_seek_safe_frames():
    p = load_project(EXAMPLE)
    scene = p.scenes[0]
    p0 = actor_pose(scene, scene["characters"][0], .4)
    p1 = actor_pose(scene, scene["characters"][0], 1.4)
    assert p0.x != p1.x
    assert p1.run != 0
    assert actor_pose(scene,scene["characters"][0],3.5).gesture == "point"
    assert actor_pose(scene,scene["characters"][0],3.5).expression == "surprised"
    assert actor_pose(scene,scene["characters"][0],5.8).mouth > 0
    a = render_frame(p,scene,.5,width=240,height=136)
    b = render_frame(p,scene,.5,width=240,height=136)
    c = render_frame(p,scene,1.4,width=240,height=136)
    assert a.tobytes() == b.tobytes()
    assert ImageChops.difference(a,c).getbbox() is not None
    assert advanced_hand(scene["characters"][0],p1,240,136,1.4) != advanced_hand(
        scene["characters"][0],actor_pose(scene,scene["characters"][0],3.5),240,136,3.5)


def test_rig_rejects_invalid_lengths_and_mouth_timing():
    p = copy.deepcopy(load_project(EXAMPLE).data)
    p["scenes"][0]["characters"][0]["rig"]["forearm"] = -2
    with pytest.raises(SceneError,match="forearm"):
        validate_project(p)
    p = copy.deepcopy(load_project(EXAMPLE).data)
    cues = p["scenes"][0]["actions"][-1]["mouth_cues"]
    cues[1]["at"] = -1
    with pytest.raises(SceneError,match="mouth_cues"):
        validate_project(p)
    p = copy.deepcopy(load_project(EXAMPLE).data)
    p["scenes"][0]["actions"][0]["to"] = [float("nan"),.7]
    with pytest.raises(SceneError,match="finite"):
        validate_project(p)
