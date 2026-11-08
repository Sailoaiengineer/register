import random, math
from mathutils import Euler, Quaternion, Vector
# Python stand-in for 5.0's Scatter on Surface: pick-instance from a collection, random spin, min distance, mask, one shared random-colour material.
def build(bpy):
    bpy.ops.mesh.primitive_torus_add(major_radius=0.1, minor_radius=0.057, major_segments=48, minor_segments=18)
    surf = bpy.context.object; bpy.ops.object.shade_smooth()
    sm = bpy.data.materials.new("icing"); sm.use_nodes = True; sm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.8, 0.2, 0.35, 1); surf.data.materials.append(sm)
    mat = bpy.data.materials.new("Sprinkles"); mat.use_nodes = True; nt = mat.node_tree; b = nt.nodes["Principled BSDF"]
    oi = nt.nodes.new("ShaderNodeObjectInfo"); cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.interpolation = "CONSTANT"  # constant stops = a few solid colours, not a gradient
    cr.color_ramp.elements[0].color = (0.35, 0.8, 0.8, 1)
    for pos, c in ((0.3, (0.55, 0.35, 0.8, 1)), (0.6, (0.95, 0.5, 0.7, 1)), (0.85, (0.95, 0.9, 0.55, 1))):
        cr.color_ramp.elements.new(pos).color = c
    nt.links.new(oi.outputs["Random"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.35; b.inputs["Subsurface Weight"].default_value = 1; b.inputs["Subsurface Scale"].default_value = 0.001
    variants = []
    for i, depth in enumerate((0.010, 0.013, 0.016)):  # different lengths so repetition doesn't read as fake
        bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.0018, depth=depth)
        v = bpy.context.object; v.name = f"sprinkle_{i}"; v.data.materials.append(mat); bpy.ops.object.shade_smooth()
        v.modifiers.new("Subsurf", "SUBSURF").levels = 1; v.hide_render = True; v.hide_viewport = True; variants.append(v)
    rng = random.Random(7); me = surf.data; me.calc_loop_triangles()
    tris = [t for t in me.loop_triangles if t.normal.z > 0.35]  # mask = "weight paint" top only
    weights = [t.area for t in tris]; placed = []
    for _ in range(4000):
        if len(placed) >= 250: break
        t = rng.choices(tris, weights)[0]; a, bb = rng.random(), rng.random()
        if a + bb > 1: a, bb = 1 - a, 1 - bb
        vs = [me.vertices[i].co for i in t.vertices]; p = vs[0] + a * (vs[1] - vs[0]) + bb * (vs[2] - vs[0])
        if any((p - q).length < 0.006 for q in placed): continue  # "disk" min distance
        placed.append(p)
        o = bpy.data.objects.new("s", rng.choice(variants).data); bpy.context.collection.objects.link(o)
        n = t.normal
        q = Quaternion(n, rng.uniform(0, 2 * math.pi)) @ n.to_track_quat("Z", "Y") @ Euler((math.pi / 2, 0, 0)).to_quaternion()
        o.rotation_mode = "QUATERNION"; o.rotation_quaternion = q; o.location = p + n * 0.0015
    assert len(placed) > 100, len(placed)
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")); bpy.context.scene.collection.objects.link(cam)
    cam.location, cam.rotation_euler = (0, -0.3, 0.32), (0.8, 0, 0); bpy.context.scene.camera = cam
    sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN")); bpy.context.scene.collection.objects.link(sun)
    sun.data.energy = 1.5; sun.rotation_euler = (0.7, 0.2, 0.6)
