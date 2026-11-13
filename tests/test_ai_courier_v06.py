"""Acceptance tests using real v0.6 AI-created transparent illustrated artwork.

The original generated PNG is pinned by SHA-256 and imported during the
v0.6 CI acquisition step. These tests must pass after that step, not merely
with the legacy pose-atlas fixture.
"""
from __future__ import annotations
from hashlib import sha256
from pathlib import Path
import math

import pytest
from PIL import Image,ImageChops

from aetherpaper.model import load_project
from aetherpaper.pose_atlas import select_pose,illustrated_hand
from aetherpaper.timeline import actor_pose
from aetherpaper.assets import audit_assets
from aetherpaper.physics import prop_state
from aetherpaper.paint import render_frame


ROOT=Path(__file__).resolve().parents[1]
SCENE=ROOT/"examples/ai_illustrated_courier_v06.json"
SHEET=ROOT/"examples/assets/ai_courier/original_pose_atlas.png"
CHECKSUM="21a117aba23df6a164eb631b5a7bcc4664d19491620ab2ae752da3af053d340b"

pytestmark=pytest.mark.skipif(not SHEET.is_file(),
                            reason="Original pinned illustrated artwork is acquired by the v0.6 CI job")


def test_original_ai_art_is_sha_pinned_and_genuine_rgba():
    assert sha256(SHEET.read_bytes()).hexdigest()==CHECKSUM
    with Image.open(SHEET) as img:
        assert img.format=="PNG"
        assert img.size==(1536,1024)
        assert img.mode=="RGBA"
        a=img.getchannel("A")
        assert a.getextrema()[0]==0 and a.getextrema()[1]>240
        assert len(img.getcolors(maxcolors=10_000_000) or [])>1000


def test_six_independently_imported_painted_poses():
    project=load_project(SCENE)
    refs=audit_assets(project)
    assert len(refs)==6
    assert len({x["sha256"] for x in refs})==6
    visual=project.scenes[0]["characters"][0]["visual"]
    assert set(visual["states"])=={"idle","walk","reach","carry","speak"}
    assert len(visual["states"]["walk"])==2
    for state,parts in visual["states"].items():
        for part in parts:
            image=project.source.parent/part["src"]
            with Image.open(image) as im:
                assert im.mode=="RGBA"
                assert im.size==(512,512)
                alpha=im.getchannel("A")
                assert alpha.getextrema()[0]==0
                assert alpha.getextrema()[1]>230
                coverage=sum(1 for a in alpha.getdata() if a>8)/(512*512)
                assert .12 < coverage < .50


def test_director_poses_resolve_to_original_illustrations():
    project=load_project(SCENE)
    scene=project.scenes[0]
    actor=scene["characters"][0]
    timestamps=[(.4,"walk"),(1.75,"idle"),(2.4,"reach"),(3.5,"carry"),(4.4,"speak")]
    for time,expect in timestamps:
        pose=actor_pose(scene,actor,time)
        state,part,index=select_pose(actor["visual"],pose,time)
        assert state==expect
        assert (project.source.parent/part["src"]).is_file()
    assert actor_pose(scene,actor,0.0).x<actor_pose(scene,actor,1.7).x


def test_real_ai_illustrated_frame_renders_at_different_story_beats():
    project=load_project(SCENE)
    scene=project.scenes[0]
    walk=render_frame(project,scene,.8,width=320,height=180)
    walk2=render_frame(project,scene,.8,width=320,height=180)
    hold=render_frame(project,scene,3.5,width=320,height=180)
    assert walk.tobytes()==walk2.tobytes()
    assert ImageChops.difference(walk,hold).getbbox() is not None
    assert len(walk.getcolors(maxcolors=1_000_000) or [])>500


def test_physical_lantern_uses_painted_hand_anchor():
    project=load_project(SCENE)
    scene=project.scenes[0]
    actor=scene["characters"][0]
    prop=scene["props"][0]
    def hand(actor_id,time):
        assert actor_id=="courier"
        pose=actor_pose(scene,actor,time)
        x,y=illustrated_hand(actor,pose,time,640,360,project.source.parent)
        return x/640,y/360
    initial=prop_state(scene,prop,0.5,hand)
    carried=prop_state(scene,prop,3.35,hand)
    assert initial.owner is None
    assert carried.owner=="courier"
    assert carried.center==pytest.approx(hand("courier",3.35))
    x,y=carried.center
    assert 0<x<1 and 0<y<1


def test_pose_sheet_provenance_receipt_is_consistent():
    project=load_project(SCENE)
    receipt=project.source.parent/"assets/ai_courier/poses/posepack.json"
    import json
    data=json.loads(receipt.read_text(encoding="utf-8"))
    assert data["format"]=="aetherpaper-posepack-0.6"
    assert data["source_sha256"]==CHECKSUM
    assert data["frames"]==6
    assert data["states"]["walk"]==2
