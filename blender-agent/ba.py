#!/usr/bin/env python3
"""blender-agent CLI: ingest tutorials, verify bpy recipes by rendering, keep only what works.
Needs: pip install bpy pillow ; for video URLs/files: node (npx mcp-video-analyzer) + yt-dlp."""
import argparse, json, os, re, shutil, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).parent
RECIPES, LESSONS, INDEX = HERE / "recipes", HERE / "lessons", HERE / "recipes" / "index.json"


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:60] or "item"


def load_index():
    return json.loads(INDEX.read_text()) if INDEX.exists() else {}


def _render_worker(script, out):
    """Runs inside a fresh process: reset scene, call build(), render, return stats."""
    import runpy, bpy
    bpy.ops.wm.read_factory_settings(use_empty=True)
    ns = runpy.run_path(script)
    if "build" not in ns:
        raise SystemExit("recipe must define build(bpy)")
    ns["build"](bpy)
    sc = bpy.context.scene
    if not sc.camera:  # default framing so a recipe need not set a camera
        cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
        sc.collection.objects.link(cam)
        cam.location = (6, -6, 4)
        cam.rotation_euler = (1.1, 0, 0.785)
        sc.camera = cam
    if not any(o.type == "LIGHT" for o in sc.objects):
        lt = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
        sc.collection.objects.link(lt)
        lt.rotation_euler = (0.8, 0.2, 0.6)
    sc.render.engine = "CYCLES"
    sc.cycles.samples = int(os.environ.get("BA_SAMPLES", 16))  # env raises quality for a closer look; default stays fast
    sc.render.resolution_x, sc.render.resolution_y = int(os.environ.get("BA_W", 320)), int(os.environ.get("BA_H", 240))
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print("OBJECTS", len([o for o in sc.objects if o.type == "MESH"]))


def verify(script, out=None):
    out = out or str(HERE / "last_render.png")
    t = time.time()
    p = subprocess.run([sys.executable, __file__, "_worker", str(script), out], capture_output=True, text=True, timeout=300)
    if p.returncode:
        return {"ok": False, "error": (p.stderr or p.stdout)[-1500:]}
    from PIL import Image, ImageStat
    sd = ImageStat.Stat(Image.open(out).convert("L")).stddev[0]
    meshes = int(re.search(r"OBJECTS (\d+)", p.stdout).group(1))
    # shortcut: "not blank + has meshes" is a smoke test, not a quality judge; look at the PNG too
    return {"ok": sd > 8 and meshes > 0, "contrast": round(sd, 1), "meshes": meshes, "seconds": round(time.time() - t, 1), "render": out}


def cmd_ingest(a):
    LESSONS.mkdir(exist_ok=True)
    src = a.source
    if Path(src).suffix == ".txt":
        data = {"source": src, "transcript": Path(src).read_text()}
    else:
        p = subprocess.run(["npx", "-y", "mcp-video-analyzer@latest", "analyze", src], capture_output=True, text=True)
        data = json.loads(p.stdout[p.stdout.index("{"):])
        if not data.get("transcript") and not data.get("frames"):
            sys.exit("ingest got nothing (blocked or no captions): " + "; ".join(data.get("warnings", []))[:300])
    f = LESSONS / f"{slug(a.name or Path(src).stem)}.json"
    f.write_text(json.dumps(data, indent=1))
    print("saved", f)


def cmd_verify(a):
    r = verify(a.script)
    print(json.dumps(r, indent=1))
    sys.exit(0 if r["ok"] else 1)


def cmd_save(a):
    r = verify(a.script)
    if not r["ok"]:
        sys.exit("not saved, verify failed: " + json.dumps(r))
    name = slug(a.name)
    shutil.copy(a.script, RECIPES / f"{name}.py")
    shutil.copy(r["render"], RECIPES / f"{name}.png")
    idx = load_index()
    idx[name] = {"tags": a.tags.split(","), "source": a.source, "does": a.does, "verified": r}
    INDEX.write_text(json.dumps(idx, indent=1))
    print("saved recipe", name)


def cmd_search(a):
    q = set(a.query.lower().split())
    hits = sorted(((len(q & set(re.findall(r"\w+", (k + " " + " ".join(v["tags"]) + " " + v["does"]).lower()))), k, v) for k, v in load_index().items()), reverse=True)
    for n, k, v in hits:
        if n:
            print(f"{k}  [{', '.join(v['tags'])}]  {v['does']}  -> recipes/{k}.py")


if __name__ == "__main__":
    if sys.argv[1:2] == ["_worker"]:
        _render_worker(sys.argv[2], sys.argv[3]); sys.exit()
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(required=True)
    s = sp.add_parser("ingest"); s.add_argument("source"); s.add_argument("--name"); s.set_defaults(f=cmd_ingest)
    s = sp.add_parser("verify"); s.add_argument("script"); s.set_defaults(f=cmd_verify)
    s = sp.add_parser("save"); s.add_argument("script"); s.add_argument("--name", required=True); s.add_argument("--tags", required=True)
    s.add_argument("--does", required=True); s.add_argument("--source", default="manual"); s.set_defaults(f=cmd_save)
    s = sp.add_parser("search"); s.add_argument("query"); s.set_defaults(f=cmd_search)
    a = ap.parse_args(); a.f(a)
