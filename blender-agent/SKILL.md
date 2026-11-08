---
name: blender-master
description: Build, edit or automate Blender scenes with bpy scripts and learn new techniques from tutorial videos. Use whenever the user asks for anything in Blender (modeling, materials, lighting, animation, rendering), says "teach/learn from this video/tutorial", or wants to grow the Blender recipe library, even if they don't say "recipe".
---

# Blender master

Claude does not retrain. "Learning" here means: turn a tutorial into a bpy recipe, prove it renders, and keep it in `recipes/` so later tasks reuse it. Only recipes that pass verification are stored, so the library never fills with broken guesses.

All commands run from this folder: `python3 ba.py <cmd>` (needs `pip install bpy pillow`).

## Doing a task
1. `python3 ba.py search "<keywords>"`. Read any matching `recipes/<name>.py` and adapt it instead of starting cold.
2. Write `build(bpy)` in a scratch file. Recipes build geometry/materials only; the harness resets the scene and adds a default camera and sun if missing.
3. `python3 ba.py verify scratch.py`, then LOOK at the PNG it names. The check only proves it ran, has meshes and isn't blank; it cannot tell good from ugly. Fix lighting, scale and materials until it looks right.
4. Deliver the script (and the render) to the user.

## Learning from a video
1. `python3 ba.py ingest <youtube-url|video file|transcript.txt> --name <topic>` writes `lessons/<topic>.json` (transcript, key frames, OCR when available). YouTube blocks cloud servers; run this on the user's machine, or ingest a downloaded file or pasted transcript.
2. Read the lesson. List the concrete steps and values (modifiers, node setups, shortcuts become `bpy.ops`/data API calls). Ignore chatter and UI navigation.
3. Translate to a recipe, `verify`, view the render, iterate.
4. `python3 ba.py save recipe.py --name <slug> --tags a,b,c --does "<one line>" --source <video url>`. Refused if verification fails.
5. Tell the user what was learned and any step you could not reproduce.

## Rules that keep it honest
- Prefer the data API (`bpy.data`, node trees) over `bpy.ops` that depends on UI context; ops fail headless.
- Never claim a technique is learned until its recipe is saved.
- Photoreal needs more than this loop: see `photoreal-3d-pipeline:photoreal-blender` and `blender-web-export` for lighting/HDRI/export.
