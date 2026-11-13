import copy
import json
from pathlib import Path
import shutil
import subprocess
import pytest
from aetherpaper.assets import production_manifest, audit_assets
from aetherpaper.model import load_project,SceneError
from aetherpaper.renderer import render
from aetherpaper.qa import verify_video
from aetherpaper.cli import main

ROOT=Path(__file__).resolve().parents[1]
DEMO=ROOT/"examples"/"explainer_demo.json"


def test_24_second_four_scene_production_manifest():
    p=load_project(DEMO)
    manifest=production_manifest(p)
    assert manifest["duration_seconds"] == 24
    assert manifest["scene_count"] == 4
    assert manifest["ai_runtime_required"] is False
    assert manifest["network_required"] is False
    assert audit_assets(p)==[]


def test_asset_audit_rejects_broken_references(tmp_path):
    p=load_project(DEMO)
    data=copy.deepcopy(p.data)
    data["scenes"][0]["layers"].append(
        {"type":"image","x":0,"y":0,"width":.1,"height":.1,"src":"missing.png"})
    from aetherpaper.model import Project
    invalid=Project(tmp_path/"project.json",data)
    with pytest.raises(SceneError,match="missing"):
        audit_assets(invalid)


def test_manifest_cli(capsys):
    assert main(["manifest",str(DEMO)])==0
    output=json.loads(capsys.readouterr().out)
    assert output["scene_count"]==4


@pytest.mark.skipif(not (shutil.which("ffmpeg") and shutil.which("ffprobe")),reason="FFmpeg unavailable")
def test_qa_real_animated_video(tmp_path):
    p=load_project(ROOT/"examples"/"rig_demo.json")
    # A short subset keeps the integration test quick; it still decodes a real H.264.
    p.scenes[0]["duration"]=1
    p.scenes[0]["actions"]=[]
    p.scenes[0]["camera"]=[]
    out=tmp_path/"test.mp4"
    result=render(p,out,width=160,height=90,fps=5)
    assert result["frames"]==5
    qa=verify_video(out,tmp_path/"frames")
    assert qa["codec"]=="h264"
    assert qa["frames"]==5
    assert qa["fps"]==5
    assert len(qa["frame_checks"])==3
    assert set(x.name for x in (tmp_path/"frames").iterdir())=={"qa_01.png","qa_02.png","qa_03.png"}
