import math
from mathutils import Vector
# Modern 3-storey villa (reference photo): white volumes, thick dark cantilever slabs, glass rail balcony + roof terrace, glass entry, boundary wall with dark gates, palms, dusk.
def build(bpy):
    sc = bpy.context.scene
    def mat(name, col, rough=0.5, metal=0, emit=0, glass=False):
        m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = col; b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
        if emit: b.inputs["Emission Color"].default_value = col; b.inputs["Emission Strength"].default_value = emit
        if glass: b.inputs["Transmission Weight"].default_value = 1; b.inputs["Roughness"].default_value = 0.03; b.inputs["IOR"].default_value = 1.45
        return m
    white, dark, glass = mat("white", (0.9, 0.9, 0.92, 1), 0.7), mat("dark", (0.07, 0.075, 0.085, 1), 0.45), mat("glass", (0.6, 0.75, 0.85, 1), glass=True)
    warm, pave, green = mat("warm", (1, 0.65, 0.3, 1), emit=14), mat("pave", (0.35, 0.35, 0.38, 1), 0.8), mat("leaf", (0.08, 0.3, 0.1, 1), 0.6)
    def box(name, x0, x1, y0, y1, z0, z1, m, bevel=0):
        bpy.ops.mesh.primitive_cube_add(size=1, location=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
        o = bpy.context.object; o.name = name; o.scale = (x1 - x0, y1 - y0, z1 - z0); bpy.ops.object.transform_apply(scale=True)
        o.data.materials.append(m)
        if bevel: o.modifiers.new("Bevel", "BEVEL").width = bevel; o.modifiers["Bevel"].segments = 4
        return o
    # volumes (x right, y toward back, z up); front faces y = -4.5
    box("ground", -6, 6, -4.5, 4.5, 0, 3, white)
    box("floor1", -6, 4, -4.5, 4.5, 3.4, 6.4, white)
    box("floor2", -3.5, 3.5, -3.5, 3.5, 6.8, 9.6, white)
    box("tower", 2.5, 5.5, 0, 4.5, 6.4, 10.4, white)
    # dark cantilever slabs, rounded edges, overhanging the front
    box("slab_g", -7, 7, -6.2, 5.2, 3, 3.4, dark, 0.12)
    box("slab_1", -7, 6.5, -6.0, 5.2, 6.4, 6.8, dark, 0.12)
    box("slab_roof", -4.2, 4.2, -4.6, 4.5, 9.6, 10.0, dark, 0.12)
    # glazing: entry, floor1 windows, floor2 windows
    box("g_entry", -2.5, 1.5, -4.55, -4.4, 0.3, 2.8, glass)
    box("g_f1a", -5, -2, -4.55, -4.4, 3.9, 5.8, glass); box("g_f1b", 0.5, 3.2, -4.55, -4.4, 3.9, 5.8, glass)
    box("g_f2", -2.8, 2.8, -3.55, -3.4, 7.2, 9.2, glass)
    # balcony + roof terrace glass rails
    box("rail_bal", -6.8, -1, -6.0, -5.9, 3.4, 4.5, glass); box("rail_roof", -4.2, 4.2, -4.6, -4.5, 10.0, 11.0, glass)
    box("rail_side", -4.2, -4.1, -4.6, 4.5, 10.0, 11.0, glass)
    # warm downlights under the slabs + lit interior
    for x in (-5, -2.5, 0, 2.5, 5):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.12, depth=0.04, location=(x, -5.2, 2.97)); bpy.context.object.data.materials.append(warm)
    box("interior_glow", -2.4, 1.4, -4.3, -4.2, 0.4, 2.7, warm)
    # boundary wall, pillars, dark gates
    box("wall", -9, 9, -12, -11.8, 0, 1.0, white)
    for x in (-9, -3, 3, 9): box("pillar", x - .25, x + .25, -12.1, -11.7, 0, 1.5, white)
    box("gate_l", -2.7, -0.1, -12.05, -11.85, 0, 1.3, dark); box("gate_r", 0.1, 2.7, -12.05, -11.85, 0, 1.3, dark)
    box("drive", -9, 9, -11.7, -4.5, -0.05, 0.02, pave); box("lawn", -30, 30, -30, 30, -0.1, -0.05, mat("ground", (0.15, 0.2, 0.12, 1), 0.9))
    # palms: tapered trunk + drooping fronds
    for (px, py, h) in ((-8, -9.5, 5.5), (8.5, -9, 6.5), (7, -7, 5)):
        bpy.ops.mesh.primitive_cone_add(radius1=0.14, radius2=0.08, depth=h, location=(px, py, h / 2)); bpy.context.object.data.materials.append(mat("trunk", (0.25, 0.2, 0.15, 1), 0.8))
        for k in range(12):
            a = k * 2 * math.pi / 12
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.7, location=(px + math.cos(a) * 1.2, py + math.sin(a) * 1.2, h - 0.3))
            f = bpy.context.object; f.scale = (1.7, 0.22, 0.05); f.rotation_euler = (0, math.radians(25), a); f.data.materials.append(green)
    # dusk world + cool fill + camera
    w = bpy.data.worlds.new("dusk"); w.use_nodes = True; bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.35, 0.42, 0.7, 1); bg.inputs["Strength"].default_value = 0.9; sc.world = w
    sun = bpy.data.objects.new("moon", bpy.data.lights.new("moon", "SUN")); sc.collection.objects.link(sun)
    sun.data.energy = 0.7; sun.data.color = (0.6, 0.7, 1); sun.rotation_euler = (math.radians(55), 0, math.radians(-35))
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")); sc.collection.objects.link(cam)
    cam.location = (19, -27, 8); cam.data.lens = 28
    cam.rotation_euler = (Vector((0, 0, 4.5)) - cam.location).to_track_quat("-Z", "Y").to_euler(); sc.camera = cam
    assert len([o for o in sc.objects if o.type == "MESH"]) > 30
