# AetherPaper JSON contract — v0.2

AetherPaper's Python renderer accepts `"version":"0.1"` (backwards-compatible) and `"version":"0.2"`. All coordinates are normalized scene coordinates. Character `x,y` means feet position; prop `x,y` means center. Times are scene-local seconds and durations must contain a whole number of project frames. Assets are **local**; no URL or cloud call is needed at render time.

## Example

```json
{
  "version": "0.2",
  "style": "paper_cut",
  "canvas": {"width": 960, "height": 540, "fps": 24},
  "scenes": [
    {
      "id": "room",
      "duration": 6,
      "style": "storybook",
      "transition": {"type": "fade", "duration": 0.4},
      "background": "#E9DAC3",
      "layers": [{"type": "room"}],
      "characters": [
        {
          "id": "alex", "x": 0.2, "y": 0.79,
          "rig": {"torso": 0.30, "head": 0.17, "spring": 3.0}
        }
      ],
      "props": [{"id": "book", "shape": "book", "x": 0.6, "y": 0.63}],
      "actions": [
        {"type": "walk", "target": "alex", "start": 0.2, "end": 1.6, "to": [0.45, 0.79]},
        {"type": "pickup", "target": "alex", "start": 1.8, "end": 2.7, "prop": "book"},
        {"type": "place", "target": "alex", "start": 3.3, "end": 4.2, "prop": "book", "to": [0.8, 0.63]},
        {"type": "speak", "target": "alex", "start": 4.3, "end": 5.9, "text": "Hello from AetherPaper"}
      ],
      "camera": [{"start": 0, "end": 6, "zoom_from": 1, "zoom_to": 1.1}]
    }
  ]
}
```

## Actions

Each action requires `type`, a valid character `target`, and `start,end` where `0 <= start < end <= scene.duration`. Currently supported:

| Type | Fields | Effect |
| --- | --- | --- |
| `walk`, `run` | `to:[x,y]` | Root motion with procedural leg gait; root stays at destination |
| `wave` | none | Blend an arm wave on/off |
| `gesture` | `name: wave\|point\|raise` | Blended arm gesture |
| `look` | `to:[x,y]` | Head/gaze target |
| `expression` | `state: neutral\|happy\|sad\|surprised` | Facial expression |
| `pose` | `angles:{bone: radians}` | Ease named skeleton bone angles |
| `pickup` | `prop: id` | Reach, attach and follow actor hand |
| `place` | `prop: id, to:[x,y]` | Carry object to new position then detach |
| `release` | `prop: id`, optional `gravity, ground, bounce, velocity_x` | Damped ballistic fall and ground collisions |
| `spring` | `prop: id,to:[x,y]`, optional `frequency,damping` | Analytic spring translation |
| `speak` | `text`, optional `audio`, `mouth_cues` | Captions, mouth movement and scheduled WAV audio |

A `place` or `release` must follow a `pickup` by the same actor. `spring` targets a free prop and may be supplied an arbitrary valid scene actor as `target` under the current unified action schema. Prefer chronological actions and avoid overlapping incompatible actions on the same object.

`mouth_cues` is an ordered array of `{"at": relative_seconds, "openness":0..1}`. Interpolates between cues inside the speech interval. It does **not** extract phonemes from WAV automatically. When cues are absent, the mouth uses the original rhythmic approximation.

## Rigs

Add `"rig": {}` to an actor to opt into articulated painting. Omitting `rig` keeps the compatible v0.1 puppet. Built-in dimensions (in fractions of puppet scale): `torso, neck, upper_arm, forearm, thigh, shin, head`; `spring` controls analytic head-follow behaviour.

Optional custom hierarchy (topologically sorted parent before child):

```json
"rig": {
  "bones": [
    {"name":"pelvis","parent":null,"length":0.05,"angle":-1.5707963268},
    {"name":"torso","parent":"pelvis","length":0.3,"angle":0},
    {"name":"neck","parent":"torso","length":0.12,"angle":0},
    {"name":"scarf","parent":"torso","length":0.13,"angle":0.38,"at":0.7}
  ]
}
```

The renderer requires `pelvis`, `torso`, `neck` to anchor its standard character proportions; additional bones render as segments and respond to `pose` actions. General arbitrary-puppet art, spritesheet imports and bone skinning remain future work.

## Layers and looks

Layer types: `room, rectangle, ellipse, polygon, text, image, rope`. Image `src` must be a local, readable path beneath the project JSON directory. `rope` uses `from,to` normalized points and optional `sag,wind`. Per-layer `depth` (0 far/1 near), `outline` (`#RRGGBB`), and `edge_width` customize appearance.

Presets: `paper_cut`, `scrapbook`, `storybook`. Set globally via project `style` or override per scene. Optional scene `transition` uses `{"type":"fade"|"wipe","duration":seconds}`. Camera actions support `zoom_from,to` (1..2.5), `center_from,to` and `track:"actor-id"`.

Rendering is seek-safe and stateless. Scene-local events are evaluated at time `t` without requiring a sequential frame pass. These are deterministic within the same renderer/Pillow/font environment; pixel-identical results across different font/Pillow versions are **not** guaranteed.

## Audio

An action `speak` may contain `"audio":"assets/line.wav"` (e.g., Kokoro-exported WAV). AetherPaper inserts it at the speech action's start and muxes AAC. Alternatively, use `--voice espeak` for basic offline generated narration. Neither approach makes external model/API calls at render time. No automatic resampling of speech duration to match the scene is performed.

## Validation

```bash
aetherpaper validate examples/rig_demo.json
aetherpaper manifest examples/explainer_demo.json
aetherpaper render examples/explainer_demo.json --voice espeak --out output/explainer.mp4
aetherpaper qa output/explainer.mp4 --frames-dir output/qa
```

Asset preflight rejects missing files, path traversal, oversized image data, unsupported audio extensions, and remote URI-style asset references. Treat externally sourced JSON and image files as untrusted until reviewed: this is a constrained local renderer, **not** an operating-system sandbox.
