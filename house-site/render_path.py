"""Render the villa camera move to PNG frames. usage: python3 render_path.py OUT_DIR N [first last]"""
import math, runpy, sys, time
import bpy
from mathutils import Vector
out, N = sys.argv[1], int(sys.argv[2]); first = int(sys.argv[3]) if len(sys.argv) > 3 else 1; last = int(sys.argv[4]) if len(sys.argv) > 4 else N
bpy.ops.wm.read_factory_settings(use_empty=True)
runpy.run_path("/home/user/register/blender-agent/recipes/modern-villa-realistic.py")["build"](bpy)
sc = bpy.context.scene; cam = sc.camera
sc.render.engine = "CYCLES"; sc.cycles.samples = 24; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
cam.data.dof.use_dof = False  # focus shifts as the camera moves; wide aperture look comes from the sky and light instead
for i in range(first, last + 1):
    t = (i - 1) / (N - 1); e = t * t * (3 - 2 * t)
    r = 25 - 10 * e; th = math.radians(-128 + 52 * e)  # arc from front-left toward the front, pushing in
    cam.location = Vector((1 + r * math.cos(th), -1 + r * math.sin(th), 2.8 + 1.8 * e))
    aim = Vector((1, -1, 5.6)).lerp(Vector((0.5, -2, 5.0)), e)
    cam.rotation_euler = (aim - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = f"{out}/f_{i:04d}.png"; t0 = time.time(); bpy.ops.render.render(write_still=True); print(i, round(time.time() - t0, 1), flush=True)
