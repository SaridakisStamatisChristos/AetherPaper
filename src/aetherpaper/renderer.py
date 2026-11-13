"""Seek-safe frame snapshots and streaming H.264 video rendering."""
from __future__ import annotations
from pathlib import Path
from tempfile import TemporaryDirectory
import shutil
import subprocess
from .model import Project
from .timeline import at_time
from .paint import render_frame
from .audio import mux_voice
from .assets import audit_assets


def snapshot(project:Project,t:float,out:str|Path,width:int|None=None,height:int|None=None) -> Path:
    scene,local=at_time(project,t)
    image=render_frame(project,scene,local,width=width,height=height)
    path=Path(out);path.parent.mkdir(parents=True,exist_ok=True)
    image.save(path,format='PNG')
    return path


def render(project:Project,out:str|Path,width:int|None=None,height:int|None=None,
           fps:int|None=None,voice:str='none') -> dict:
    W=width or project.canvas['width']; H=height or project.canvas['height']
    if W<64 or H<64 or W%2 or H%2:
        raise ValueError('width and height must be even integers >=64')
    fps=fps or project.canvas['fps']
    if fps<1 or fps>60:
        raise ValueError('fps must be within 1..60')
    if voice not in ('none','espeak'):
        raise ValueError('unsupported voice backend')
    # Preflight all local image/WAV references before creating any output.
    audit_assets(project)
    executable=shutil.which('ffmpeg')
    if not executable:
        raise RuntimeError('FFmpeg is required to render MP4; install ffmpeg')
    out=Path(out).resolve();out.parent.mkdir(parents=True,exist_ok=True)
    frames=sum(round(s['duration']*fps) for s in project.scenes)
    with TemporaryDirectory(prefix='aetherpaper-render-') as tmp:
        raw=Path(tmp)/'silent.mp4'
        command=[executable,'-y','-hide_banner','-loglevel','error',
                 '-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}',
                 '-r',str(fps),'-i','pipe:0','-c:v','libx264','-preset','veryfast',
                 '-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',str(raw)]
        proc=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        try:
            assert proc.stdin is not None
            for scene in project.scenes:
                n=round(scene['duration']*fps)
                for i in range(n):
                    img=render_frame(project,scene,i/fps,width=W,height=H)
                    proc.stdin.write(img.tobytes())
            proc.stdin.close()
            stderr=proc.stderr.read().decode('utf-8','replace') if proc.stderr else ''
            status=proc.wait()
            if status:
                raise RuntimeError('FFmpeg video render failed: '+stderr[-1200:])
            mux_voice(raw,project,out,backend=voice)
        except BaseException:
            if proc.poll() is None:
                proc.kill()
                proc.wait()
            raise
    return {'output':str(out),'width':W,'height':H,'fps':fps,'frames':frames,
            'duration':project.duration,'bytes':out.stat().st_size,'voice':voice}
