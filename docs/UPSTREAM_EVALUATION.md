# Upstream source evaluation and license boundary

Evaluated 13 November 2026. **No upstream code or assets are copied into AetherPaper v0.2**; its Python implementations of IK, skeletons, springs, materials, transforms and timeline evaluation were written independently, using common graphics/mathematical ideas. Refer to each source and its own license before future reuse.

| Project | Source inspected | Useful findings | Decision |
| --- | --- | --- | --- |
| [Papermotion](https://github.com/francozanardi/papermotion) | `src/core/math.ts`, `Spring.ts`, `src/rig/Bone.ts`, `Skeleton.ts`, `Gait.ts`; README and MIT license | Parent-child bone frames, analytic geometry for two-link IK, spring-follow motion, phase-driven gait, physics components | Translate the underlying concepts into new Python/Pillow primitives. Do **not** vendor a TypeScript/Chromium renderer into a local-first Python app. |
| [Papercut Explainer](https://github.com/0xS4N4TG/papercut-explainer) | `library/papercut/kit/paper/motion.ts`, `camera.tsx`, `transitions.tsx`; README and license | Declarative cameras, depth layers, reusable transitions, kinetic text, agent rendering QA | Use a simplified camera/transition contract in native Pillow. No mandatory React/Remotion installation, no imported backdrops, fonts, audio or third-party assets. |
| [Paper Collage Skill](https://github.com/rafiimanggala/paper-collage-skill) | `template/assets/lib/collage.js`, `template/scripts/build.py`; README, credits and license | Time-seekable collage motion, generated compositions, scrapbook paper aesthetics and deterministic seeded effects | Implement a lightweight native scrapbook preset. HyperFrames HTML/GSAP, supplied fonts and photo assets remain optional future adapters. |

All three repositories advertise MIT for their own code. **This does not automatically license external assets**: Papercut Explainer includes separate font/media source considerations; Paper Collage lists SIL OFL fonts, CC0 examples, and HyperFrames (Apache-2.0). No upstream media/font redistribution is performed in AetherPaper.

Integration later could use optional subprocess adapters, but the stable AetherPaper JSON CLI should remain engine-independent. Revalidate all source licenses and media at any future import date.
