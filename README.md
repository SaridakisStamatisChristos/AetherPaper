# AetherPaper

**Local-first, model-independent, JSON-driven 2D paper-cut animation.** The render engine works without calling Claude, Gemini, ChatGPT, any external API, or an AI coding agent. A scene document describes character movement, prop interaction, captions, camera motion and timing. AetherPaper renders actual frames into an MP4. The core is reusable across productions.

## v0.6 — illustration-first full-pose character animation

**Feature branch:** `feature/illustrated-assets-v0.6` (stacked on v0.5; main unchanged).

**Why:** Earlier characters looked like polygon puppets. v0.6 can animate **whole artist-painted PNG character poses** instead of reconstructing faces, hair and limbs out of rotated cutouts. It supports imported transparent pose sheets, strict asset validation, director-controlled idle/walk/reach/carry/speak switching and precise painted-hand contact markers.

```bash
sudo apt update && sudo apt install -y git python3 python3-venv python3-pip ffmpeg espeak-ng
git clone https://github.com/SaridakisStamatisChristos/AetherPaper.git
cd AetherPaper
git switch feature/illustrated-assets-v0.6
python3 -m venv .venv && source .venv/bin/activate
python -m pip install -e '.[dev]'
pytest -q

# Verified pipeline demo using preserved v0.5 artwork, NOT premium painted art:
aetherpaper pose-demo --source examples/last_light_directed_v05.json --out examples
aetherpaper manifest examples/pose_atlas_demo_v06.json
aetherpaper render examples/pose_atlas_demo_v06.json --out output/pose_atlas_demo_v06.mp4
aetherpaper qa output/pose_atlas_demo_v06.mp4 --frames-dir output/qa_v06

# Import a REAL transparent artist/AI-created pose sheet instead:
aetherpaper posepack --sheet artwork/poses.png --layout artwork/layout.json --out examples/assets/poses
```

See [v0.6 Pose Atlas guide](docs/POSE_ATLAS_V06.md) for the complete JSON interface, production asset authoring brief, rigless character specification, importer safety rules and limitations.

**Real v0.6 illustrated character now verified:** A third image-generation attempt produced a genuine transparent **1536×1024 PNG sprite sheet** with six consistent, fully illustrated body poses. The source, all six split RGBA frames, and a **five-second H.264 acceptance film (640×360, 12 fps, 60 frames)** are preserved in [examples/assets/ai_courier](examples/assets/ai_courier/) and [samples/v0.6/ai](samples/v0.6/ai/). The first two generation attempts produced unusable marketing posters; those were not imported.

To render the actual new art (already bundled on this feature branch):

```bash
aetherpaper validate examples/ai_illustrated_courier_v06.json
aetherpaper manifest examples/ai_illustrated_courier_v06.json
aetherpaper render examples/ai_illustrated_courier_v06.json --out output/v06_ai_illustrated_movie.mp4
aetherpaper qa output/v06_ai_illustrated_movie.mp4 --frames-dir output/ai_qa
```

**Quality boundary:** The character is a substantial visual improvement over the geometry-based v0.5 puppet, but six poses alone cannot deliver fully fluid acting; the original scene backgrounds remain relatively simple. Both independent code verification and human review of the actual film are still required.

---

## v0.5 — director-controlled storybook performance

**Feature branch:** `feature/art-direction-v0.5` (stacked on v0.4). This release focuses on improving visual direction, not simply increasing the number of rendered frames.

- **20 independent original studio PNGs:** unified indigo/russet art direction, textured paper and watercolor treatment, shaded cut-paper borders, expression and lip variants. Artists can replace these with their own painted parts.
- **Directed choreography:** time-aware keyframes for body blocking, head angles, gaze, animated hand targets and separately **world-planted left/right feet**. Keyframes support smooth/linear/hold interpolation and deterministic random seeking.
- **A second handcrafted environment:** sunset cliff with mountains, sea, lighthouse, village, foreground foliage and atmospheric depth.
- **14-second acceptance film:** a courier walks into the sunset, approaches a lantern, anticipates the reach, picks it up, carries and places it, then looks to the lighthouse and speaks.
- No web, AI model or API cost during artkit creation or MP4 rendering. Existing v0.1–0.4 projects remain supported.

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip ffmpeg espeak-ng
git clone https://github.com/SaridakisStamatisChristos/AetherPaper.git
cd AetherPaper
git switch feature/art-direction-v0.5
python3 -m venv .venv && source .venv/bin/activate
python -m pip install -e '.[dev]'
pytest -q
aetherpaper artkit --edition studio --out examples/assets/studio_courier
aetherpaper validate examples/last_light_directed_v05.json
aetherpaper render examples/last_light_directed_v05.json --out output/last_light_directed_v05.mp4
aetherpaper qa output/last_light_directed_v05.mp4 --frames-dir output/studio_qa
```

For the full performance keyframe API, asset authoring and limitations, see [v0.5 Art Direction Guide](docs/ART_DIRECTION_V05.md). **The included imagery is original, procedural illustration with richer artistic treatment; it should not be described as professional studio character art until independently reviewed.**

---

## v0.4 — 20-piece original artkit and fully tracked character motion

**Feature branch:** feature/character-art-v0.4 (stacked on v0.3; main unchanged).

v0.4 adds a reproducible, independently painted 20-PNG character kit, 14 skeletal bones with actual shoulder/hip offsets, two-link IK for four limbs, hair/cape sway, interchangeable facial expression and mouth art, and a physically connected sprite hand for pickup/carry/place. Artists can replace any generated part with better transparent artwork without altering the scene JSON.

Ubuntu / Linux Mint:

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip ffmpeg espeak-ng
git clone https://github.com/SaridakisStamatisChristos/AetherPaper.git
cd AetherPaper
git switch feature/character-art-v0.4
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
pytest -q
aetherpaper artkit --out examples/assets/atelier_courier
aetherpaper manifest examples/last_light_v04.json
aetherpaper render examples/last_light_v04.json --out output/last_light_v04.mp4
aetherpaper qa output/last_light_v04.mp4 --frames-dir output/qa_v04
```

The accompanying 11-second film is built from **real independent transparent PNG artwork**, not a screenshot or single still frame. Its default canvas is 960×540 at 24fps with a 2× antialiasing supersample.

See [Character Art v0.4 — complete workflow](docs/CHARACTER_ART_V04.md) for sprite authoring, facial/mouth states, anatomical IK and asset replacement.

**Quality boundary:** The included art is source-generated cutout illustration, not studio-grade hand-painted animation. The system now enables high-quality artist-authored replacement art, but supplied artwork and art direction still determine output quality.

---
## v0.3 — illustrated characters and cinematic acceptance film

**Status:** Working development feature branch. AetherPaper now supports an original illustrated character painter, interchangeable artist-authored transparent PNG parts on hierarchical bones, a detailed moonlit atelier scene, moving lantern illumination, foreground depth, improved reaching animation, and optional 2×/3× anti-aliasing. It preserves the same offline JSON → Pillow → FFmpeg runtime and the older v0.1/v0.2 scenes.

To work with the visual-quality branch instead of v0.2:

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip ffmpeg espeak-ng
git clone https://github.com/SaridakisStamatisChristos/AetherPaper.git
cd AetherPaper
git switch feature/visual-quality-v0.3
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
pytest -q
aetherpaper validate examples/lantern_keeper_v03.json
aetherpaper render examples/lantern_keeper_v03.json --out output/lantern_keeper_v03.mp4
aetherpaper qa output/lantern_keeper_v03.mp4 --frames-dir output/qa
```

The supplied acceptance video is 10 seconds, 960×540 at 24 fps by default. The CI preview uses 640×360 at 24 fps. It depicts a keeper walking into a moonlit study, picking up and carrying a lantern, placing it elsewhere, and speaking. `supersample: 2` produces internally double-resolution character/stage artwork before downscaling. No API tokens or browser runtime are needed.

**For genuinely sophisticated character art**, use `visual.type="sprites"` with separately authored transparent PNG parts, attached to named rig bones. This gives you an actual interchangeable illustration pipeline instead of requiring procedurally drawn geometric puppets.

Read [v0.3 Visual Quality and Sprite Asset Guide](docs/VISUAL_QUALITY_V03.md) for the complete JSON interface, pivot coordinates, artist workflow, examples and limitations. The new built-in puppet is more detailed than the v0.2 one, but its appearance still does **not** guarantee artist-grade animation; deliberate art assets remain essential.

---

## v0.2 — preserved animation baseline (feature branch)

AetherPaper v0.2 retains every v0.1 scene while adding reusable articulated 2D rigs and prop physics. A model may write **JSON only**; the locally installed Python/Pillow engine renders frames itself, uses FFmpeg for MP4, and can synchronize pre-generated narration WAVs. It does not invoke an AI model during rendering.

### Ubuntu / Linux Mint — complete installation

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip ffmpeg
sudo apt install -y espeak-ng  # optional, for narration without external WAVs

git clone https://github.com/SaridakisStamatisChristos/AetherPaper.git
cd AetherPaper
git switch feature/advanced-animation-v0.2

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'

aetherpaper validate examples/rig_demo.json
python -m pytest -q
```

Python 3.10+, Pillow and FFmpeg are required. Node, browsers, Remotion, HyperFrames, cloud accounts and AI subscriptions are **not** required. The GitHub CI target is Ubuntu; Linux Mint is designed to work with equivalent `apt` packages, but has not been manually tested on every Mint version.

### Render five actual example films

```bash
mkdir -p output
aetherpaper render examples/rig_demo.json --out output/rig_demo.mp4
aetherpaper render examples/interaction_demo.json --out output/interaction_demo.mp4
aetherpaper render examples/physics_demo.json --out output/physics_demo.mp4
aetherpaper render examples/visual_demo.json --out output/visual_demo.mp4
aetherpaper render examples/explainer_demo.json --voice espeak --out output/explainer_demo.mp4
```

For a fast 320x180 preview, add `--width 320 --height 180 --fps 12`. For a vertical social reel add `--width 1080 --height 1920 --fps 30`. Even dimensions are required.

The demonstrations cover character IK, gestures, custom skeletal poses, walking/running and timed mouths; entering, lifting, carrying, placing and releasing objects; grounded gravity, spring and rope motion; three paper presets, camera tracking/parallax and transitions; and a **24-second narrated** four-scene animated explainer.

CI-generated MP4s and representative PNG frames are attached to [successful GitHub Actions runs](https://github.com/SaridakisStamatisChristos/AetherPaper/actions). A separate publishing gate preserves canonical samples under `samples/v0.2/` when that workflow completes.

### Preview, manifest and QA

```bash
aetherpaper snapshot examples/rig_demo.json --at 3.5 --out output/frame.png
aetherpaper manifest examples/explainer_demo.json > output/production-manifest.json
aetherpaper qa output/explainer_demo.mp4 --frames-dir output/qa > output/qa.json
```

`manifest` validates local image/WAV references and reports SHA-256 hashes. `qa` probes actual H.264 streams and decodes representative frames; it is not a substitute for artistic review. `validate` rejects unsupported JSON versions, bad timing, missing character/prop links, invalid joint parameters and unsafe coordinates.

### Connect Kokoro, ClaudeCreate, AetherMotion or AetherRendering

The authoring system emits a versioned JSON scene file. AetherPaper executes it offline. For speech, attach a pre-generated local Kokoro WAV to a `speak` action:

```json
{"type":"speak","target":"narrator","start":0.5,"end":4.5,
 "text":"Welcome.","audio":"assets/line.wav"}
```

WAV is referenced relative to the JSON directory. AetherPaper aligns each clip to its action's start and muxes AAC, but does not run Kokoro itself or automatically align visemes. Use `--voice espeak` only when a basic local synthesis demo is sufficient.

### v0.2 references

- [Versioned JSON schema and all actions](docs/SCHEMA_V02.md)
- [Cross-project CLI and audio integration contracts](docs/INTEGRATIONS.md)
- [Actual source/architecture evaluation and licensing notes](docs/UPSTREAM_EVALUATION.md)
- [Implementation and verification ledger](docs/PROGRESS_V02.md)

**Scope:** configurable humanoid bone hierarchies, two-bone IK, deterministic object attachment/grounded falls, layered visuals, camera tracking and three looks are implemented. Full general-purpose soft-body physics, arbitrary imported puppet skinning, automatic lipsync, advanced collision response and production-grade art direction are **not** claimed. Review before merging.

---

## v0.1 foundation — historical notes (retained for compatibility)

Implemented and testable:

- Versioned, validated JSON animation projects and a CLI (`validate`, `snapshot`, `render`).
- Procedural hand-cut paper look with stable, seeded textures and shadows.
- Scene layers: room, rectangle, ellipse, polygon, text, transparent PNG image.
- Reusable articulated human character with arms/legs, walking, waving, reaching, holding and rhythmic speaking mouth.
- Interaction events: `walk`, `pickup`, `speak`, `wave`; reusable paper objects: book, box, ball, star, cup.
- Camera push/zoom, multi-scene timelines, captions fixed to the screen.
- Frame-indexed deterministic animation, offline H.264 MP4 video using FFmpeg.
- Optional offline eSpeak narration or external pre-generated WAV voice lines (for example, from Kokoro).
- Tests + an Ubuntu GitHub Actions build that renders and probes a real MP4.

**Legacy limitations:** v0.1 had no inverse kinematics or configurable rigs; v0.2 adds these. Still missing: integrated Kokoro generation, image segmentation, arbitrary skinned puppet imports, browser UI, direct HyperFrames/Papermotion adapters, asset-license registry, automatic phoneme recognition, and production-grade audio mastering. The current mouth motion is timed, not viseme-synchronized. This is an engineering foundation, not a claim of feature parity with upstream projects.

## Install — Linux Mint / Ubuntu

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip ffmpeg

git clone https://github.com/SaridakisStamatisChristos/AetherPaper.git
cd AetherPaper
# While v0.1 is under review:
git checkout feature/advanced-animation-v0.2

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'

# Optional speech engine (else silent MP4 with animated mouth and captions)
sudo apt install -y espeak
```

Use Python **3.10 or newer**. Linux is the primary tested target; Windows/macOS may work with Python and FFmpeg but have not yet been verified.

## Try a genuine animation

```bash
# Verify input contract before rendering
aetherpaper validate examples/room_pickup.json

# Snapshots can be used to inspect character pose at specific timestamps
aetherpaper snapshot examples/room_pickup.json --at 1.5 --out output/walk.png
aetherpaper snapshot examples/room_pickup.json --at 3.9 --out output/pickup.png
aetherpaper snapshot examples/room_pickup.json --at 5.5 --out output/speaking.png

# A complete 7.5-second MP4 (default 960x540, 24fps)
aetherpaper render examples/room_pickup.json --out output/room_pickup.mp4

# Same video, local basic speech audio (requires eSpeak)
aetherpaper render examples/room_pickup.json --voice espeak --out output/room_pickup_voice.mp4

# Smaller, faster preview
aetherpaper render examples/room_pickup.json --width 480 --height 270 --fps 12 --out output/preview.mp4

# Three different scenes, with a walking puppet and interaction
aetherpaper render examples/three_scenes.json --out output/three_scenes.mp4
```

The first example shows one character **walking into a room, picking up a book and speaking**. No animation code is generated to render it. Its movement is entirely described in JSON. With no `--voice`, speech is visible through a mouth animation and caption but has **no voice audio**; choose eSpeak or supply WAV files to hear speech.

## JSON scene contract

- Coordinates are normalized to the image width and height (0 to 1 is the normal viewport). Character `x,y` represent **feet position**. Prop `x,y` represent **center**.
- `duration` must be a multiple of `1/fps`. Times within each scene are relative to that scene.
- `walk` animates a target to `to: [x, y]`. `pickup` names an existing `prop`. `speak` shows captions and drives mouth movement; `wave` animates an arm.
- Repeated actions in the same scene compose in the order supplied; actions and camera shots can overlap. For basic v0.1 usage, have one pickup per character and avoid simultaneous walks.
- `camera` supports `zoom_from`, `zoom_to` (1–2.5), optional `center_from`, `center_to` (normalized).
- `speak` action may include `"audio": "assets/line.wav"` (path relative to the JSON directory); that WAV will be muxed at the action's starting timestamp. It is not automatically time-stretched; create voice clips whose duration matches the associated speech interval.
- Transparent PNG image layers support source files located below the JSON document's directory.
- No remote URLs, prompts, or executable code can appear in a scene as assets. Invalid references and unsupported shapes fail validation or rendering.

Example:

```json
{
  "version": "0.1",
  "canvas": {"width": 960, "height": 540, "fps": 24},
  "scenes": [{
    "id": "test", "duration": 6,
    "background": "#F2DABC",
    "layers": [{"type": "room"}],
    "characters": [{"id": "sam", "x": 0.3, "y": 0.8}],
    "props": [{"id": "item", "shape": "book", "x": 0.7, "y": 0.62}],
    "actions": [
      {"type": "walk", "target": "sam", "start": 0.2, "end": 2.0, "to": [0.55, 0.8]},
      {"type": "pickup", "target": "sam", "start": 2.1, "end": 3.6, "prop": "item"},
      {"type": "speak", "target": "sam", "start": 3.7, "end": 5.9, "text": "Hello from AetherPaper!"}
    ]
  }]
}
```

For complete examples see `examples/*.json`. For architecture, development limitations, and future integrations see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Automated tests

```bash
python -m pytest -q
# Check output with ffprobe
ffprobe -hide_banner output/room_pickup.mp4
```

Tests check invalid schemas, duplicate references, deterministic frames, actual motion, actor interaction, real MP4 encoding, stream dimensions and image path traversal.

## Integration boundary

**ClaudeCreate or Gemini** produces JSON only → **AetherPaper** validates and animates it offline → **AetherRendering** can replace/upgrade local eSpeak audio with Kokoro WAV tracks and process delivery formats. This avoids generating animation source code for every production. The visual systems of Papermotion, Paper Collage Skill and Papercut Explainer remain **inspiration for future adapters**, not bundled or represented as imported code in v0.1.

## License and attribution

AetherPaper v0.1 is original MIT-licensed code and **does not copy or bundle** source/assets from the three reference repositories. Their licenses and dependencies will be reviewed individually before any future reuse. Pillow and FFmpeg have their own license terms.
