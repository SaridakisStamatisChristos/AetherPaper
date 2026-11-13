# AetherPaper v0.5 — Art Direction and Hand-Choreographed Performance

**Development branch:** `feature/art-direction-v0.5`, stacked on v0.4. Do not merge into main automatically.

## Why this release exists

v0.4 proved the 20-piece PNG cutout pipeline but its artwork and joint motion were still obviously primitive. v0.5 adds a cohesive original watercolor-paper character art treatment, a dedicated cinematic sunset environment, and **director-authored, time-indexed pose keyframes**. Unlike generic sines, a performance track is independently evaluated at any time and can control body blocking, head angle, gaze, grounded feet, deliberate hand reaching, hold phases and expression.

This is a serious art/animation infrastructure improvement, **not a claim that the generated sample art is equivalent to professional hand-painted production artwork**. Human-authored or commissioned layers can still be dropped into the same pipeline without editing the renderer.

## Linux Mint / Ubuntu

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip ffmpeg espeak-ng
git clone https://github.com/SaridakisStamatisChristos/AetherPaper.git
cd AetherPaper
git switch feature/art-direction-v0.5
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
pytest -q
```

Generate the coherent original 20-layer studio character pack:

```bash
aetherpaper artkit --edition studio --out examples/assets/studio_courier
aetherpaper validate examples/last_light_directed_v05.json
aetherpaper manifest examples/last_light_directed_v05.json > output/studio_manifest.json
aetherpaper render examples/last_light_directed_v05.json --out output/last_light_directed_v05.mp4
aetherpaper qa output/last_light_directed_v05.mp4 --frames-dir output/qa_v05
```

The demo is **14 seconds, 960×540 at 24fps** by default. CI renders at 640×360/24fps for verification while preserving 960×540 snapshots. Supersampling draws at double-resolution then resizes with Lanczos. For a very quick preview, override `--width 480 --height 270` on the render command. The full artkit PNG pack is persisted by successful CI in the `examples/assets/studio_courier/` folder.

## New performance action

A `performance` action is a continuous, hand-directed, stateless track with precisely timed keyframes. It can be combined with existing walk, speak, pickup and place events; keyframe controls override only their named properties.

```json
{
  "type":"performance",
  "target":"courier",
  "start":0.0,
  "end":4.0,
  "keyframes":[
    {"at":0,"position":[0.16,0.88],
     "feet_world":{"l":[0.13,0.88],"r":[0.19,0.88]},
     "angles":{"head":0.06},"hand_weight":0},
    {"at":1.0,"position":[0.22,0.88],
     "feet_world":{"l":[0.13,0.88],"r":[0.25,0.84]},
     "angles":{"head":0.0}},
    {"at":2.0,"position":[0.29,0.88],
     "feet_world":{"l":[0.27,0.88],"r":[0.25,0.88]},
     "interpolation":"smooth"},
    {"at":3.0,"position":[0.32,0.88],
     "feet_world":{"l":[0.29,0.88],"r":[0.34,0.88]},
     "hand_to":[0.42,0.67],"hand_weight":1},
    {"at":4.0,"position":[0.32,0.88],
     "feet_world":{"l":[0.29,0.88],"r":[0.34,0.88]},
     "hand_to":[0.42,0.67],"hand_weight":0}
  ]
}
```

Keyframe timestamps `at` are **relative to action start** and must strictly increase. The first must be zero and the last must equal `end-start`; this avoids uncontrolled extrapolation. `interpolation` is `smooth` (time-aware, bounded cubic Hermite), `linear` or `hold` (holds the preceding value until the next stamp). Cubic Hermite uses adjacent keyframes for tangents and clamps any overshoot to the segment endpoint interval; this keeps poses controlled.

Supported keyframe properties are:

| Key | Meaning |
|---|---|
| `position:[x,y]` | Character world position, normalized by frame width/height |
| `body_shift:[dx,dy]` | Additional subtle silhouette movement |
| `angles:{bone:radians}` | Individually authored joint angles, with generic IK suppressed on directly controlled limbs |
| `feet_world:{l:[x,y],r:[x,y]}` | **World-anchored** left/right foot landing positions, which can remain fixed while torso moves |
| `feet:{l:[dx,dy],r:[dx,dy]}` | Actor-relative foot offsets (world targets take precedence) |
| `hand_to:[x,y]` | Absolute directed right-hand target |
| `hand_weight:0..1` | Blend neutral / current gesture to the target |
| `gait:-1..1` | Optional procedural stepping envelope |
| `look:[x,y]` | World-space gaze target |
| `gaze_weight:0..1` | Amount of gaze-driven head response |
| `expression:neutral/happy/sad/surprised` | Switched artistic expression layer |

This is a deterministic path-based animation editor interface. It is not automatically extracted from film or speech.

## Actual art changes

The new `studio_art.py` edition builds 20 real transparent PNGs from the editable original artwork definitions, with a unified indigo/navy coat, warm skin tones, russet scarf and copper accessories. Alpha-masked watercolor washes, fiber/paper grain, etched hatching and edge contour shading are applied once at asset-generation time. Frame rendering simply transforms the final PNG layers. Artist-modified files are never overwritten by the generator. The scene still accepts external hand-painted PNGs using the existing `visual.type="sprites"` contract.

The new `sunset_cliff` environment is an original illustrated warm coastal location with atmospheric mountain ridges, orange/mauve gradient sky, sea highlights, village lights, lighthouse, cliff strata and nearby foliage. It is deterministic offline art; the water and sky have stable texture plus small seek-safe drifting pollen details. Use it via:

```json
{"environment":{"type":"sunset_cliff"},"style":"cinematic_storybook"}
```

The acceptance scene `examples/last_light_directed_v05.json` directs 26 distinct movement beats over 14 seconds. It includes an independent path for left and right foot planting, physical lantern pickup and placement on stone plinths, posture anticipation, raised gaze, mouth cue animation and a moving camera.

## Front-facing cutout anatomy — v0.5 optical IK

Front-view human knees bend into and out of the screen, not only sideways.
The original mathematically exact planar two-link solver therefore caused
X-shaped knees and exaggerated wing-like elbows when painting a character
facing camera. The new optional actor rig property:

```json
"rig": {
  "root_height": 0.365,
  "front_view": true,
  "bones": [ "... existing named bone definitions ..." ]
}
```

selects an optical 2.5-D *projected* knee/elbow layout for the sprite
character. The hand and foot endpoints remain locked to authored targets,
while elbow/knee midpoints are placed close to the correct limb centerlines.
The drawn segments are deliberately foreshortened, so their projected pixel
lengths are **not required to equal the actual authored bone length**. This
is a visible-illustration mode, not a physical IK solution. It allows natural
planted front-facing legs while preserving the original exact two-bone solver
for all rigs without `front_view`.

The scripted acceptance scene also uses a small `root_height` override and
a shorter pelvis connector, so the painted shirt visibly joins the hips, and
uses carved limestone pedestal layers rather than unlit rectangular boxes.
These changes are opt-in and leave all v0.1–v0.4 projects unchanged.

## Verification criteria and boundaries

`tests/test_studio_v05.py` exercises the real art kit and manifest, deterministic frame changes, interpolated trajectories and planted-foot holds, IK contact continuity, invalid keyframe validation and preservation of artist edits. GitHub Actions additionally renders an actual H.264 MP4, uses FFprobe and decoded frame QA, and stores all PNGs, film, stills and manifests on the branch.

The following are **not implemented**: automatic photographic character segmentation, photographic realism, weight-skinned mesh deformation, full hand/finger rigs, native illustration editor, phoneme recognition from audio, advanced cinematic global illumination, measured human art-quality scoring. These are separate future stages; no false production-readiness claim should be made solely from passing tests.

## Development policy

Only `feature/art-direction-v0.5` is modified. The version 0.4 code, v0.3, v0.2 and `main` remain unchanged. Keep the v0.5 PR in draft until a human sees the actual rendered video and accepts its artwork.
