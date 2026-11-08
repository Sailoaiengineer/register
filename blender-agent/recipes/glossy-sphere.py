def build(bpy):
    bpy.ops.mesh.primitive_plane_add(size=12)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.2, location=(0, 0, 1.2))
    bpy.ops.object.shade_smooth()
    sph = bpy.context.object
    m = bpy.data.materials.new("Glossy"); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.9, 0.25, 0.05, 1)
    b.inputs["Roughness"].default_value = 0.08
    sph.data.materials.append(m)
