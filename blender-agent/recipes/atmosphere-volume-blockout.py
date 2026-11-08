def build(bpy):
    # blockout: plane + cubes at human scale (1 unit = 1 m), then a Principled Volume cube for atmosphere
    bpy.ops.mesh.primitive_plane_add(size=40)
    for x, h in [(-4, 3), (0, 5), (5, 2)]:
        bpy.ops.mesh.primitive_cube_add(size=2, location=(x, 6, h))
        bpy.context.object.scale = (1.5, 1.5, h)
        bpy.context.object.location.z = h
    bpy.ops.mesh.primitive_cube_add(size=40, location=(0, 0, 10))
    fog = bpy.context.object
    m = bpy.data.materials.new("Fog"); m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    vol, out = nt.nodes.new("ShaderNodeVolumePrincipled"), nt.nodes.new("ShaderNodeOutputMaterial")
    vol.inputs["Density"].default_value = 0.03
    nt.links.new(vol.outputs["Volume"], out.inputs["Volume"])
    fog.data.materials.append(m)
    fog.display_type = "WIRE"  # viewport only; renders as volume
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")); bpy.context.scene.collection.objects.link(cam)
    cam.location, cam.rotation_euler = (0, -16, 2.5), (1.5, 0, 0)  # eye height, looking down +Y at the blocks
    bpy.context.scene.camera = cam
    sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN")); bpy.context.scene.collection.objects.link(sun)
    sun.data.energy = 4; sun.rotation_euler = (0.9, 0.3, 0.5)
