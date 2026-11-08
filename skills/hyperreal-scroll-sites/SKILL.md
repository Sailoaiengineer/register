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
   Budget: under ~6 MB total mobile; serve a 800px set via `matchMedia`.
4. **Bind to scroll** (Lenis + GSAP ScrollTrigger, canvas draw):
   ```js
   gsap.registerPlugin(ScrollTrigger);
   const lenis = new Lenis(); lenis.on('scroll', ScrollTrigger.update);
   gsap.ticker.add(t => lenis.raf(t * 1000)); gsap.ticker.lagSmoothing(0);
   const N = 120, imgs = Array.from({length:N}, (_, i) => { const im = new Image(); im.src = `frames/f_${String(i+1).padStart(4,'0')}.webp`; return im; });
   const ctx = canvas.getContext('2d'), st = { f: 0 };
   const draw = () => { const im = imgs[Math.round(st.f)]; if (im?.complete) { /* cover-fit */ const r = Math.max(canvas.width/im.width, canvas.height/im.height); ctx.drawImage(im, (canvas.width-im.width*r)/2, (canvas.height-im.height*r)/2, im.width*r, im.height*r); } };
   gsap.to(st, { f: N-1, ease: 'none', onUpdate: draw,
     scrollTrigger: { trigger: '.hero', start: 'top top', end: '+=400%', scrub: 0.5, pin: true } });
   ```
   Load frame 0 first and show it immediately; stream the rest. Size canvas to `devicePixelRatio` (cap at 2).
5. **Choreograph text over footage** (this sells the effect): big uppercase headline, tight tracking, white on dark overlay (`linear-gradient` scrim, ~40%). Reveal copy at scroll thresholds, use `scrub` timelines with opacity+translateY, one beat per 100-150vh of scroll. Add a scroll cue and a minimal glass nav pill.
6. **Fallbacks**: `prefers-reduced-motion` → show the final still, no pin. Provide `<noscript>` poster.

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
