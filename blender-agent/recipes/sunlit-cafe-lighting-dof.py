import math
# Sunlit-cafe lighting from the tutorial: sun + big-radius blue sky + white bounce, blockers as fake window, DOF on the subject, Eevee quality settings.
def build(bpy):
    sc = bpy.context.scene
    bpy.ops.mesh.primitive_plane_add(size=3); bpy.context.object.name = "table"
    bpy.ops.mesh.primitive_torus_add(major_radius=0.1, minor_radius=0.057, location=(0, 0, 0.057)); sub = bpy.context.object; sub.name = "donut"; bpy.ops.object.shade_smooth()
    bpy.ops.mesh.primitive_cylinder_add(radius=0.07, depth=0.1, location=(0.25, 0.25, 0.05)); bpy.ops.object.shade_smooth()
    def light(name, kind, energy, rot=None, loc=None, color=(1, 1, 1), radius=None):
        L = bpy.data.lights.new(name, kind); L.energy = energy; L.color = color
        if radius is not None: L.shadow_soft_size = radius  # radius = shadow softness
        o = bpy.data.objects.new(name, L); sc.collection.objects.link(o)
        if rot: o.rotation_euler = rot
        if loc: o.location = loc
        return o
    sun = light("sun", "SUN", 3, rot=(math.radians(60), 0, math.radians(35)), color=(1, 0.85, 0.65))  # only rotation matters for a sun
    light("sky", "POINT", 40, loc=(-1.0, -1.0, 1.5), color=(0.6, 0.75, 1), radius=0.8)             # far + large = soft skylight
    light("indoor bounce", "POINT", 15, loc=(0.9, -0.8, 0.5), radius=0.5)                             # fills the dark side
    for loc, rot in (((-0.9, 0.6, 0.8), (math.radians(90), 0, 0)), ((-0.8, 0.0, 0.8), (math.radians(90), 0, math.radians(90)))):
        bpy.ops.mesh.primitive_plane_add(size=0.5, location=loc, rotation=rot); bpy.context.object.name = "blocker"  # shadow-casting window frame
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")); sc.collection.objects.link(cam)
    cam.location, cam.rotation_euler = (0, -0.6, 0.4), (1.0, 0, 0); sc.camera = cam
    cam.data.dof.use_dof = True; cam.data.dof.focus_object = sub; cam.data.dof.aperture_fstop = 2.0
    for attr, val in (("use_raytracing", True), ("shadow_ray_count", 4), ("shadow_step_count", 16)):  # Eevee: names vary by version, so guarded
        if hasattr(sc.eevee, attr): setattr(sc.eevee, attr, val)
    try: sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "Medium High Contrast"
    except TypeError: pass
    assert cam.data.dof.use_dof and len([o for o in sc.objects if o.type == "LIGHT"]) == 3
