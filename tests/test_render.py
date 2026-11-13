from pathlib import Path
import json
import shutil
import subprocess
import pytest
from PIL import Image, ImageChops
from aetherpaper.model import load_project, validate_project, SceneError
from aetherpaper.paint import render_frame
from aetherpaper.renderer import render, snapshot
from aetherpaper.cli import main

ROOT=Path(__file__).resolve().parents[1]


def test_deterministic_and_dynamic_frames():
    project=load_project(ROOT/'examples/room_pickup.json')
    scene=project.scenes[0]
    a=render_frame(project,scene,1,width=240,height=136)
    b=render_frame(project,scene,1,width=240,height=136)
    c=render_frame(project,scene,2,width=240,height=136)
    assert a.tobytes()==b.tobytes()
    assert ImageChops.difference(a,c).getbbox() is not None


def test_snapshot_file(tmp_path):
    project=load_project(ROOT/'examples/room_pickup.json')
    path=snapshot(project,5,tmp_path/'snap.png',width=320,height=180)
    with Image.open(path) as image:
        assert image.size==(320,180)
        assert image.format=='PNG'


def test_image_path_cannot_escape_project(tmp_path):
    p=load_project(ROOT/'examples/room_pickup.json')
    p.data['scenes'][0]['layers'].append({'type':'image','x':0,'y':0,'width':.1,'height':.1,'src':'../../../../etc/passwd'})
    with pytest.raises(ValueError,match='stay within'):
        render_frame(p,p.scenes[0],0,width=240,height=136)


@pytest.mark.skipif(not shutil.which('ffmpeg'),reason='FFmpeg unavailable')
def test_real_mp4_and_ffprobe(tmp_path):
    p=load_project(ROOT/'examples/room_pickup.json')
    p.scenes[0]['duration']=1.0
    p.scenes[0]['actions']=[]
    p.scenes[0]['camera']=[]
    output=tmp_path/'actual.mp4'
    result=render(p,output,width=160,height=90,fps=5)
    assert result['frames']==5
    assert result['bytes']>1000
    if shutil.which('ffprobe'):
        info=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0',
            '-show_entries','stream=codec_name,width,height,nb_frames','-of','json',str(output)]))
        st=info['streams'][0]
        assert st['codec_name']=='h264'
        assert (st['width'],st['height'])==(160,90)
        assert int(st['nb_frames'])==5


def test_bad_speech_type_rejected():
    p=load_project(ROOT/'examples/room_pickup.json')
    p.scenes[0]['actions'][2]['type']='teleport'
    with pytest.raises(SceneError,match='unsupported action'):
        validate_project(p.data)
