---
name: image-to-real
description: Turn a single photo (a house, a room, a product, a street, a landscape) into a realistic, explorable 3D camera move and a scroll-driven website, by estimating depth with AI, rebuilding the photo as a 2.5D scene in Blender, and rendering a slow parallax fly-through. Use whenever the user wants a photo to "look real in 3D", asks to "reverse engineer this picture", "recreate this image in Blender", "make it move", "make a scroll animation from this image", or says hand-modelled Blender scenes look fake and they want it to look like the reference photo. Make sure to use it for any "make this image feel real / 3D / cinematic" request, even if they do not name the technique.
---

# Image to real

Hand-modelling a scene from one photo never looks like the photo (flat materials, empty surroundings, too few details). This skill does the opposite: **keep the photo's own pixels** and give them depth, so the realism is already there and only the camera moves.

Read `HOW-IT-WAS-BUILT.md` for the story, numbers and mistakes behind these rules.

## Pipeline (run inside a work folder holding `ref.jpg`)

```bash
pip install bpy torch transformers pillow numpy opencv-python-headless   # CPU torch is fine
S=/path/to/skills/image-to-real/scripts
python3 $S/depth.py                 # -> depth_raw.npy  (Depth Anything V2 small; ~1 min)
python3 $S/upscale.py               # -> ref_sr4.png    (Swin2SR x4, tiled; ~1.5 min for 447px)
python3 $S/blend.py                 # -> ref_blend.png  (60% AI + 40% bicubic)
mkdir png && python3 $S/build_photo_scene.py png 1     # FIT CHECK: exact original view
python3 $S/build_photo_scene.py png 120                # the camera move (6 s/frame at 1200px, 4 CPU cores)
```
Then convert frames (`ffmpeg -i f_%04d.png -c:v libwebp -quality 85 f_%04d.webp`), drop them in the page template and publish. `scripts/make_artifact.py` inlines frames + libraries into one HTML file for hosts that need a single file (keep it under 16 MB: ~1000-1200 px, quality 80-88).

## How it works
1. **Depth**: the AI model gives relative depth per pixel (bright = near). Convert to metres with assumed near/far (`NEAR=9`, `FAR=140`) and an assumed 60 degree field of view. The photo has no metadata, so these are guesses; wrong values only warp perspective a little.
2. **Sharpen**: an AI upscaler removes JPEG blocking and gives crisp edges. Blend it 60/40 with a plain resize, because AI alone looks painted and etches foliage.
3. **Rebuild**: every pixel (on a 2x finer grid) becomes a mesh vertex pushed to its depth. The photo is the texture, drawn as unlit **emission** with **Standard** colour management so the colours are exactly the photo's.
4. **Fit check (always do this first)**: render the original view and compare with the photo. Mean absolute difference should be about 5-12 out of 255 (resampling softness). Much higher means the mapping is wrong. Compare against the centre crop when `ZOOM` is above 1.
5. **Move the camera** and render.

## Motion rules (the move must not be short)
A short, timid move feels like a gimmick; the realism needs time to sink in. Defaults that held up:
- **Camera path**: slide sideways +-1.6 m (3.2 m total) and dolly forward 3.5 m, with smooth ease in and out (`PB_LATERAL`, `PB_PUSH`). Anything under +-1 m sideways or 2 m forward reads as a wobble.
- **Frames**: at least 120 (5 s at 24 fps); 60 frames is the floor, not the target. More frames beat bigger frames for smoothness.
- **Scroll length**: pin the hero for **800-900% of the viewport height** (about 9 screens), not 450%. Spread 4+ text beats along it. Short scroll distance makes the frames fly past.
- **Margin**: `PB_ZOOM=1.45` keeps photo around the frame so the move never shows the image edge. Raise it before you lengthen the move; never let a grey or empty strip show.
- **Check the extremes** (first, middle, last frame) before rendering all frames. Smearing at the first and last frames is the signal that the path is too long for this photo; shorten the end that smears or hold the first/last frames longer.
- **Aim**: point the camera half-way between straight ahead and the subject, not fully at it, or the frame tilts.

## Page recipe
Square picture on the right, feathered into a dark panel on the left (mask gradient), text left; on phones the picture on top and text over its lower part. Frame sequence on a `<canvas>` driven by GSAP ScrollTrigger + Lenis (`assets/page-template.html`). The first headline must be visible with scripts off; add `prefers-reduced-motion` and no-JS fallbacks; text-shadow plus a scrim for legibility over bright frames. If the page is hosted as a single file, test it from the single file, not only from the folder.

## Be honest in the result
- It is the photo with depth, not a modelled object. Only the visible side exists; a big turn would show missing sides.
- The AI upscaler **invents small details** (glass patterns, edge shapes). Say so.
- Depth jumps (palm fronds, railings, roof edges) stretch and warp when the camera moves; mention it.
- A small source image caps sharpness. Ask for the original or a bigger version before promising "clear".
- Use only photos the user has the right to use.

## Ideas not built yet
Inpaint the revealed background behind depth edges (would allow longer moves); merge several photos of one place; hand-clean depth for hero objects; real PBR textures for a truly modelled version.

Related: `hyperreal-scroll-sites` (page techniques and video scrubbing), `photoreal-3d-pipeline:*` (when a fully modelled scene is required).
