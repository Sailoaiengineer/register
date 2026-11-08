# Overview video: cloth sim for flags. Pin one edge with a vertex group, add a Wind force field, step frames, assert the free edge moved and the pinned edge did not.
def build(bpy):
    sc = bpy.context.scene
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=24, y_subdivisions=16, size=2, location=(0, 0, 2), rotation=(1.5708, 0, 0))
    fl = bpy.context.object; fl.name = "flag"; bpy.ops.object.shade_smooth(); me = fl.data
    minx = min(v.co.x for v in me.vertices)
    vg = fl.vertex_groups.new(name="pin"); vg.add([v.index for v in me.vertices if abs(v.co.x - minx) < 1e-4], 1.0, "REPLACE")
    cl = fl.modifiers.new("Cloth", "CLOTH"); cl.settings.vertex_group_mass = "pin"; cl.settings.quality = 8
    bpy.ops.object.effector_add(type="WIND", location=(-3, 0, 2), rotation=(0, 1.5708, 0)); wd = bpy.context.object; wd.field.strength = 600
    rest = {v.index: v.co.copy() for v in me.vertices}
    for f in range(1, 61): sc.frame_set(f)
    ev = fl.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
    pinned = [v.index for v in me.vertices if abs(v.co.x - minx) < 1e-4]
    free = max(range(len(ev.vertices)), key=lambda i: rest[i].x)
    moved = (ev.vertices[free].co - rest[free]).length
    assert moved > 0.2 and all((ev.vertices[i].co - rest[i]).length < 1e-3 for i in pinned), moved
    m = bpy.data.materials.new("cloth"); m.use_nodes = True; m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.8, 0.1, 0.1, 1); fl.data.materials.append(m)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.04, depth=4, location=(-1, 0, 1)); bpy.ops.mesh.primitive_plane_add(size=10)
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")); sc.collection.objects.link(cam)
    cam.location, cam.rotation_euler = (1, -5, 2.5), (1.35, 0, 0.1); sc.camera = cam
