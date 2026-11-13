import copy
from pathlib import Path
import pytest
from PIL import ImageChops
from aetherpaper.model import load_project,validate_project,SceneError
from aetherpaper.paint import render_frame
from aetherpaper.timeline import camera_state
from aetherpaper.styles import transition_frame

EXAMPLE=Path(__file__).resolve().parents[1]/"examples"/"visual_demo.json"


def test_three_presets_render_distinct_frames():
    p=load_project(EXAMPLE)
    assert [s["style"] for s in p.scenes]==["paper_cut","scrapbook","storybook"]
    images=[render_frame(p,s,2,width=240,height=136) for s in p.scenes]
    assert images[0].tobytes()!=images[1].tobytes()
    assert images[1].tobytes()!=images[2].tobytes()
    assert render_frame(p,p.scenes[2],2,width=240,height=136).tobytes()==images[2].tobytes()


def test_camera_tracking_moves_with_actor():
    p=load_project(EXAMPLE)
    scene=p.scenes[1]
    start=camera_state(scene,.15)
    finish=camera_state(scene,2.7)
    assert finish[0]>start[0]
    assert finish[2]>start[2]


def test_invalid_presets_and_transition_rejected():
    p=copy.deepcopy(load_project(EXAMPLE).data)
    p["scenes"][0]["style"]="invented"
    with pytest.raises(SceneError,match="preset"):
        validate_project(p)
    p=copy.deepcopy(load_project(EXAMPLE).data)
    p["scenes"][1]["transition"]["type"]="nope"
    with pytest.raises(SceneError,match="transition"):
        validate_project(p)
    p=copy.deepcopy(load_project(EXAMPLE).data)
    p["scenes"][1]["layers"][0]["depth"]=2
    with pytest.raises(SceneError,match="depth"):
        validate_project(p)


def test_transition_is_deterministic_and_visible():
    p=load_project(EXAMPLE)
    scene=p.scenes[2]
    a=render_frame(p,scene,.02,width=240,height=136)
    b=render_frame(p,scene,.32,width=240,height=136)
    assert ImageChops.difference(a,b).getbbox() is not None
    assert a.tobytes()==render_frame(p,scene,.02,width=240,height=136).tobytes()
