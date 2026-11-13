"""CLI: one JSON document -> validated frames and MP4."""
from __future__ import annotations
import argparse
import json
from .model import load_project, SceneError
from .renderer import snapshot, render


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
    args=parser.parse_args(argv)
    try:
        project=load_project(args.project)
        if args.command=='validate':
            print(json.dumps({'valid':True,'title':project.data.get('title','Untitled'),
                              'scenes':len(project.scenes),'duration':project.duration},indent=2))
        elif args.command=='snapshot':
            print(snapshot(project,args.at,args.out,width=args.width,height=args.height))
        else:
            print(json.dumps(render(project,args.out,width=args.width,height=args.height,
                                    fps=args.fps,voice=args.voice),indent=2))
        return 0
    except (SceneError,ValueError,RuntimeError,OSError,FileNotFoundError) as exc:
        parser.exit(2,f'error: {exc}\n')
