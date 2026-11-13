# AetherPaper v0.1 — Architecture and next gates

## Invariant

An accepted scene JSON must render to the same logical motion frames without a model, a cloud call, a code-generation pass, a GUI, or a video-generation API. PNG outputs should be deterministic on a given renderer/Pillow/font environment; MP4 bytes may differ by FFmpeg build.

## Modules

- `model.py`: versioned JSON input contract, eager reference and timing validation.
- `timeline.py`: stateless character actions, prop attachment and camera beats.
- `paint.py`: reusable cutout visual primitives, rig-like puppet geometry, captions, optional local transparent PNG layers.
- `renderer.py`: frame streaming into FFmpeg; snapshot at arbitrary timeline timestamps.
- `audio.py`: offline optional eSpeak / external WAV scheduling and mux.
- `cli.py`: CLI boundary; no external API or hidden model selection.

## Phase roadmap

### v0.1 (current): JSON-first rendering

A built-in puppet walks, picks up a paper object and speaks. CI requires passing tests, real H.264 output, and a probe of stream dimensions. Renderer is intentionally small and local-first.

### v0.2: Articulated/physics engine

Evaluate importing Papermotion MIT motion/IK primitives and/or a separately maintained adapter. Match visual semantics across renderer implementations; preserve JSON contracts. Add deterministic gait rigs, real arm reaching/IK, multi-actor interactions and animation-state tests. Do **not** claim current puppet motion is a Papermotion port.

### v0.3: Style plugins

Build a HyperFrames Paper Collage adapter and Remotion Papercut templates behind the same JSON contract; respect version and third-party licenses. Neither should be a mandatory dependency for v0.1 installations.

### v0.4: Better production workflows

Kokoro via AetherRendering, speaker-wise phoneme timing, audio ducking/mixing, improved vertical presets (1080×1920), caption safe areas, asset segmentation/rigging, render reproducibility manifest, asset-attribution registry and batch rendering.

## Constraints

- This first version is not a movie production suite. No imported arbitrary characters or automatic image segmentation.
- Character gestures are vector-style primitives, not photoreal animation.
- Animations interpolate deterministically; output is not the same as AI video generation.
- `espeak` is optional and low-quality but proves local, correctly timed narration. Production voice should use imported pre-generated Kokoro WAV clips.
- Input JSON must come from a trusted or reviewed source for now: schema validation constrains values but v0.1 does not implement CPU/memory/time quotas against maliciously large asset files.
- Imported local images and audio are restricted to paths below the scene directory, but are not sandboxed against symlink swaps made during rendering.

## Definition of done for v0.1

1. JSON validation rejects invalid references/timing.
2. Two source-independent renders of the same frame are pixel identical locally.
3. Walking changes position, pickup attaches prop, speech animates mouth and captions.
4. Multi-scene rendering is supported.
5. Rendered MP4 is H.264 and can be decoded by ffprobe/ffmpeg.
6. Linux CI installs from clean source, tests, renders and probes a real video.
7. Feature branch can be reviewed before promotion into `main`.
