# How image-to-real was built (what happened, in order)

Goal from the user: a website like the hyper-real, scroll-driven MotionSites templates, for the house in one reference photo (447 x 447 px, modern white villa with dark curved slabs, dusk).

## 1. Hand-modelled Blender scenes (failed three times)
- `modern-villa`: boxes, cylinders. Recognisable massing, looked like a toy.
- `modern-villa-realistic`: bevelled slabs, louvres, procedural materials, scattered palms. Better, still CG, and, when I laid a grid over the photo, **the layout was wrong**: I had invented a different house (the photo has a big rounded roof slab with a rail, a left balcony block, a recessed glass entry, and a louvred right wing).
- `modern-villa-v3`: borrowed the `reference-look-calibration` idea from a community Blender skill: **measure** the photo (sky RGB about 154/188/254, saturation 0.33, brightness 141) and tune the render to the numbers. My sky was grey (saturation 0.11); after calibration 0.25-0.28. First attempt came out flat pink because the gradient range sat above where the camera looks; measuring and viewing caught it. Mood improved, geometry realism did not.

Why they stayed fake: missing small details, uniform materials, empty surroundings, few lights, no camera character. Matching a photo exactly by modelling needs measured geometry and real textures.

## 2. The change of approach
Two options were offered: (1) rebuild from measurements, (2) project the photo onto proxy geometry. Chosen: do both at once, as **depth-based camera mapping**, because the pixels stay real.

## 3. Pipeline built
- Depth Anything V2 (small) depth map: house, slabs and palms separated cleanly.
- Depth to metres with `NEAR=9`, `FAR=140`, 60 degree field of view (assumptions).
- Mesh from pixels (numpy `foreach_set`, no per-vertex Python), UV = pixel position, emission texture, Standard view transform, 4 Cycles samples (about 3 s/frame at 1080 px).
- **Fit check**: original view vs photo: mean abs difference **8.7/255**. This is what proved the mapping right.

## 4. Problems met, with fixes
| Problem | Cause | Fix |
|---|---|---|
| Grey strip at top, slanted edge | Camera moved/rotated and saw past the photo's edge | Zoom crop 1.3x (later 1.45x), sky-coloured world, half-way aim, smaller move |
| Smear at left edge in first frames, palm warping | Triangles stretched across depth jumps | Accepted; keep path moderate; documented |
| Text hard to read over bright frames | Light sky behind white text | Darker scrim, text-shadow, text on a dark side panel |
| Hero blank on a phone (earlier page) | Frames and libraries loaded from files that did not resolve in the host; text invisible until JS ran | Inline frames + libraries in one file; first headline visible without JS |
| Video scrub snapped back to 0 (video test) | Python `http.server` lacks Range requests | Use a server with Range support |
| Image looked soft ("make it clearer") | 447 px source | Swin2SR x4 AI upscale; AI alone painted/etched palms, so 60/40 blend with bicubic; mesh 2x finer; frames at higher quality |
| Motion felt short | +-1 m slide, 2 m push, 60 frames, 450% scroll | +-1.6 m, 3.5 m push, zoom 1.45, 120 frames, 900% scroll (see SKILL.md) |

## 5. Numbers worth remembering
Depth 1 min, upscale 1.5 min, 6 s/frame at 1200 px (4 cores), page 7-10 MB inlined. Single-file hosting limit 16 MB.

## 6. What is not solved
Hidden sides, true metric scale, invented AI detail, depth-edge stretching on long moves, 447 px source.
