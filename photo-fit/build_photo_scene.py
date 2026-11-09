"""Rebuild a photo as a 2.5D Blender scene: each pixel becomes a vertex pushed out to its estimated distance
(Depth Anything V2 relative depth), photo projected back from the original camera as an unlit emission texture.
usage: python3 build_photo_scene.py OUT_DIR N_FRAMES [first last]"""
import math, sys, time
import numpy as np, cv2, bpy
from PIL import Image

import os
LATERAL = float(os.environ.get("PB_LATERAL", 1.6))   # camera slides from -LATERAL to +LATERAL metres
PUSH = float(os.environ.get("PB_PUSH", 3.5))          # and dollies forward this many metres
ZOOM = float(os.environ.get("PB_ZOOM", 1.45))         # crop-in factor: margin of photo kept around the frame so the move never shows its edge
HFOV = 60.0                      # assumed: the photo has no EXIF; a wrong value only warps perspective slightly
NEAR, FAR = 9.0, 140.0           # metres: nearest foreground tree and sky; the building lands ~25-35 m, a plausible villa distance
out, N = sys.argv[1], int(sys.argv[2]); first = int(sys.argv[3]) if len(sys.argv) > 3 else 1; last = int(sys.argv[4]) if len(sys.argv) > 4 else N

im = Image.open("ref.jpg").convert("RGB"); W, H = im.size
TEXFILE = "ref_blend.png"   # 60% AI 4x upscale (Swin2SR, upscale.py) + 40% plain bicubic: crisp but keeps photographic grain; the AI part invents small details
d = np.load("depth_raw.npy").astype(np.float32)
UP = 2; d = cv2.resize(d, (W * UP, H * UP), interpolation=cv2.INTER_CUBIC)   # finer mesh so object edges are not stair-stepped
d = cv2.bilateralFilter(d, 9, 0.25, 9)                                     # calm depth noise, keep edges
dn = np.clip((d - d.min()) / (d.max() - d.min()), 0, 1)                    # 0 = sky, 1 = nearest
inv = dn * (1 / NEAR - 1 / FAR) + 1 / FAR; Z = 1 / inv                      # relative disparity -> metres
f = (W / 2) / math.tan(math.radians(HFOV / 2)); cx, cy = W / 2, H / 2

bpy.ops.wm.read_factory_settings(use_empty=True)
W2, H2 = W * UP, H * UP
us, vs = np.meshgrid(np.arange(W2) / UP, np.arange(H2) / UP)
X = (us - cx) / f * Z; Yw = Z; Zw = (cy - vs) / f * Z
verts = np.stack([X, Yw, Zw], -1).reshape(-1, 3).astype(np.float32)
idx = np.arange(W2 * H2).reshape(H2, W2)
a, b, c, e = idx[:-1, :-1].ravel(), idx[:-1, 1:].ravel(), idx[1:, 1:].ravel(), idx[1:, :-1].ravel()
quads = np.stack([a, e, c, b], -1)
me = bpy.data.meshes.new("photo"); me.vertices.add(len(verts)); me.vertices.foreach_set("co", verts.ravel())
me.loops.add(len(quads) * 4); me.loops.foreach_set("vertex_index", quads.ravel())
me.polygons.add(len(quads)); me.polygons.foreach_set("loop_start", np.arange(len(quads), dtype=np.int32) * 4); me.polygons.foreach_set("loop_total", np.full(len(quads), 4, np.int32))
me.update(); uvl = me.uv_layers.new(name="UV")
uv = np.stack([us / (W - 1 / UP), 1 - vs / (H - 1 / UP)], -1).reshape(-1, 2).astype(np.float32)
uvl.data.foreach_set("uv", uv[quads.ravel()].ravel())
ob = bpy.data.objects.new("photo", me); bpy.context.scene.collection.objects.link(ob)
m = bpy.data.materials.new("photo"); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = bpy.data.images.load(bpy.path.abspath("//ref_x3.png") if False else __import__("os").path.abspath(TEXFILE)); tx.interpolation = "Cubic"
em = nt.nodes.new("ShaderNodeEmission"); o = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(tx.outputs["Color"], em.inputs["Color"]); nt.links.new(em.outputs["Emission"], o.inputs["Surface"]); me.materials.append(m)

sc = bpy.context.scene; sc.render.engine = "CYCLES"; sc.cycles.samples = 4; sc.cycles.use_denoising = False
sc.render.resolution_x = sc.render.resolution_y = 1200
sc.view_settings.view_transform = "Standard"; sc.view_settings.look = "None"   # no tone mapping: reproduce the photo's own colours
bpy.ops.world.new(); sc.world = bpy.data.worlds[-1]; sc.world.use_nodes = True
top = np.asarray(im, float)[:12].reshape(-1, 3).mean(0) / 255; lin = np.where(top <= 0.04045, top / 12.92, ((top + 0.055) / 1.055) ** 2.4)
bg = sc.world.node_tree.nodes["Background"]; bg.inputs["Color"].default_value = (*lin, 1); bg.inputs["Strength"].default_value = 1.0   # sky colour beyond the photo's top edge
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.sensor_fit = "HORIZONTAL"; cam.data.sensor_width = 36; cam.data.lens = f / W * 36 * ZOOM   # zoom in: leaves a margin of photo around the frame so the move never shows its edge
tgt = np.array([0.0, 28.0, 3.0])                                          # look-at point: the house, so the orbit pivots around it
for i in range(first, last + 1):
    t = (i - 1) / max(N - 1, 1); e_ = t * t * (3 - 2 * t)
    pos = np.array([(-LATERAL + 2 * LATERAL * e_) if N > 1 else 0.0, PUSH * e_ if N > 1 else 0.0, 0.0])
    cam.location = pos
    from mathutils import Vector
    aim = Vector((0, 1, 0)).lerp((Vector(tgt) - Vector(pos)).normalized(), 0.5)   # half-way between straight ahead and the house
    cam.rotation_euler = aim.to_track_quat("-Z", "Y").to_euler()
    if N == 1: cam.rotation_euler = (math.pi / 2, 0, 0)                    # exact original view for the fit check
    sc.render.filepath = f"{out}/f_{i:04d}.png"; t0 = time.time(); bpy.ops.render.render(write_still=True); print(i, round(time.time() - t0, 1), flush=True)
