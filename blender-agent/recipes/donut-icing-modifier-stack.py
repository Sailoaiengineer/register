import bmesh, random
from mathutils import Vector
# Blender Guru donut (5.0): torus -> duplicate -> delete bottom half -> Shrinkwrap, Solidify(offset 1), Subsurf in THAT order.
def build(bpy):
    bpy.ops.mesh.primitive_torus_add(major_radius=0.1, minor_radius=0.057, major_segments=48, minor_segments=18)
    d = bpy.context.object; d.name = "donut"; bpy.ops.object.shade_smooth()
    ic = d.copy(); ic.data = d.data.copy(); ic.name = "icing"; bpy.context.collection.objects.link(ic)
    bm = bmesh.new(); bm.from_mesh(ic.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_center_median().z < 0], context="FACES")
    rng = random.Random(3)  # "imperfection is the digital perfection": ragged edge
    for v in bm.verts:
        if any(e.is_boundary for e in v.link_edges):
            v.co.z -= rng.uniform(0, 0.02)
    bm.to_mesh(ic.data); bm.free()
    sw = ic.modifiers.new("Shrinkwrap", "SHRINKWRAP"); sw.target = d
    so = ic.modifiers.new("Solidify", "SOLIDIFY"); so.thickness = 0.004; so.offset = 1
    ic.modifiers.new("Subsurf", "SUBSURF").levels = 2
    assert [m.type for m in ic.modifiers] == ["SHRINKWRAP", "SOLIDIFY", "SUBSURF"]
    for ob, col, sss in ((d, (0.55, 0.32, 0.12, 1), 0.05), (ic, (0.9, 0.35, 0.5, 1), 0.02)):
        m = bpy.data.materials.new(ob.name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = col; b.inputs["Roughness"].default_value = 0.35
        b.inputs["Subsurface Weight"].default_value = 1  # tutorial: weight 1, all three radius channels 1
        b.inputs["Subsurface Radius"].default_value = (1, 1, 1); b.inputs["Subsurface Scale"].default_value = sss
        ob.data.materials.append(m)
    bpy.ops.mesh.primitive_plane_add(size=1)
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")); bpy.context.scene.collection.objects.link(cam)
    cam.location, cam.rotation_euler = (0, -0.4, 0.3), (0.93, 0, 0); bpy.context.scene.camera = cam
    sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN")); bpy.context.scene.collection.objects.link(sun)
    sun.data.energy = 1.5; sun.rotation_euler = (0.7, 0.2, 0.6)
