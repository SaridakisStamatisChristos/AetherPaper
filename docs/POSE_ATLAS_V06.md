# AetherPaper v0.6 — Illustration-First Animation

**Branch:** feature/illustrated-assets-v0.6, based on verified v0.5. Main untouched.

## Goal and the artistic limitation

The old character looks archaic because it consists of geometrically drawn pieces. Version 0.6 offers a different renderer: **each character pose is a complete, independently illustrated transparent PNG**, preserving its painted anatomy, hair, fabric and facial appearance. The timeline switches illustrations and moves the complete person without rotating geometric arms and legs. A director can specify precise switching beats.

**The included demo uses legacy v0.5 artwork for automated regression, NOT a new professional illustration pack.** The image-generation attempts in this development turn produced promotional posters, not isolated transparent sprites. Do not treat a poster as imported character art. Good source art is still necessary before declaring the visual-quality objective complete.

The engine does not perform arbitrary AI segmentation, weight-skinned deformation or optical flow. It does not invent new in-between drawings. Supply enough artist-created frames for smooth movement.

## Ubuntu / Linux Mint setup

~~~bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip ffmpeg espeak-ng
git clone https://github.com/SaridakisStamatisChristos/AetherPaper.git
cd AetherPaper
git switch feature/illustrated-assets-v0.6
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
pytest -q
~~~

## Generate or commission the character art

Obtain an equal-cell sprite sheet with truly transparent PNG alpha. Each cell contains one entire character pose at a consistent scale, with boots on the same baseline, no backgrounds, logos, scene captions, grids or opaque poster frames.

Recommended pose inventory for a single consistent traveler: idle, two or more walk poses (ideally 4–8), approach, reach, grasp, carry, place, turn, speaking and smiling. The camera view and clothing should remain identical. Record the asset author/model, provenance and usage rights. Edit any AI-generated anatomical errors before import.

**Artist brief:** One coherent cinematic storybook character with auburn curls, indigo jacket, russet scarf, boots, expressive eyes, rich watercolor-paper materials, natural posture. Draw independent complete transparent full-body images for every pose, each with a consistent ground-contact anchor. No scene, decorations, typography, collage, posters or other people.

A complete high-quality pose atlas is **not** the same as a promotional image. This engine rejects opaque poster backgrounds rather than pretending it can automatically separate them.

## Importing an actual transparent PNG sheet

Save a layout file as, for example, traveler_layout.json:

~~~json
{
  "columns": 3, "rows": 2, "fps": 8, "height": 0.56,
  "foot_anchor": [0.5, 0.97], "default": "idle",
  "frames": [
    {"state": "walk", "cell": [0, 0], "hand_anchor": [0.72, 0.44]},
    {"state": "walk", "cell": [1, 0], "hand_anchor": [0.70, 0.46]},
    {"state": "idle", "cell": [2, 0], "hand_anchor": [0.68, 0.48]},
    {"state": "reach", "cell": [0, 1], "hand_anchor": [0.84, 0.56]},
    {"state": "carry", "cell": [1, 1], "hand_anchor": [0.77, 0.32]},
    {"state": "speak", "cell": [2, 1], "hand_anchor": [0.70, 0.48]}
  ]
}
~~~

~~~bash
aetherpaper posepack --sheet artwork/traveler.png \
  --layout artwork/traveler_layout.json \
  --out examples/assets/traveler/poses
~~~

The importer splits cells without changing their original canvas alignment, validates alpha transparency, dimensions, duplicate cells, poses and file safety, protects changed artist-created art from accidental replacement, and saves checksums in posepack.json. The JSON returned by the command includes a reusable visual configuration.

**Important:** Frame source paths returned by the importer are relative to its output folder. Prefix them relative to your final scene JSON location (for example, assets/traveler/poses/walk_000.png) when copying into a scene.

If your illustrations are already independent RGBA PNGs, refer to them directly; a sheet is optional.

## Using complete character frames

For an actor, replace the geometric rig with visual type "pose_atlas":

~~~json
{
  "id": "traveler", "x": 0.3, "y": 0.88, "scale": 1.0,
  "visual": {
    "type": "pose_atlas", "default": "idle", "height": 0.56,
    "fps": 8, "playback": "loop", "foot_anchor": [0.5, 0.97],
    "states": {
      "idle": [{"src":"assets/traveler/poses/idle_000.png"}],
      "walk": [
        {"src":"assets/traveler/poses/walk_000.png"},
        {"src":"assets/traveler/poses/walk_001.png"}
      ],
      "reach": [{"src":"assets/traveler/poses/reach_000.png"}],
      "carry": [{"src":"assets/traveler/poses/carry_000.png"}]
    }
  }
}
~~~

The character is anchored by the painted shoes. Body motion, stage lighting, camera movement and captions still come from the existing runtime. The renderer selects idle, walk, reach, carry or speak from actions, or honors explicit states in performance keyframes:

~~~json
{
  "type": "performance", "target": "traveler",
  "start": 0, "end": 3,
  "keyframes": [
    {"at":0, "position":[0.2,0.88], "sprite_state":"walk"},
    {"at":1.2, "position":[0.45,0.88], "sprite_state":"walk"},
    {"at":1.6, "position":[0.48,0.88], "sprite_state":"idle"},
    {"at":2.2, "position":[0.48,0.88], "sprite_state":"reach"},
    {"at":3, "position":[0.48,0.88], "sprite_state":"idle"}
  ]
}
~~~

Complete-pose frame selection is deterministic and can seek to any timestamp. Playback modes are "loop" and "once". If a frame includes an accurate "hand_anchor" for a visible painted hand, attached props use that same position. Missing hand anchors fail explicitly for contact-dependent actions instead of producing floating props.

## Testing the implementation

The self-contained demo deliberately uses the legacy v0.5 rendered character as a test source, not as the artistic endpoint. It constructs a six-cell transparent pose sheet from actual artwork, imports it, exercises performance state selection and renders an MP4:

~~~bash
aetherpaper pose-demo --source examples/last_light_directed_v05.json --out examples
aetherpaper validate examples/pose_atlas_demo_v06.json
aetherpaper manifest examples/pose_atlas_demo_v06.json
aetherpaper render examples/pose_atlas_demo_v06.json --out output/pose_atlas_demo_v06.mp4
aetherpaper qa output/pose_atlas_demo_v06.mp4 --frames-dir output/qa_v06
~~~

CI archives the six independent PNGs, transparent source sheet, 5-second film, sample frames and SHA-256 manifest.

**Artistic acceptance gate remains open:** To claim a meaningful visual upgrade over v0.5, the six legacy illustrations must be replaced with genuinely sophisticated consistent character drawings. The working pipeline alone does not make that quality claim true.
