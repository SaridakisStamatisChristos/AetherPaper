# AetherPaper v0.6 — Whole-Pose Illustration Engine

**Development status:** opt-in feature branch `feature/pose-art-cinematography-v0.6`, stacked on the validated v0.5 branch. No changes to `main`.

## Motivation

The v0.3–v0.5 demonstrations proved the JSON-to-video pipeline, deterministic rigging, audio, camera animation and prop attachment. But their sample character remains visually crude: rectangular limbs, variable silhouette, and disconnected sections. Greater filter complexity is not a substitute for actual illustration.

v0.6 adds a **second character animation system** alongside the existing reusable skeletal rig: whole-body illustrated pose sheets. Artists can supply complete, consistent, transparent PNG cels with the character's coat, hair, face, hands and legs painted *together*. Pose selection changes a full drawing, rather than bending 20 rectangular pieces independently.

The runtime still renders locally through Python/Pillow/FFmpeg. No LLM call, cloud subscription or browser is required for video production. The sample posekit command generates a fallback six-pose PNG from the previous source art, but artists can **replace the generated file** with genuinely sophisticated artwork.

## Linux Mint / Ubuntu setup

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip ffmpeg espeak-ng
git clone https://github.com/SaridakisStamatisChristos/AetherPaper.git
cd AetherPaper
git switch feature/pose-art-cinematography-v0.6
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
pytest -q
```

## Real video example

```bash
aetherpaper posekit --source examples/last_light_directed_v05.json --out examples/assets/pose_courier.png
aetherpaper validate examples/illustrated_poses_v06.json
aetherpaper manifest examples/illustrated_poses_v06.json
aetherpaper render examples/illustrated_poses_v06.json --width 640 --height 360 --fps 24 --out output/illustrated_poses_v06.mp4
aetherpaper snapshot examples/illustrated_poses_v06.json --at 5.5 --out output/illustrated_carry.png
aetherpaper qa output/illustrated_poses_v06.mp4 --frames-dir output/pose_qa
```

The JSON scene has a 14-second runtime with 11 pose switches, a cinematic sunset environment, hand-directed movement/camera and subtitles. The bundled generator creates a transparent **1536×1024** PNG containing six equal **512×512** poses in a 3×2 grid. Generated fallback art remains editable; `posekit` deliberately refuses to overwrite a modified artist file.

## Source art specification

Pose cels must be placed inside one RGBA PNG with a regular grid. Every pose must depict the **same character** from the **same coherent angle and relative scale**, with its feet aligned to the same intended pivot. Prefer a clean transparent background with the entire character inside each cell, without labels, borders or shadows beyond the character cutout.

`visual.type="pose_atlas"` accepts:

```json
{
  "type":"pose_atlas",
  "src":"assets/pose_courier.png",
  "columns":3,
  "rows":2,
  "height":0.77,
  "aspect_ratio":1.0,
  "anchor":[0.5,0.875],
  "poses":{
    "idle":{"cell":0},
    "step":{"cell":1},
    "reach":{"cell":2},
    "carry":{"cell":3},
    "place":{"cell":4},
    "gaze":{"cell":5}
  },
  "timeline":[
    {"at":0,"pose":"idle"},
    {"at":0.6,"pose":"step","crossfade":0.07},
    {"at":2.0,"pose":"idle"}
  ]
}
```

Positions `x,y` in the actor still come from the normal movement/performance JSON. The `anchor` is the normalized point in the 512×512 cell that should land on `actor.x, actor.y`. Use individual `poses[id].anchor` overrides when a pose's feet are painted at a different pixel coordinate. `height` is the fraction of video height occupied by the full atlas cell, not necessarily by the opaque body. `aspect_ratio` is the cell width/height for correctly mapping any `hand` anchor (1.0 for square cells).

Each switch uses an absolute scene-local `at` time and a mapped `pose`. All switches must be strictly increasing and start at zero. `crossfade` is optional and defaults to zero (sharp cut). A short 0.05–0.10 second crossover can soften a jump, but crossfading two visibly different limb positions creates ghost limbs; do not use long fades for walking. The result is **cel/pose-based** motion with continuously animated actor positions and camera, not automatic interpolation of the painted anatomy.

### Props and contact

If lanterns are painted directly into a `carry` or `place` pose, **do not add a separate lantern prop to the same scene** or it will appear twice. Alternatively, paint the character *without* a prop, add a normalized `hand` anchor to every illustrated variant, and let the existing prop physics attach the separate lantern to that coordinate:

```json
"carry": {"cell":3,"anchor":[0.5,0.875],"hand":[0.77,0.49]}
```

The hand anchor is authored by the artist and should be checked visually. A painted pose atlas does **not** have a live skeleton; its hand location is artist-specified rather than automatically solved through inverse kinematics. For physics-critical interactions use the existing `visual.type="sprites"` with skeletal IK or authored exact hand anchors.

### Existing systems remain available

`visual.type="illustrated"` remains the original drawn character. `visual.type="sprites"` remains the 20-part rig with source PNGs, head/face animations and 2.5D projected limbs. `visual.type="pose_atlas"` is the new alternate renderer for more coherent professionally illustrated silhouettes.

Legacy 0.1–0.5 projects remain valid and are part of CI regression tests. Pose PNG assets are included in the preflight asset audit and SHA-256 production manifest. File traversal and remote URL references are rejected.

## Quality honesty and limitations

Using complete painted poses can dramatically improve silhouette quality **when the supplied artwork is excellent**, but this engine still has no automatic motion capture, morphing between drawings, hand-painted in-betweens, 3-D relighting, neural frame interpolation, or automatic clean asset extraction from an arbitrary picture.

The sample fallback atlas generated from v0.5 source art reproduces v0.5's crude visual characteristics; the point is to **prove the engine accepts genuinely better full-pose art without rewrites**. The rendered CI demo verifies motion functionality, not professional aesthetic quality. The separately created illustration reference sheet is an art direction/reference asset, not a proof that it is committed to the GitHub repository until its file is actually placed at the specified local path.

Keep this branch and PR as a draft pending real video inspection. Do not merge into main without quality review.
