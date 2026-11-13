# Offline integration contracts — AetherPaper v0.2

## Design invariant

Scene authoring and deterministic rendering are different processes:

`Topic / script -> external story planner -> versioned scene JSON -> AetherPaper CLI -> H.264 MP4 -> optional AetherRendering postprocess`.

**AetherPaper never invokes an AI service during scene validation, snapshots or rendering.** No Claude Code/Gemini/LLM dependency is installed. A local or remote model may generate JSON before AetherPaper runs.

## AetherMotion

Pass a v0.2 JSON scene directly or import the renderer's mathematical primitives as Python libraries. The stable interchange format is scene JSON, not Papermotion's TypeScript internal objects. For advanced reusable puppets, use `rig`, named `bones` and `pose` angle maps.

## ClaudeCreate

ClaudeCreate may generate:

1. `version`, `canvas` and optional global `style`.
2. An ordered array of scenes, each with local `duration`, characters, props and layers.
3. Timed actions and camera beats.

Then call:

```bash
aetherpaper validate movie.json
aetherpaper manifest movie.json > production-manifest.json
aetherpaper render movie.json --width 1080 --height 1920 --fps 30 --out movie.mp4
aetherpaper qa movie.mp4 --frames-dir ./qa-frames > video-qa.json
```

This works offline after dependencies are installed. Height and width must be even; UI-safe title placements depend on the chosen output aspect ratio.

## AetherRendering / Kokoro

External Kokoro WAV clips are referenced by local file path under the JSON directory:

```json
{"type":"speak","target":"narrator","start":0.5,"end":4.5,
 "text":"Welcome to this tutorial.","audio":"assets/narrator-1.wav"}
```

AetherPaper places WAV clips on the timeline and muxes AAC; AetherRendering may later normalize loudness, refine captions and encode delivery formats. WAV **must already exist**, and AetherPaper doesn't time-stretch it or generate Kokoro speech itself. To generate a complete local sample without Kokoro, install `espeak-ng` and use `--voice espeak`.

## CLI contract

`aetherpaper validate PROJECT`: strict model validation; returns JSON metadata to stdout on success.

`aetherpaper manifest PROJECT`: JSON source/asset inventory with SHA-256 file checksums; errors on broken references.

`aetherpaper snapshot PROJECT --at SEC --out PNG`: render a frame at absolute project time.

`aetherpaper render PROJECT --out MP4 [--width W --height H --fps F --voice none|espeak]`: stream RGB frames into FFmpeg, mux optional local WAV/eSpeak, emit result metadata JSON.

`aetherpaper qa MP4 --frames-dir DIR`: ffprobe codec/duration/dimensions/fps and decode multiple real frames for pixel-variance QA.

Error conditions exit nonzero. Missing assets and invalid JSON fail before rendering; missing ffmpeg or eSpeak results in a useful error. No browser, Node.js, cloud account, authentication or model tokens are needed.

## Current constraints

This interface intentionally does not promise arbitrary imported characters, automatic visual segmentation, audio-to-phoneme alignment, perceptual art quality checks, exact cross-platform encoded-video byte equality, full deformable-body physics, or synchronized multi-character collisions. Those remain future work, not substitutes for the working JSON interpreter.
