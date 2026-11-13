# AetherPaper v0.3 — Visual Quality and Sprite Asset Guide

AetherPaper v0.3 is an opt-in visual overhaul on top of the offline JSON/FFmpeg engine. **Rendering does not invoke an AI service.** Version 0.1 and 0.2 projects remain supported.

## Two independent artwork approaches

### Built-in illustrated paper puppet

Set a character's `rig` and `visual`:

```json
{
  "id": "keeper", "x": 0.21, "y": 0.855, "scale": 1.05,
  "skin": "#E1B38E", "hair": "#303C45", "pants": "#435665",
  "rig": {"torso": 0.31, "neck": 0.12, "upper_arm": 0.20, "forearm": 0.21, "spring": 2.9},
  "visual": {"type": "illustrated", "coat": "#427486", "lining": "#CE9B61"}
}
```

The original, layered, vector-like character implementation has anatomical limb masses, sewn clothing, styled hair, facial expressions and timed mouth movement. It is drawn in the existing Pillow renderer with two-bone IK; it does not rely on external fonts, images, SVG converters or web access.

This is a **starter illustration aesthetic, not a claim of professional hand-drawn character art**. To reach a more sophisticated level, use artist-authored PNG sprite parts instead of the built-in puppet.

### Import your own layered transparent PNG artwork

Cut out each independent illustration as a separate transparent PNG and place the files beside or below the scene JSON. Each sprite is authored along the positive X direction (left to right), and its width is the default graphic representation of one bone length. The `pivot` coordinate identifies the start of the bone inside the image as a normalized fraction of its width and height.

Example, assuming `assets/coat.png` and `assets/head.png` exist:

```json
{
  "id": "actor", "x": 0.44, "y": 0.84, "scale": 1,
  "rig": {
    "bones": [
      {"name": "pelvis", "parent": null, "length": 0.05, "angle": -1.5707963268},
      {"name": "torso", "parent": "pelvis", "length": 0.30, "angle": 0},
      {"name": "neck", "parent": "torso", "length": 0.15, "angle": 0}
    ]
  },
  "visual": {
    "type": "sprites",
    "parts": [
      {"bone": "torso", "src": "assets/coat.png", "pivot": [0, 0.5], "scale": 1.1, "z": 0},
      {"bone": "neck", "src": "assets/head.png", "pivot": [0, 0.5], "scale": 1.3, "z": 1}
    ]
  }
}
```

`z` orders layers back-to-front. `scale` multiplies the graphic length relative to its supporting bone, without changing the skeleton. `pose` actions animate named bone angles in radians, with smooth entry/exit blending. A sprite cast remains coherent across arbitrary frame seek order because each layer's transform is re-evaluated from the scene time. Required bones: `pelvis`, `torso`, `neck`; up to 64 PNG parts can be attached to additional custom bones.

All PNG references must be local, inside the JSON project directory. The `manifest` command checks files and reports SHA-256 checksums; rendering fails preflight for missing images, path traversal and oversized assets. Current sprites are rigid illustrations, **not deformable weighted skinning**; shoulders and other joints should be hidden by overlap between separately illustrated parts.

For good results, have an illustrator prepare:
- A consistent portrait/three-quarter art style, one body-part image per articulated bone, with transparent padding around the overlap.
- A neutral facial expression/eyes and optional expression variants as independent assets, plus layered hair/clothing foreground pieces.
- Joint pivots at the painted seam; overlap sleeves across elbows and skirts across hip/upper-leg pivots.
- Lighting, ink weights, palette, pixel density and scale consistently across parts.

These are asset-authoring guidelines; AetherPaper does not yet automatically segment or weight-skin full-body illustrations.

## Cinematic JSON scene

`"version":"0.3"`, `"style":"cinematic_storybook"` and `"environment":{"type":"moonlit_atelier"}` select the new original built-in environment. It combines a nighttime arched window, bookshelves, detailed interior geometry, layered floor, atmospheric light shafts, paper grain, animated dust motes, a vignette and foreground branches.

`"title_card":{"text":"THE LANTERN KEEPER","start":0.1,"end":2.65}` overlays a cinematic title. A new `"shape":"lantern"` prop has a dynamic warm halo that follows the actual evaluated prop position, including while a character carries it.

For a pickup, the optional `hand_to` coordinate directs the right-arm IK reach toward the object and blends back to a relaxed carrying pose. `place` actions also steer the arm toward the drop-off destination:

```json
{"type":"pickup","target":"keeper","prop":"light",
 "start":3.0,"end":4.22,"hand_to":[0.585,0.648]}
```

This new behavior is opt-in; legacy pickup scenes without `hand_to` retain their v0.2 behavior.

## Render the acceptance scene on Linux Mint / Ubuntu

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip ffmpeg espeak-ng
git clone https://github.com/SaridakisStamatisChristos/AetherPaper.git
cd AetherPaper
git switch feature/visual-quality-v0.3
python3 -m venv .venv && source .venv/bin/activate
python -m pip install -e '.[dev]'
pytest -q

aetherpaper validate examples/lantern_keeper_v03.json
aetherpaper manifest examples/lantern_keeper_v03.json
aetherpaper render examples/lantern_keeper_v03.json --out output/lantern_keeper_v03.mp4
aetherpaper snapshot examples/lantern_keeper_v03.json --at 5.7 --out output/lantern_carry.png
aetherpaper qa output/lantern_keeper_v03.mp4 --frames-dir output/lantern_qa
```

The 10-second accepted JSON source is `examples/lantern_keeper_v03.json`; its default canvas is 960 × 540 at 24 fps. Its scene declares `supersample: 2`, meaning a frame is internally drawn at twice the requested size then downsampled with Lanczos filtering. Other scenes default to 1; values 1, 2, and 3 are accepted with a raster-memory bound. The CI preview is 640 × 360 at 24 fps, while sampled PNGs are rendered at 960 × 540. The animated story: a keeper enters a moonlit atelier, approaches a lantern, picks it up with articulated motion, carries it, places it down, and delivers a short captioned line.

### Current quality limits

Professional production quality still depends heavily on the original supplied character artwork. The programmatic illustrated character has a single front/three-quarter style, not pose-dependent silhouette replacement, animated perspective turns, complex hand rigging or weighted meshes. Cinematic background assets are currently one original `moonlit_atelier` set, not a catalog of full backgrounds. The importer is a reusable **rigid-part** sprite system, not automatic animation extraction from one flat image.

The ongoing acceptance gate is **actual rendered output and inspected frame sheets**; successful tests are necessary but do not, by themselves, prove artistic quality.
