"""Independent FFprobe + decoded-frame verification for actual rendered files."""
from __future__ import annotations
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import shutil
import subprocess
from PIL import Image, ImageStat


def _run(args: list[str]) -> str:
    proc=subprocess.run(args,text=True,capture_output=True)
    if proc.returncode:
        raise RuntimeError("video QA command failed: "+proc.stderr[-800:])
    return proc.stdout


def verify_video(path: str | Path, sample_dir: str | Path | None = None) -> dict:
    video=Path(path).resolve()
    if not video.is_file() or video.stat().st_size < 100:
        raise ValueError("missing or empty video")
    ffprobe=shutil.which("ffprobe")
    ffmpeg=shutil.which("ffmpeg")
    if not ffprobe or not ffmpeg:
        raise RuntimeError("ffmpeg and ffprobe must be installed for video QA")
    payload=json.loads(_run([ffprobe,"-v","error","-show_entries",
        "format=duration:stream=index,codec_name,codec_type,width,height,r_frame_rate,nb_frames",
        "-of","json",str(video)]))
    streams=payload.get("streams",[])
    visual=next((s for s in streams if s.get("codec_type")=="video"),None)
    if not visual or visual.get("codec_name")!="h264":
        raise RuntimeError("expected H.264 video stream")
    w,h=visual["width"],visual["height"]
    duration=float(payload["format"]["duration"])
    if duration<=0 or w<64 or h<64:
        raise RuntimeError("invalid video duration or dimensions")
    num,den=(int(n) for n in visual["r_frame_rate"].split("/"))
    if den==0 or num<=0:
        raise RuntimeError("invalid frame rate")
    output_dir=Path(sample_dir).resolve() if sample_dir else None
    sample_times=(.1,.5,.9)
    checks=[]
    with TemporaryDirectory(prefix="aetherpaper-qa-") as tmp:
        destination=output_dir or Path(tmp)
        destination.mkdir(parents=True,exist_ok=True)
        for idx,fraction in enumerate(sample_times):
            timestamp=duration*fraction
            frame=destination/f"qa_{idx+1:02d}.png"
            _run([ffmpeg,"-y","-hide_banner","-loglevel","error",
                  "-ss",f"{timestamp:.4f}","-i",str(video),
                  "-frames:v","1",str(frame)])
            with Image.open(frame) as img:
                stat=ImageStat.Stat(img.convert("L"))
                checks.append({"time":round(timestamp,4),
                               "variance":round(stat.var[0],3),
                               "readable":True})
                if stat.var[0]<1:
                    raise RuntimeError(f"nearly uniform image at {timestamp:.2f}s")
    return {"video":str(video),"codec":visual["codec_name"],
            "width":w,"height":h,"fps":num/den,
            "frames":int(visual.get("nb_frames") or round(duration*num/den)),
            "duration":duration,
            "audio_codecs":[s["codec_name"] for s in streams if s.get("codec_type")=="audio"],
            "frame_checks":checks,
            "sample_dir":str(output_dir) if output_dir else None}
