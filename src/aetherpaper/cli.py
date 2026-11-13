"""CLI: one JSON document -> validated frames and MP4."""
from __future__ import annotations
import argparse
import json
from .model import load_project, SceneError
from .renderer import snapshot, render
from .assets import production_manifest
from .qa import verify_video
from .artkit import build_artkit
from .studio_art import generate_studio_kit
from .pose_atlas import import_pose_sheet
from .pose_demo import make_demo


def main(argv=None) -> int:
    parser=argparse.ArgumentParser(prog='aetherpaper',description='Deterministic JSON-driven paper animation')
    sub=parser.add_subparsers(dest='command',required=True)
    v=sub.add_parser('validate',help='validate versioned scene JSON')
    v.add_argument('project')
    s=sub.add_parser('snapshot',help='render a single still frame at time T')
    s.add_argument('project');s.add_argument('--at',type=float,required=True)
    s.add_argument('--out',default='output/frame.png')
    s.add_argument('--width',type=int);s.add_argument('--height',type=int)
    r=sub.add_parser('render',help='produce an H.264 MP4 offline')
    r.add_argument('project');r.add_argument('--out',default='output/movie.mp4')
    r.add_argument('--width',type=int);r.add_argument('--height',type=int)
    r.add_argument('--fps',type=int);r.add_argument('--voice',choices=['none','espeak'],default='none')
    m=sub.add_parser('manifest',help='validate scene assets and export offline production manifest')
    m.add_argument('project')
    q=sub.add_parser('qa',help='probe H.264 stream and decode three real video frames')
    q.add_argument('video');q.add_argument('--frames-dir')
    g=sub.add_parser('artkit',help='generate original transparent PNG artwork for the v0.4 rig')
    g.add_argument('--out',default='examples/assets/atelier_courier')
    g.add_argument('--edition',choices=['original','studio'],default='original')
    pa=sub.add_parser('posepack',help='import artist-supplied transparent PNG pose sheet using JSON cell layout')
    pa.add_argument('--sheet',required=True)
    pa.add_argument('--layout',required=True)
    pa.add_argument('--out',required=True)
    pd=sub.add_parser('pose-demo',help='generate an actual pose-atlas regression scene from preserved artwork')
    pd.add_argument('--source',default='examples/last_light_directed_v05.json')
    pd.add_argument('--out',default='examples')
    args=parser.parse_args(argv)
    try:
        if args.command=='pose-demo':
            print(json.dumps(make_demo(args.source,args.out),indent=2))
            return 0
        if args.command=='posepack':
            print(json.dumps(import_pose_sheet(args.sheet,args.layout,args.out),indent=2))
            return 0
        if args.command=='artkit':
            print(json.dumps(generate_studio_kit(args.out) if args.edition=='studio' else build_artkit(args.out),indent=2))
            return 0
        if args.command=='qa':
            print(json.dumps(verify_video(args.video,sample_dir=args.frames_dir),indent=2))
            return 0
        project=load_project(args.project)
        if args.command=='manifest':
            print(json.dumps(production_manifest(project),indent=2))
        elif args.command=='validate':
            print(json.dumps({'valid':True,'title':project.data.get('title','Untitled'),
                              'scenes':len(project.scenes),'duration':project.duration},indent=2))
        elif args.command=='snapshot':
            print(snapshot(project,args.at,args.out,width=args.width,height=args.height))
        else:
            print(json.dumps(render(project,args.out,width=args.width,height=args.height,
                                    fps=args.fps,voice=args.voice),indent=2))
        return 0
    except (SceneError,ValueError,RuntimeError,OSError,FileNotFoundError,FileExistsError) as exc:
        parser.exit(2,f'error: {exc}\n')
