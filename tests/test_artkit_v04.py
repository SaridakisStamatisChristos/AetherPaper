"""V0.4: real 20-layer PNG artwork, IK contact, motion and offline scene."""
from pathlib import Path
import copy
import json
import math
import pytest
from PIL import Image, ImageChops

from aetherpaper.artkit import BUILDERS, build_artkit
from aetherpaper.assets import audit_assets
from aetherpaper.model import Project,load_project,validate_project,SceneError
from aetherpaper.rig import Bone,Skeleton,two_bone_ik
from aetherpaper.sprite_rig import posed_sprite_joints,sprite_hand
from aetherpaper.timeline import actor_pose
from aetherpaper.physics import prop_state
from aetherpaper.paint import render_frame
from aetherpaper.cli import main

SCENE=Path(__file__).resolve().parents[1]/"examples"/"last_light_v04.json"


@pytest.fixture
def project(tmp_path):
    output=tmp_path/"assets"/"atelier_courier"
    kit=build_artkit(output)
    assert kit["parts"]>=20
    data=json.loads(SCENE.read_text(encoding="utf-8"))
    validate_project(data)
    path=tmp_path/"last_light_v04.json"
    path.write_text(json.dumps(data),encoding="utf-8")
    return Project(path,data)


def test_anatomical_offsets_and_legacy_skeleton():
    bones=[Bone("root",None,1,0),Bone("arm","root",.5,0,1,(.2,-.3))]
    root=Skeleton(bones).solve((5,6),3)
    assert root["arm"][0]==pytest.approx((8.6,5.1))
    assert root["arm"][1]==pytest.approx((10.1,5.1))
    with pytest.raises(ValueError,match="offset"):
        Skeleton([Bone("bad",None,.3,offset=(float("nan"),0))])


def test_generated_artkit_contains_real_alpha_illustrations(project):
    entries=audit_assets(project)
    assert len(entries)==20
    art=project.source.parent/"assets"/"atelier_courier"
    assert all(Path(entry["path"]).suffix==".png" for entry in entries)
    for name in ("torso.png","head.png","cape.png","forearm_r.png","face_happy.png"):
        with Image.open(art/name) as img:
            assert img.mode=="RGBA" and img.width>=500
            assert 0<img.getextrema()[3][0]<256 or img.getextrema()[3]==(0,255)
            assert len(img.getcolors(maxcolors=10_000_000) or [])>3
    # Generated artkit is reproducible in the same Python/Pillow environment.
    build_artkit(art)
    (art/"head.png").write_bytes(b"artist modified")
    with pytest.raises(FileExistsError,match="refusing"):
        build_artkit(art)


def test_v04_real_frame_determinism_and_nontrivial_motion(project):
    s=project.scenes[0]
    a=render_frame(project,s,1.5,width=320,height=180)
    b=render_frame(project,s,1.5,width=320,height=180)
    c=render_frame(project,s,5.8,width=320,height=180)
    assert a.tobytes()==b.tobytes()
    assert ImageChops.difference(a,c).getbbox()
    assert a.getbbox()
    assert len(a.getcolors(maxcolors=1_000_000) or [])>200


def test_ik_sprite_rig_maintains_lengths_and_reaches_grasp(project):
    scene=project.scenes[0];actor=scene["characters"][0]
    p=actor_pose(scene,actor,4.39)
    w,h=640,360
    j=posed_sprite_joints(actor,p,w,h,4.39)
    for upper,lower in (("arm_r","forearm_r"),("arm_l","forearm_l"),
                        ("thigh_l","shin_l"),("thigh_r","shin_r")):
        assert j[upper][1]==pytest.approx(j[lower][0])
        expected=next(b["length"] for b in actor["rig"]["bones"] if b["name"]==upper)
        assert math.dist(*j[upper][:2])==pytest.approx(expected*h*.66*actor["scale"],abs=.01)
    hand=sprite_hand(actor,p,w,h,4.39)
    target=(.625*w,.676*h)
    assert math.dist(hand,target)<32


def test_physical_held_prop_is_exactly_at_visible_sprite_hand(project):
    scene=project.scenes[0];actor=scene["characters"][0];prop=scene["props"][0]
    def hand(aid,t):
        assert aid=="courier"
        p=actor_pose(scene,actor,t)
        x,y=sprite_hand(actor,p,640,360,t)
        return (x/640,y/360)
    for t in (4.55,5.9,6.8):
        state=prop_state(scene,prop,t,hand)
        assert state.owner=="courier"
        assert state.center==pytest.approx(hand("courier",t))
    after=prop_state(scene,prop,9.2,hand)
    assert after.owner is None
    assert after.center==pytest.approx((.795,.666))


def test_expression_and_mouth_assets_selection(project):
    from aetherpaper.sprite_rig import _selected
    actor=project.scenes[0]["characters"][0];scene=project.scenes[0]
    p=actor_pose(scene,actor,8.90)
    assert p.expression=="happy" and p.talking
    parts=actor["visual"]["parts"]
    happy=next(part for part in parts if part.get("expression")=="happy")
    neutral=next(part for part in parts if part.get("expression")=="neutral")
    assert _selected(happy,p,8.90)
    assert not _selected(neutral,p,8.90)
    mouth_parts=[part for part in parts if part.get("mouth_state")]
    assert sum(_selected(part,p,8.90) for part in mouth_parts)==1


def test_sprite_schema_validation_rejects_bad_offsets_and_expressions(project):
    data=project.data
    wrong=copy.deepcopy(data)
    wrong["scenes"][0]["characters"][0]["rig"]["bones"][0]["offset"]=[9,0]
    with pytest.raises(SceneError,match="offset"):
        validate_project(wrong)
    wrong=copy.deepcopy(data)
    wrong["scenes"][0]["characters"][0]["visual"]["parts"][0]["mouth_state"]="maybe"
    with pytest.raises(SceneError,match="mouth_state"):
        validate_project(wrong)
    wrong=copy.deepcopy(data)
    wrong["scenes"][0]["characters"][0]["visual"]["parts"][0]["expression"]="wild"
    with pytest.raises(SceneError,match="expression"):
        validate_project(wrong)


def test_artkit_cli_generates_20_pngs(tmp_path,capsys):
    location=tmp_path/"art"
    assert main(["artkit","--out",str(location)])==0
    receipt=json.loads(capsys.readouterr().out)
    assert receipt["parts"]==20
    assert all((location/name).is_file() for name in receipt["sha256"])
