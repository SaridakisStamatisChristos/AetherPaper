from pathlib import Path
import pytest
from aetherpaper.model import load_project
from aetherpaper.timeline import at_time, actor_pose, active_caption, camera_state

ROOT=Path(__file__).resolve().parents[1]

def test_walk_ends_at_target():
    scene=load_project(ROOT/'examples/room_pickup.json').scenes[0]
    actor=scene['characters'][0]
    assert actor_pose(scene,actor,0.0).x == actor['x']
    assert actor_pose(scene,actor,3).x == pytest.approx(.54)
    assert actor_pose(scene,actor,2).walk != 0


def test_prop_attach_and_speech():
    scene=load_project(ROOT/'examples/room_pickup.json').scenes[0]
    actor=scene['characters'][0]
    assert actor_pose(scene,actor,4.0).holding is None
    assert actor_pose(scene,actor,4.6).holding == 'book'
    assert actor_pose(scene,actor,5).talking
    assert active_caption(scene,5) == 'Found it! This is real animation.'
    assert active_caption(scene,3) is None


def test_camera_and_scene_boundaries():
    project=load_project(ROOT/'examples/three_scenes.json')
    assert at_time(project,0)[0]['id']=='opening'
    assert at_time(project,3)[0]['id']=='sunny-day'
    assert at_time(project,6)[0]['id']=='finale'
    assert camera_state(project.scenes[1],3)[2]==pytest.approx(1.09)
    with pytest.raises(ValueError):
        at_time(project,9)
