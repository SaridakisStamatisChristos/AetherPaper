# AetherPaper

**Local-first, model-independent, JSON-driven 2D paper-cut animation.** The render engine works without calling Claude, Gemini, ChatGPT, any external API, or an AI coding agent. A scene document describes character movement, prop interaction, captions, camera motion and timing. AetherPaper renders actual frames into an MP4. The core is reusable across productions.

## Status: v0.1 foundation

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

**Not yet implemented:** integrated Kokoro generation, image segmentation, sophisticated inverse-kinematics, generic imported skeleton rigs, a browser UI, direct HyperFrames/Papermotion adapters, an asset-license registry, automated lip phoneme alignment, or production-grade audio mastering. The current mouth motion is timed, not viseme-synchronized. This is an engineering foundation, not a claim of feature parity with upstream projects.

## Install — Linux Mint / Ubuntu

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip ffmpeg

git clone https://github.com/SaridakisStamatisChristos/AetherPaper.git
cd AetherPaper
# While v0.1 is under review:
git checkout feature/json-animation-v0.1

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
