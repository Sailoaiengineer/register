---
name: hyperreal-scroll-sites
description: Build hyper-realistic, scroll-driven 3D/cinematic websites in the style of MotionSites showcase pages (scroll-scrubbed AI video, frame sequences, particle/point-cloud 3D, camera-path GLB scenes). Use whenever the user wants a "hyperrealistic", "cinematic", "Apple-style", "scrollytelling" or "3D scroll" site, wants to copy a motionsites.ai look, or wants a hero that animates as the page scrolls, even if they don't name a technique.
---

# Hyperreal scroll-driven sites

Provenance: derived from public observation of motionsites.ai previews and standard web techniques. It does NOT contain MotionSites' paid prompt text. For their exact prompts the user needs a MotionSites plan (https://motionsites.ai/unlimited).

## The core insight
The "3D" in most of these sites is not live 3D. It is **pre-rendered photoreal footage whose playhead is bound to scroll**. Realism comes from the offline asset (AI video / Blender render); the page only scrubs it. Only pick live WebGL when the user needs interaction (drag, cursor reaction, real camera moves).

## Pick a technique
| Look | Technique | Cost |
|---|---|---|
| Aerial/product footage that advances as you scroll (e.g. train hero) | A. Frame sequence on `<canvas>` | cheap, most realistic |
| Photoreal object rotating/exploding | A with Blender/AI turntable frames | cheap |
| Glowing point-cloud head/object reacting to cursor | B. Three.js Points + shader | medium |
| Real model, camera flies through scene | C. GLB + three.js/R3F camera path | heavy, needs optimized asset |

## Pipeline
1. **Keyframes**: generate 2-4 hero stills with an image model (same seed/style, consistent lighting). Realism cues: shallow depth of field, film grain, volumetric haze, motivated light, dark neutral palette with ONE accent colour.
2. **Footage**: image-to-video between keyframes (start frame + end frame) with a video model, 5-10 s, slow camera move. Or render a Blender turntable (see `photoreal-3d-pipeline:photoreal-blender`).
3. **Extract frames** (aim 90-180 frames, 1600px wide, WebP):
   ```bash
   ffmpeg -i hero.mp4 -vf "fps=24,scale=1600:-2" -c:v libwebp -quality 70 frames/f_%04d.webp
   ```
   Budget: aim under ~6 MB on mobile (120 noisy 1600px frames measured 8 MB, so lower quality/frame count or width for busy footage); serve a 800px set via `matchMedia`.
4. **Bind to scroll** (Lenis + GSAP ScrollTrigger, canvas draw):
   ```js
   gsap.registerPlugin(ScrollTrigger);
   const lenis = new Lenis(); lenis.on('scroll', ScrollTrigger.update);
   gsap.ticker.add(t => lenis.raf(t * 1000)); gsap.ticker.lagSmoothing(0);
   const N = 120, imgs = Array.from({length:N}, (_, i) => { const im = new Image(); im.src = `frames/f_${String(i+1).padStart(4,'0')}.webp`; return im; });
   canvas.width = innerWidth * Math.min(devicePixelRatio, 2); canvas.height = innerHeight * Math.min(devicePixelRatio, 2);
   const ctx = canvas.getContext('2d'), st = { f: 0 };
   const draw = () => { const im = imgs[Math.round(st.f)]; if (im?.complete && im.naturalWidth) { /* cover-fit */ const r = Math.max(canvas.width/im.width, canvas.height/im.height); ctx.drawImage(im, (canvas.width-im.width*r)/2, (canvas.height-im.height*r)/2, im.width*r, im.height*r); } };
   gsap.to(st, { f: N-1, ease: 'none', onUpdate: draw,
     scrollTrigger: { trigger: '.hero', start: 'top top', end: '+=400%', scrub: 0.5, pin: true } });
   ```
   Load frame 0 first and show it immediately; stream the rest. Size canvas to `devicePixelRatio` (cap at 2).
5. **Choreograph text over footage** (this sells the effect): big uppercase headline, tight tracking, white on dark overlay (`linear-gradient` scrim, ~40%). Reveal copy at scroll thresholds, use `scrub` timelines with opacity+translateY, one beat per 100-150vh of scroll. Add a scroll cue and a minimal glass nav pill.
6. **Fallbacks**: `prefers-reduced-motion` → show the final still, no pin. Provide `<noscript>` poster.

## What MotionSites-style pages actually are (observed from public material only)
Evidence: public preview images and clips, their own site (a Vite + React app), image hosts named after an AI generator, and templates offered for AI site builders. I have NOT seen their paid prompts or template code, so treat this as an informed reading, not a copy of their method.
- **Realism is in the footage, not the code.** Heroes are ~10 s, 24 fps, H.264 loops of one calm, richly lit subject (a flower on water, a meadow, a train seen from above), made with AI image-to-video or stock footage.
- **The page is thin**: full-bleed `<video autoplay muted loop playsinline>`, a dark scrim, huge uppercase type, a glass nav pill, one accent colour, a couple of scroll beats.
- **The prompt is the product**: a long structured spec for an AI site builder (layout, type pairing, colours, motion). Write the same kind of spec, see "Spec anatomy".

## Technique A2: video-backed hero (no JS)
```html
<video autoplay muted loop playsinline preload="auto" poster="frame0.webp" src="hero.mp4"></video>
```
Encode small: `ffmpeg -i in.mp4 -an -c:v libx264 -crf 26 -preset slow -vf scale=1920:-2 -movflags +faststart hero.mp4` (keep a 1280 version for phones). Always give a `poster` so the first paint is the hero, and let `prefers-reduced-motion` show only the poster. Make loops seamless by generating the clip with start frame = end frame.

## Technique A3: scrub a video with scroll (fewer files than frame sequences)
Re-encode so every frame is a keyframe, or seeking stutters: `ffmpeg -i in.mp4 -an -c:v libx264 -g 1 -crf 23 -vf scale=1280:-2 -movflags +faststart scrub.mp4` (WebM: `-c:v libvpx-vp9 -g 1 -b:v 0 -crf 34`). Files get big (all-intra), so keep clips short (5-10 s) and narrow.
```js
const v = document.querySelector('video'); let cur = 0, dur = 0;
v.addEventListener('loadedmetadata', () => { dur = v.duration; v.pause(); });
(function tick() {
  const p = Math.min(1, Math.max(0, scrollY / (hero.offsetHeight - innerHeight)));
  cur += (p * dur - cur) * 0.12;                                 // ease so it feels smooth
  if (dur && !v.seeking && Math.abs(v.currentTime - cur) > 1/60) v.currentTime = cur; // one seek at a time
  requestAnimationFrame(tick);
})();
```
Tested: playhead went 0 -> 2.49 -> 4.99 s of a 5 s clip at 0/50/100% scroll. Pitfalls found: the server MUST support HTTP Range requests (Python's `http.server` does not, so `currentTime` snaps back to 0; `npx http-server`, nginx and every CDN are fine); iOS Safari is stricter, so prefer the frame sequence (technique A) when phones matter most.

## Spec anatomy (what to hand an AI site builder, or follow yourself)
1. Subject + mood in one line. 2. Hero asset: how it was generated, duration, loop or scrub. 3. Palette: background, text, one accent. 4. Type: display face + body face, sizes, tracking. 5. Layout of each scroll beat with the exact copy. 6. Motion: what moves, when, easing, durations. 7. Nav and CTA. 8. Performance and fallback rules (poster, reduced motion, mobile asset).

## Technique B: particle / point-cloud subject (e.g. "Kin" head)
- Source: a GLB/scan, or a depth map of a portrait → sample N≈150k points (`MeshSurfaceSampler` or depth→xyz).
- `THREE.Points` + `ShaderMaterial`: size attenuation, additive blending, per-point random for twinkle, soft round sprite.
- Cursor: pass `uMouse` (raycast to plane) and push points away within a radius, spring back with `mix` over time.
- Behind it: huge pixel/mono display type that the subject partially occludes (put text in DOM behind a transparent canvas). Bottom glow gradient in the accent colour.
- Scroll: map progress to `uProgress` to dissolve/assemble the cloud.

## Technique C: live GLB camera path
Use `photoreal-3d-pipeline:blender-web-export` then `web-3d-embed`; keyframe the camera with `theatre-motion:theatre-scroll` or a `CatmullRomCurve3` sampled by scroll progress. HDRI lighting, ACES tone mapping, contact shadows.

## Realism checklist
- One art-directed palette; never default blue-purple gradients.
- Grain + vignette overlay (SVG noise, 4-6% opacity).
- Motion eased and slow; scrub smoothing 0.3-0.8.
- Compress hard; test on throttled mobile. LCP = frame 0 as `<img>` with preload.
- Don't ship UI copy with filler or AI-sounding phrases.

## Related skills to chain
`premium-design-guard:premium-design` (layout/type polish), `ai-giveaway-guard:avoid-ai-giveaways` (copy), `photoreal-3d-pipeline:*` (assets).
